# SPDX-License-Identifier: MIT
# AetherPS4 - Modern PlayStation 4 Emulator Core
# Lead Architect & Developer: PRIYAN-A-1
# Copyright (c) 2026 PRIYAN-A-1. All rights reserved.

cmake_minimum_required(VERSION 3.20)
project(AetherPS4 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

include_directories(include)

add_executable(aether_ps4
    src/main.cpp
)
