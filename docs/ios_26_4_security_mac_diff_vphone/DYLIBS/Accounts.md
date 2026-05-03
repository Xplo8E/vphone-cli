## Accounts

> `/System/Library/Frameworks/Accounts.framework/Versions/A/Accounts`

```diff

-1025.0.0.0.0
-  __TEXT.__text: 0x64498
-  __TEXT.__auth_stubs: 0xb50
-  __TEXT.__objc_methlist: 0x42c4
+1035.0.0.0.0
+  __TEXT.__text: 0x64844
+  __TEXT.__auth_stubs: 0xb40
+  __TEXT.__objc_methlist: 0x42d4
   __TEXT.__const: 0x190
-  __TEXT.__gcc_except_tab: 0x3f78
+  __TEXT.__gcc_except_tab: 0x3f94
   __TEXT.__cstring: 0x3d9b
   __TEXT.__oslogstring: 0x536c
-  __TEXT.__unwind_info: 0x1ab0
+  __TEXT.__unwind_info: 0x1cd0
   __TEXT.__objc_classname: 0x599
-  __TEXT.__objc_methname: 0x89b7
+  __TEXT.__objc_methname: 0x89d3
   __TEXT.__objc_methtype: 0x1523
-  __TEXT.__objc_stubs: 0x6580
+  __TEXT.__objc_stubs: 0x65c0
   __DATA_CONST.__got: 0x388
   __DATA_CONST.__const: 0xf00
   __DATA_CONST.__objc_classlist: 0x1a8
   __DATA_CONST.__objc_catlist: 0x30
   __DATA_CONST.__objc_protolist: 0x60
   __DATA_CONST.__objc_imageinfo: 0x8
-  __DATA_CONST.__objc_selrefs: 0x2280
+  __DATA_CONST.__objc_selrefs: 0x2288
   __DATA_CONST.__objc_protorefs: 0x20
   __DATA_CONST.__objc_superrefs: 0x140
   __DATA_CONST.__objc_arraydata: 0x28
-  __AUTH_CONST.__auth_got: 0x5b8
-  __AUTH_CONST.__const: 0x1c50
+  __AUTH_CONST.__auth_got: 0x5b0
+  __AUTH_CONST.__const: 0x1c80
   __AUTH_CONST.__cfstring: 0x4980
   __AUTH_CONST.__objc_const: 0x5e40
   __AUTH_CONST.__objc_intobj: 0x558

   - /System/Library/PrivateFrameworks/UserManagement.framework/Versions/A/UserManagement
   - /usr/lib/libSystem.B.dylib
   - /usr/lib/libobjc.A.dylib
-  UUID: EC98CFB9-C721-331F-B24E-EEFBAE3A69A3
-  Functions: 2005
-  Symbols:   4784
-  CStrings:  3458
+  UUID: 6EE0898E-75B7-3B03-B339-0593C023AA2F
+  Functions: 2024
+  Symbols:   4835
+  CStrings:  3459
 
Symbols:
+ -[ACAccountStoreCache clearCachedAccountsForType:]
+ _OUTLINED_FUNCTION_14
+ __114-[ACAccountStore openAuthenticationURLForAccount:withDelegateClassName:fromBundleAtPath:shouldConfirm:completion:]_block_invoke.363
+ __28-[ACAccountStore handleURL:]_block_invoke.403
+ __28-[ACAccountStore handleURL:]_block_invoke.403.cold.1
+ __28-[ACAccountStore handleURL:]_block_invoke.403.cold.2
+ __33-[ACAccountStore _uidOfAccountsd]_block_invoke.416
+ __36-[ACAccountStore shutdownAccountsD:]_block_invoke.411
+ __36-[ACAccountStore shutdownAccountsD:]_block_invoke_2.412
+ __40-[ACAccountStore clientTokenForAccount:]_block_invoke.339
+ __41-[ACAccountStore removeObsoleteAccounts:]_block_invoke.380
+ __44-[ACAccountStore addClientToken:forAccount:]_block_invoke.342
+ __45-[ACAccountStore credentialForAccount:error:]_block_invoke.274
+ __45-[ACAccountStore runAccountMigrationPlugins:]_block_invoke.265
+ __45-[ACAccountStore runAccountMigrationPlugins:]_block_invoke.270
+ __46-[ACAccountStore scheduleBackupIfNonexistent:]_block_invoke.406
+ __46-[ACAccountStore scheduleBackupIfNonexistent:]_block_invoke.408
+ __46-[ACAccountStore scheduleBackupIfNonexistent:]_block_invoke_2.407
+ __46-[ACAccountStore scheduleBackupIfNonexistent:]_block_invoke_2.407.cold.1
+ __48-[ACAccountStore childAccountsForAccount:error:]_block_invoke.299
+ __48-[ACAccountStore parentAccountForAccount:error:]_block_invoke.296
+ __53-[ACAccountStore enabledDataclassesForAccount:error:]_block_invoke.307
+ __54-[ACAccountStore triggerKeychainMigrationIfNecessary:]_block_invoke.377
+ __55-[ACAccountStore credentialForAccount:serviceID:error:]_block_invoke.275
+ __55-[ACAccountStore dataclassActionsForAccountSave:error:]_block_invoke.321
+ __55-[ACAccountStore preloadDataclassOwnersWithCompletion:]_block_invoke.317
+ __55-[ACAccountStore preloadDataclassOwnersWithCompletion:]_block_invoke_2.318
+ __56-[ACAccountStore resetDatabaseToVersion:withCompletion:]_block_invoke.409
+ __56-[ACAccountStore resetDatabaseToVersion:withCompletion:]_block_invoke_2.410
+ __57-[ACAccountStore migrateCredentialForAccount:completion:]_block_invoke.256
+ __57-[ACAccountStore migrateCredentialForAccount:completion:]_block_invoke.264
+ __57-[ACAccountStore provisionedDataclassesForAccount:error:]_block_invoke.308
+ __59-[ACAccountStore dataclassActionsForAccountDeletion:error:]_block_invoke.322
+ __59-[ACAccountStore saveCredentialItem:withCompletionHandler:]_block_invoke.294
+ __59-[ACAccountStore setCredential:forAccount:serviceID:error:]_block_invoke.277
+ __61-[ACAccountStore _removeObsoleteAccountsInternal:completion:]_block_invoke.384
+ __61-[ACAccountStore insertCredentialItem:withCompletionHandler:]_block_invoke.287
+ __61-[ACAccountStore insertCredentialItem:withCompletionHandler:]_block_invoke.291
+ __61-[ACAccountStore insertCredentialItem:withCompletionHandler:]_block_invoke_2.288
+ __61-[ACAccountStore removeCredentialItem:withCompletionHandler:]_block_invoke.295
+ __63-[ACAccountStore isPerformingDataclassActionsForAccount:error:]_block_invoke.325
+ __64-[ACAccountStore renewCredentialsForAccount:options:completion:]_block_invoke.246
+ __64-[ACAccountStore renewCredentialsForAccount:options:completion:]_block_invoke.255
+ __65-[ACAccountStore verifyCredentialsForAccount:options:completion:]_block_invoke.245
+ __66-[ACAccountStore discoverPropertiesForAccount:options:completion:]_block_invoke.343
+ __67-[ACAccountStore saveAccount:toPairedDeviceWithOptions:completion:]_block_invoke.366
+ __67-[ACAccountStore saveAccount:toPairedDeviceWithOptions:completion:]_block_invoke.368
+ __67-[ACAccountStore saveAccount:toPairedDeviceWithOptions:completion:]_block_invoke_2.367
+ __67-[ACAccountStore saveAccount:toPairedDeviceWithOptions:completion:]_block_invoke_2.367.cold.1
+ __71-[ACAccountStore removeAccountFromPairedDevice:withOptions:completion:]_block_invoke.372
+ __71-[ACAccountStore removeAccountFromPairedDevice:withOptions:completion:]_block_invoke.374
+ __71-[ACAccountStore removeAccountFromPairedDevice:withOptions:completion:]_block_invoke_2.373
+ __71-[ACAccountStore removeAccountFromPairedDevice:withOptions:completion:]_block_invoke_2.373.cold.1
+ __71-[ACAccountStore removeAccountsFromPairedDeviceWithOptions:completion:]_block_invoke.369
+ __71-[ACAccountStore removeAccountsFromPairedDeviceWithOptions:completion:]_block_invoke.371
+ __71-[ACAccountStore removeAccountsFromPairedDeviceWithOptions:completion:]_block_invoke_2.370
+ __71-[ACAccountStore removeAccountsFromPairedDeviceWithOptions:completion:]_block_invoke_2.370.cold.1
+ __76-[ACAccountStore openAuthenticationURL:forAccount:shouldConfirm:completion:]_block_invoke.347
+ __76-[ACAccountStore openAuthenticationURL:forAccount:shouldConfirm:completion:]_block_invoke_2.348
+ __78-[ACAccountStore notifyRemoteDevicesOfModifiedAccount:withOptions:completion:]_block_invoke.364
+ __78-[ACAccountStore notifyRemoteDevicesOfModifiedAccount:withOptions:completion:]_block_invoke.364.cold.1
+ __81-[ACAccountStore notifyRemoteDevicesOfUpdatedCredentials:withOptions:completion:]_block_invoke.365
+ __81-[ACAccountStore notifyRemoteDevicesOfUpdatedCredentials:withOptions:completion:]_block_invoke.365.cold.1
+ __96-[ACAccountStore accountIdentifiersEnabledForDataclasses:withAccountTypeIdentifiers:completion:]_block_invoke.335
+ __96-[ACAccountStore accountIdentifiersEnabledForDataclasses:withAccountTypeIdentifiers:completion:]_block_invoke_2.336
+ ___50-[ACAccountStoreCache clearCachedAccountsForType:]_block_invoke
+ ___block_descriptor_64_e8_32s40s48s56bs_e31_v24?0"ACAccount"8"NSError"16l
+ __block_literal_global.379
+ __block_literal_global.418
+ _objc_msgSend$clearCachedAccounts
+ _objc_msgSend$clearCachedAccountsForType:
- __114-[ACAccountStore openAuthenticationURLForAccount:withDelegateClassName:fromBundleAtPath:shouldConfirm:completion:]_block_invoke.357
- __28-[ACAccountStore handleURL:]_block_invoke.400
- __28-[ACAccountStore handleURL:]_block_invoke.400.cold.1
- __28-[ACAccountStore handleURL:]_block_invoke.400.cold.2
- __33-[ACAccountStore _uidOfAccountsd]_block_invoke.413
- __36-[ACAccountStore shutdownAccountsD:]_block_invoke.408
- __36-[ACAccountStore shutdownAccountsD:]_block_invoke_2.409
- __40-[ACAccountStore clientTokenForAccount:]_block_invoke.336
- __41-[ACAccountStore removeObsoleteAccounts:]_block_invoke.377
- __44-[ACAccountStore addClientToken:forAccount:]_block_invoke.339
- __45-[ACAccountStore credentialForAccount:error:]_block_invoke.271
- __45-[ACAccountStore runAccountMigrationPlugins:]_block_invoke.262
- __45-[ACAccountStore runAccountMigrationPlugins:]_block_invoke.267
- __46-[ACAccountStore scheduleBackupIfNonexistent:]_block_invoke.403
- __46-[ACAccountStore scheduleBackupIfNonexistent:]_block_invoke.405
- __46-[ACAccountStore scheduleBackupIfNonexistent:]_block_invoke_2.404
- __46-[ACAccountStore scheduleBackupIfNonexistent:]_block_invoke_2.404.cold.1
- __48-[ACAccountStore childAccountsForAccount:error:]_block_invoke.296
- __48-[ACAccountStore parentAccountForAccount:error:]_block_invoke.293
- __53-[ACAccountStore enabledDataclassesForAccount:error:]_block_invoke.304
- __54-[ACAccountStore triggerKeychainMigrationIfNecessary:]_block_invoke.374
- __55-[ACAccountStore credentialForAccount:serviceID:error:]_block_invoke.272
- __55-[ACAccountStore dataclassActionsForAccountSave:error:]_block_invoke.318
- __55-[ACAccountStore preloadDataclassOwnersWithCompletion:]_block_invoke.314
- __55-[ACAccountStore preloadDataclassOwnersWithCompletion:]_block_invoke_2.315
- __56-[ACAccountStore resetDatabaseToVersion:withCompletion:]_block_invoke.406
- __56-[ACAccountStore resetDatabaseToVersion:withCompletion:]_block_invoke_2.407
- __57-[ACAccountStore migrateCredentialForAccount:completion:]_block_invoke.253
- __57-[ACAccountStore migrateCredentialForAccount:completion:]_block_invoke.258
- __57-[ACAccountStore provisionedDataclassesForAccount:error:]_block_invoke.305
- __59-[ACAccountStore dataclassActionsForAccountDeletion:error:]_block_invoke.319
- __59-[ACAccountStore saveCredentialItem:withCompletionHandler:]_block_invoke.291
- __59-[ACAccountStore setCredential:forAccount:serviceID:error:]_block_invoke.274
- __61-[ACAccountStore _removeObsoleteAccountsInternal:completion:]_block_invoke.381
- __61-[ACAccountStore insertCredentialItem:withCompletionHandler:]_block_invoke.284
- __61-[ACAccountStore insertCredentialItem:withCompletionHandler:]_block_invoke.288
- __61-[ACAccountStore insertCredentialItem:withCompletionHandler:]_block_invoke_2.285
- __61-[ACAccountStore removeCredentialItem:withCompletionHandler:]_block_invoke.292
- __63-[ACAccountStore isPerformingDataclassActionsForAccount:error:]_block_invoke.322
- __64-[ACAccountStore renewCredentialsForAccount:options:completion:]_block_invoke.243
- __64-[ACAccountStore renewCredentialsForAccount:options:completion:]_block_invoke.249
- __66-[ACAccountStore discoverPropertiesForAccount:options:completion:]_block_invoke.340
- __67-[ACAccountStore saveAccount:toPairedDeviceWithOptions:completion:]_block_invoke.363
- __67-[ACAccountStore saveAccount:toPairedDeviceWithOptions:completion:]_block_invoke.365
- __67-[ACAccountStore saveAccount:toPairedDeviceWithOptions:completion:]_block_invoke_2.364
- __67-[ACAccountStore saveAccount:toPairedDeviceWithOptions:completion:]_block_invoke_2.364.cold.1
- __71-[ACAccountStore removeAccountFromPairedDevice:withOptions:completion:]_block_invoke.369
- __71-[ACAccountStore removeAccountFromPairedDevice:withOptions:completion:]_block_invoke.371
- __71-[ACAccountStore removeAccountFromPairedDevice:withOptions:completion:]_block_invoke_2.370
- __71-[ACAccountStore removeAccountFromPairedDevice:withOptions:completion:]_block_invoke_2.370.cold.1
- __71-[ACAccountStore removeAccountsFromPairedDeviceWithOptions:completion:]_block_invoke.366
- __71-[ACAccountStore removeAccountsFromPairedDeviceWithOptions:completion:]_block_invoke.368
- __71-[ACAccountStore removeAccountsFromPairedDeviceWithOptions:completion:]_block_invoke_2.367
- __71-[ACAccountStore removeAccountsFromPairedDeviceWithOptions:completion:]_block_invoke_2.367.cold.1
- __76-[ACAccountStore openAuthenticationURL:forAccount:shouldConfirm:completion:]_block_invoke.344
- __76-[ACAccountStore openAuthenticationURL:forAccount:shouldConfirm:completion:]_block_invoke_2.345
- __78-[ACAccountStore notifyRemoteDevicesOfModifiedAccount:withOptions:completion:]_block_invoke.361
- __78-[ACAccountStore notifyRemoteDevicesOfModifiedAccount:withOptions:completion:]_block_invoke.361.cold.1
- __81-[ACAccountStore notifyRemoteDevicesOfUpdatedCredentials:withOptions:completion:]_block_invoke.362
- __81-[ACAccountStore notifyRemoteDevicesOfUpdatedCredentials:withOptions:completion:]_block_invoke.362.cold.1
- __96-[ACAccountStore accountIdentifiersEnabledForDataclasses:withAccountTypeIdentifiers:completion:]_block_invoke.332
- __96-[ACAccountStore accountIdentifiersEnabledForDataclasses:withAccountTypeIdentifiers:completion:]_block_invoke_2.333
- ___65-[ACAccountStore verifyCredentialsForAccount:options:completion:]_block_invoke_3
- __block_literal_global.376
- __block_literal_global.415
- _objc_retainAutoreleaseReturnValue
CStrings:
+ "clearCachedAccountsForType:"

```

