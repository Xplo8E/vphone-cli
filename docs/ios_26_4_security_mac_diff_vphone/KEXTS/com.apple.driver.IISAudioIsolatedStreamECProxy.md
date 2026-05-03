## com.apple.driver.IISAudioIsolatedStreamECProxy

> `com.apple.driver.IISAudioIsolatedStreamECProxy`

```diff

-520.2.0.0.0
-  __TEXT.__cstring: 0x2f3
-  __TEXT.__os_log: 0x193
-  __TEXT_EXEC.__text: 0x12a4
+540.16.0.0.0
+  __TEXT.__cstring: 0x4cf
+  __TEXT.__os_log: 0x2e8
+  __TEXT_EXEC.__text: 0x1dc8
   __TEXT_EXEC.__auth_stubs: 0x0
   __DATA.__data: 0xc8
-  __DATA.__common: 0x38
-  __DATA.__bss: 0x8
-  __DATA_CONST.__auth_got: 0x90
+  __DATA.__common: 0x60
+  __DATA.__bss: 0x10
+  __DATA_CONST.__auth_got: 0xa0
   __DATA_CONST.__got: 0x28
-  __DATA_CONST.__mod_init_func: 0x8
-  __DATA_CONST.__mod_term_func: 0x8
-  __DATA_CONST.__const: 0x9b8
-  __DATA_CONST.__kalloc_type: 0x40
-  UUID: 5DE84BCE-DB1D-3A34-8794-8F24B07C8D46
-  Functions: 45
-  Symbols:   377
-  CStrings:  18
+  __DATA_CONST.__mod_init_func: 0x10
+  __DATA_CONST.__mod_term_func: 0x10
+  __DATA_CONST.__const: 0x1370
+  __DATA_CONST.__kalloc_type: 0x80
+  UUID: 93223FE6-4162-3714-95C2-7B520975AE55
+  Functions: 84
+  Symbols:   436
+  CStrings:  25
 
Symbols:
+ _GLOBAL__sub_I_IISAudioIsolatedOutputStreamECProxy.cpp
+ _OUTLINED_FUNCTION_0
+ _OUTLINED_FUNCTION_1
+ _ZN35IISAudioIsolatedOutputStreamECProxy10_configureEP9IOService.cold.1
+ _ZN35IISAudioIsolatedOutputStreamECProxy10_configureEP9IOService.cold.2
+ _ZN35IISAudioIsolatedOutputStreamECProxy10_configureEP9IOService.cold.3
+ _ZN35IISAudioIsolatedOutputStreamECProxy11withPhandleEPK6OSData.cold.1
+ _ZN35IISAudioIsolatedOutputStreamECProxy5startEP9IOService.cold.1
+ _ZN35IISAudioIsolatedOutputStreamECProxy5startEP9IOService.cold.2
+ _ZN35IISAudioIsolatedOutputStreamECProxy5startEP9IOService.cold.3
+ _ZN35IISAudioIsolatedOutputStreamECProxy5startEP9IOService.cold.4
+ _ZN35IISAudioIsolatedOutputStreamECProxy5startEP9IOService.cold.5
+ __ZL39IISAudioIsolatedOutputStreamECProxy_ktv
+ __ZN35IISAudioIsolatedOutputStreamECProxy10_configureEP9IOService
+ __ZN35IISAudioIsolatedOutputStreamECProxy10gMetaClassE
+ __ZN35IISAudioIsolatedOutputStreamECProxy10superClassE
+ __ZN35IISAudioIsolatedOutputStreamECProxy10teardownIOEv
+ __ZN35IISAudioIsolatedOutputStreamECProxy11withPhandleEPK6OSData
+ __ZN35IISAudioIsolatedOutputStreamECProxy14writeMixOutputEyj
+ __ZN35IISAudioIsolatedOutputStreamECProxy20getStreamDescriptionER30IOAudio2StreamBasicDescription
+ __ZN35IISAudioIsolatedOutputStreamECProxy20setStreamDescriptionERK30IOAudio2StreamBasicDescriptionj
+ __ZN35IISAudioIsolatedOutputStreamECProxy4stopEP9IOService
+ __ZN35IISAudioIsolatedOutputStreamECProxy5startEP9IOService
+ __ZN35IISAudioIsolatedOutputStreamECProxy7setupIOEv
+ __ZN35IISAudioIsolatedOutputStreamECProxy9MetaClassC1Ev
+ __ZN35IISAudioIsolatedOutputStreamECProxy9MetaClassC2Ev
+ __ZN35IISAudioIsolatedOutputStreamECProxy9MetaClassD0Ev
+ __ZN35IISAudioIsolatedOutputStreamECProxy9MetaClassD1Ev
+ __ZN35IISAudioIsolatedOutputStreamECProxy9metaClassE
+ __ZN35IISAudioIsolatedOutputStreamECProxyC1EPK11OSMetaClass
+ __ZN35IISAudioIsolatedOutputStreamECProxyC1Ev
+ __ZN35IISAudioIsolatedOutputStreamECProxyC2EPK11OSMetaClass
+ __ZN35IISAudioIsolatedOutputStreamECProxyC2Ev
+ __ZN35IISAudioIsolatedOutputStreamECProxyD0Ev
+ __ZN35IISAudioIsolatedOutputStreamECProxyD1Ev
+ __ZN35IISAudioIsolatedOutputStreamECProxyD2Ev
+ __ZN35IISAudioIsolatedOutputStreamECProxydlEPvm
+ __ZN35IISAudioIsolatedOutputStreamECProxynwEm
+ __ZN45ExclavesAudioProxyOutputStreamDriverInterface6createEP9IOServiceP26ExclavesAudioProxyEndpoint
+ __ZN5Audio7KextLib22AppleAudioSystemHelper12isInRecoveryEv
+ __ZNK35IISAudioIsolatedOutputStreamECProxy12getMetaClassEv
+ __ZNK35IISAudioIsolatedOutputStreamECProxy9MetaClass5allocEv
+ __ZTV35IISAudioIsolatedOutputStreamECProxy
+ __ZTVN35IISAudioIsolatedOutputStreamECProxy9MetaClassE
+ __ZZN35IISAudioIsolatedOutputStreamECProxy10_configureEP9IOServiceE11_os_log_fmt
+ __ZZN35IISAudioIsolatedOutputStreamECProxy10_configureEP9IOServiceE11_os_log_fmt_0
+ __ZZN35IISAudioIsolatedOutputStreamECProxy10_configureEP9IOServiceE11_os_log_fmt_1
+ __ZZN35IISAudioIsolatedOutputStreamECProxy11withPhandleEPK6OSDataE11_os_log_fmt
+ __ZZN35IISAudioIsolatedOutputStreamECProxy5startEP9IOServiceE11_os_log_fmt
+ __ZZN35IISAudioIsolatedOutputStreamECProxy5startEP9IOServiceE11_os_log_fmt_0
+ __ZZN35IISAudioIsolatedOutputStreamECProxy5startEP9IOServiceE11_os_log_fmt_1
+ __ZZN35IISAudioIsolatedOutputStreamECProxy5startEP9IOServiceE11_os_log_fmt_2
+ __ZZN35IISAudioIsolatedOutputStreamECProxy5startEP9IOServiceE11_os_log_fmt_3
CStrings:
+ "!(AppleAudioSystemHelper::isInRecovery())"
+ "/AppleInternal/Library/BuildRoots/4~CLdcugD_bARxI3IReOMf0PBP1UCa5zOxYLYd_zw/Library/Caches/com.apple.xbs/TemporaryDirectory.qzlWuc/Sources/AppleARMIISAudio/src/kext/IsolatedStreamECProxy/IOService/IISAudioIsolatedOutputStreamECProxy.cpp"
+ "/AppleInternal/Library/BuildRoots/4~CLdcugD_bARxI3IReOMf0PBP1UCa5zOxYLYd_zw/Library/Caches/com.apple.xbs/TemporaryDirectory.qzlWuc/Sources/AppleARMIISAudio/src/kext/IsolatedStreamECProxy/IOService/IISAudioIsolatedStreamECProxy.cpp"
+ "1211111212221212111"
+ "IISAudio,IsolatedOutputStreamHandle"
+ "IISAudio::IsolatedOutputStreamECProxy"
+ "IISAudioIsolatedOutputStreamECProxy"
+ "site.IISAudioIsolatedOutputStreamECProxy"
- "/AppleInternal/Library/BuildRoots/4~CHzhugCYiQdJTFtDmc6VwR-3pQJ9bfqH0BYJ-L8/Library/Caches/com.apple.xbs/Sources/AppleARMIISAudio/src/kext/IsolatedStreamECProxy/IOService/IISAudioIsolatedStreamECProxy.cpp"

```
