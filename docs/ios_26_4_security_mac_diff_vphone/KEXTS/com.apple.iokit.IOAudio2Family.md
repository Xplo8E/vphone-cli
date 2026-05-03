## com.apple.iokit.IOAudio2Family

> `com.apple.iokit.IOAudio2Family`

```diff

 500.2.0.0.0
   __TEXT.__cstring: 0x3af
   __TEXT.__const: 0x18
-  __TEXT_EXEC.__text: 0x6bf0
+  __TEXT_EXEC.__text: 0x65b4
   __TEXT_EXEC.__auth_stubs: 0x0
   __DATA.__data: 0xc8
   __DATA.__common: 0x60

   __DATA_CONST.__mod_term_func: 0x10
   __DATA_CONST.__const: 0x1b58
   __DATA_CONST.__kalloc_type: 0x80
-  UUID: 72B7E263-87E6-3B35-AE4E-74F02543FDED
+  UUID: 85A57E1E-DF78-3DF4-AF30-8C614A353724
   Functions: 350
   Symbols:   727
   CStrings:  63
Functions:
~ __Z29IOAudio2Dictionary_getBooleanP12OSDictionaryPKc : 244 -> 228
~ __Z29IOAudio2Dictionary_setBooleanP12OSDictionaryPKcb : 356 -> 324
~ __Z28IOAudio2Dictionary_getUInt32P12OSDictionaryPKc : 152 -> 144
~ __Z28IOAudio2Dictionary_setUInt32P12OSDictionaryPKcj : 356 -> 324
~ __Z28IOAudio2Dictionary_getUInt64P12OSDictionaryPKc : 152 -> 144
~ __Z28IOAudio2Dictionary_setUInt64P12OSDictionaryPKcy : 356 -> 324
~ __ZN25IOAudio2ControlDictionary6createEjjjjjbjP8OSString : 316 -> 308
~ __ZN25IOAudio2ControlDictionary29createLevelControlSimpleRangeEjjjjjjjxjxjbjP8OSString : 380 -> 336
~ __ZN25IOAudio2ControlDictionary18createLevelControlEjjjjjjP7OSArrayjbjP8OSString : 180 -> 172
~ __ZN25IOAudio2ControlDictionary21createSelectorControlEjjjjjjP7OSArraybjP8OSString : 160 -> 152
~ __ZN25IOAudio2ControlDictionary26createMultiSelectorControlEjjjjjP7OSArrayS1_bjP8OSString : 224 -> 208
~ __ZN25IOAudio2ControlDictionary18createBlockControlEjjjjjjP12OSDictionarybjP8OSString : 160 -> 152
~ __ZN25IOAudio2ControlDictionary14getControlByIDEP7OSArrayj : 264 -> 232
~ __ZN25IOAudio2ControlDictionary8copyNameEP12OSDictionary : 148 -> 132
~ __ZN25IOAudio2ControlDictionary33setSliderControlPropertySelectorsEP12OSDictionaryjj : 476 -> 380
~ __ZN25IOAudio2ControlDictionary26getLevelControlSimpleRangeEP12OSDictionaryRjRxS2_S3_ : 188 -> 172
~ __ZN25IOAudio2ControlDictionary24copyLevelControlRangeMapEP12OSDictionary : 148 -> 132
~ __ZN25IOAudio2ControlDictionary27getLevelControlRangeByIndexEP7OSArrayjRjRxS2_S3_ : 204 -> 196
~ __ZN25IOAudio2ControlDictionary26setLevelControlSimpleRangeEP12OSDictionaryjxjx : 336 -> 300
~ __ZN25IOAudio2ControlDictionary32setLevelControlPropertySelectorsEP12OSDictionaryjjjjjj : 1044 -> 804
~ __ZN25IOAudio2ControlDictionary34setBooleanControlPropertySelectorsEP12OSDictionaryj : 340 -> 280
~ __ZN25IOAudio2ControlDictionary33copyMultiSelectorControlValueListEP12OSDictionary : 148 -> 132
~ __ZN25IOAudio2ControlDictionary30copySelectorControlSelectorMapEP12OSDictionary : 148 -> 132
~ __ZN25IOAudio2ControlDictionary35setSelectorControlPropertySelectorsEP12OSDictionaryjjj : 624 -> 492
~ __ZN25IOAudio2ControlDictionary36createSelectorControlSelectorMapItemEjP8OSString : 144 -> 136
~ __ZN25IOAudio2ControlDictionary36createSelectorControlSelectorMapItemEjP8OSStringj : 168 -> 160
~ __ZN25IOAudio2ControlDictionary36setStereoPanControlPropertySelectorsEP12OSDictionaryjj : 476 -> 380
~ __ZN25IOAudio2ControlDictionary26copyBlockControlDescriptorEP12OSDictionary : 148 -> 132
~ __ZN25IOAudio2ControlDictionary32setBlockControlPropertySelectorsEP12OSDictionaryjj : 476 -> 380
~ __ZN14IOAudio2Device4freeEv : 172 -> 152
~ __ZN14IOAudio2Device18destroyIOReportersEv : 80 -> 72
~ __ZN14IOAudio2Device5startEP9IOService : 300 -> 284
~ __ZN14IOAudio2Device17createIOReportersEv : 512 -> 476
~ __ZN14IOAudio2Device4stopEP9IOService : 128 -> 120
~ __ZN14IOAudio2Device13setPropertiesEP8OSObject : 272 -> 248
~ __ZN14IOAudio2Device13startIOEngineEv : 316 -> 308
~ __ZN14IOAudio2Device12stopIOEngineEv : 312 -> 304
~ __ZN14IOAudio2Device22startIOEngineWithFlagsEjPy : 104 -> 96
~ __ZN14IOAudio2Device21stopIOEngineWithFlagsEjPy : 104 -> 96
~ __ZN14IOAudio2Device13newUserClientEP4taskPvjP12OSDictionaryPP12IOUserClient : 748 -> 688
~ __ZN14IOAudio2Device15clientWasClosedEP24IOAudio2DeviceUserClient : 196 -> 188
~ __ZN14IOAudio2Device19clientMemoryForTypeEjPjPP18IOMemoryDescriptor : 392 -> 384
~ __ZN14IOAudio2Device19requestConfigChangeEjjyy : 296 -> 288
~ __ZN14IOAudio2Device18handleConfigChangeEP20IOAudio2Notificationy : 240 -> 232
~ __ZN14IOAudio2Device12updateReportEP19IOReportChannelListjPvS2_ : 332 -> 324
~ __ZN24IOAudio2DeviceUserClient12initWithTaskEP4taskPvjP12OSDictionary : 128 -> 120
~ __ZN24IOAudio2DeviceUserClient4freeEv : 124 -> 112
~ __ZN24IOAudio2DeviceUserClient5startEP9IOService : 432 -> 400
~ __ZN24IOAudio2DeviceUserClient4stopEP9IOService : 256 -> 224
~ __ZN24IOAudio2DeviceUserClient13clientCleanupEv : 160 -> 152
~ __ZN24IOAudio2DeviceUserClient12_clientCloseEP8OSObjectPvS2_S2_S2_ : 140 -> 132
~ __ZN24IOAudio2StreamDictionary6createEjjP12OSDictionaryP7OSArray : 256 -> 248
~ __ZN24IOAudio2StreamDictionary6createEjjjP12OSDictionaryP7OSArray : 280 -> 272
~ __ZN24IOAudio2StreamDictionary16getCurrentFormatEP12OSDictionaryR30IOAudio2StreamBasicDescription : 128 -> 120
~ __ZN24IOAudio2StreamDictionary16setCurrentFormatEP12OSDictionaryRK30IOAudio2StreamBasicDescription : 192 -> 168
~ __ZN24IOAudio2StreamDictionary27copyCurrentFormatDictionaryEP12OSDictionary : 148 -> 132
~ __ZN24IOAudio2StreamDictionary20copyAvailableFormatsEP12OSDictionary : 148 -> 132
~ __ZN24IOAudio2StreamDictionary15printDictionaryEP12OSDictionary : 408 -> 380
~ __ZN30IOAudio2StreamFormatDictionary21printRangedDictionaryEP12OSDictionary : 64 -> 48

```
