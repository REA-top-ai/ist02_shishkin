# Bitmap task 2 — independent project

This is a standalone implementation of the required items from “Bitmaps pt. 2”. It does not print the BMP header or corner colors from the first assignment.

Implemented:
- `Pixel` with `R`, `G`, `B`, `Y`
- `Bitmap` class and `GetPixel(int x, int y) const`
- luminance formula `Y = 0.2126*R + 0.7152*G + 0.0722*B`
- exposure estimate (Y histogram, mean, median)
- white balance gains, channel correction with clamp to 255, and post-correction statistics
- histograms for Y, R, G, B

The starred tasks (focus map and false color) are intentionally omitted.

## Build
```bash
cmake -B build -S .
cmake --build build
```

## Run
Pass the path to a BMP file as the first argument. If omitted, the program tries `image/lena.bmp`.

Windows example:
```text
build\Debug\bitmap_task2.exe image\lena.bmp
```

Run with a working directory where the `image` folder exists, or provide an absolute path to the BMP.
