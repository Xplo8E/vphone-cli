## PrintKitUI

> `/System/iOSSupport/System/Library/PrivateFrameworks/PrintKitUI.framework/Versions/A/PrintKitUI`

```diff

-78.4.0.0.0
-  __TEXT.__text: 0x1ca44
-  __TEXT.__auth_stubs: 0xca0
+78.8.0.0.0
+  __TEXT.__text: 0x1e0f0
+  __TEXT.__auth_stubs: 0xc50
   __TEXT.__objc_methlist: 0x21d4
   __TEXT.__const: 0x238
   __TEXT.__cstring: 0xdc5
-  __TEXT.__gcc_except_tab: 0x5e8
+  __TEXT.__gcc_except_tab: 0x550
   __TEXT.__ustring: 0x8
-  __TEXT.__unwind_info: 0x778
+  __TEXT.__unwind_info: 0x858
   __TEXT.__objc_classname: 0x329
   __TEXT.__objc_methname: 0x5f39
   __TEXT.__objc_methtype: 0xb54

   __DATA_CONST.__objc_protorefs: 0x10
   __DATA_CONST.__objc_superrefs: 0x80
   __DATA_CONST.__objc_arraydata: 0x60
-  __AUTH_CONST.__auth_got: 0x660
+  __AUTH_CONST.__auth_got: 0x638
   __AUTH_CONST.__const: 0x70
   __AUTH_CONST.__cfstring: 0xe40
   __AUTH_CONST.__objc_const: 0x3078

   __AUTH_CONST.__objc_arrayobj: 0x30
   __AUTH_CONST.__objc_doubleobj: 0x10
   __AUTH_CONST.__objc_dictobj: 0x28
-  __AUTH.__objc_data: 0x5f0
+  __AUTH.__objc_data: 0xf0
   __DATA.__objc_ivar: 0x264
   __DATA.__data: 0x2a8
   __DATA.__bss: 0x48
-  __DATA_DIRTY.__objc_data: 0x1e0
+  __DATA_DIRTY.__objc_data: 0x6e0
   - /System/Library/Frameworks/CoreFoundation.framework/Versions/A/CoreFoundation
   - /System/Library/Frameworks/CoreGraphics.framework/Versions/A/CoreGraphics
   - /System/Library/Frameworks/Foundation.framework/Versions/C/Foundation

   - /System/iOSSupport/System/Library/PrivateFrameworks/UIKitCore.framework/Versions/A/UIKitCore
   - /usr/lib/libSystem.B.dylib
   - /usr/lib/libobjc.A.dylib
-  UUID: 82B22FE7-2EE7-3A17-93D6-82CC5E8DC4E5
-  Functions: 736
-  Symbols:   2180
+  UUID: A77F31AB-F7DD-3CD2-B969-28F33A2A0634
+  Functions: 737
+  Symbols:   2176
   CStrings:  1589
 
Symbols:
+ NupManagerCreate.cold.1
- _objc_claimAutoreleasedReturnValue
- _objc_retainAutoreleaseReturnValue
- _objc_retain_x1
- _objc_retain_x4
- _objc_retain_x9
Functions:
~ +[UIPrintInteractionController printableUTIs] : 216 -> 244
~ +[UIPrintInteractionController canPrintURL:] : 60 -> 64
~ +[UIPrintInteractionController canPrintData:] : 60 -> 64
~ +[UIPrintInteractionController utiForNSURL:] : 188 -> 196
~ _IsAssetURL : 88 -> 92
~ +[UIPrintInteractionController utiForNSData:] : 176 -> 184
~ +[UIPrintInteractionController hasValidPDFHeader:] : 232 -> 248
~ +[UIPrintInteractionController createCGPDFDocumentRefWithNSURL:] : 300 -> 308
~ +[UIPrintInteractionController sharedPrintController] : 84 -> 92
~ -[UIPrintInteractionController dealloc] : 184 -> 188
~ -[UIPrintInteractionController setPrintingItem:] : 208 -> 216
~ -[UIPrintInteractionController updatePrintingItems:] : 2196 -> 2316
~ -[UIPrintInteractionController _presentAnimated:hostingScene:completionHandler:] : 800 -> 812
~ ___80-[UIPrintInteractionController _presentAnimated:hostingScene:completionHandler:]_block_invoke : 284 -> 300
~ -[UIPrintInteractionController presentFromRect:inView:animated:completionHandler:] : 668 -> 704
~ ___82-[UIPrintInteractionController presentFromRect:inView:animated:completionHandler:]_block_invoke : 244 -> 260
~ -[UIPrintInteractionController presentFromBarButtonItem:animated:completionHandler:] : 652 -> 692
~ ___84-[UIPrintInteractionController presentFromBarButtonItem:animated:completionHandler:]_block_invoke : 236 -> 252
~ -[UIPrintInteractionController printToPrinter:completionHandler:] : 868 -> 948
~ -[UIPrintInteractionController _preparePrintingForIOSMac] : 396 -> 436
~ -[UIPrintInteractionController _cleanPrintState] : 400 -> 404
~ -[UIPrintInteractionController _currentPrintInfo] : 76 -> 80
~ -[UIPrintInteractionController _printItemContentSize:] : 344 -> 364
~ -[UIPrintInteractionController _printItemContentSize] : 160 -> 172
~ -[UIPrintInteractionController _canShowDuplex] : 352 -> 364
~ -[UIPrintInteractionController _canShowPageRange] : 208 -> 220
~ -[UIPrintInteractionController _canShowPaperList] : 108 -> 112
~ -[UIPrintInteractionController _canShowColor] : 132 -> 140
~ -[UIPrintInteractionController _canShowStaple] : 84 -> 88
~ -[UIPrintInteractionController _canShowPunch] : 84 -> 88
~ -[UIPrintInteractionController _canShowAnnotations] : 396 -> 384
~ -[UIPrintInteractionController _canShowLayout] : 356 -> 368
~ -[UIPrintInteractionController setPageRanges:] : 344 -> 336
~ -[UIPrintInteractionController printer] : 132 -> 128
~ -[UIPrintInteractionController paper] : 1700 -> 1772
~ -[UIPrintInteractionController setPaper:] : 208 -> 216
~ -[UIPrintInteractionController setTempPreviewFileURL:] : 160 -> 164
~ -[UIPrintInteractionController _updatePrintInfoWithAnnotations] : 108 -> 112
~ -[UIPrintInteractionController rendererToUse] : 672 -> 732
~ -[UIPrintInteractionController _updatePageCount] : 1688 -> 1796
~ -[UIPrintInteractionController isPhone] : 104 -> 112
~ -[UIPrintInteractionController _setupPrintPanel:forPDFGenerationOnly:] : 1472 -> 1632
~ -[UIPrintInteractionController _generatePDFWithNupForPrintingCompletion:] : 1276 -> 1352
~ _IsPDFURL : 112 -> 120
~ -[UIPrintInteractionController redrawPDFwithPageRange:] : 848 -> 896
~ -[UIPrintInteractionController _newPDFURLWithPath:isContentManaged:] : 68 -> 72
~ -[UIPrintInteractionController _tempFilePath] : 204 -> 216
~ -[UIPrintInteractionController _updateRendererWithQuality:] : 148 -> 156
~ -[UIPrintInteractionController _fullPagesRange] : 144 -> 152
~ -[UIPrintInteractionController _isPageCancelled:] : 160 -> 168
~ -[UIPrintInteractionController _pageRendererAvailable] : 140 -> 152
~ -[UIPrintInteractionController _mediaRect] : 288 -> 312
~ -[UIPrintInteractionController _printingItemPrintablePDFURL] : 288 -> 300
~ -[UIPrintInteractionController _generatePDFWithCompletionHandler:] : 808 -> 840
~ ___66-[UIPrintInteractionController _generatePDFWithCompletionHandler:]_block_invoke : 576 -> 592
~ -[UIPrintInteractionController numberOfPages] : 56 -> 60
~ -[UIPrintInteractionController getPrintingItemForPageNum:pdfItemPageNum:] : 444 -> 448
~ -[UIPrintInteractionController paperSizeForPageNum:] : 868 -> 916
~ -[UIPrintInteractionController drawImageForPageNum:toContext:sheetSize:] : 752 -> 788
~ -[UIPrintInteractionController createWebKitPDFForAllPages] : 520 -> 548
~ -[UIPrintInteractionController recalculateWebKitPageCount] : 112 -> 116
~ -[UIPrintInteractionController drawPagesWithPreviewState:] : 1188 -> 1220
~ -[UIPrintInteractionController drawImage:toContext:sheetSize:] : 596 -> 620
~ _ConvertCIBasedImage : 144 -> 152
~ -[UIPrintInteractionController convertedPrintableItem:] : 108 -> 116
~ -[UIPrintInteractionController _convertItemToPrintableItem:] : 1260 -> 1300
~ -[UIPrintInteractionController _drawPrintItem:toContext:printAllPages:] : 924 -> 992
~ -[UIPrintInteractionController _addPDFWithCGPDFDocumentRef:toContext:addAllPages:] : 1092 -> 1136
~ ___59-[UIPrintInteractionController _makePrintDocumentGenerator]_block_invoke : 404 -> 412
~ -[UIPrintInteractionController _cancelAllPreviewGeneration] : 256 -> 260
~ -[UIPrintInteractionController _printPanelDidPresent] : 100 -> 104
~ -[UIPrintInteractionController _printPanelWillDismissWithAction:] : 236 -> 240
~ -[UIPrintInteractionController _printPanelDidDismissWithAction:] : 312 -> 324
~ -[UIPrintInteractionController printInteractionController:cutLengthForPaper:] : 452 -> 460
~ -[UIPrintInteractionController printInteractionController:choosePaper:] : 164 -> 176
~ -[UIPrintInteractionController _updateCutterBehavior] : 876 -> 940
~ -[UIPrintInteractionController _preparePrintInfo] : 1096 -> 1220
~ -[UIPrintInteractionController _paperForPDFItem:withDuplexMode:] : 376 -> 396
~ -[UIPrintInteractionController _paperForContentType:] : 424 -> 440
~ -[UIPrintInteractionController _getCutLengthFromDelegateForPaper:] : 304 -> 308
~ ___66-[UIPrintInteractionController _getCutLengthFromDelegateForPaper:]_block_invoke : 96 -> 100
~ -[UIPrintInteractionController _getChosenPaperFromDelegateForPaperList:] : 380 -> 384
~ ___72-[UIPrintInteractionController _getChosenPaperFromDelegateForPaperList:]_block_invoke : 108 -> 116
~ -[UIPrintInteractionController _updatePrintPaper] : 244 -> 252
~ -[UIPrintInteractionController _canPrintPDFData:] : 124 -> 132
~ -[UIPrintInteractionController _printablePDFDataSize:] : 240 -> 256
~ -[UIPrintInteractionController _canPrintURL:] : 116 -> 124
~ -[UIPrintInteractionController _canShowPreview] : 728 -> 744
~ -[UIPrintInteractionController _canPreviewContent] : 600 -> 628
~ -[UIPrintInteractionController _printablePDFURLSize:] : 288 -> 304
~ -[UIPrintInteractionController _ensurePDFIsUnlockedFirstAttempt:completionHandler:] : 1488 -> 1552
~ ___83-[UIPrintInteractionController _ensurePDFIsUnlockedFirstAttempt:completionHandler:]_block_invoke_3 : 312 -> 336
~ ___83-[UIPrintInteractionController _ensurePDFIsUnlockedFirstAttempt:completionHandler:]_block_invoke_4 : 172 -> 184
~ -[UIPrintInteractionController _printingItemIsReallyTallPDF:] : 496 -> 512
~ -[UIPrintInteractionController needRedrawWithNUp] : 208 -> 224
~ -[UIPrintInteractionController _createDocInfoDict] : 1212 -> 1300
~ -[UIPrintInteractionController _newSaveContext:withMediaRect:] : 124 -> 128
~ -[UIPrintInteractionController _printPageWithRenderer:] : 620 -> 660
~ -[UIPrintInteractionController _endPrintJobWithAction:error:] : 212 -> 208
~ ___61-[UIPrintInteractionController _endPrintJobWithAction:error:]_block_invoke : 780 -> 840
~ -[UIPrintInteractionController appOptionsViewController] : 144 -> 156
~ -[UIPrintInteractionController setPrintInfo:] : 12 -> 64
~ -[UIPrintInteractionController setPrintPageRenderer:] : 12 -> 64
~ -[UIPrintInteractionController setPrintFormatter:] : 12 -> 64
~ -[UIPrintInteractionController setHostingWindowScene:] : 12 -> 64
~ -[UIPrintInteractionController(UIPrintInteractionController_Private) dismissAnimated:completionHandler:] : 156 -> 160
~ -[UIPrintInteractionController(UIPrintInteractionController_Private) savePDFToURL:showProgress:hostingScene:completionHandler:] : 152 -> 148
~ -[UIPrinterPickerController setSelectedPrinter:] : 12 -> 64
~ -[UIPrintInfo _initWithDictionary:] : 1844 -> 1912
~ _CopyDictionaryString : 144 -> 140
~ _GetDefaultJobName : 140 -> 152
~ -[UIPrintInfo dictionaryRepresentation] : 1232 -> 1308
~ -[UIPrintInfo initWithCoder:] : 752 -> 792
~ -[UIPrintInfo encodeWithCoder:] : 860 -> 856
~ ___36-[UIPrintInfo updateWithDictionary:]_block_invoke : 1248 -> 1272
~ -[UIPrintInfo resetToDefaultSettings:] : 384 -> 404
~ -[UIPrintInfo applyPreset:] : 1864 -> 1924
~ _arrayForKey : 92 -> 108
~ -[UIPrintInfo clearPreset:origPrintInfo:] : 2056 -> 2116
~ -[UIPrintInfo copyWithZone:] : 84 -> 88
~ -[UIPrintInfo _updateWithPrinter:] : 568 -> 612
~ -[UIPrintInfo _createPrintSettingsForPrinter:] : 4076 -> 4260
~ -[UIPrintInfo numNUpRows] : 80 -> 88
~ -[UIPrintInfo numNUpColumns] : 80 -> 88
~ -[UIPrintInfo setCurrentPrinter:] : 12 -> 64
~ -[UIPrintInfo setJobPreset:] : 12 -> 64
~ -[UIPrintInfo setAppliedPresetsList:] : 12 -> 64
~ -[UIPrintInfo setPageRanges:] : 12 -> 64
~ -[UIPrintInfo setPrintPaper:] : 12 -> 64
~ -[UIPrintInfo setJobAccountID:] : 12 -> 64
~ -[UIPrintInfo setMediaType:] : 12 -> 64
~ -[UIPrintInfo setInputSlot:] : 12 -> 64
~ -[UIPrintInfo setNUpRowsColumns:] : 12 -> 64
~ -[UIPrintInfo setFinishingTemplate:] : 12 -> 64
~ -[UIPrintInfo setOutputBin:] : 12 -> 64
~ -[UIPrintInfo setPageStackOrder:] : 12 -> 64
~ -[UIPrintInfo setPdfPassword:] : 12 -> 64
~ _GetAppName : 236 -> 272
~ +[UIPrinterInfoRequest requestInfoForPrinter:] : 116 -> 108
~ -[UIPrinterInfoRequest requestPrinterInfo] : 144 -> 148
~ ___42-[UIPrinterInfoRequest requestPrinterInfo]_block_invoke : 168 -> 172
~ ___42-[UIPrinterInfoRequest requestPrinterInfo]_block_invoke_2 : 180 -> 188
~ __UIPrinterInfoStartRequest : 224 -> 240
~ __UIPrinterInfoHasInfo : 124 -> 136
~ __UIPrinterInfoGetState : 228 -> 240
~ __UIPrinterInfoCancelRequest : 172 -> 188
~ __UIPrintInfoPrinterLookup : 264 -> 268
~ ____UIPrintInfoPrinterLookup_block_invoke : 172 -> 168
~ +[UIPrinter printerWithURL:] : 88 -> 96
~ -[UIPrinter URL] : 128 -> 140
~ -[UIPrinter displayName] : 96 -> 116
~ -[UIPrinter displayLocation] : 132 -> 144
~ -[UIPrinter supportedJobTypes] : 92 -> 100
~ -[UIPrinter makeAndModel] : 132 -> 144
~ -[UIPrinter supportsColor] : 144 -> 156
~ -[UIPrinter supportsDuplex] : 144 -> 156
~ -[UIPrinter contactPrinter:] : 348 -> 372
~ -[UIPrinter _printerID] : 76 -> 84
~ -[UIPrinter loadPrinterInfoDict] : 100 -> 108
~ -[UIPrinter printerFinishingOptions] : 168 -> 184
~ -[UIPrinter finishingTemplates] : 168 -> 184
~ -[UIPrinter outputBins] : 168 -> 184
~ -[UIPrinter supportedPresets] : 156 -> 172
~ -[UIPrinter supportedTrays] : 156 -> 172
~ -[UIPrinter loadedPapers] : 36 -> 40
~ -[UIPrinter supportedPapers] : 36 -> 40
~ -[UIPrinter supportedMediaTypes] : 156 -> 172
~ -[UIPrinter supportedQualities] : 156 -> 172
~ -[UIPrinter supportsJobAccountID] : 56 -> 60
~ -[UIPrinter jobAccountIDSupport] : 56 -> 60
~ -[UITextView(UITextViewPrintFormatter) drawRect:forViewPrintFormatter:] : 112 -> 116
~ -[UITextViewPrintFormatter adjustedPageBottom:] : 232 -> 252
~ -[UITextViewPrintFormatter pageData] : 1016 -> 1060
~ ___36-[UITextViewPrintFormatter pageData]_block_invoke : 540 -> 544
~ -[UITextViewPrintFormatter _recalcPageCount] : 72 -> 76
~ -[UITextViewPrintFormatter rectForPageAtIndex:] : 124 -> 132
~ -[UITextViewPrintFormatter drawInRect:forPageAtIndex:] : 1012 -> 1052
~ ___54-[UITextViewPrintFormatter drawInRect:forPageAtIndex:]_block_invoke : 292 -> 296
~ ___54-[UITextViewPrintFormatter drawInRect:forPageAtIndex:]_block_invoke_2 : 276 -> 284
~ ___54-[UITextViewPrintFormatter drawInRect:forPageAtIndex:]_block_invoke_3 : 188 -> 196
~ -[UITextViewPrintFormatter setText:] : 100 -> 104
~ -[UITextViewPrintFormatter text] : 76 -> 84
~ -[UITextViewPrintFormatter setAttributedText:] : 100 -> 104
~ -[UITextViewPrintFormatter attributedText] : 76 -> 84
~ -[UITextViewPrintFormatter setFont:] : 100 -> 104
~ -[UITextViewPrintFormatter font] : 76 -> 84
~ -[UITextViewPrintFormatter setColor:] : 96 -> 100
~ -[UITextViewPrintFormatter color] : 76 -> 84
~ -[UITextViewPrintFormatter setTextAlignment:] : 88 -> 92
~ -[UITextViewPrintFormatter textAlignment] : 56 -> 60
~ -[UITextViewPrintFormatter setPageData:] : 20 -> 80
~ -[UIPrintMessageAndSpinnerView initWithFrame:] : 428 -> 440
~ -[UIPrintMessageAndSpinnerView updateFont] : 144 -> 152
~ -[UIPrintMessageAndSpinnerView updateConstraints] : 552 -> 596
~ -[UIPrintMessageAndSpinnerView messageText] : 76 -> 84
~ -[UIPrintMessageAndSpinnerView setMessageText:] : 100 -> 104
~ -[UIPrintMessageAndSpinnerView spinSpinner] : 56 -> 60
~ -[UIPrintMessageAndSpinnerView setSpinSpinner:] : 88 -> 92
~ -[UIPrintMessageAndSpinnerView spinnerHidden] : 72 -> 80
~ -[UIPrintMessageAndSpinnerView setSpinnerHidden:] : 148 -> 152
~ -[UIPrintMessageAndSpinnerView setLabel:] : 20 -> 80
~ -[UIPrintMessageAndSpinnerView setSpinner:] : 20 -> 80
~ -[UIPrintMessageAndSpinnerView setCurrentVerticalConstraints:] : 20 -> 80
~ -[UIPrintMessageAndSpinnerView setHorizLabelConstraints:] : 20 -> 80
~ -[UIPrintMessageAndSpinnerView setHorizSpinnerConstraint:] : 20 -> 80
~ +[UIPrintPaper bestPaperForPageSize:withPapersFromArray:] : 364 -> 384
~ +[UIPrintPaper bestPaperForPageSize:andContentType:withPapersFromArray:] : 2172 -> 2228
~ +[UIPrintPaper _readyPaperListForPrinter:withDuplexMode:forContentType:contentSize:] : 432 -> 444
~ +[UIPrintPaper _readyDocumentPaperListForPrinter:withDuplexMode:contentSize:scaleUpForRoll:] : 412 -> 420
~ +[UIPrintPaper _defaultPKPaperForOuptutType:] : 356 -> 380
~ +[UIPrintPaper _genericPaperListForOutputType:] : 812 -> 888
~ +[UIPrintPaper _defaultPaperListForOutputType:] : 452 -> 468
~ +[UIPrintPaper _defaultPaperForOutputType:] : 92 -> 96
~ -[UIPrintPaper _updatePKPaper:] : 112 -> 120
~ -[UIPrintPaper isEqual:] : 112 -> 120
~ -[UIPrintPaper paperSize] : 112 -> 116
~ -[UIPrintPaper unAdjustedPaperSize] : 96 -> 100
~ -[UIPrintPaper unAdjustedPrintableRect] : 96 -> 100
~ -[UIPrintPaper printableRect] : 352 -> 356
~ -[UIPrintPaper description] : 120 -> 128
~ -[UIPrintPaper _localizedName] : 76 -> 84
~ -[UIPrintPaper _localizedMediaTypeName] : 76 -> 84
~ -[UIPrintPaper mediaType] : 108 -> 120
~ -[UIViewPrintFormatter copyWithZone:] : 100 -> 116
~ -[_UIPKPaperIOSMac paperSize] : 92 -> 96
~ -[_UIPKPaperIOSMac imageableAreaRect] : 116 -> 120
~ -[_UIPKPaperIOSMac leftMargin] : 92 -> 96
~ -[_UIPKPaperIOSMac topMargin] : 92 -> 96
~ -[_UIPKPaperIOSMac rightMargin] : 92 -> 96
~ -[_UIPKPaperIOSMac bottomMargin] : 92 -> 96
~ -[_UIPKPaperIOSMac topMarginInPoints] : 92 -> 96
~ -[_UIPKPaperIOSMac bottomMarginInPoints] : 92 -> 96
~ -[UIWebViewPrintFormatter _webDocumentView] : 76 -> 84
~ -[UIPrintingMessageView initInView:title:] : 1088 -> 1132
~ _redrawPDFWithNUp : 3532 -> 3552
~ -[UIPrintPanelViewController initWithPrintInterationController:inParentController:usingSplitView:] : 172 -> 164
~ -[UIPrintPanelViewController dismissAnimated:completionHandler:] : 96 -> 100
~ -[UIPrintPanelViewController _presentPrintPanelMacOS] : 152 -> 164
~ -[UIPrintPanelViewController _dismissMacOSPrintPanelWithoutPrinting] : 64 -> 68
~ -[UIPrintPanelViewController _dismissParentControllerUIIfPresent] : 264 -> 280
~ -[UIPrintPanelViewController setPrintInfo:] : 20 -> 80
~ -[UIPrintPanelViewController setPrintOptionsNavController:] : 20 -> 80
~ -[UIPrintPanelViewController setPrintOptionsTableView:] : 20 -> 80
~ -[UIPrintPanelViewController setPrintInteractionController:] : 20 -> 80
~ -[UIPrintPageRenderer printFormatters] : 120 -> 124
~ -[UIPrintPageRenderer addPrintFormatter:startingAtPageAtIndex:] : 200 -> 208
~ -[UIPrintPageRenderer printFormattersForPageAtIndex:] : 368 -> 376
~ -[UIPrintPageRenderer _removePrintFormatter:] : 136 -> 140
~ -[UIPrintPageRenderer _maxFormatterPage] : 308 -> 312
~ -[UIPrintPageRenderer setHeaderHeight:] : 268 -> 272
~ -[UIPrintPageRenderer setFooterHeight:] : 268 -> 272
~ -[UIPrintPageRenderer setPaperRect:] : 328 -> 332
~ -[UIPrintPageRenderer setPrintableRect:] : 328 -> 332
~ -[UIPrintPageRenderer drawPageAtIndex:inRect:] : 604 -> 608
~ -[UIPrintPageRenderer drawPrintFormatter:forPageAtIndex:] : 348 -> 352
~ -[UIPrintPageRenderer _endPrintJobContext] : 112 -> 116
~ -[UIPrintPageRenderer _drawPage:withScale:drawingToPDF:] : 264 -> 272
~ _NupManagerCreate : 864 -> 848
~ _NupManagerDrawASheet : 764 -> 760
~ _NupDrawAtRowCol : 848 -> 820
~ _LocalizedInteger : 108 -> 116
~ _LocalizedUnsignedInteger : 108 -> 116
~ _PMAppendToSummaryString : 212 -> 216
~ __cgImageToPaperTransform : 484 -> 468
~ _WindowSceneForPrintPanel : 508 -> 548
~ -[UITallPDFPrintFormatter initWithPDFURL:pdfPassword:] : 244 -> 232
~ -[UITallPDFPrintFormatter initWithPDFData:pdfPassword:] : 256 -> 252
~ -[UIMarkupTextPrintFormatter copyWithZone:] : 180 -> 196
~ -[UIMarkupTextPrintFormatter setMarkupText:] : 180 -> 184
~ -[UIMarkupTextPrintFormatter _recalcPageCount] : 296 -> 300
~ -[UIPrintFormatter _pageContentRect:] : 516 -> 520
~ -[UIPrinterDestination initWithURL:] : 156 -> 164
~ -[UIPrinterDestination dictionaryRepresentation] : 164 -> 168
~ -[UIPrinterDestination encodeWithCoder:] : 108 -> 112
~ -[UIPrinterDestination initWithCoder:] : 272 -> 288
~ -[UIPrintServiceExtensionContext _gatherPrintersForPrintInfo:reply:] : 348 -> 364
~ ___68-[UIPrintServiceExtensionContext _gatherPrintersForPrintInfo:reply:]_block_invoke : 88 -> 92
~ -[UIPrintServiceExtensionContext _authenticatedRequestForRequest:challengeResponse:reply:] : 196 -> 192
~ -[UIWebDocumentViewPrintFormatter copyWithZone:] : 100 -> 116
~ -[UIWebDocumentViewPrintFormatter _recalcPageCount] : 312 -> 320
~ -[UIWebDocumentViewPrintFormatter drawInRect:forPageAtIndex:] : 200 -> 204
~ -[UIWebDocumentViewPrintFormatter setFrameToPrint:] : 20 -> 80
~ -[UISimpleTextPrintFormatter initWithText:] : 184 -> 188

```
