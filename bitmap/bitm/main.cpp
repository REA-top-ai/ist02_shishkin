#include <iostream>
#include <fstream>
#include <string>
#include <vector>
#include <stdint.h>

using namespace std;

static unsigned short read_u16(const unsigned char* p) {
    return (unsigned short)(p[0] | (p[1] << 8));
}

static unsigned int read_u32(const unsigned char* p) {
    return (unsigned int)p[0] |
           ((unsigned int)p[1] << 8) |
           ((unsigned int)p[2] << 16) |
           ((unsigned int)p[3] << 24);
}

static int read_i32(const unsigned char* p) {
    return (int)read_u32(p);
}

struct RGB {
    int r, g, b;
    RGB() : r(0), g(0), b(0) {}
    RGB(int rr, int gg, int bb) : r(rr), g(gg), b(bb) {}
};

static int mask_shift(unsigned int mask) {
    int s = 0;
    if (mask == 0) return 0;
    while ((mask & 1U) == 0) {
        mask >>= 1;
        ++s;
    }
    return s;
}

static int mask_bits(unsigned int mask) {
    int n = 0;
    while (mask != 0) {
        n += (mask & 1U);
        mask >>= 1;
    }
    return n;
}

static int scale_to_8(unsigned int value, unsigned int mask) {
    if (mask == 0) return 0;
    int shift = mask_shift(mask);
    int bits = mask_bits(mask);
    unsigned int v = (value & mask) >> shift;
    unsigned int maxv = (1U << bits) - 1U;
    return (int)((v * 255U + maxv / 2U) / maxv);
}

static bool get_pixel(const vector<unsigned char>& data,
                      unsigned int pixel_offset,
                      int width, int height, int bpp,
                      unsigned int compression,
                      unsigned int red_mask,
                      unsigned int green_mask,
                      unsigned int blue_mask,
                      const vector<RGB>& palette,
                      int x, int y, RGB& color) {
    if (x < 0 || y < 0 || x >= width || y >= height) return false;

    int bytes_per_row;
    if (bpp == 4) {
        bytes_per_row = ((width + 1) / 2 + 3) & ~3;
    } else if (bpp == 8) {
        bytes_per_row = (width + 3) & ~3;
    } else {
        bytes_per_row = ((width * bpp + 31) / 32) * 4;
    }

    // Positive BMP height: rows are stored bottom-to-top.
    // Negative BMP height: rows are stored top-to-bottom.
    // This function receives the original signed height through caller-normalized y.
    int row = y;
    size_t pos = pixel_offset + (size_t)row * bytes_per_row;

    if (bpp == 24) {
        pos += (size_t)x * 3;
        if (pos + 2 >= data.size()) return false;
        color.b = data[pos];
        color.g = data[pos + 1];
        color.r = data[pos + 2];
        return true;
    }

    if (bpp == 32) {
        pos += (size_t)x * 4;
        if (pos + 3 >= data.size()) return false;
        unsigned int value = read_u32(&data[pos]);

        if (compression == 3) {
            color.r = scale_to_8(value, red_mask);
            color.g = scale_to_8(value, green_mask);
            color.b = scale_to_8(value, blue_mask);
        } else {
            color.b = data[pos];
            color.g = data[pos + 1];
            color.r = data[pos + 2];
        }
        return true;
    }

    if (bpp == 16) {
        pos += (size_t)x * 2;
        if (pos + 1 >= data.size()) return false;
        unsigned int value = read_u16(&data[pos]);
        color.r = scale_to_8(value, red_mask);
        color.g = scale_to_8(value, green_mask);
        color.b = scale_to_8(value, blue_mask);
        return true;
    }

    if (bpp == 8) {
        pos += (size_t)x;
        if (pos >= data.size()) return false;
        unsigned int index = data[pos];
        if (index >= palette.size()) return false;
        color = palette[index];
        return true;
    }

    if (bpp == 4) {
        pos += (size_t)(x / 2);
        if (pos >= data.size()) return false;
        unsigned int byte = data[pos];
        unsigned int index = (x % 2 == 0) ? (byte >> 4) : (byte & 0x0F);
        if (index >= palette.size()) return false;
        color = palette[index];
        return true;
    }

    return false;
}

