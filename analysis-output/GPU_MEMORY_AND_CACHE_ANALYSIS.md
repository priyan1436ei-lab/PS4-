# GPU Memory, Texture Caches & Swizzling

Source references:
- `src/video_core/texture_cache/`
- `src/video_core/buffer_cache/`
- `src/video_core/amdgpu/tiling.cpp`

## 2D Morton Z-Order Curve Swizzling
PS4 textures are organized into 8x8 microtiles with bit-interleaved Morton coordinates:
$$\text{morton}(x, y) = \text{spread}(x) \mid (\text{spread}(y) \ll 1)$$
The emulator deswizzles tiled texture buffers into linear buffers before uploading them to Vulkan `VkImage` objects.

## Case Study: GT Sport Menu Rendering Fix (Commit `4f48eabe69`)
The fix resolved:
1. Workgroup barrier memory handling in compute shaders.
2. Cropped texture synchronization across overlapping guest memory ranges.
3. Checkerboard texture rendering artifacts caused by aliased texture cache lookups.
