"""
AMD GCN (Liverpool) Morton-order 2D Texture Swizzling & Deswizzling.
Hardware textures on PS4 are organized into 8x8 micro-tiles with bit-interleaved
Morton Z-order curve coordinates to optimize GPU cache locality and memory bandwidth.
"""

from typing import Tuple

def morton_2d(x: int, y: int) -> int:
    """
    Computes 2D Morton Z-order index by interleaving bits of x and y.
    """
    def spread_bits(val: int) -> int:
        val &= 0xFFFF
        val = (val | (val << 8)) & 0x00FF00FF
        val = (val | (val << 4)) & 0x0F0F0F0F
        val = (val | (val << 2)) & 0x33333333
        val = (val | (val << 1)) & 0x55555555
        return val

    return spread_bits(x) | (spread_bits(y) << 1)

def compact_bits(val: int) -> int:
    """
    Extracts even bits from a Morton code to recover a 1D coordinate.
    """
    val &= 0x55555555
    val = (val | (val >> 1)) & 0x33333333
    val = (val | (val >> 2)) & 0x0F0F0F0F
    val = (val | (val >> 4)) & 0x00FF00FF
    val = (val | (val >> 8)) & 0x0000FFFF
    return val

def morton_2d_decode(z: int) -> Tuple[int, int]:
    """
    Decodes a 2D Morton index back to (x, y) coordinates.
    """
    x = compact_bits(z)
    y = compact_bits(z >> 1)
    return x, y

def deswizzle_image_rgba8(swizzled: bytes, width: int, height: int) -> bytes:
    """
    Converts AMD GCN 8x8 micro-tiled Morton swizzled RGBA8 image to linear row-major buffer.
    """
    bpp = 4 # 4 bytes per pixel (RGBA8)
    linear = bytearray(width * height * bpp)

    tile_w = 8
    tile_h = 8
    tiles_x = (width + tile_w - 1) // tile_w
    tiles_y = (height + tile_h - 1) // tile_h

    tile_bytes = tile_w * tile_h * bpp # 8 * 8 * 4 = 256 bytes per microtile

    for ty in range(tiles_y):
        for tx in range(tiles_x):
            tile_linear_idx = (ty * tiles_x + tx) * tile_bytes
            for ly in range(tile_h):
                for lx in range(tile_w):
                    # Local Morton offset within the 8x8 micro-tile
                    morton_offset = morton_2d(lx, ly) * bpp
                    src_offset = tile_linear_idx + morton_offset

                    gx = tx * tile_w + lx
                    gy = ty * tile_h + ly

                    if gx < width and gy < height:
                        dst_offset = (gy * width + gx) * bpp
                        if src_offset + bpp <= len(swizzled):
                            linear[dst_offset:dst_offset + bpp] = swizzled[src_offset:src_offset + bpp]

    return bytes(linear)

def swizzle_image_rgba8(linear: bytes, width: int, height: int) -> bytes:
    """
    Swizzles a linear RGBA8 image into AMD GCN 8x8 micro-tiled Morton format.
    """
    bpp = 4
    tile_w = 8
    tile_h = 8
    tiles_x = (width + tile_w - 1) // tile_w
    tiles_y = (height + tile_h - 1) // tile_h
    tile_bytes = tile_w * tile_h * bpp

    swizzled = bytearray(tiles_x * tiles_y * tile_bytes)

    for ty in range(tiles_y):
        for tx in range(tiles_x):
            tile_linear_idx = (ty * tiles_x + tx) * tile_bytes
            for ly in range(tile_h):
                for lx in range(tile_w):
                    gx = tx * tile_w + lx
                    gy = ty * tile_h + ly

                    morton_offset = morton_2d(lx, ly) * bpp
                    dst_offset = tile_linear_idx + morton_offset

                    if gx < width and gy < height:
                        src_offset = (gy * width + gx) * bpp
                        if src_offset + bpp <= len(linear):
                            swizzled[dst_offset:dst_offset + bpp] = linear[src_offset:src_offset + bpp]

    return bytes(swizzled)

