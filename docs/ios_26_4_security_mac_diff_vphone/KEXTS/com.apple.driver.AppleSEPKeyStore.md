## com.apple.driver.AppleSEPKeyStore

> `com.apple.driver.AppleSEPKeyStore`

```diff

-2155.80.2.0.0
-  __TEXT.__cstring: 0x462c
-  __TEXT.__const: 0x884
-  __TEXT_EXEC.__text: 0x3ed40
+2155.100.115.0.0
+  __TEXT.__cstring: 0x4805
+  __TEXT.__const: 0x96c
+  __TEXT_EXEC.__text: 0x3db5c
   __TEXT_EXEC.__auth_stubs: 0x0
   __DATA.__data: 0x3a4
   __DATA.__common: 0xe8
   __DATA.__bss: 0x300
-  __DATA_CONST.__auth_got: 0x498
+  __DATA_CONST.__auth_got: 0x4f8
   __DATA_CONST.__got: 0x98
   __DATA_CONST.__auth_ptr: 0x18
   __DATA_CONST.__mod_init_func: 0x10

   __DATA_CONST.__const: 0x4c88
   __DATA_CONST.__kalloc_type: 0xe00
   __DATA_CONST.__kalloc_var: 0xa0
-  UUID: 3FCD0FC4-F0A3-3891-B0F0-5E4B755A4ADC
-  Functions: 974
-  Symbols:   1770
-  CStrings:  366
+  UUID: 8ED537BE-3940-3726-9117-415D8FD4F4AC
+  Functions: 1024
+  Symbols:   1843
+  CStrings:  378
 
Symbols:
+ _OUTLINED_FUNCTION_101
+ _OUTLINED_FUNCTION_105
+ _OUTLINED_FUNCTION_108
+ _OUTLINED_FUNCTION_109
+ _OUTLINED_FUNCTION_110
+ _OUTLINED_FUNCTION_111
+ _OUTLINED_FUNCTION_112
+ _OUTLINED_FUNCTION_113
+ _OUTLINED_FUNCTION_114
+ _OUTLINED_FUNCTION_115
+ _OUTLINED_FUNCTION_117
+ _OUTLINED_FUNCTION_118
+ _OUTLINED_FUNCTION_119
+ _OUTLINED_FUNCTION_120
+ _OUTLINED_FUNCTION_121
+ _OUTLINED_FUNCTION_122
+ _OUTLINED_FUNCTION_124
+ _OUTLINED_FUNCTION_125
+ _OUTLINED_FUNCTION_126
+ _ZN23AppleKeyStoreUserClient24handleUserClientSelectorEjP25IOExternalMethodArguments.cold.4
+ __ZN12OSDictionary11withObjectsEPPK8OSObjectPPK8OSStringjj
+ __ZN13AppleKeyStore15identity_createEyP6OSDataS1_iS1_S1_yjS1_PiPS1_
+ __ZN19IOPerfControlClient10copyClientEP9IOServicey
+ __ZN19IOPerfControlClient15copyWorkContextEv
+ __ZN19IOPerfControlClient18workEndWithContextEP9IOServiceP8OSObjectPNS_11WorkEndArgsEb
+ __ZN19IOPerfControlClient20workBeginWithContextEP9IOServiceP8OSObjectPNS_13WorkBeginArgsE
+ __ZN19IOPerfControlClient21workSubmitWithContextEP9IOServiceP8OSObjectPNS_14WorkSubmitArgsE
+ __ZN23AppleKeyStoreUserClient36submit_coreanalytics_keybag_selectorEPKcij
+ __ZN8OSNumber10withNumberEyj
+ __ZN8OSString11withCStringEPKc
+ __ZN9IOService22CoreAnalyticsSendEventEyP8OSStringP12OSDictionaryPFiP15OSMetaClassBase5IORPCE
+ __ZN9OSBoolean11withBooleanEb
+ __ZZN13AppleKeyStore13event_enqueueEP14events_entry_sE21kalloc_type_view_3743
+ __ZZN13AppleKeyStore13handle_eventsEvE21kalloc_type_view_3776
+ __ZZN13AppleKeyStore13tdm_new_entryEP19AppleTDMAKSServicesE21kalloc_type_view_3456
+ __ZZN13AppleKeyStore13unload_keybagEyiE21kalloc_type_view_1821
+ __ZZN13AppleKeyStore16tdm_remove_entryEP19AppleTDMAKSServicesE21kalloc_type_view_3485
+ __ZZN13AppleKeyStore17set_volume_keybagEyijP6OSDataS1_S1_bE21kalloc_type_view_2713
+ __ZZN13AppleKeyStore17set_volume_keybagEyijP6OSDataS1_S1_bE21kalloc_type_view_2740
+ __ZZN13AppleKeyStore22unload_session_keybagsEyiE21kalloc_type_view_1845
+ __block_descriptor_tmp.107
+ __block_descriptor_tmp.136
+ __block_descriptor_tmp.145
+ __block_descriptor_tmp.146
+ __block_descriptor_tmp.166
+ __block_descriptor_tmp.172
+ __block_descriptor_tmp.180
+ __block_descriptor_tmp.215
+ __block_descriptor_tmp.80
+ __block_descriptor_tmp.82
+ __ipc_create_keybag_v5
+ _cs_identity_get
+ _proc_name
+ _strcmp
- _OUTLINED_FUNCTION_100
- _ZN13AppleKeyStore26add_entropy_to_kernel_prngEPvj.cold.1
- _ZN13AppleKeyStore34add_class_f_entropy_to_kernel_prngEv.cold.1
- _ZN13AppleKeyStore34add_class_f_entropy_to_kernel_prngEv.cold.2
- _ZN13AppleKeyStore34add_class_f_entropy_to_kernel_prngEv.cold.3
- _ZN13AppleKeyStore34add_class_f_entropy_to_kernel_prngEv.cold.4
- _ZN13AppleKeyStore34add_class_f_entropy_to_kernel_prngEv.cold.5
- __ZN13AppleKeyStore15identity_createEyP6OSDataS1_iS1_S1_yPiPS1_
- __ZN13AppleKeyStore26add_entropy_to_kernel_prngEPvj
- __ZN13AppleKeyStore34add_class_f_entropy_to_kernel_prngEv
- __ZZN13AppleKeyStore13event_enqueueEP14events_entry_sE21kalloc_type_view_3671
- __ZZN13AppleKeyStore13handle_eventsEvE21kalloc_type_view_3704
- __ZZN13AppleKeyStore13tdm_new_entryEP19AppleTDMAKSServicesE21kalloc_type_view_3384
- __ZZN13AppleKeyStore13unload_keybagEyiE21kalloc_type_view_1760
- __ZZN13AppleKeyStore16tdm_remove_entryEP19AppleTDMAKSServicesE21kalloc_type_view_3413
- __ZZN13AppleKeyStore17set_volume_keybagEyijP6OSDataS1_S1_bE21kalloc_type_view_2679
- __ZZN13AppleKeyStore17set_volume_keybagEyijP6OSDataS1_S1_bE21kalloc_type_view_2706
- __ZZN13AppleKeyStore22unload_session_keybagsEyiE21kalloc_type_view_1784
- __block_descriptor_tmp.103
- __block_descriptor_tmp.132
- __block_descriptor_tmp.141
- __block_descriptor_tmp.142
- __block_descriptor_tmp.158
- __block_descriptor_tmp.168
- __block_descriptor_tmp.176
- __block_descriptor_tmp.211
- __block_descriptor_tmp.76
- __block_descriptor_tmp.78
- _write_random
CStrings:
+ "%s:%spid:%d,%s:%s%s%s%s%s%u:%s CoreAnalytics: Failed to send CA event %d%s\n"
+ "%s:%spid:%d,%s:%s%s%s%s%s%u:%s IOPerfControlClient::copyClient failed%s\n"
+ "%s:%spid:%d,%s:%s%s%s%s%s%u:%s IOPerfControlClient::registerDevice failed%s\n"
+ "%s:%spid:%d,%s:%s%s%s%s%s%u:%s ioPerfControl is enabled: %d, %d%s\n"
+ "%s:%spid:%d,%s:%s%s%s%s%s%u:%s secret_is_hash option requires hash_iterations%s\n"
+ "%s:%spid:%d,%s:%s%s%s%s%s%u:%s secret_is_hash option requires hash_salt%s\n"
+ "/AppleInternal/Library/BuildRoots/4~CLdcugATCBL0x-xuzKaWWi6zdwuRGAOmb6Rsr-g/Library/Caches/com.apple.xbs/TemporaryDirectory.p6JJqm/Sources/AppleKeyStore_SEP_kexts/AppleKeyStore.cpp"
+ "/AppleInternal/Library/BuildRoots/4~CLdcugATCBL0x-xuzKaWWi6zdwuRGAOmb6Rsr-g/Library/Caches/com.apple.xbs/TemporaryDirectory.p6JJqm/Sources/AppleKeyStore_SEP_kexts/ipc.c"
+ "/AppleInternal/Library/BuildRoots/4~CLdcugATCBL0x-xuzKaWWi6zdwuRGAOmb6Rsr-g/Library/Caches/com.apple.xbs/TemporaryDirectory.p6JJqm/Sources/AppleKeyStore_SEP_kexts/msg.c"
+ "/AppleInternal/Library/BuildRoots/4~CLdcugATCBL0x-xuzKaWWi6zdwuRGAOmb6Rsr-g/Library/Caches/com.apple.xbs/TemporaryDirectory.p6JJqm/Sources/AppleKeyStore_SEP_kexts/platform/platform.c"
+ "/AppleInternal/Library/BuildRoots/4~CLdcugATCBL0x-xuzKaWWi6zdwuRGAOmb6Rsr-g/Library/Caches/com.apple.xbs/TemporaryDirectory.p6JJqm/Sources/AppleKeyStore_SEP_kexts/platform/platform_kernel.c"
+ "19:16:38"
+ "2155.100.115"
+ "Mar 19 2026"
+ "aks-io-perf-control"
+ "bag_type"
+ "bundle_id"
+ "com.apple.applekeystore.selector.keybag_create"
+ "com.apple.applekeystore.selector.keybag_load"
+ "com.apple.keystore.keybag.create"
+ "com.apple.keystore.keybag.load"
+ "device_keybag_access"
+ "keybag_create_access"
+ "keybag_load_access"
+ "process_name"
+ "result"
+ "secureRoot"
+ "version"
- "\"failed to add entropy to kernel prng\" @%s:%d"
- "\"invalid pub key\" @%s:%d"
- "%s:%spid:%d,%s:%s%s%s%s%s%u:%s bad uuid lenght%s\n"
- "%s:%spid:%d,%s:%s%s%s%s%s%u:%s failed to create der%s\n"
- "%s:%spid:%d,%s:%s%s%s%s%s%u:%s failed to create refkey %d%s\n"
- "%s:%spid:%d,%s:%s%s%s%s%s%u:%s failed to get pub%s\n"
- "%s:%spid:%d,%s:%s%s%s%s%s%u:%s failed to set opt%s\n"
- "%s:%spid:%d,%s:%s%s%s%s%s%u:%s re-seeded prng with %u bytes%s\n"
- "/AppleInternal/Library/BuildRoots/4~CHzhugC6Y_zufVX9ivEk-eWEdqCajSzzfYdnYcE/Library/Caches/com.apple.xbs/Sources/AppleKeyStore_SEP_kexts/AppleKeyStore.cpp"
- "/AppleInternal/Library/BuildRoots/4~CHzhugC6Y_zufVX9ivEk-eWEdqCajSzzfYdnYcE/Library/Caches/com.apple.xbs/Sources/AppleKeyStore_SEP_kexts/ipc.c"
- "/AppleInternal/Library/BuildRoots/4~CHzhugC6Y_zufVX9ivEk-eWEdqCajSzzfYdnYcE/Library/Caches/com.apple.xbs/Sources/AppleKeyStore_SEP_kexts/msg.c"
- "/AppleInternal/Library/BuildRoots/4~CHzhugC6Y_zufVX9ivEk-eWEdqCajSzzfYdnYcE/Library/Caches/com.apple.xbs/Sources/AppleKeyStore_SEP_kexts/platform/platform.c"
- "/AppleInternal/Library/BuildRoots/4~CHzhugC6Y_zufVX9ivEk-eWEdqCajSzzfYdnYcE/Library/Caches/com.apple.xbs/Sources/AppleKeyStore_SEP_kexts/platform/platform_kernel.c"
- "20:35:38"
- "2155.80.2"
- "Jan 28 2026"

```
