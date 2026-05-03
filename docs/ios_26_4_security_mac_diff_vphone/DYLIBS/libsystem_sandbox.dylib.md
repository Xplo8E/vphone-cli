## libsystem_sandbox.dylib

> `/usr/lib/system/libsystem_sandbox.dylib`

```diff

-2680.80.20.0.0
-  __TEXT.__text: 0x492c
-  __TEXT.__auth_stubs: 0x4a0
+2680.100.174.0.0
+  __TEXT.__text: 0x4b54
+  __TEXT.__auth_stubs: 0x4b0
   __TEXT.__const: 0x198
-  __TEXT.__cstring: 0xbc6
+  __TEXT.__cstring: 0xbfe
   __TEXT.__unwind_info: 0x1f8
   __DATA_CONST.__got: 0x8
   __DATA_CONST.__const: 0xb8
-  __AUTH_CONST.__auth_got: 0x250
+  __AUTH_CONST.__auth_got: 0x258
   __AUTH_CONST.__const: 0x40
   __DATA.__data: 0x13
   __DATA.__bss: 0x8
   __DATA_DIRTY.__bss: 0x28
-  - /usr/lib/system/libcompiler_rt.dylib
   - /usr/lib/system/libdispatch.dylib
   - /usr/lib/system/libdyld.dylib
   - /usr/lib/system/libsystem_blocks.dylib

   - /usr/lib/system/libsystem_kernel.dylib
   - /usr/lib/system/libsystem_malloc.dylib
   - /usr/lib/system/libsystem_platform.dylib
-  UUID: 8875D51A-D22D-3A6B-9A17-8D565C96262C
-  Functions: 145
-  Symbols:   286
-  CStrings:  110
+  UUID: AF76231D-EADC-3399-9414-6AD90FB4EA89
+  Functions: 149
+  Symbols:   291
+  CStrings:  113
 
Symbols:
+ _dyld_get_program_min_os_version
+ _sandbox_check_network
+ _sandbox_checkattr_alloc
+ _sandbox_checkattr_disable_reporting
+ _sandbox_checkattr_free
CStrings:
+ "%s: failed to allocate"
+ "network-"
+ "sandbox_checkattr_alloc"

```
