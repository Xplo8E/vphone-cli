## com.apple.driver.AppleMobileFileIntegrity

> `com.apple.driver.AppleMobileFileIntegrity`

```diff

-1045.81.1.0.0
-  __TEXT.__cstring: 0x1c111
-  __TEXT.__const: 0x1b80
+1045.100.81.0.0
+  __TEXT.__cstring: 0x1ba00
+  __TEXT.__const: 0x1b68
   __TEXT.__os_log: 0x47a
-  __TEXT_EXEC.__text: 0x35530
+  __TEXT_EXEC.__text: 0x34748
   __TEXT_EXEC.__auth_stubs: 0x0
-  __DATA.__data: 0xbda
+  __DATA.__data: 0xa72
   __DATA.__common: 0xb0
   __DATA.__bss: 0x121
-  __DATA_CONST.__auth_got: 0x938
+  __DATA_CONST.__auth_got: 0x950
   __DATA_CONST.__got: 0x150
   __DATA_CONST.__auth_ptr: 0x28
   __DATA_CONST.__mod_init_func: 0x20
   __DATA_CONST.__mod_term_func: 0x18
-  __DATA_CONST.__const: 0xbf20
+  __DATA_CONST.__const: 0xbf78
   __DATA_CONST.__kalloc_type: 0x12c0
   __DATA_CONST.__kalloc_var: 0x1310
   __DATA_CONST.__assert: 0xdc
-  UUID: 5A056354-F139-3415-85EA-ECDE7A7E91A2
-  Functions: 1026
-  Symbols:   2182
-  CStrings:  3417
+  UUID: 4194BDA2-96B7-3224-95D8-DA796CC129D0
+  Functions: 1030
+  Symbols:   2187
+  CStrings:  3379
 
Symbols:
+ DeallocCredentialList.kalloc_type_view_1943
+ DeserializeCredentialList.kalloc_type_view_1905
+ LibCall_ACMContextLoadFromImage.kalloc_type_view_1570
+ LibCall_ACMContextLoadFromImage.kalloc_type_view_1631
+ _CEContextCreateAsLegacyContext
+ _CEDictionaryCheckSubset
+ _CEElementCheckSubset
+ _CEEnvironmentFree
+ _OUTLINED_FUNCTION_2
+ _OUTLINED_FUNCTION_3
+ _ZN14OSEntitlements17adjustWithMonitorEPK10_CEContext.cold.1
+ _ZN3TLE10RefCountedD0Ev.46
+ _ZN3TLE10RefCountedD1Ev.50
+ _ZN3TLE9Operation12shouldIgnoreEv.32
+ _ZN7libkern15safe_allocationINS_20intrusive_shared_ptrIN3TLE9OperationENS2_14RefCountPolicyEEEN9os_detail21IOKit_typed_allocatorIS5_Lb0EEENS6_21panic_trapping_policyEED1Ev.39
+ _ZN9os_detail21panic_trapping_policy4trapEPKc.34
+ _ZTVN3TLE10RefCountedE.40
+ _ZZN3TLE10RefCounteddlEPvmE20kalloc_type_view_101.47
+ _ZZN9os_detail21IOKit_typed_allocatorIN7libkern20intrusive_shared_ptrIN3TLE9OperationENS3_14RefCountPolicyEEELb0EE7kt_viewEvE7kt_view.51
+ __Block_byref_object_copy_.58
+ __Block_byref_object_copy_.63
+ __Block_byref_object_dispose_.59
+ __Block_byref_object_dispose_.64
+ __Z25CEElementCreateAsOSObjectPK10_CEElementPPK8OSObject
+ __Z27OSEntitlementsBridge_adjustPvP7cs_blobPK10_CEContext
+ __ZL30mte_data_tagging_override_list
+ __ZN14OSEntitlements17adjustWithMonitorEPK10_CEContext
+ __ZN14OSEntitlements6adjustEPK7cs_blobPK10_CEContext
+ __ZZL27_process_matches_constraintP4procyE21kalloc_type_view_5233
+ __ZZL27_process_matches_constraintP4procyE21kalloc_type_view_5256
+ __ZZN15ProcessAccessordlEPvE19kalloc_type_view_44
+ __ZZN15ProcessAccessornwEmE19kalloc_type_view_39
+ __ZZN20StaticPlatformPolicyILb1ELb1ELb0ELb1ELb0ELb1ELb1ELb0ELb0ELb1ELb0ELb1ELb0ELb0ELb1ELb0ELj2ELb1ELb0EE15check_signatureEP13VnodeLazyPathiP7cs_blobPjS5_ibbbjPPcPmE21kalloc_type_view_3003
+ __ZZN20StaticPlatformPolicyILb1ELb1ELb0ELb1ELb0ELb1ELb1ELb0ELb0ELb1ELb0ELb1ELb0ELb0ELb1ELb0ELj2ELb1ELb0EE15check_signatureEP13VnodeLazyPathiP7cs_blobPjS5_ibbbjPPcPmE21kalloc_type_view_3243
+ __ZZN20StaticPlatformPolicyILb1ELb1ELb1ELb1ELb1ELb1ELb1ELb0ELb1ELb0ELb1ELb0ELb1ELb1ELb0ELb0ELj1ELb1ELb0EE15check_signatureEP13VnodeLazyPathiP7cs_blobPjS5_ibbbjPPcPmE21kalloc_type_view_3003
+ __ZZN20StaticPlatformPolicyILb1ELb1ELb1ELb1ELb1ELb1ELb1ELb0ELb1ELb0ELb1ELb0ELb1ELb1ELb0ELb0ELj1ELb1ELb0EE15check_signatureEP13VnodeLazyPathiP7cs_blobPjS5_ibbbjPPcPmE21kalloc_type_view_3243
+ ____Z23hsp_proc_check_map_anonP4procP5ucredyyiiPi_block_invoke
+ ___keyValueLoop
+ ___matchLoop
+ __block_descriptor_tmp.10.196
+ __block_descriptor_tmp.130
+ __block_descriptor_tmp.178
+ __block_descriptor_tmp.189
+ __block_descriptor_tmp.26
+ __block_descriptor_tmp.29
+ __block_descriptor_tmp.32
+ __block_descriptor_tmp.321
+ __block_descriptor_tmp.35
+ __block_descriptor_tmp.411
+ __block_descriptor_tmp.44
+ __block_descriptor_tmp.454
+ __block_descriptor_tmp.47
+ __block_descriptor_tmp.471
+ __block_descriptor_tmp.49
+ __block_descriptor_tmp.5.322
+ __block_descriptor_tmp.53
+ __block_descriptor_tmp.62
+ __block_descriptor_tmp.68
+ __block_descriptor_tmp.75
+ __block_descriptor_tmp.9.323
+ _amfi_has_mte_data_tagging_override_impl
+ _buildIndex
+ _dictionarySubsetIterate
+ _keyFromIndex
+ _ml_satisfies_x86_64_requirements
+ _module3EntryConstraintCategory
+ _module3EntryFlags
+ _module3HashType
+ _module3UUID
+ _parseApplicationVN
+ _pmap_ce_allocate_acceleration_buffer
+ _pmap_ce_free_acceleration_buffer
+ _queryModule3
+ _sequenceSubsetIterate
+ _trustCacheQueryWithLength
+ _validateModule3
+ _validateSpecForString
- DeallocCredentialList.kalloc_type_view_1935
- DeserializeCredentialList.kalloc_type_view_1897
- LibCall_ACMContextLoadFromImage.kalloc_type_view_1479
- LibCall_ACMContextLoadFromImage.kalloc_type_view_1540
- _CEContextExecuteQuery
- _CEContextSetLegacyContext
- _ZN14OSEntitlements17adjustWithMonitorEPKv.cold.1
- _ZN14OSEntitlements17adjustWithMonitorEPKv.cold.2
- _ZN3TLE10RefCountedD0Ev.47
- _ZN3TLE10RefCountedD1Ev.51
- _ZN3TLE9Operation12shouldIgnoreEv.33
- _ZN7libkern15safe_allocationINS_20intrusive_shared_ptrIN3TLE9OperationENS2_14RefCountPolicyEEEN9os_detail21IOKit_typed_allocatorIS5_Lb0EEENS6_21panic_trapping_policyEED1Ev.40
- _ZN9os_detail21panic_trapping_policy4trapEPKc.35
- _ZTVN3TLE10RefCountedE.41
- _ZZN3TLE10RefCounteddlEPvmE20kalloc_type_view_101.48
- _ZZN9os_detail21IOKit_typed_allocatorIN7libkern20intrusive_shared_ptrIN3TLE9OperationENS3_14RefCountPolicyEEELb0EE7kt_viewEvE7kt_view.52
- __Block_byref_object_copy_.59
- __Block_byref_object_copy_.64
- __Block_byref_object_dispose_.60
- __Block_byref_object_dispose_.65
- __Z25CEElementCreateAsOSObjectPK14der_vm_contextPPK8OSObject
- __Z38OSEntitlementsBridge_adjustWithMonitorPvP14CEQueryContextPKvPKcj
- __Z41OSEntitlementsBridge_adjustWithoutMonitorPvP7cs_blob
- __ZL28mte_data_tagging_opt_in_list
- __ZL28mte_inheritance_opt_out_list
- __ZN14OSEntitlements17adjustWithMonitorEPKv
- __ZN14OSEntitlements6adjustEPK7cs_blobPKv
- __ZZL27_process_matches_constraintP4procyE21kalloc_type_view_5239
- __ZZL27_process_matches_constraintP4procyE21kalloc_type_view_5262
- __ZZN15ProcessAccessordlEPvE19kalloc_type_view_43
- __ZZN15ProcessAccessornwEmE19kalloc_type_view_38
- __ZZN20StaticPlatformPolicyILb1ELb1ELb0ELb1ELb0ELb1ELb1ELb0ELb0ELb1ELb0ELb1ELb0ELb0ELb1ELb0ELj2ELb1ELb0EE15check_signatureEP13VnodeLazyPathiP7cs_blobPjS5_ibbbjPPcPmE21kalloc_type_view_2998
- __ZZN20StaticPlatformPolicyILb1ELb1ELb0ELb1ELb0ELb1ELb1ELb0ELb0ELb1ELb0ELb1ELb0ELb0ELb1ELb0ELj2ELb1ELb0EE15check_signatureEP13VnodeLazyPathiP7cs_blobPjS5_ibbbjPPcPmE21kalloc_type_view_3238
- __ZZN20StaticPlatformPolicyILb1ELb1ELb1ELb1ELb1ELb1ELb1ELb0ELb1ELb0ELb1ELb0ELb1ELb1ELb0ELb0ELj1ELb1ELb0EE15check_signatureEP13VnodeLazyPathiP7cs_blobPjS5_ibbbjPPcPmE21kalloc_type_view_2998
- __ZZN20StaticPlatformPolicyILb1ELb1ELb1ELb1ELb1ELb1ELb1ELb0ELb1ELb0ELb1ELb0ELb1ELb1ELb0ELb0ELj1ELb1ELb0EE15check_signatureEP13VnodeLazyPathiP7cs_blobPjS5_ibbbjPPcPmE21kalloc_type_view_3238
- ___der_vm_iterate_count_block_invoke
- __block_descriptor_tmp.10.212
- __block_descriptor_tmp.132
- __block_descriptor_tmp.190
- __block_descriptor_tmp.203
- __block_descriptor_tmp.30
- __block_descriptor_tmp.33
- __block_descriptor_tmp.337
- __block_descriptor_tmp.37
- __block_descriptor_tmp.406
- __block_descriptor_tmp.41
- __block_descriptor_tmp.449
- __block_descriptor_tmp.466
- __block_descriptor_tmp.48
- __block_descriptor_tmp.5.338
- __block_descriptor_tmp.50
- __block_descriptor_tmp.54
- __block_descriptor_tmp.63
- __block_descriptor_tmp.69
- __block_descriptor_tmp.7
- __block_descriptor_tmp.76
- __block_descriptor_tmp.9.339
- _amfi_has_mte_data_tagging_opt_in_impl
- _amfi_has_mte_inheritance_opt_out_impl
- _derVMIterateCallback
- _der_vm_CEType_from_ccder_tag
- _validateContextWithType
- _validateDictionary
- _validateDuplicateKeys
- _validateDuplicateKeysSub
- _validateKeyValuePair
- _validateSingleType
- _validateSpec
- _validateSpecForApplication
- _validateString
- _validateValueTypePair
- mapToCEReturn.1
- mapToCEReturn.4
CStrings:
+ "(data && dataLength && dataLength <= kACMControlMaxDataLength) || (!data && !dataLength)"
+ "(data && dataLength && dataLength <= kACMEnvironmentVariableMaxDataLength) || (!data && !dataLength)"
+ "(keybagUuid && keybagUuidLength == UUID_LEN) || (!keybagUuid && !keybagUuidLength)"
+ "*"
+ "/AppleInternal/Library/BuildRoots/4~CJ8MugBV5w78PBSFH882o7t-Z0DZH7wKyzQUEYY/Library/Caches/com.apple.xbs/TemporaryDirectory.LwaIN9/Sources/AppleCredentialManager_KernelLibs/ACMKernelLib/ACMKernelTransport.cpp"
+ "/AppleInternal/Library/BuildRoots/4~CJ8MugBV5w78PBSFH882o7t-Z0DZH7wKyzQUEYY/Library/Caches/com.apple.xbs/TemporaryDirectory.LwaIN9/Sources/AppleCredentialManager_KernelLibs/common/CommonMem.c"
+ "/AppleInternal/Library/BuildRoots/4~CJ8MugBV5w78PBSFH882o7t-Z0DZH7wKyzQUEYY/Library/Caches/com.apple.xbs/TemporaryDirectory.LwaIN9/Sources/AppleCredentialManager_KernelLibs/common/LibCall.c"
+ "19:17:10"
+ "B16@?0r*8"
+ "CoreEntitlements: subset | %.*s: 0x%04X\n"
+ "HardenedSystemPolicy: (%d) (%s) allowing due to x86_64 compat entitlement\n"
+ "Mar 19 2026"
+ "S24@?0r^{_CEKeyValuePair={_CEElement={?=*Q}{?=Q{?=*Q}}}{_CEValueTypePair=I{_CEElement={?=*Q}{?=Q{?=*Q}}}}}8^{_CEIterateArgs=Q^vB}16"
+ "UTIL_OPTIONAL_BUFFER(outBuffer,outSize)"
+ "cmd = (acm_command_t *)acm_malloc_data(cmdSize)"
+ "com.apple.aa"
+ "com.apple.aa-internal"
+ "com.apple.aea"
+ "com.apple.aea-internal"
+ "com.apple.contactsd"
+ "com.apple.internal.arm_mte_data_tagging_opt_out_test"
+ "com.apple.mdutil"
+ "os_add_overflow(sizeof(acm_command_t), dataSize, &cmdSize) == 0 "
+ "v16@?0r^{_OSEntitlementsReadOnly=^{OSEntitlements}{_CEContext={_CEContextInfo=CI}{_CEElement={?=*Q}{?=Q{?=*Q}}}^{_CEElementIndex}Q{CEQueryContext={der_vm_context=^{CERuntime}{CEAccelerationContext=^{CEAccelerationElement}Q}QBB(?={ccder_read_blob=**}{?=**})}B}B}^{_CEContext}*{?=^{__SC_GenericBlob}}{?=BB}}8"
- "\"AMFI: unable to update legacy context: %u\" @%s:%d"
- "( ((outSize != nullptr && *outSize > 0) && outBuffer != nullptr) || ((outSize == nullptr || *outSize == 0) && outBuffer == nullptr) )"
- "(data && dataLength && dataLength <= 128) || (!data && !dataLength)"
- "(data && dataLength && dataLength <= 4096) || (!data && !dataLength)"
- "(keybagUuid && keybagUuidLength == 16) || (!keybagUuid && !keybagUuidLength)"
- "/AppleInternal/Library/BuildRoots/4~CG4MugA3N0m8W_Z-RmNueDtLYLtrwuDkDkermW4/Library/Caches/com.apple.xbs/Sources/AppleCredentialManager_KernelLibs/ACMKernelLib/ACMKernelTransport.cpp"
- "/AppleInternal/Library/BuildRoots/4~CG4MugA3N0m8W_Z-RmNueDtLYLtrwuDkDkermW4/Library/Caches/com.apple.xbs/Sources/AppleCredentialManager_KernelLibs/common/CommonMem.c"
- "/AppleInternal/Library/BuildRoots/4~CG4MugA3N0m8W_Z-RmNueDtLYLtrwuDkDkermW4/Library/Caches/com.apple.xbs/Sources/AppleCredentialManager_KernelLibs/common/LibCall.c"
- "20:38:03"
- "CoreEntitlements: %.*s | validate: 0x%04X\n"
- "CoreEntitlements: duplicate key | %.*s\n"
- "Jan 28 2026"
- "S24@?0r^{_CEKeyValuePair={der_vm_context=^{CERuntime}{CEAccelerationContext=^{CEAccelerationElement}Q}QBB(?={ccder_read_blob=**}{?=**})}{_CEValueTypePair=I{der_vm_context=^{CERuntime}{CEAccelerationContext=^{CEAccelerationElement}Q}QBB(?={ccder_read_blob=**}{?=**})}}}8^{_CEIterateArgs=^vQQBS}16"
- "__os_warn_unused(__builtin_add_overflow((sizeof(acm_command_t)), (dataSize), (&cmdSize))) == 0 "
- "cmd = (acm_command_t *)({ size_t sizeVal = (cmdSize); void *ptr = acm_mem_alloc_data(sizeVal); acm_mem_alloc_info(\"<data>\", ptr, sizeVal, \"/AppleInternal/Library/BuildRoots/4~CG4MugA3N0m8W_Z-RmNueDtLYLtrwuDkDkermW4/Library/Caches/com.apple.xbs/Sources/AppleCredentialManager_KernelLibs/common/LibCall.c\", 22, __func__); ptr; })"
- "com.apple.DriverKit-AppleBCMWLAN"
- "com.apple.FTLivePhotoService"
- "com.apple.GenerativePlaygroundApp.MessagesExtension"
- "com.apple.ImageIO.imageimporter"
- "com.apple.MADownloadServiceBuiltin"
- "com.apple.PDFKit.PDFImporter"
- "com.apple.PassbookUIService.PeerPaymentMessagesExtension"
- "com.apple.Photos.CPLDiagnose"
- "com.apple.SharePlay.NearbyInvitationsService"
- "com.apple.Spotlight"
- "com.apple.TelephonyUtilities.PhoneIntentHandler"
- "com.apple.UserEventAgent"
- "com.apple.VoiceMemos.SpotlightIndexExtension"
- "com.apple.WebKit.Networking"
- "com.apple.WebKit.WebContent.EnhancedSecurity"
- "com.apple.WorkflowKit.BackgroundShortcutRunner"
- "com.apple.WorkflowKit.ShortcutsIntents"
- "com.apple.accessoryd"
- "com.apple.accountsd"
- "com.apple.audiomxd"
- "com.apple.avconferenced"
- "com.apple.backupd"
- "com.apple.captiveagent"
- "com.apple.contacts.ContactsCoreSpotlightExtension"
- "com.apple.contextstored"
- "com.apple.coreduetd"
- "com.apple.eapolclient"
- "com.apple.iBooks.iBooksSpotlightExtension"
- "com.apple.icloud.findmydeviced"
- "com.apple.internal.arm_mte_data_tagging_opt_in_test"
- "com.apple.internal.arm_mte_inheritance_opt_out_test"
- "com.apple.mobileassetd"
- "com.apple.podcasts.SpotlightIndexExtension"
- "com.apple.quicklook.externalSatellite.arm64"
- "com.apple.reminders.spotlightindexextension"
- "com.apple.sbd"
- "com.apple.security.cryptexd"
- "com.apple.siri.SiriGeo.SiriGeoAppIntentExtension"
- "com.apple.siri.SiriNotificationsAppIntentsExtension"
- "com.apple.siri.SiriVideoAppIntents"
- "com.apple.siri.messages.SiriMessagesAppIntentsExtension"
- "com.apple.siriactionsd"
- "com.apple.spotlightknowledged.updater"
- "com.apple.thermalmonitord"
- "der_vm_container_from_context"
- "der_vm_iterate_nocopy"
- "v16@?0r^{_OSEntitlementsReadOnly=^{OSEntitlements}{_CEContext={_CEContextInfo=CI}{CEQueryContext={der_vm_context=^{CERuntime}{CEAccelerationContext=^{CEAccelerationElement}Q}QBB(?={ccder_read_blob=**}{?=**})}B}}^{_CEContext}*{?=^{__SC_GenericBlob}}{?=BB}}8"

```
