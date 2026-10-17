#include <iostream>
#include <fstream>
#include <string>
#include <vector>
#include <algorithm>
#include <cmath>
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


struct Pixel {
    int R;
    int G;
    int B;
    double Y;

    Pixel() : R(0), G(0), B(0), Y(0.0) {}
    Pixel(int r, int g, int b) : R(r), G(g), B(b), Y(0.0) {
        CalculateY();
    }

    void CalculateY() {
        Y = 0.2126 * R + 0.7152 * G + 0.0722 * B;
    }
};

class Bitmap {
private:
    vector<Pixel> pixels;
    int width;
    int height;

    static int clamp255(int value) {
        if (value < 0) return 0;
        if (value > 255) return 255;
        return value;
    }

    int index(int x, int y) const {
        return y * width + x;
    }

    int roundedY(const Pixel& p) const {
        int value = (int)(p.Y + 0.5);
        if (value < 0) value = 0;
        if (value > 255) value = 255;
        return value;
    }

    void makeHistogram(const vector<Pixel>& image, char channel, unsigned long histogram[256]) const {
        int i;
        for (i = 0; i < 256; ++i) histogram[i] = 0;

        for (i = 0; i < (int)image.size(); ++i) {
            int value;
            if (channel == 'Y') value = (int)(image[i].Y + 0.5);
            else if (channel == 'R') value = image[i].R;
            else if (channel == 'G') value = image[i].G;
            else value = image[i].B;

            if (value < 0) value = 0;
            if (value > 255) value = 255;
            ++histogram[value];
        }
    }

    double meanFromHistogram(const unsigned long histogram[256], unsigned long count) const {
        if (count == 0) return 0.0;
        unsigned long sum = 0;
        int i;
        for (i = 0; i < 256; ++i) {
            sum += (unsigned long)i * histogram[i];
        }
        return (double)sum / (double)count;
    }

    int medianFromHistogram(const unsigned long histogram[256], unsigned long count) const {
        if (count == 0) return 0;
        unsigned long left = (count + 1) / 2;
        unsigned long right = (count + 2) / 2;
        unsigned long cumulative = 0;
        int first = 0;
        int second = 0;
        bool firstFound = false;
        int i;
        for (i = 0; i < 256; ++i) {
            cumulative += histogram[i];
            if (!firstFound && cumulative >= left) {
                first = i;
                firstFound = true;
            }
            if (cumulative >= right) {
                second = i;
                break;
            }
        }
        return (first + second) / 2;
    }

public:
    Bitmap() : width(0), height(0) {}

    bool Load(const char* path,
              unsigned int& declared_size,
              unsigned int& pixel_offset,
              unsigned int& dib_size,
              unsigned short& bpp,
              unsigned int& compression,
              bool& top_down) {
        ifstream file(path, ios::in | ios::binary);
        if (!file) return false;

        file.seekg(0, ios::end);
        streamoff file_size = file.tellg();
        file.seekg(0, ios::beg);

        if (file_size < 54) return false;

        vector<unsigned char> data((size_t)file_size);
        file.read(reinterpret_cast<char*>(&data[0]), file_size);
        if (!file) return false;

        if (data[0] != 'B' || data[1] != 'M') return false;

        declared_size = read_u32(&data[2]);
        pixel_offset = read_u32(&data[10]);
        dib_size = read_u32(&data[14]);
        width = read_i32(&data[18]);
        int signed_height = read_i32(&data[22]);
        unsigned short planes = read_u16(&data[26]);
        bpp = read_u16(&data[28]);
        compression = read_u32(&data[30]);

        if (width <= 0 || signed_height == 0 || planes != 1) return false;
        height = signed_height < 0 ? -signed_height : signed_height;
        top_down = signed_height < 0;

        unsigned int red_mask = 0;
        unsigned int green_mask = 0;
        unsigned int blue_mask = 0;

        if (bpp == 16 || (bpp == 32 && compression == 3)) {
            if (compression == 3) {
                if (dib_size >= 52 && 14 + dib_size <= data.size()) {
                    red_mask = read_u32(&data[54]);
                    green_mask = read_u32(&data[58]);
                    blue_mask = read_u32(&data[62]);
                } else if (pixel_offset >= 66 && 66 <= data.size()) {
                    red_mask = read_u32(&data[54]);
                    green_mask = read_u32(&data[58]);
                    blue_mask = read_u32(&data[62]);
                }
            } else {
                red_mask = 0x7C00;
                green_mask = 0x03E0;
                blue_mask = 0x001F;
            }
        }

        vector<RGB> palette;
        if (bpp <= 8) {
            unsigned int colors_used = read_u32(&data[46]);
            unsigned int colors = colors_used != 0 ? colors_used : (1U << bpp);
            size_t palette_start = 14 + dib_size;
            if (palette_start + (size_t)colors * 4 > data.size()) return false;
            palette.resize(colors);
            unsigned int i;
            for (i = 0; i < colors; ++i) {
                const unsigned char* p = &data[palette_start + (size_t)i * 4];
                palette[i] = RGB(p[2], p[1], p[0]);
            }
        }

        pixels.clear();
        pixels.resize((size_t)width * (size_t)height);

        int y;
        for (y = 0; y < height; ++y) {
            int physical_row = top_down ? y : height - 1 - y;
            int x;
            for (x = 0; x < width; ++x) {
                RGB color;
                if (!get_pixel(data, pixel_offset, width, height, bpp, compression,
                               red_mask, green_mask, blue_mask, palette,
                               x, physical_row, color)) return false;
                pixels[index(x, y)] = Pixel(color.r, color.g, color.b);
            }
        }
        return true;
    }