int main(int argc, char** argv) {
    const char* path = argc > 1 ? argv[1] : "image/lena.bmp";

    ifstream file(path, ios::in | ios::binary);
    if (!file) {
        cerr << "Error: cannot open file: " << path << endl;
        return 1;
    }

    file.seekg(0, ios::end);
    streamoff file_size = file.tellg();
    file.seekg(0, ios::beg);

    if (file_size < 54) {
        cerr << "Error: file is too small to be a BMP file." << endl;
        return 1;
    }

    vector<unsigned char> data((size_t)file_size);
    file.read(reinterpret_cast<char*>(&data[0]), file_size);

    if (data[0] != 'B' || data[1] != 'M') {
        cerr << "Error: not a BMP file." << endl;
        return 1;
    }

    unsigned int declared_size = read_u32(&data[2]);
    unsigned int pixel_offset = read_u32(&data[10]);
    unsigned int dib_size = read_u32(&data[14]);
    int width = read_i32(&data[18]);
    int signed_height = read_i32(&data[22]);
    unsigned short planes = read_u16(&data[26]);
    unsigned short bpp = read_u16(&data[28]);
    unsigned int compression = read_u32(&data[30]);

    if (width <= 0 || signed_height == 0 || planes != 1) {
        cerr << "Error: unsupported BMP header." << endl;
        return 1;
    }

    int height = signed_height < 0 ? -signed_height : signed_height;
    bool top_down = signed_height < 0;

    // BMP color masks.
    unsigned int red_mask = 0;
    unsigned int green_mask = 0;
    unsigned int blue_mask = 0;

    if (bpp == 16 || (bpp == 32 && compression == 3)) {
        if (compression == 3) {
            if (dib_size >= 52) {
                red_mask = read_u32(&data[14 + 40]);
                green_mask = read_u32(&data[14 + 44]);
                blue_mask = read_u32(&data[14 + 48]);
            } else if (pixel_offset >= 66) {
                red_mask = read_u32(&data[54]);
                green_mask = read_u32(&data[58]);
                blue_mask = read_u32(&data[62]);
            }
        } else {
            // Standard BI_RGB 16-bit BMP: 5-5-5.
            red_mask = 0x7C00;
            green_mask = 0x03E0;
            blue_mask = 0x001F;
        }
    }

    // Palette for 4/8-bit BMP.
    vector<RGB> palette;
    if (bpp <= 8) {
        unsigned int colors_used = read_u32(&data[46]);
        unsigned int colors = colors_used != 0 ? colors_used : (1U << bpp);
        size_t palette_start = 14 + dib_size;

        if (palette_start + (size_t)colors * 4 > data.size()) {
            cerr << "Error: invalid BMP palette." << endl;
            return 1;
        }

        palette.resize(colors);
        unsigned int i;
        for (i = 0; i < colors; ++i) {
            const unsigned char* p = &data[palette_start + (size_t)i * 4];
            palette[i] = RGB(p[2], p[1], p[0]);
        }
    }

    cout << "BMP header" << endl;
    cout << "Signature: BM" << endl;
    cout << "File size: " << declared_size << " bytes" << endl;
    cout << "Width: " << width << endl;
    cout << "Height: " << height << endl;
    cout << "Bits per pixel: " << bpp << endl;
    cout << "Compression: " << compression << endl;
    cout << "Pixel data offset: " << pixel_offset << endl;
    cout << endl;

    // Convert image coordinates (top-to-bottom) to the physical BMP row.
    int top_row = top_down ? 0 : height - 1;
    int bottom_row = top_down ? height - 1 : 0;

    RGB top_left, top_right, bottom_left, bottom_right;

    bool ok =
        get_pixel(data, pixel_offset, width, height, bpp, compression,
                  red_mask, green_mask, blue_mask, palette,
                  0, top_row, top_left) &&
        get_pixel(data, pixel_offset, width, height, bpp, compression,
                  red_mask, green_mask, blue_mask, palette,
                  width - 1, top_row, top_right) &&
        get_pixel(data, pixel_offset, width, height, bpp, compression,
                  red_mask, green_mask, blue_mask, palette,
                  0, bottom_row, bottom_left) &&
        get_pixel(data, pixel_offset, width, height, bpp, compression,
                  red_mask, green_mask, blue_mask, palette,
                  width - 1, bottom_row, bottom_right);

    if (!ok) {
        cerr << "Error: unsupported BMP pixel format." << endl;
        return 1;
    }

    cout << "Top-left:     R: " << top_left.r
         << " G: " << top_left.g << " B: " << top_left.b << endl;

    cout << "Top-right:    R: " << top_right.r
         << " G: " << top_right.g << " B: " << top_right.b << endl;

    cout << "Bottom-left:  R: " << bottom_left.r
         << " G: " << bottom_left.g << " B: " << bottom_left.b << endl;

    cout << "Bottom-right: R: " << bottom_right.r
         << " G: " << bottom_right.g << " B: " << bottom_right.b << endl;

    return 0;
}
