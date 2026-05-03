## LocalAuthentication

> `/System/Library/Frameworks/LocalAuthentication.framework/Versions/A/LocalAuthentication`

```diff

-2005.80.10.0.0
-  __TEXT.__text: 0x4db48
-  __TEXT.__auth_stubs: 0xdc0
-  __TEXT.__objc_methlist: 0x3d88
-  __TEXT.__const: 0x650
-  __TEXT.__gcc_except_tab: 0x1284
-  __TEXT.__cstring: 0x32ba
+2005.100.186.0.0
+  __TEXT.__text: 0x4d45c
+  __TEXT.__auth_stubs: 0xe00
+  __TEXT.__objc_methlist: 0x3d50
+  __TEXT.__const: 0x660
+  __TEXT.__gcc_except_tab: 0x1120
+  __TEXT.__cstring: 0x2397
   __TEXT.__dlopen_cstrs: 0x177
-  __TEXT.__oslogstring: 0x2c6b
+  __TEXT.__oslogstring: 0x2ebb
   __TEXT.__swift5_typeref: 0x240
   __TEXT.__constg_swiftt: 0x4a4
   __TEXT.__swift5_reflstr: 0xc9

   __TEXT.__swift5_builtin: 0x3c
   __TEXT.__swift5_assocty: 0x30
   __TEXT.__swift5_proto: 0x14
-  __TEXT.__unwind_info: 0x1a38
-  __TEXT.__eh_frame: 0x6a0
-  __TEXT.__objc_classname: 0x77e
-  __TEXT.__objc_methname: 0x7484
-  __TEXT.__objc_methtype: 0x1cd2
-  __TEXT.__objc_stubs: 0x4140
-  __DATA_CONST.__got: 0x628
+  __TEXT.__unwind_info: 0x19f8
+  __TEXT.__eh_frame: 0x850
+  __TEXT.__objc_classname: 0xee1
+  __TEXT.__objc_methname: 0x79c4
+  __TEXT.__objc_methtype: 0x1e05
+  __TEXT.__objc_stubs: 0x4ec0
+  __DATA_CONST.__got: 0x658
   __DATA_CONST.__const: 0x330
-  __DATA_CONST.__objc_classlist: 0x318
-  __DATA_CONST.__objc_protolist: 0xf8
+  __DATA_CONST.__objc_classlist: 0x310
+  __DATA_CONST.__objc_protolist: 0x100
   __DATA_CONST.__objc_imageinfo: 0x8
-  __DATA_CONST.__objc_selrefs: 0x1ec0
+  __DATA_CONST.__objc_selrefs: 0x1ee0
   __DATA_CONST.__objc_protorefs: 0x48
-  __DATA_CONST.__objc_superrefs: 0x160
+  __DATA_CONST.__objc_superrefs: 0x158
   __DATA_CONST.__objc_arraydata: 0x18
-  __AUTH_CONST.__auth_got: 0x6f0
-  __AUTH_CONST.__const: 0x2018
-  __AUTH_CONST.__cfstring: 0x1700
-  __AUTH_CONST.__objc_const: 0x8568
-  __AUTH_CONST.__objc_intobj: 0x1e0
+  __AUTH_CONST.__auth_got: 0x710
+  __AUTH_CONST.__const: 0x1e68
+  __AUTH_CONST.__cfstring: 0x16e0
+  __AUTH_CONST.__objc_const: 0x8450
+  __AUTH_CONST.__objc_intobj: 0x1f8
   __AUTH_CONST.__objc_arrayobj: 0x18
   __AUTH.__objc_data: 0x11d8
   __AUTH.__data: 0xc20
-  __DATA.__objc_ivar: 0x250
-  __DATA.__data: 0xdb0
-  __DATA.__bss: 0x550
+  __DATA.__objc_ivar: 0x244
+  __DATA.__data: 0xe10
+  __DATA.__bss: 0x540
   __DATA.__common: 0x18
-  __DATA_DIRTY.__objc_data: 0xf78
+  __DATA_DIRTY.__objc_data: 0xf28
   __DATA_DIRTY.__data: 0x28
-  __DATA_DIRTY.__bss: 0xd0
+  __DATA_DIRTY.__bss: 0x50
   - /System/Library/Frameworks/Combine.framework/Versions/A/Combine
   - /System/Library/Frameworks/CoreFoundation.framework/Versions/A/CoreFoundation
   - /System/Library/Frameworks/Foundation.framework/Versions/C/Foundation

   - /usr/lib/swift/libswiftXPC.dylib
   - /usr/lib/swift/libswift_Builtin_float.dylib
   - /usr/lib/swift/libswiftos.dylib
-  UUID: 6034EF89-4F89-3FE5-9A14-8E24CC1ACBEC
-  Functions: 2080
-  Symbols:   3802
-  CStrings:  2449
+  UUID: 9AA51AF9-13CA-3739-AC3F-BA836E772A7D
+  Functions: 2057
+  Symbols:   3880
+  CStrings:  2403
 
Symbols:
+ +[LARightStore makeStore]
+ -[LAClient _connectToServerWithRecovery:userSession:legacyService:].cold.1
+ -[LAClient externalizedContextProvider]
+ -[LAClient externalizedContextWithError:]
+ -[LAClient setExternalizedContextProvider:]
+ -[LAContext optionIgnoreExistingDoublePress]
+ -[LAContext setOptionIgnoreExistingDoublePress:]
+ GCC_except_table184
+ GCC_except_table189
+ GCC_except_table24
+ GCC_except_table27
+ GCC_except_table35
+ GCC_except_table39
+ GCC_except_table46
+ GCC_except_table49
+ GCC_except_table50
+ GCC_except_table57
+ GCC_except_table66
+ GCC_except_table71
+ OBJC_IVAR_$_LAClient._externalizedContextProvider
+ _LACErrorCodeInternal
+ _LACErrorCodeNotFound
+ _LACErrorCodeRequestFailed
+ _LACErrorDomain
+ _LACLogAuthorization
+ _LACLogStorage
+ _LACUserIdentityCreationPolicyAutomatic
+ _LAUserErrorCodePolicy
+ _OBJC_CLASS_$_LACExternalizedContextProvider
+ _OBJC_CLASS_$_LACInstanceIDGenerator
+ _OBJC_CLASS_$_LACUserCredentialHash
+ _OBJC_CLASS_$_LACUserPasswordHash
+ _OUTLINED_FUNCTION_10
+ _OUTLINED_FUNCTION_11
+ _OUTLINED_FUNCTION_12
+ __32-[LAStorage _connectToEndpoint:]_block_invoke.113
+ __43-[LARight authorizeWithOptions:completion:]_block_invoke.96
+ __43-[LARight checkCanAuthorizeWithCompletion:]_block_invoke.87
+ __44-[LAStorage processError:completionHandler:]_block_invoke.30
+ __51-[LAStorage exchangeData:forKey:completionHandler:]_block_invoke.26
+ __56-[LARightStore _saveRight:identifier:secret:completion:]_block_invoke.63
+ __56-[LARightStore _saveRight:identifier:secret:completion:]_block_invoke_2.59
+ __56-[LARightStore _saveRight:identifier:secret:completion:]_block_invoke_2.64
+ __68-[LAStorage _callProxyBlock:authenticationPolicy:completionHandler:]_block_invoke.120
+ __INSTANCE_METHODS_LAUserStore
+ __OBJC_$_PROTOCOL_INSTANCE_METHODS_LACContextExternalizingXPC
+ __OBJC_$_PROTOCOL_INSTANCE_METHODS_LACContextObserver
+ __OBJC_$_PROTOCOL_METHOD_TYPES_LACContextExternalizingXPC
+ __OBJC_$_PROTOCOL_METHOD_TYPES_LACContextObserver
+ __OBJC_$_PROTOCOL_REFS_LACContextExternalizingXPC
+ __OBJC_$_PROTOCOL_REFS_LACContextObserver
+ __OBJC_LABEL_PROTOCOL_$_LACContextExternalizingXPC
+ __OBJC_LABEL_PROTOCOL_$_LACContextObserver
+ __OBJC_PROTOCOL_$_LACContextExternalizingXPC
+ __OBJC_PROTOCOL_$_LACContextObserver
+ ___41-[LAClient externalizedContextWithError:]_block_invoke
+ ___41-[LAClient externalizedContextWithError:]_block_invoke_2
+ ___block_descriptor_48_e8_32s40s_e21_"NSMutableArray"8?0l
+ ___block_descriptor_72_e8_32s40s48s56bs64w_e29_v24?0"NSArray"8"NSError"16l
+ ___block_descriptor_72_e8_32s40s48s56bs64w_e49_v24?0"<LAKeyStoreGenericPassword>"8"NSError"16l
+ _objc_msgSend$addRecoveryKey:authorizer:error:
+ _objc_msgSend$addRecoveryKey:authorizerKey:error:
+ _objc_msgSend$addRecoveryKey:error:
+ _objc_msgSend$authenticateUser:domain:targetDisk:contextRef:error:
+ _objc_msgSend$authenticateUser:domain:targetDisk:error:
+ _objc_msgSend$authenticateUser:targetDisk:contextRef:error:
+ _objc_msgSend$authenticateUser:targetDisk:error:
+ _objc_msgSend$backoff
+ _objc_msgSend$changePasswordForUser:to:error:
+ _objc_msgSend$checkExistsOTIForUserWithUUID:targetDisk:error:
+ _objc_msgSend$checkExistsUserWithUUID:targetDisk:error:
+ _objc_msgSend$checkOwnershipStatusForTargetDisk:error:
+ _objc_msgSend$confirmed
+ _objc_msgSend$createUser:authorizer:error:
+ _objc_msgSend$createUser:identityCreationPolicy:error:
+ _objc_msgSend$createUser:recoveryCredential:error:
+ _objc_msgSend$createUserWithHash:identityCreationPolicy:error:
+ _objc_msgSend$credential
+ _objc_msgSend$deletePasswordHintForUserWithUUID:error:
+ _objc_msgSend$deleteUserWithUUID:error:
+ _objc_msgSend$diskNameForSystemVolumeWithError:
+ _objc_msgSend$diskNameForVolumeAtPath:error:
+ _objc_msgSend$externalData
+ _objc_msgSend$externalDataUUID
+ _objc_msgSend$externalizedContextProvider
+ _objc_msgSend$failedAttempts
+ _objc_msgSend$featureFlagUserAuthDaemonEnabled
+ _objc_msgSend$fetchPasswordHintForUserWithUUID:error:
+ _objc_msgSend$fetchRecoveryKeysInTargetDisk:
+ _objc_msgSend$fetchRecoveryKeysInTargetDisk:error:
+ _objc_msgSend$fetchUIDForUserWithUUID:error:
+ _objc_msgSend$fetchUserBy:inTargetDisk:
+ _objc_msgSend$fetchUsersInTargetDisk:
+ _objc_msgSend$fetchUsersInTargetDisk:error:
+ _objc_msgSend$iCloudRecoveryCredentialWithPassword:
+ _objc_msgSend$iCloudRecoveryData:
+ _objc_msgSend$iCloudRecoveryKeyIdentifier
+ _objc_msgSend$initWithBytes:
+ _objc_msgSend$initWithCoder:
+ _objc_msgSend$initWithContextRef:
+ _objc_msgSend$initWithContextRef:salt:iterations:
+ _objc_msgSend$initWithController:database:disk:
+ _objc_msgSend$initWithCoreLockState:
+ _objc_msgSend$initWithCoreLockoutState:
+ _objc_msgSend$initWithCredential:externalData:
+ _objc_msgSend$initWithExternalizer:
+ _objc_msgSend$initWithIdentifier:credential:
+ _objc_msgSend$initWithIdentifier:credential:externalData:
+ _objc_msgSend$initWithIdentifier:oneTimePassword:
+ _objc_msgSend$initWithLockState:
+ _objc_msgSend$initWithLockoutState:
+ _objc_msgSend$initWithM1:publicKeyA:
+ _objc_msgSend$initWithM2:sessionKey:
+ _objc_msgSend$initWithPBKDF2Hash:iterations:salt:
+ _objc_msgSend$initWithPBKDF2HashData:iterations:salt:
+ _objc_msgSend$initWithPassword:
+ _objc_msgSend$initWithPubKeyHash:
+ _objc_msgSend$initWithSalt:publicKeyB:
+ _objc_msgSend$initWithSessionKey:
+ _objc_msgSend$initWithTargetUID:
+ _objc_msgSend$initWithUUID:contextRef:
+ _objc_msgSend$initWithUUID:data:
+ _objc_msgSend$initWithUUID:password:
+ _objc_msgSend$initWithUUID:passwordHash:
+ _objc_msgSend$initWithUUIDString:
+ _objc_msgSend$initWithUsername:
+ _objc_msgSend$initWithUuid:
+ _objc_msgSend$initWithUuid:data:
+ _objc_msgSend$initWithUuid:disk:database:controller:
+ _objc_msgSend$initWithUuid:externalDataUUID:
+ _objc_msgSend$initWithUuid:identifier:
+ _objc_msgSend$initWithUuid:password:
+ _objc_msgSend$initWithVolumePath:confirmed:
+ _objc_msgSend$installerRecoveryCredentialWithPassword:
+ _objc_msgSend$installerRecoveryKeyIdentifier
+ _objc_msgSend$institutionalRecoveryCredentialWithPassword:
+ _objc_msgSend$institutionalRecoveryData:
+ _objc_msgSend$institutionalRecoveryKeyIdentifier
+ _objc_msgSend$isClientAllowListedWithClientInfo:
+ _objc_msgSend$isConcurrentEvaluationAvailable
+ _objc_msgSend$iterations
+ _objc_msgSend$lockSessionID:error:
+ _objc_msgSend$lockStateForUserWithUUID:sessionID:error:
+ _objc_msgSend$lockoutStateForUserWithUUID:domain:error:
+ _objc_msgSend$lockoutStateForUserWithUUID:error:
+ _objc_msgSend$loginUser:sessionID:targetDisk:error:
+ _objc_msgSend$logoutSessionID:error:
+ _objc_msgSend$makeManagerWithUUID:
+ _objc_msgSend$makeUserWithUUID:disk:database:controller:
+ _objc_msgSend$makeVolumeOwnershipWithVolumePath:confirmed:
+ _objc_msgSend$maxAttempts
+ _objc_msgSend$mdmRecoveryCredentialWithPassword:
+ _objc_msgSend$mdmRecoveryKeyIdentifier
+ _objc_msgSend$password
+ _objc_msgSend$passwordHash
+ _objc_msgSend$personalRecoveryCredentialWithPassword:
+ _objc_msgSend$personalRecoveryKeyIdentifier
+ _objc_msgSend$pubKeyHash
+ _objc_msgSend$rawValue
+ _objc_msgSend$removeRecoveryKey:externalDataUUID:error:
+ _objc_msgSend$resetAllPasswords:targetDisk:error:
+ _objc_msgSend$resetPasswordForUser:authorizer:targetDisk:error:
+ _objc_msgSend$resetPasswordForUser:recoveryCredential:targetDisk:error:
+ _objc_msgSend$resetPasswordWithHashForUser:error:
+ _objc_msgSend$salt
+ _objc_msgSend$setObject:forKey:options:contextUUID:connection:completionHandler:
+ _objc_msgSend$storePasswordHintForUserWithUUID:passwordHint:error:
+ _objc_msgSend$transferOwnershipFrom:toNewRecoveryKey:volume:error:
+ _objc_msgSend$transferOwnershipFromUser:toExistingUser:targetDisk:error:
+ _objc_msgSend$transferOwnershipFromUser:toNewRecoveryKey:targetDisk:error:
+ _objc_msgSend$unlockUser:sessionID:error:
+ _objc_msgSend$unsafeContextRef
+ _objc_msgSend$updateUserRegistryConfig:error:
+ _objc_msgSend$volumePath
+ _swift_unexpectedError
- +[LACustomPasswordRequirement requestCreationWithLocalizedReason:completion:]
- +[LACustomPasswordVerificationAction submitCustomPasswordAction:]
- +[LACustomPasswordVerificationAction terminateAction]
- +[LACustomPasswordVerificationAction userCancelAction]
- +[LAKeyStoreBackendBuilder buildBackend].cold.1
- -[LAClient cachedExternalizedContext]
- -[LAClient setCachedExternalizedContext:]
- -[LAClient synchronousExternalizedContextWithError:]
- -[LACustomPasswordVerificationAction .cxx_destruct]
- -[LACustomPasswordVerificationAction initWithType:]
- -[LACustomPasswordVerificationAction initWithType:customPassword:]
- -[LACustomPasswordVerificationAction isEqual:]
- -[LAStorage accessControlForKey:error:]
- -[LAStorage accessControl]
- -[LAStorage setAccessControl:]
- GCC_except_table188
- GCC_except_table26
- GCC_except_table28
- GCC_except_table29
- GCC_except_table33
- GCC_except_table37
- GCC_except_table51
- GCC_except_table55
- GCC_except_table58
- GCC_except_table63
- GCC_except_table65
- GCC_except_table70
- GCC_except_table75
- LA_LOG.cold.1
- LA_LOG.log
- LA_LOG.once
- LA_LOG_INTERACTIVE.log
- LA_LOG_INTERACTIVE.once
- OBJC_IVAR_$_LAClient._cachedExternalizedContext
- OBJC_IVAR_$_LACustomPasswordVerificationAction._customPassword
- OBJC_IVAR_$_LACustomPasswordVerificationAction._type
- OBJC_IVAR_$_LAStorage._accessControl
- _LACStorageOperationDataExchange
- _LA_LOG
- _OBJC_CLASS_$_LACCachedExternalizedContext
- _OBJC_CLASS_$_LACustomPasswordVerificationAction
- _OBJC_CLASS_$_LAInstanceIDGenerator
- _OBJC_METACLASS_$_LACustomPasswordVerificationAction
- __32-[LAStorage _connectToEndpoint:]_block_invoke.120
- __43-[LARight authorizeWithOptions:completion:]_block_invoke.98
- __43-[LARight checkCanAuthorizeWithCompletion:]_block_invoke.89
- __44-[LAStorage processError:completionHandler:]_block_invoke.36
- __51-[LAStorage exchangeData:forKey:completionHandler:]_block_invoke.29
- __56-[LARightStore _saveRight:identifier:secret:completion:]_block_invoke.61
- __56-[LARightStore _saveRight:identifier:secret:completion:]_block_invoke_2.62
- __68-[LAStorage _callProxyBlock:authenticationPolicy:completionHandler:]_block_invoke.127
- __68-[LAStorage _callProxyBlock:authenticationPolicy:completionHandler:]_block_invoke.cold.1
- __OBJC_$_CLASS_METHODS_LACustomPasswordRequirement
- __OBJC_$_CLASS_METHODS_LACustomPasswordVerificationAction
- __OBJC_$_CLASS_PROP_LIST_LACustomPasswordVerificationAction
- __OBJC_$_INSTANCE_METHODS_LACustomPasswordVerificationAction
- __OBJC_$_INSTANCE_METHODS_LAUserStore(Internal)
- __OBJC_$_INSTANCE_VARIABLES_LACustomPasswordVerificationAction
- __OBJC_$_PROTOCOL_INSTANCE_METHODS_OPT_LAContextObserver
- __OBJC_$_PROTOCOL_METHOD_TYPES_LAContextObserver
- __OBJC_$_PROTOCOL_REFS_LAContextObserver
- __OBJC_CLASS_RO_$_LACustomPasswordVerificationAction
- __OBJC_LABEL_PROTOCOL_$_LAContextObserver
- __OBJC_METACLASS_RO_$_LACustomPasswordVerificationAction
- __OBJC_PROTOCOL_$_LAContextObserver
- ___39-[LAStorage accessControlForKey:error:]_block_invoke
- ___39-[LAStorage accessControlForKey:error:]_block_invoke_2
- ___52-[LAClient synchronousExternalizedContextWithError:]_block_invoke
- ___52-[LAClient synchronousExternalizedContextWithError:]_block_invoke_2
- ___LA_LOG_INTERACTIVE_block_invoke
- ___LA_LOG_block_invoke
- ___block_descriptor_56_e8_32s40bs48w_e17_v16?0"NSError"8l
- ___block_descriptor_56_e8_32s40bs48w_e38_v24?0"LAPersistedRight"8"NSError"16l
- ___block_descriptor_72_e8_32s40s48s56bs64w_e5_v8?0l
- ___block_descriptor_80_e8_32s40s48s56s64bs72w_e29_v24?0"NSArray"8"NSError"16l
- ___block_descriptor_80_e8_32s40s48s56s64bs72w_e49_v24?0"<LAKeyStoreGenericPassword>"8"NSError"16l
- ___block_descriptor_96_e8_32s40s48s56s64s72s80bs88w_e5_v8?0l
- ___copy_helper_block_e8_32s40s48s56s64s72s80b88w
- ___destroy_helper_block_e8_32s40s48s56s64s72s80s88w
- __block_literal_global.152
- __block_literal_global.231
- __block_literal_global.99
- _objc_msgSend$accessControl
- _objc_msgSend$aclForKey:contextUUID:connection:completionHandler:
- _objc_msgSend$initWithExternalizationDelegate:
- _objc_msgSend$isConcurrentEvaluationEnabledForClientInfo:
- _objc_msgSend$isKeyAvailable:operation:
- _objc_msgSend$setObject:acl:forKey:options:contextUUID:connection:completionHandler:
CStrings:
+ "#"
+ "%{public}@ invalidated stale XPC connection before creating a new one"
+ "@\"LACExternalizedContextProvider\""
+ "@48@0:8@16@24@32^@40"
+ "LACContextExternalizingXPC"
+ "LACContextObserver"
+ "LocalAuthentication.Authorization._saveRight.rightForIdentifier"
+ "LocalAuthentication.Authorization._saveRight.storeGenericPassword"
+ "LocalAuthentication.Authorization._saveRight.storeKey"
+ "LocalAuthentication.Authorization.authorizeWithLocalizedReason.completion"
+ "LocalAuthentication.Authorization.authorizeWithOptions.completion"
+ "LocalAuthentication.Authorization.rightForIdentifier.fetchGenericPasswords"
+ "LocalAuthentication.Authorization.rightForIdentifier.fetchKey"
+ "LocalAuthentication.Authorization.rightForIdentifier.fetchKeys"
+ "LocalAuthentication/LAUserPasswordHash.swift"
+ "Retrying on externalizedContextProvider"
+ "T@\"LACExternalizedContextProvider\",&,V_externalizedContextProvider"
+ "_externalizedContextProvider"
+ "createUser:identityCreationPolicy:error:"
+ "externalizedContextProvider"
+ "externalizedContextWithError:"
+ "featureFlagUserAuthDaemonEnabled"
+ "initWithContextRef:salt:iterations:"
+ "initWithExternalizer:"
+ "initWithPBKDF2Hash:iterations:salt:"
+ "isClientAllowListedWithClientInfo:"
+ "isConcurrentEvaluationAvailable"
+ "kLACServiceTypeEnvironment"
+ "kLACServiceTypeSecureStorage"
+ "lockoutState:"
+ "lockoutStateForUserWithUUID:error:"
+ "makeUserStoreWithDatabase:disk:registryConfig:error:"
+ "optionIgnoreExistingDoublePress"
+ "pbkdf2Hash"
+ "resetPasswordWithHashForUser:error:"
+ "setExternalizedContextProvider:"
+ "setObject:forKey:options:contextUUID:connection:completionHandler:"
+ "setOptionIgnoreExistingDoublePress:"
+ "transferOwnershipFrom:toExistingUser:volume:error:"
+ "transferOwnershipFrom:toNewRecoveryKey:volume:error:"
+ "transferOwnershipFromUser:toExistingUser:targetDisk:error:"
+ "transferOwnershipFromUser:toNewRecoveryKey:targetDisk:error:"
+ "unsafeContextRef"
+ "v24@0:8@\"<LACContext>\"16"
+ "v56@0:8@\"NSData\"16@24@\"NSDictionary\"32@\"<LACContextUIDelegate>\"40@?<v@?@\"NSDictionary\"@\"NSError\">48"
+ "v64@0:8@\"NSData\"16q24@\"NSDictionary\"32@\"NSUUID\"40@\"NSXPCConnection\"48@?<v@?@@\"NSError\">56"
+ "v64@0:8@16q24@32@40@48@?56"
- "3"
- "@\"LACCachedExternalizedContext\""
- "LAContextObserver"
- "LACustomPasswordVerificationAction"
- "Retrying on cachedExternalizedContext"
- "T@\"LACCachedExternalizedContext\",&,V_cachedExternalizedContext"
- "T@\"LACustomPasswordVerificationAction\",R"
- "T^{__SecAccessControl=},N,V_accessControl"
- "^{__SecAccessControl=}16@0:8"
- "^{__SecAccessControl=}32@0:8q16^@24"
- "_accessControl"
- "_cachedExternalizedContext"
- "_customPassword"
- "accessControl"
- "accessControlForKey:error:"
- "aclForKey:contextUUID:connection:completionHandler:"
- "addRecoveryKey:authorizer:targetDisk:error:"
- "contextRef"
- "createUser(_:)"
- "createUser(_:identityCreationPolicy:)"
- "initWithExternalizationDelegate:"
- "isConcurrentEvaluationEnabledForClientInfo:"
- "isKeyAvailable:operation:"
- "kLAServiceTypeEnvironment"
- "kLAServiceTypeSecureStorage"
- "key does not support data exchange"
- "makeUserStoreWithDatabase:disk:"
- "requestCreationWithLocalizedReason:completion:"
- "resetPassword(_:)"
- "resetPasswordForUser:recoveryCredential:error:"
- "setAccessControl:"
- "setCachedExternalizedContext:"
- "setObject:acl:forKey:options:contextUUID:connection:completionHandler:"
- "submitCustomPasswordAction:"
- "synchronousExternalizedContextWithError:"
- "terminateAction"
- "userCancelAction"
- "v24@0:8@\"LAContext\"16"
- "v24@0:8^{__SecAccessControl=}16"
- "v48@0:8q16@\"NSDictionary\"24@\"<LAUIDelegate>\"32@?<v@?@\"NSDictionary\"@\"NSError\">40"
- "v48@0:8q16@\"NSUUID\"24@\"NSXPCConnection\"32@?<v@?@\"NSData\"@\"NSError\">40"
- "v56@0:8@\"NSData\"16@24@\"NSDictionary\"32@\"<LAUIDelegate>\"40@?<v@?@\"NSDictionary\"@\"NSError\">48"
- "v72@0:8@\"NSData\"16@\"NSData\"24q32@\"NSDictionary\"40@\"NSUUID\"48@\"NSXPCConnection\"56@?<v@?@@\"NSError\">64"
- "v72@0:8@16@24q32@40@48@56@?64"

```
