# Input, Audio, and Networking Subsystems

## Input (`src/input/`, `libScePad`)
- Translates host controllers (SDL3 Gamepad API, XInput, DirectInput) to DualShock 4 reports:
  - Digital buttons, analog sticks.
  - Gyroscope & accelerometer 6-axis motion.
  - Touchpad coordinate tracking.

## Audio (`src/core/libraries/audio/`, `libSceAudioOut`)
- Decodes PCM streams and routes them through OpenAL Soft / SDL3 Audio.
- Audio codecs supported via FFmpeg / AT9 decoder.

## Network (`src/shadnet/`, `src/core/net/`)
- Emulates BSD socket layer (`sceNetSocket`, `sceNetConnect`, `sceNetSend`, `sceNetRecv`).
- Translates guest network calls to host POSIX / WinSock sockets.
