# End-to-End Function Call Graph

```
main()
  |--> Config::Load()
  |--> Log::Init()
  |--> Emulator::Run()
         |--> VFS::Mount("/app0", game_path)
         |--> SfoParser::Parse("param.sfo")
         |--> Libraries::InitHLELibs()
         |--> Memory::Initialize()
         |--> Loader::Elf::Load("eboot.bin")
         |      |--> Module::LoadModuleToMemory()
         |      |--> Linker::Relocate()
         |      |--> Linker::ResolveSymbols()
         |--> Linker::Execute()
                |--> RunMainEntry() [Native x86-64 Jump]
                       |--> Guest Game Code Execution
                              |--> sceKernelAllocateDirectMemory()
                              |--> sceGnmSubmitCommandBuffers()
                                     |--> Liverpool::Submit()
                                            |--> Liverpool::Process()
                                                   |--> ProcessPacket()
                                                   |      |--> Recompiler::Compile()
                                                   |      |--> Vulkan::Draw()
                                                   |--> Swapchain::Present()
```
