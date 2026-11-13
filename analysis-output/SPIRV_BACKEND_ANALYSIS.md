# SPIR-V Code Generation Backend

Source reference: `src/shader_recompiler/backend/spirv/`

## Emitter Operation
1. Translates optimized SSA IR into valid SPIR-V binary words.
2. Allocates Vulkan Descriptor Sets:
   - Buffer descriptors (Structured buffers, raw buffers) -> `OpTypePointer StorageBuffer`.
   - Texture descriptors -> `OpTypeSampledImage`.
   - Sampler descriptors -> `OpTypeSampler`.
3. Emits SPIR-V capabilities: `Shader`, `Matrix`, `ImageQuery`, `VulkanMemoryModel`.
4. Outputs SPIR-V binary ready for `vkCreateShaderModule()`.
