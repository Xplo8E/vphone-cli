## com.apple.driver.AppleSEPManager

> `com.apple.driver.AppleSEPManager`

```diff

-880.80.7.0.0
-  __TEXT.__const: 0x5dc
-  __TEXT.__cstring: 0xc980
-  __TEXT_EXEC.__text: 0x31638
+880.100.26.0.0
+  __TEXT.__cstring: 0xd0a0
+  __TEXT.__const: 0x56c
+  __TEXT_EXEC.__text: 0x2df4c
   __TEXT_EXEC.__auth_stubs: 0x0
   __DATA.__data: 0x168
   __DATA.__common: 0xb08
-  __DATA.__bss: 0x49
-  __DATA_CONST.__auth_got: 0x478
+  __DATA.__bss: 0xa1
+  __DATA_CONST.__auth_got: 0x498
   __DATA_CONST.__got: 0x130
   __DATA_CONST.__auth_ptr: 0x8
   __DATA_CONST.__mod_init_func: 0xa8
   __DATA_CONST.__mod_term_func: 0xa8
-  __DATA_CONST.__const: 0xa9c0
+  __DATA_CONST.__const: 0xa9e0
   __DATA_CONST.__kalloc_type: 0xc00
   __DATA_CONST.__kalloc_var: 0x50
-  UUID: FE1B24B7-93D2-31D9-8D3C-0C7EF4BD0535
-  Functions: 1668
-  Symbols:   2513
-  CStrings:  1121
+  UUID: F331AD6E-CDD1-3E48-8163-EE36BC0E91EB
+  Functions: 1733
+  Symbols:   2587
+  CStrings:  1141
 
Symbols:
+ _OUTLINED_FUNCTION_20
+ _OUTLINED_FUNCTION_21
+ _Z20register_longrunningv.cold.1
+ _ZN15AppleSEPManager11_didTimeoutEP18IOTimerEventSource.cold.3
+ _ZN15AppleSEPManager14_setPowerStateEPm.cold.10
+ _ZN15AppleSEPManager14_setPowerStateEPm.cold.11
+ _ZN15AppleSEPManager14_setPowerStateEPm.cold.12
+ _ZN15AppleSEPManager14_setPowerStateEPm.cold.13
+ _ZN15AppleSEPManager14_setPowerStateEPm.cold.14
+ _ZN15AppleSEPManager14_setPowerStateEPm.cold.15
+ _ZN15AppleSEPManager14_setPowerStateEPm.cold.9
+ _ZN15AppleSEPManager20_notifyOSActiveGatedEv.cold.4
+ _ZN15AppleSEPManager28_waitUntilSEPStateLPWMinimumEv.cold.1
+ _ZN15AppleSEPManager28_waitUntilSEPStateLPWMinimumEv.cold.2
+ _ZN15AppleSEPManager29_nonPowerManagedEpEnableAsyncEv.cold.1
+ _ZN15AppleSEPManager29_nonPowerManagedEpEnableAsyncEv.cold.2
+ _ZN18AppleSEPUserClient36DispatchUserClientGigalockerShutdownEPS_PvP25IOExternalMethodArguments.cold.2
+ __Z17check_longrunningv
+ __Z20register_longrunningv
+ __Z22unregister_longrunningv
+ __ZL11longrunning
+ __ZL4lock
+ __ZN15AppleSEPControl8cmsgWAKEEj
+ __ZN15AppleSEPManager28_waitUntilSEPStateLPWMinimumEv
+ __ZZ12gl_rec_writeP6gl_ctxPK9gl_rec_idPKhmE20kalloc_type_view_705
+ __ZZ12gl_rec_writeP6gl_ctxPK9gl_rec_idPKhmE20kalloc_type_view_749
+ __ZZ13gl_rec_deletePK6gl_ctxyE20kalloc_type_view_634
+ __ZZ13gl_rec_deletePK6gl_ctxyE20kalloc_type_view_649
+ __ZZ22gl_crash_recovery_testP6gl_ctxE20kalloc_type_view_983
+ __ZZ22gl_crash_recovery_testP6gl_ctxE21kalloc_type_view_1063
+ __ZZ25gl_corrupt_nand_size_testP6gl_ctxE21kalloc_type_view_1339
+ __ZZ25gl_corrupt_nand_size_testP6gl_ctxE21kalloc_type_view_1409
+ __ZZ30gl_many_duplicate_records_testP6gl_ctxE21kalloc_type_view_1080
+ __ZZ30gl_many_duplicate_records_testP6gl_ctxE21kalloc_type_view_1159
+ __ZZ41gl_many_types_many_duplicate_records_testP6gl_ctxE21kalloc_type_view_1179
+ __ZZ41gl_many_types_many_duplicate_records_testP6gl_ctxE21kalloc_type_view_1182
+ __ZZ41gl_many_types_many_duplicate_records_testP6gl_ctxE21kalloc_type_view_1317
+ __ZZ41gl_many_types_many_duplicate_records_testP6gl_ctxE21kalloc_type_view_1322
+ __ZZN21IOTypedOperatorsMixinI14XARTDisableLogEnwEmE20kalloc_type_view_871
+ ____ZN15AppleSEPManager28_waitUntilSEPStateLPWMinimumEv_block_invoke
+ __block_descriptor_tmp.157
+ __block_descriptor_tmp.159
+ __block_descriptor_tmp.164
+ __block_descriptor_tmp.167
+ __block_descriptor_tmp.196
+ __block_descriptor_tmp.199
+ __block_descriptor_tmp.204
+ __block_descriptor_tmp.317
+ __block_descriptor_tmp.323
+ _absolutetime_to_nanoseconds
+ _lck_mtx_lock
+ _lck_mtx_unlock
+ _nanoseconds_to_absolutetime
- __ZZ12gl_rec_writeP6gl_ctxPK9gl_rec_idPKhmE20kalloc_type_view_703
- __ZZ12gl_rec_writeP6gl_ctxPK9gl_rec_idPKhmE20kalloc_type_view_747
- __ZZ13gl_rec_deletePK6gl_ctxyE20kalloc_type_view_632
- __ZZ13gl_rec_deletePK6gl_ctxyE20kalloc_type_view_647
- __ZZ22gl_crash_recovery_testP6gl_ctxE20kalloc_type_view_981
- __ZZ22gl_crash_recovery_testP6gl_ctxE21kalloc_type_view_1061
- __ZZ25gl_corrupt_nand_size_testP6gl_ctxE21kalloc_type_view_1337
- __ZZ25gl_corrupt_nand_size_testP6gl_ctxE21kalloc_type_view_1407
- __ZZ30gl_many_duplicate_records_testP6gl_ctxE21kalloc_type_view_1078
- __ZZ30gl_many_duplicate_records_testP6gl_ctxE21kalloc_type_view_1157
- __ZZ41gl_many_types_many_duplicate_records_testP6gl_ctxE21kalloc_type_view_1177
- __ZZ41gl_many_types_many_duplicate_records_testP6gl_ctxE21kalloc_type_view_1180
- __ZZ41gl_many_types_many_duplicate_records_testP6gl_ctxE21kalloc_type_view_1315
- __ZZ41gl_many_types_many_duplicate_records_testP6gl_ctxE21kalloc_type_view_1320
- __ZZN21IOTypedOperatorsMixinI14XARTDisableLogEnwEmE20kalloc_type_view_850
- __block_descriptor_tmp.156
- __block_descriptor_tmp.158
- __block_descriptor_tmp.163
- __block_descriptor_tmp.190
- __block_descriptor_tmp.193
- __block_descriptor_tmp.198
- __block_descriptor_tmp.308
- __block_descriptor_tmp.314
CStrings:
+ "%s: SEP/OS is alive in %d state\n"
+ "/AppleInternal/Library/BuildRoots/4~CLdeugBfawOR7RknkgksMhOiGZS3ChEq1n1RwIE/Library/Caches/com.apple.xbs/TemporaryDirectory.iwRlVk/Sources/AppleSEPManager/AllocMPM.cpp"
+ "/AppleInternal/Library/BuildRoots/4~CLdeugBfawOR7RknkgksMhOiGZS3ChEq1n1RwIE/Library/Caches/com.apple.xbs/TemporaryDirectory.iwRlVk/Sources/AppleSEPManager/AppleSEPBooter.cpp"
+ "/AppleInternal/Library/BuildRoots/4~CLdeugBfawOR7RknkgksMhOiGZS3ChEq1n1RwIE/Library/Caches/com.apple.xbs/TemporaryDirectory.iwRlVk/Sources/AppleSEPManager/AppleSEPCommand.cpp"
+ "/AppleInternal/Library/BuildRoots/4~CLdeugBfawOR7RknkgksMhOiGZS3ChEq1n1RwIE/Library/Caches/com.apple.xbs/TemporaryDirectory.iwRlVk/Sources/AppleSEPManager/AppleSEPControl.cpp"
+ "/AppleInternal/Library/BuildRoots/4~CLdeugBfawOR7RknkgksMhOiGZS3ChEq1n1RwIE/Library/Caches/com.apple.xbs/TemporaryDirectory.iwRlVk/Sources/AppleSEPManager/AppleSEPCoreBuffer.cpp"
+ "/AppleInternal/Library/BuildRoots/4~CLdeugBfawOR7RknkgksMhOiGZS3ChEq1n1RwIE/Library/Caches/com.apple.xbs/TemporaryDirectory.iwRlVk/Sources/AppleSEPManager/AppleSEPDebug.cpp"
+ "/AppleInternal/Library/BuildRoots/4~CLdeugBfawOR7RknkgksMhOiGZS3ChEq1n1RwIE/Library/Caches/com.apple.xbs/TemporaryDirectory.iwRlVk/Sources/AppleSEPManager/AppleSEPDebugArgs.cpp"
+ "/AppleInternal/Library/BuildRoots/4~CLdeugBfawOR7RknkgksMhOiGZS3ChEq1n1RwIE/Library/Caches/com.apple.xbs/TemporaryDirectory.iwRlVk/Sources/AppleSEPManager/AppleSEPDevice.cpp"
+ "/AppleInternal/Library/BuildRoots/4~CLdeugBfawOR7RknkgksMhOiGZS3ChEq1n1RwIE/Library/Caches/com.apple.xbs/TemporaryDirectory.iwRlVk/Sources/AppleSEPManager/AppleSEPDiscovery.cpp"
+ "/AppleInternal/Library/BuildRoots/4~CLdeugBfawOR7RknkgksMhOiGZS3ChEq1n1RwIE/Library/Caches/com.apple.xbs/TemporaryDirectory.iwRlVk/Sources/AppleSEPManager/AppleSEPEndpoint.cpp"
+ "/AppleInternal/Library/BuildRoots/4~CLdeugBfawOR7RknkgksMhOiGZS3ChEq1n1RwIE/Library/Caches/com.apple.xbs/TemporaryDirectory.iwRlVk/Sources/AppleSEPManager/AppleSEPFirmware.cpp"
+ "/AppleInternal/Library/BuildRoots/4~CLdeugBfawOR7RknkgksMhOiGZS3ChEq1n1RwIE/Library/Caches/com.apple.xbs/TemporaryDirectory.iwRlVk/Sources/AppleSEPManager/AppleSEPLogger.cpp"
+ "/AppleInternal/Library/BuildRoots/4~CLdeugBfawOR7RknkgksMhOiGZS3ChEq1n1RwIE/Library/Caches/com.apple.xbs/TemporaryDirectory.iwRlVk/Sources/AppleSEPManager/AppleSEPManagerARM.cpp"
+ "/AppleInternal/Library/BuildRoots/4~CLdeugBfawOR7RknkgksMhOiGZS3ChEq1n1RwIE/Library/Caches/com.apple.xbs/TemporaryDirectory.iwRlVk/Sources/AppleSEPManager/AppleSEPPairing.cpp"
+ "/AppleInternal/Library/BuildRoots/4~CLdeugBfawOR7RknkgksMhOiGZS3ChEq1n1RwIE/Library/Caches/com.apple.xbs/TemporaryDirectory.iwRlVk/Sources/AppleSEPManager/AppleSEPSharedMemoryBuffer.cpp"
+ "/AppleInternal/Library/BuildRoots/4~CLdeugBfawOR7RknkgksMhOiGZS3ChEq1n1RwIE/Library/Caches/com.apple.xbs/TemporaryDirectory.iwRlVk/Sources/AppleSEPManager/AppleSEPTesting.cpp"
+ "/AppleInternal/Library/BuildRoots/4~CLdeugBfawOR7RknkgksMhOiGZS3ChEq1n1RwIE/Library/Caches/com.apple.xbs/TemporaryDirectory.iwRlVk/Sources/AppleSEPManager/AppleSEPTraceBuffer.cpp"
+ "/AppleInternal/Library/BuildRoots/4~CLdeugBfawOR7RknkgksMhOiGZS3ChEq1n1RwIE/Library/Caches/com.apple.xbs/TemporaryDirectory.iwRlVk/Sources/AppleSEPManager/AppleSEPUserClient.cpp"
+ "/AppleInternal/Library/BuildRoots/4~CLdeugBfawOR7RknkgksMhOiGZS3ChEq1n1RwIE/Library/Caches/com.apple.xbs/TemporaryDirectory.iwRlVk/Sources/AppleSEPManager/FIFO.h"
+ "/AppleInternal/Library/BuildRoots/4~CLdeugBfawOR7RknkgksMhOiGZS3ChEq1n1RwIE/Library/Caches/com.apple.xbs/TemporaryDirectory.iwRlVk/Sources/AppleSEPManager/Longrunning.cpp"
+ "/AppleInternal/Library/BuildRoots/4~CLdeugBfawOR7RknkgksMhOiGZS3ChEq1n1RwIE/Library/Caches/com.apple.xbs/TemporaryDirectory.iwRlVk/Sources/AppleSEPManager/SEPApNonce.cpp"
+ "/AppleInternal/Library/BuildRoots/4~CLdeugBfawOR7RknkgksMhOiGZS3ChEq1n1RwIE/Library/Caches/com.apple.xbs/TemporaryDirectory.iwRlVk/Sources/AppleSEPManager/SEPEpoch.cpp"
+ "/AppleInternal/Library/BuildRoots/4~CLdeugBfawOR7RknkgksMhOiGZS3ChEq1n1RwIE/Library/Caches/com.apple.xbs/TemporaryDirectory.iwRlVk/Sources/AppleSEPManager/SEPROMPanicBuffer.cpp"
+ "/AppleInternal/Library/BuildRoots/4~CLdeugBfawOR7RknkgksMhOiGZS3ChEq1n1RwIE/Library/Caches/com.apple.xbs/TemporaryDirectory.iwRlVk/Sources/AppleSEPManager/xART/AppleSEPXART.cpp"
+ "/AppleInternal/Library/BuildRoots/4~CLdeugBfawOR7RknkgksMhOiGZS3ChEq1n1RwIE/Library/Caches/com.apple.xbs/TemporaryDirectory.iwRlVk/Sources/AppleSEPManager/xART/AppleSEPXART_embedded.cpp"
+ "/AppleInternal/Library/BuildRoots/4~CLdeugBfawOR7RknkgksMhOiGZS3ChEq1n1RwIE/Library/Caches/com.apple.xbs/TemporaryDirectory.iwRlVk/Sources/AppleSEPManager/xART/DisableLog.cpp"
+ "/AppleInternal/Library/BuildRoots/4~CLdeugBfawOR7RknkgksMhOiGZS3ChEq1n1RwIE/Library/Caches/com.apple.xbs/TemporaryDirectory.iwRlVk/Sources/AppleSEPManager/xART/gigalocker/gigalocker.cpp"
+ "12112121222"
+ "AppleSEP:WARNING: %lu threads currently in long running operations:\n"
+ "AppleSEP:WARNING: Long-running thread %p for %llu ms\n"
+ "AppleSEP:WARNING: Unable to track thread %p entering long-running task\n"
+ "AppleSEP:WARNING: Unable to track thread %p exiting long-running task\n"
+ "AppleSEP:WARNING: attempt to send message to SEP while in Low Power Wake\n"
+ "Longrunning.cpp"
+ "_current_pm_state != PM_STATE_LOW"
+ "_current_pm_state == PM_STATE_LOW"
+ "_current_pm_state == PM_STATE_ON"
+ "_current_pm_state == PM_STATE_ON || _current_pm_state == PM_STATE_LOW"
+ "_sep_panic_buffer"
+ "kIOReturnSuccess == getCommandGate()->runActionBlock(^IOReturn { _waitUntilSEPStateLPWMinimum(); return kIOReturnSuccess; })"
+ "longrunning.insert(me, now)"
+ "nullptr != target->_asep->xartSEPMasterEP()"
+ "sepd_flag_entry->app == 'SEPD'"
+ "void AppleSEPManager::_didTimeout(IOTimerEventSource *)"
+ "void AppleSEPManager::_nonPowerManagedEpEnableAsync()"
+ "void AppleSEPManager::_waitUntilSEPStateLPWMinimum()"
+ "void register_longrunning()"
- "%s: SEP/OS is alive\n"
- "/AppleInternal/Library/BuildRoots/4~CHzhugBmiKkrLLTG8fbnlM668ZQJqAQivd4DeiA/Library/Caches/com.apple.xbs/Sources/AppleSEPManager/AllocMPM.cpp"
- "/AppleInternal/Library/BuildRoots/4~CHzhugBmiKkrLLTG8fbnlM668ZQJqAQivd4DeiA/Library/Caches/com.apple.xbs/Sources/AppleSEPManager/AppleSEPBooter.cpp"
- "/AppleInternal/Library/BuildRoots/4~CHzhugBmiKkrLLTG8fbnlM668ZQJqAQivd4DeiA/Library/Caches/com.apple.xbs/Sources/AppleSEPManager/AppleSEPCommand.cpp"
- "/AppleInternal/Library/BuildRoots/4~CHzhugBmiKkrLLTG8fbnlM668ZQJqAQivd4DeiA/Library/Caches/com.apple.xbs/Sources/AppleSEPManager/AppleSEPControl.cpp"
- "/AppleInternal/Library/BuildRoots/4~CHzhugBmiKkrLLTG8fbnlM668ZQJqAQivd4DeiA/Library/Caches/com.apple.xbs/Sources/AppleSEPManager/AppleSEPCoreBuffer.cpp"
- "/AppleInternal/Library/BuildRoots/4~CHzhugBmiKkrLLTG8fbnlM668ZQJqAQivd4DeiA/Library/Caches/com.apple.xbs/Sources/AppleSEPManager/AppleSEPDebug.cpp"
- "/AppleInternal/Library/BuildRoots/4~CHzhugBmiKkrLLTG8fbnlM668ZQJqAQivd4DeiA/Library/Caches/com.apple.xbs/Sources/AppleSEPManager/AppleSEPDebugArgs.cpp"
- "/AppleInternal/Library/BuildRoots/4~CHzhugBmiKkrLLTG8fbnlM668ZQJqAQivd4DeiA/Library/Caches/com.apple.xbs/Sources/AppleSEPManager/AppleSEPDevice.cpp"
- "/AppleInternal/Library/BuildRoots/4~CHzhugBmiKkrLLTG8fbnlM668ZQJqAQivd4DeiA/Library/Caches/com.apple.xbs/Sources/AppleSEPManager/AppleSEPDiscovery.cpp"
- "/AppleInternal/Library/BuildRoots/4~CHzhugBmiKkrLLTG8fbnlM668ZQJqAQivd4DeiA/Library/Caches/com.apple.xbs/Sources/AppleSEPManager/AppleSEPEndpoint.cpp"
- "/AppleInternal/Library/BuildRoots/4~CHzhugBmiKkrLLTG8fbnlM668ZQJqAQivd4DeiA/Library/Caches/com.apple.xbs/Sources/AppleSEPManager/AppleSEPFirmware.cpp"
- "/AppleInternal/Library/BuildRoots/4~CHzhugBmiKkrLLTG8fbnlM668ZQJqAQivd4DeiA/Library/Caches/com.apple.xbs/Sources/AppleSEPManager/AppleSEPLogger.cpp"
- "/AppleInternal/Library/BuildRoots/4~CHzhugBmiKkrLLTG8fbnlM668ZQJqAQivd4DeiA/Library/Caches/com.apple.xbs/Sources/AppleSEPManager/AppleSEPManagerARM.cpp"
- "/AppleInternal/Library/BuildRoots/4~CHzhugBmiKkrLLTG8fbnlM668ZQJqAQivd4DeiA/Library/Caches/com.apple.xbs/Sources/AppleSEPManager/AppleSEPPairing.cpp"
- "/AppleInternal/Library/BuildRoots/4~CHzhugBmiKkrLLTG8fbnlM668ZQJqAQivd4DeiA/Library/Caches/com.apple.xbs/Sources/AppleSEPManager/AppleSEPSharedMemoryBuffer.cpp"
- "/AppleInternal/Library/BuildRoots/4~CHzhugBmiKkrLLTG8fbnlM668ZQJqAQivd4DeiA/Library/Caches/com.apple.xbs/Sources/AppleSEPManager/AppleSEPTesting.cpp"
- "/AppleInternal/Library/BuildRoots/4~CHzhugBmiKkrLLTG8fbnlM668ZQJqAQivd4DeiA/Library/Caches/com.apple.xbs/Sources/AppleSEPManager/AppleSEPTraceBuffer.cpp"
- "/AppleInternal/Library/BuildRoots/4~CHzhugBmiKkrLLTG8fbnlM668ZQJqAQivd4DeiA/Library/Caches/com.apple.xbs/Sources/AppleSEPManager/AppleSEPUserClient.cpp"
- "/AppleInternal/Library/BuildRoots/4~CHzhugBmiKkrLLTG8fbnlM668ZQJqAQivd4DeiA/Library/Caches/com.apple.xbs/Sources/AppleSEPManager/FIFO.h"
- "/AppleInternal/Library/BuildRoots/4~CHzhugBmiKkrLLTG8fbnlM668ZQJqAQivd4DeiA/Library/Caches/com.apple.xbs/Sources/AppleSEPManager/SEPApNonce.cpp"
- "/AppleInternal/Library/BuildRoots/4~CHzhugBmiKkrLLTG8fbnlM668ZQJqAQivd4DeiA/Library/Caches/com.apple.xbs/Sources/AppleSEPManager/SEPEpoch.cpp"
- "/AppleInternal/Library/BuildRoots/4~CHzhugBmiKkrLLTG8fbnlM668ZQJqAQivd4DeiA/Library/Caches/com.apple.xbs/Sources/AppleSEPManager/SEPROMPanicBuffer.cpp"
- "/AppleInternal/Library/BuildRoots/4~CHzhugBmiKkrLLTG8fbnlM668ZQJqAQivd4DeiA/Library/Caches/com.apple.xbs/Sources/AppleSEPManager/xART/AppleSEPXART.cpp"
- "/AppleInternal/Library/BuildRoots/4~CHzhugBmiKkrLLTG8fbnlM668ZQJqAQivd4DeiA/Library/Caches/com.apple.xbs/Sources/AppleSEPManager/xART/AppleSEPXART_embedded.cpp"
- "/AppleInternal/Library/BuildRoots/4~CHzhugBmiKkrLLTG8fbnlM668ZQJqAQivd4DeiA/Library/Caches/com.apple.xbs/Sources/AppleSEPManager/xART/DisableLog.cpp"
- "/AppleInternal/Library/BuildRoots/4~CHzhugBmiKkrLLTG8fbnlM668ZQJqAQivd4DeiA/Library/Caches/com.apple.xbs/Sources/AppleSEPManager/xART/gigalocker/gigalocker.cpp"
- "1211211222"

```