    Pixel GetPixel(int x, int y) const {
        if (x < 0 || y < 0 || x >= width || y >= height) return Pixel();
        return pixels[index(x, y)];
    }

    void PrintExposure() const {
        unsigned long histogram[256];
        makeHistogram(pixels, 'Y', histogram);
        unsigned long count = (unsigned long)pixels.size();

        cout << "Exposure:" << endl;
        cout << "Mean Y: " << meanFromHistogram(histogram, count) << endl;
        cout << "Median Y: " << medianFromHistogram(histogram, count) << endl;
    }

    void PrintWhiteBalance() {
        unsigned long sumR = 0;
        unsigned long sumG = 0;
        unsigned long sumB = 0;
        unsigned long count = (unsigned long)pixels.size();
        int i;

        for (i = 0; i < (int)pixels.size(); ++i) {
            sumR += pixels[i].R;
            sumG += pixels[i].G;
            sumB += pixels[i].B;
        }

        if (count == 0) return;

        double meanR = (double)sumR / count;
        double meanG = (double)sumG / count;
        double meanB = (double)sumB / count;
        double target = max(meanR, max(meanG, meanB));
        double gainR = meanR == 0.0 ? 1.0 : target / meanR;
        double gainG = meanG == 0.0 ? 1.0 : target / meanG;
        double gainB = meanB == 0.0 ? 1.0 : target / meanB;

        cout << "White balance:" << endl;
        cout << "Red gain: " << gainR << endl;
        cout << "Green gain: " << gainG << endl;
        cout << "Blue gain: " << gainB << endl;

        for (i = 0; i < (int)pixels.size(); ++i) {
            pixels[i].R = clamp255((int)(pixels[i].R * gainR + 0.5));
            pixels[i].G = clamp255((int)(pixels[i].G * gainG + 0.5));
            pixels[i].B = clamp255((int)(pixels[i].B * gainB + 0.5));
            pixels[i].CalculateY();
        }

        unsigned long hR[256], hG[256], hB[256];
        makeHistogram(pixels, 'R', hR);
        makeHistogram(pixels, 'G', hG);
        makeHistogram(pixels, 'B', hB);

        cout << "After correction:" << endl;
        cout << "R mean: " << meanFromHistogram(hR, count)
             << ", median: " << medianFromHistogram(hR, count) << endl;
        cout << "G mean: " << meanFromHistogram(hG, count)
             << ", median: " << medianFromHistogram(hG, count) << endl;
        cout << "B mean: " << meanFromHistogram(hB, count)
             << ", median: " << medianFromHistogram(hB, count) << endl;
    }

    void PrintHistograms() const {
        unsigned long hY[256], hR[256], hG[256], hB[256];
        makeHistogram(pixels, 'Y', hY);
        makeHistogram(pixels, 'R', hR);
        makeHistogram(pixels, 'G', hG);
        makeHistogram(pixels, 'B', hB);

        cout << "Histograms:" << endl;
        cout << "Value Y R G B" << endl;
        int i;
        for (i = 0; i < 256; ++i) {
            cout << i << " " << hY[i] << " " << hR[i]
                 << " " << hG[i] << " " << hB[i] << endl;
        }
    }
};

int main(int argc, char** argv) {
    const char* path = argc > 1 ? argv[1] : "image/lena.bmp";

    Bitmap bitmap;
    unsigned int declared_size = 0;
    unsigned int pixel_offset = 0;
    unsigned int dib_size = 0;
    unsigned short bpp = 0;
    unsigned int compression = 0;
    bool top_down = false;

    if (!bitmap.Load(path, declared_size, pixel_offset, dib_size,
                     bpp, compression, top_down)) {
        ifstream test(path, ios::in | ios::binary);
        if (!test) cerr << "Error: cannot open file: " << path << endl;
        else cerr << "Error: unsupported or invalid BMP file: " << path << endl;
        return 1;
    }

    cout << "Bitmap analysis" << endl;
    cout << "Input file: " << path << endl;
    cout << "Exposure:" << endl;
    bitmap.PrintExposure();
    cout << endl;
    bitmap.PrintWhiteBalance();
    cout << endl;
    bitmap.PrintHistograms();
    return 0;
}
