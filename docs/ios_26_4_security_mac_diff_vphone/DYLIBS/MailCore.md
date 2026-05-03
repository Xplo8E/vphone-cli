## MailCore

> `/System/Library/PrivateFrameworks/MailCore.framework/Versions/A/MailCore`

```diff

-3864.400.21.0.0
-  __TEXT.__text: 0x8934c
-  __TEXT.__auth_stubs: 0x1220
-  __TEXT.__objc_methlist: 0x8044
+3864.500.181.0.0
+  __TEXT.__text: 0x8a8d0
+  __TEXT.__auth_stubs: 0x1210
+  __TEXT.__objc_methlist: 0x80e4
   __TEXT.__const: 0x4a0
-  __TEXT.__cstring: 0x7d22
-  __TEXT.__gcc_except_tab: 0x16ec
-  __TEXT.__oslogstring: 0x1be5
-  __TEXT.__unwind_info: 0x1ff0
+  __TEXT.__cstring: 0x7dc3
+  __TEXT.__gcc_except_tab: 0x1650
+  __TEXT.__oslogstring: 0x1c2e
+  __TEXT.__unwind_info: 0x2328
   __TEXT.__objc_classname: 0xdd0
-  __TEXT.__objc_methname: 0x141ee
-  __TEXT.__objc_methtype: 0x2b76
-  __TEXT.__objc_stubs: 0x10680
-  __DATA_CONST.__got: 0x10f8
+  __TEXT.__objc_methname: 0x144ab
+  __TEXT.__objc_methtype: 0x2b93
+  __TEXT.__objc_stubs: 0x10880
+  __DATA_CONST.__got: 0x1108
   __DATA_CONST.__const: 0x1208
   __DATA_CONST.__objc_classlist: 0x360
   __DATA_CONST.__objc_catlist: 0xb8
   __DATA_CONST.__objc_protolist: 0x120
   __DATA_CONST.__objc_imageinfo: 0x8
-  __DATA_CONST.__objc_selrefs: 0x53a0
+  __DATA_CONST.__objc_selrefs: 0x5420
   __DATA_CONST.__objc_protorefs: 0x8
   __DATA_CONST.__objc_superrefs: 0x280
   __DATA_CONST.__objc_arraydata: 0x1a0
-  __AUTH_CONST.__auth_got: 0x920
-  __AUTH_CONST.__const: 0x1320
-  __AUTH_CONST.__cfstring: 0x9000
-  __AUTH_CONST.__objc_const: 0xc9f0
+  __AUTH_CONST.__auth_got: 0x918
+  __AUTH_CONST.__const: 0x1370
+  __AUTH_CONST.__cfstring: 0x9040
+  __AUTH_CONST.__objc_const: 0xca80
   __AUTH_CONST.__objc_arrayobj: 0xa8
   __AUTH_CONST.__objc_dictobj: 0x50
   __AUTH_CONST.__objc_intobj: 0x180
   __AUTH.__objc_data: 0xaa0
-  __DATA.__objc_ivar: 0x78c
+  __DATA.__objc_ivar: 0x798
   __DATA.__data: 0xdb0
   __DATA.__crash_info: 0x148
-  __DATA.__bss: 0x1e8
+  __DATA.__bss: 0x1f8
   __DATA_DIRTY.__objc_data: 0x1720
   __DATA_DIRTY.__bss: 0x3f0
   - /System/Library/Frameworks/Accounts.framework/Versions/A/Accounts

   - /usr/lib/libSystem.B.dylib
   - /usr/lib/libicucore.A.dylib
   - /usr/lib/libobjc.A.dylib
-  UUID: A1292D4E-92A3-36E3-BD14-AC7A8AB343E1
-  Functions: 2819
-  Symbols:   7891
-  CStrings:  6737
+  UUID: 2A2D0AF7-5F6E-3BE0-A0DF-083C53797E97
+  Functions: 2871
+  Symbols:   7981
+  CStrings:  6767
 
Symbols:
+ -[MCAttachment hasUntrustedRemoteURL]
+ -[MCProgressEntry _removeObserversFromProgress:]
+ -[MCRemoteURLAttachmentDataSource _createArchiveFileWrapperFromData:]
+ -[MCRemoteURLAttachmentDataSource _createFileWrapperFromData:]
+ -[MCRemoteURLAttachmentDataSource _createFileWrapperFromURL:error:]
+ -[MCRemoteURLAttachmentDataSource _downloadRemoteAttachmentDirect]
+ -[MCRemoteURLAttachmentDataSource _downloadRemoteAttachmentWithPrivacyProxy]
+ -[MCRemoteURLAttachmentDataSource _finalizeAndPersistFileWrapper:originalContentsURL:error:]
+ -[MCRemoteURLAttachmentDataSource _persistDownloadedFileWrapper:originalContentsURL:error:]
+ -[MCRemoteURLAttachmentDataSource _signalDownloadCompletionWithError:]
+ -[MCRemoteURLAttachmentDataSource _waitForDownloadCompletionCancellingTask:]
+ -[MCRemoteURLAttachmentDataSource hasUntrustedRemoteURL]
+ -[MCRemoteURLAttachmentDataSource privacyProxySession]
+ -[MCRemoteURLAttachmentDataSource setPrivacyProxySession:]
+ GCC_except_table58
+ GCC_except_table67
+ GCC_except_table73
+ GCC_except_table75
+ GCC_except_table84
+ OBJC_IVAR_$_MCProgressEntry._progressesWithObservers
+ OBJC_IVAR_$_MCRemoteURLAttachmentDataSource._hasUntrustedRemoteURL
+ OBJC_IVAR_$_MCRemoteURLAttachmentDataSource._privacyProxySession
+ _OBJC_CLASS_$_EMRemoteContentURLSession
+ _OBJC_CLASS_$_NSMutableURLRequest
+ _OUTLINED_FUNCTION_10
+ _OUTLINED_FUNCTION_11
+ _OUTLINED_FUNCTION_12
+ _OUTLINED_FUNCTION_13
+ _OUTLINED_FUNCTION_14
+ _OUTLINED_FUNCTION_8
+ _OUTLINED_FUNCTION_9
+ __48-[MCAttachment fileWrapperForAccessLevel:error:]_block_invoke.111
+ ___76-[MCRemoteURLAttachmentDataSource _downloadRemoteAttachmentWithPrivacyProxy]_block_invoke
+ ____ef_log_MCProgressEntry_block_invoke
+ ___block_descriptor_48_e8_32s40w_e46_v32?0"NSData"8"NSURLResponse"16"NSError"24l
+ __ef_log_MCProgressEntry
+ _ef_log_MCProgressEntry.cold.1
+ _ef_log_MCProgressEntry.log
+ _ef_log_MCProgressEntry.onceToken
+ _objc_msgSend$_createArchiveFileWrapperFromData:
+ _objc_msgSend$_createFileWrapperFromData:
+ _objc_msgSend$_createFileWrapperFromURL:error:
+ _objc_msgSend$_downloadRemoteAttachmentDirect
+ _objc_msgSend$_downloadRemoteAttachmentWithPrivacyProxy
+ _objc_msgSend$_finalizeAndPersistFileWrapper:originalContentsURL:error:
+ _objc_msgSend$_persistDownloadedFileWrapper:originalContentsURL:error:
+ _objc_msgSend$_removeObserversFromProgress:
+ _objc_msgSend$_signalDownloadCompletionWithError:
+ _objc_msgSend$_waitForDownloadCompletionCancellingTask:
+ _objc_msgSend$dataTaskWithRequest:isSynthetic:allowProxying:failOpen:background:completionHandler:
+ _objc_msgSend$hasUntrustedRemoteURL
+ _objc_msgSend$initWithCache:
+ _objc_msgSend$invalidateAndCancel:
+ _objc_msgSend$loadRemoteContentWithProxy
+ _objc_msgSend$requestWithURL:
+ _objc_msgSend$setPrivacyProxySession:
- -[MCRemoteURLAttachmentDataSource _persistDownloadedFileWrapper:originalContentsURL:]
- GCC_except_table55
- GCC_except_table57
- GCC_except_table66
- GCC_except_table71
- GCC_except_table74
- GCC_except_table83
- __48-[MCAttachment fileWrapperForAccessLevel:error:]_block_invoke.110
- _objc_msgSend$_persistDownloadedFileWrapper:originalContentsURL:
- _objc_retainAutoreleaseReturnValue
CStrings:
+ "@\"EMRemoteContentURLSession\""
+ "Failed to create file wrapper from downloaded data"
+ "Remote attachment download returned empty data"
+ "Removing %lu completed NSProgress objects from entry %@ (remaining: %lu)"
+ "T@\"EMRemoteContentURLSession\",&,N,V_privacyProxySession"
+ "TB,R,N,V_hasUntrustedRemoteURL"
+ "_createArchiveFileWrapperFromData:"
+ "_createFileWrapperFromData:"
+ "_createFileWrapperFromURL:error:"
+ "_downloadRemoteAttachmentDirect"
+ "_downloadRemoteAttachmentWithPrivacyProxy"
+ "_finalizeAndPersistFileWrapper:originalContentsURL:error:"
+ "_hasUntrustedRemoteURL"
+ "_persistDownloadedFileWrapper:originalContentsURL:error:"
+ "_privacyProxySession"
+ "_progressesWithObservers"
+ "_removeObserversFromProgress:"
+ "_signalDownloadCompletionWithError:"
+ "_waitForDownloadCompletionCancellingTask:"
+ "dataTaskWithRequest:isSynthetic:allowProxying:failOpen:background:completionHandler:"
+ "hasUntrustedRemoteURL"
+ "initWithCache:"
+ "invalidateAndCancel:"
+ "privacyProxySession"
+ "requestWithURL:"
+ "setPrivacyProxySession:"
+ "v32@?0@\"NSData\"8@\"NSURLResponse\"16@\"NSError\"24"
- "_persistDownloadedFileWrapper:originalContentsURL:"

```
