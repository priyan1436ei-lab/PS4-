# Vulkan 1.3 Rasterizer & Rendering Backend

Source reference: `src/video_core/renderer_vulkan/vk_rasterizer.cpp`

## Pipeline Management
- Translates Liverpool context registers directly to Vulkan pipeline dynamic states:
  - Viewport & Scissor: `VK_DYNAMIC_STATE_VIEWPORT`, `VK_DYNAMIC_STATE_SCISSOR`.
  - Depth/Stencil State: Depth test enable, depth write enable, depth compare op.
  - Blend State: Per-attachment color blend enable, blend equations, color write mask.
- Swapchain Presentation: Managed via Vulkan Swapchain with mailbox or FIFO presentation modes.
