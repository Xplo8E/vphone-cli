## AccountsUI

> `/System/Library/PrivateFrameworks/AccountsUI.framework/Versions/A/AccountsUI`

```diff

-150.0.0.0.0
-  __TEXT.__text: 0x219dc
-  __TEXT.__auth_stubs: 0x500
+151.0.0.0.0
+  __TEXT.__text: 0x21b14
+  __TEXT.__auth_stubs: 0x4f0
   __TEXT.__objc_methlist: 0x22a8
   __TEXT.__const: 0x98
-  __TEXT.__cstring: 0x33b4
-  __TEXT.__gcc_except_tab: 0x130
+  __TEXT.__cstring: 0x33cd
+  __TEXT.__gcc_except_tab: 0x134
   __TEXT.__oslogstring: 0x3
-  __TEXT.__unwind_info: 0x6b8
+  __TEXT.__unwind_info: 0x6d0
   __TEXT.__objc_classname: 0x34b
   __TEXT.__objc_methname: 0x663e
   __TEXT.__objc_methtype: 0x15f1

   __DATA_CONST.__objc_protorefs: 0x8
   __DATA_CONST.__objc_superrefs: 0x88
   __DATA_CONST.__objc_arraydata: 0xe0
-  __AUTH_CONST.__auth_got: 0x290
+  __AUTH_CONST.__auth_got: 0x288
   __AUTH_CONST.__const: 0xb50
-  __AUTH_CONST.__cfstring: 0x2800
+  __AUTH_CONST.__cfstring: 0x2820
   __AUTH_CONST.__objc_const: 0x5078
   __AUTH_CONST.__objc_arrayobj: 0x30
   __AUTH_CONST.__objc_intobj: 0x30

   - /usr/lib/libSystem.B.dylib
   - /usr/lib/libbz2.1.0.dylib
   - /usr/lib/libobjc.A.dylib
-  UUID: 3300AFB1-1F96-3B5C-B36E-F2BA51DFDE60
+  UUID: 3CE599B0-DED4-3D8F-A660-A7558368433F
   Functions: 730
-  Symbols:   2175
-  CStrings:  2089
+  Symbols:   2174
+  CStrings:  2091
 
Symbols:
- _objc_retainAutoreleaseReturnValue
Functions:
~ +[ACUIAccountDataclass _supportedDataclasses] : 160 -> 180
~ -[ACUIAccountDataclass initWithIdentifier:] : 124 -> 120
~ -[ACUIAccountDataclass localizedName] : 72 -> 84
~ -[ACUIAccountDataclass setIcon:] : 12 -> 68
~ -[ACUIAccountDataclass setLocalizedName:] : 12 -> 68
~ -[ACUIViewController initWithAccount:] : 352 -> 356
~ ___45-[ACUIViewController _reloadAccountIfNeeded:]_block_invoke_2 : 212 -> 224
~ -[ACUIViewController persistVerifiedAccountWithActions:] : 308 -> 312
~ ___56-[ACUIViewController persistVerifiedAccountWithActions:]_block_invoke_2 : 172 -> 184
~ -[ACUIViewController _setAccount:] : 240 -> 236
~ -[ACUIViewController saveAccountWithVerificationOptions:dataclassActions:] : 432 -> 428
~ ___74-[ACUIViewController saveAccountWithVerificationOptions:dataclassActions:]_block_invoke_3 : 188 -> 196
~ -[ACUIViewController handleInsecureConnectionForAccount:withSaveError:inWindow:] : 1188 -> 1184
~ -[ACUIViewController digestSaveError:inWindow:isSetup:] : 1140 -> 1136
~ +[ACAccountType(AccountsUI) accountTypeForHostname:] : 1052 -> 1064
~ -[ACAccountType(AccountsUI) _imageWithSuffix:] : 644 -> 648
~ +[ACAccountType(AccountsUI) internetAccountTypes] : 160 -> 180
~ -[ACAccount(AccountsUI) uiDataclasses] : 752 -> 760
~ ___38-[ACAccount(AccountsUI) uiDataclasses]_block_invoke : 332 -> 328
~ -[ACAccount(AccountsUI) displayUsername] : 396 -> 392
~ -[ACAccount(AccountsUI) descriptionSubTitle] : 124 -> 128
~ -[ACAccount(AccountsUI) enabledDataclassesStringFittingWidth:] : 1356 -> 1364
~ -[ACAccount(AccountsUI) isDifferent:] : 2112 -> 2108
~ -[ACAccount(AccountsUI) promptUserForDeletionInWindow:completion:] : 1696 -> 1704
~ -[ACAccount(AccountsUI) activateInWindow:completion:] : 1544 -> 1536
~ -[ACAccount(AccountsUI) localizedStringForSaveError:] : 852 -> 856
~ +[ACUIPluginManager sharedManager] : 68 -> 88
~ ___33-[ACUIPluginManager _loadPlugins]_block_invoke_2 : 376 -> 380
~ -[ACUIPluginManager _validateAndLoadPlugin:] : 304 -> 300
~ -[ACUIAccountSetupViewController performsChecksInWindow:] : 1832 -> 1820
~ -[ACUIAccountSetupViewController beginSetupInSheet:attachedToWindow:verifyError:completion:] : 656 -> 660
~ -[ACUIAccountSetupViewController willPersistVerifiedAccount] : 856 -> 860
~ -[ACUIAccountSetupViewController webAuthViewController:loginEndedWithError:] : 328 -> 332
~ -[ACUIAccountSetupViewController handleInsecureConnectionForAccount:withSaveError:] : 140 -> 136
~ ___45+[ACUIUtilities shouldUseChineseAccountTypes]_block_invoke_2 : 456 -> 448
~ -[NSView(ACUIAdditions) setContentSubview:] : 640 -> 644
~ -[NSView(ACUIAdditions) animateChanges:completion:] : 272 -> 268
~ ___51-[NSView(ACUIAdditions) animateChanges:completion:]_block_invoke : 1480 -> 1468
~ -[NSString(ACUIAdditions) localizedStringWithKeyPrefix:andIdentifier:] : 416 -> 412
~ -[ACUISetupManagerViewController startSetupInWindow:completion:] : 452 -> 448
~ -[ACUISetupManagerViewController _accountTypeIdentifierForDataclass:] : 272 -> 276
~ +[ACUISetupManagerViewController shouldOfferAccountSetupForAccountType:username:] : 600 -> 592
~ -[ACUISetupManagerViewController startSetupInWindow:accountType:username:password:completion:] : 368 -> 352
~ ___47-[ACUISetupManagerViewController _allowAction:]_block_invoke : 220 -> 216
~ -[ACUICertificatePanelManager initWithError:] : 184 -> 188
~ -[ACUICertificatePanelManager showCertificatePanelInWindow:completion:] : 312 -> 300
~ -[ACUICertificatePanelManager showCertificatePanelInWindow:isSetup:withAccount:saveHandler:completion:] : 672 -> 644
~ -[ACUICertificatePanelManager _showCertificatePanelInWindow:withAccount:canContinue:saveHandler:completion:] : 1144 -> 1112
~ ___108-[ACUICertificatePanelManager _showCertificatePanelInWindow:withAccount:canContinue:saveHandler:completion:]_block_invoke : 828 -> 844
~ ___108-[ACUICertificatePanelManager _showCertificatePanelInWindow:withAccount:canContinue:saveHandler:completion:]_block_invoke_2 : 600 -> 620
~ ___108-[ACUICertificatePanelManager _showCertificatePanelInWindow:withAccount:canContinue:saveHandler:completion:]_block_invoke_3 : 508 -> 500
~ ___108-[ACUICertificatePanelManager _showCertificatePanelInWindow:withAccount:canContinue:saveHandler:completion:]_block_invoke_4 : 632 -> 644
~ ___108-[ACUICertificatePanelManager _showCertificatePanelInWindow:withAccount:canContinue:saveHandler:completion:]_block_invoke_5 : 264 -> 260
~ -[ACUICredentialPromptViewController initWithAccount:] : 240 -> 244
~ -[ACUICredentialPromptViewController displayInWindow:completion:] : 1316 -> 1308
~ ___69-[ACUICredentialPromptViewController _showAutoCompletePromptIfNeeded]_block_invoke : 216 -> 220
~ -[ACUICredentialPromptViewController helpButton:] : 96 -> 92
~ _SPSafariPlatformSupportFunction : 12 -> 64
~ -[NSStackView(AccountsUI) addView:] : 132 -> 136
~ +[ACUIWebLoginViewController supportsAccount:] : 364 -> 368
~ -[ACUIWebLoginViewController webClient] : 288 -> 296
~ -[ACUIWebLoginViewController _webLoginFailureWithError:] : 1008 -> 1004
~ -[ACUIWebLoginViewController _performRequest:withHandler:] : 244 -> 232
~ ___58-[ACUIWebLoginViewController _performRequest:withHandler:]_block_invoke : 268 -> 272
~ ___58-[ACUIWebLoginViewController _performRequest:withHandler:]_block_invoke_2 : 340 -> 324
~ -[ACUIWebLoginViewController _webViewDidReceiveTitle:] : 252 -> 256
~ ___49-[ACUIWebLoginViewController _getTokensWithCode:]_block_invoke : 540 -> 532
~ ___54-[ACUIWebLoginViewController _fetchUserInfoWithToken:]_block_invoke : 712 -> 704
~ -[ACUIWebLoginViewController webView:didFailNavigation:withError:] : 88 -> 92
~ -[ACUIWebLoginViewController webView:didReceiveAuthenticationChallenge:completionHandler:] : 672 -> 668
~ -[ACUIAccountsTableViewController _sortedAccountRowItemsArray:groupByRMID:] : 1316 -> 1332
~ -[ACUIAccountsTableViewController _dataclassMatchingFilteringOption] : 80 -> 96
~ -[ACUIAccountsTableViewController _reloadAccounts:] : 228 -> 224
~ ___51-[ACUIAccountsTableViewController _reloadAccounts:]_block_invoke : 1524 -> 1516
~ ___51-[ACUIAccountsTableViewController _reloadAccounts:]_block_invoke_2 : 2796 -> 2816
~ -[ACUIAccountsTableViewController setSelectedAccount:] : 200 -> 196
~ -[ACUIAccountsTableViewController setAutoSelectAccount:] : 20 -> 84
~ +[ACUIAccountNotifier sharedNotifier] : 68 -> 88
~ -[ACUIAccountNotifier postInvalidCredentialNotificationForAccount:] : 1408 -> 1404
~ -[ACUIAccountNotifier postNewAddNotificationForAccount:] : 2052 -> 2068
~ -[ACUIAccountNotifier dismissNotificationsForAccount:] : 716 -> 708
~ -[ACUIAccountNotifier userNotificationCenter:didActivateNotification:] : 708 -> 712
~ -[ACUIAccountInfoViewController _verifyCredentialAndPromptIfNeeded:] : 316 -> 312
~ ___68-[ACUIAccountInfoViewController _verifyCredentialAndPromptIfNeeded:]_block_invoke : 344 -> 348
~ ___68-[ACUIAccountInfoViewController _verifyCredentialAndPromptIfNeeded:]_block_invoke_2 : 332 -> 348
~ -[ACUIAccountInfoViewController didToggleDataclass:] : 256 -> 260
~ ___52-[ACUIAccountInfoViewController didToggleDataclass:]_block_invoke : 528 -> 524
~ +[ACUIWebAuthViewController supportsAccount:] : 364 -> 368
~ __47-[ACUIWebAuthViewController startAuthorization]_block_invoke.8 : 232 -> 228
CStrings:
+ "com.apple.passwords.help"

```

