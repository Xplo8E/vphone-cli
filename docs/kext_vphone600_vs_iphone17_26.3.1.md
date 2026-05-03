# Kext load lists: vphone600 vs iPhone 17 (hardware)

Generated from kernel extension enumeration dumps for the same IPSW/train context.


| Source file        | Path                                                      |
| ------------------ | --------------------------------------------------------- |
| vphone (VM)        | `vm/iPhone17,3_26.3.1_23D8133_Restore/vphone600_kext.txt` |
| iPhone 17 hardware | `vm/iPhone17,3_26.3.1_23D8133_Restore/iphone17_kexts.txt` |


Bundle identifier is the primary key; version strings are taken verbatim from each file.

For these two dumps, **every bundle in the intersection (143/143) reports the same version string on vphone and on hardware.** That does not guarantee identical binaries—only that the reported kext version metadata matched when the lists were captured.

**Interpretation (high level):** Entries present only on vphone skew toward **virtual platform / VirtIO / paravirt GPU–video / VM FairPlay / EndpointSecurity / USB-serial and PCI XHCI**. Entries present only on iPhone skew toward **SoC peripherals (GPU, DCP display path, TB, NVMe, baseband, sensors, extended audio/haptics).**

## Summary


| Metric                          | Count |
| ------------------------------- | ----- |
| Unique bundles (vphone)         | 161   |
| Unique bundles (iphone)         | 320   |
| Common (same bundle ID in both) | 143   |
| Only vphone                     | 18    |
| Only iphone                     | 177   |


## Common bundles (both lists)


| Bundle ID                                                 | Version (vphone) | Version (iphone) | Same version? |
| --------------------------------------------------------- | ---------------- | ---------------- | ------------- |
| `com.apple.AUC`                                           | `1.0`            | `1.0`            | yes           |
| `com.apple.AppleFSCompression.AppleFSCompressionTypeZlib` | `1.0.0`          | `1.0.0`          | yes           |
| `com.apple.IOTextEncryptionFamily`                        | `1.0.0`          | `1.0.0`          | yes           |
| `com.apple.driver.AppleA7IOP`                             | `1.0.2`          | `1.0.2`          | yes           |
| `com.apple.driver.AppleARMPMU`                            | `1.0`            | `1.0`            | yes           |
| `com.apple.driver.AppleARMPlatform`                       | `1.0.2`          | `1.0.2`          | yes           |
| `com.apple.driver.AppleARMWatchdogTimer`                  | `1`              | `1`              | yes           |
| `com.apple.driver.AppleActuatorDriver`                    | `9130.2`         | `9130.2`         | yes           |
| `com.apple.driver.AppleAudioClockLibs`                    | `500.4`          | `500.4`          | yes           |
| `com.apple.driver.AppleBSDKextStarter`                    | `3`              | `3`              | yes           |
| `com.apple.driver.AppleBSDKextStarterTMPFS`               | `1`              | `1`              | yes           |
| `com.apple.driver.AppleBSDKextStarterVPN`                 | `3`              | `3`              | yes           |
| `com.apple.driver.AppleCallbackPowerSource`               | `1`              | `1`              | yes           |
| `com.apple.driver.AppleDiagnosticDataAccessReadOnly`      | `1.0.0`          | `1.0.0`          | yes           |
| `com.apple.driver.AppleDiskImages2`                       | `514.80.3`       | `514.80.3`       | yes           |
| `com.apple.driver.AppleEffaceableStorage`                 | `1.0`            | `1.0`            | yes           |
| `com.apple.driver.AppleEmbeddedAudioLibs`                 | `500.4`          | `500.4`          | yes           |
| `com.apple.driver.AppleEmbeddedLightSensor`               | `1.0.0d1`        | `1.0.0d1`        | yes           |
| `com.apple.driver.AppleEmbeddedPCIE`                      | `1`              | `1`              | yes           |
| `com.apple.driver.AppleEmbeddedTempSensor`                | `1.0.0`          | `1.0.0`          | yes           |
| `com.apple.driver.AppleEmbeddedUSB`                       | `1`              | `1`              | yes           |
| `com.apple.driver.AppleEmbeddedUSBHost`                   | `1`              | `1`              | yes           |
| `com.apple.driver.AppleFirmwareKit`                       | `1`              | `1`              | yes           |
| `com.apple.driver.AppleFirmwareUpdateKext`                | `1`              | `1`              | yes           |
| `com.apple.driver.AppleGameControllerPersonality`         | `13.3.1`         | `13.3.1`         | yes           |
| `com.apple.driver.AppleHIDKeyboard`                       | `8000.5`         | `8000.5`         | yes           |
| `com.apple.driver.AppleHIDKeyboardEmbedded`               | `1.2.0a3`        | `1.2.0a3`        | yes           |
| `com.apple.driver.AppleIISController`                     | `500.2`          | `500.2`          | yes           |
| `com.apple.driver.AppleInputDeviceSupport`                | `9100.29.1`      | `9100.29.1`      | yes           |
| `com.apple.driver.AppleLockdownMode`                      | `1`              | `1`              | yes           |
| `com.apple.driver.AppleM2ScalerCSCDriver`                 | `265.0.0`        | `265.0.0`        | yes           |
| `com.apple.driver.AppleM68Buttons`                        | `1.0.0d1`        | `1.0.0d1`        | yes           |
| `com.apple.driver.AppleMobileApNonce`                     | `1`              | `1`              | yes           |
| `com.apple.driver.AppleMobileFileIntegrity`               | `1.0.5`          | `1.0.5`          | yes           |
| `com.apple.driver.AppleMultitouchDriver`                  | `9130.2`         | `9130.2`         | yes           |
| `com.apple.driver.AppleMultitouchSPI`                     | `9130.2`         | `9130.2`         | yes           |
| `com.apple.driver.AppleNANDConfigAccess`                  | `1.0.0`          | `1.0.0`          | yes           |
| `com.apple.driver.AppleOnboardSerial`                     | `1.0`            | `1.0`            | yes           |
| `com.apple.driver.ApplePIODMA`                            | `1`              | `1`              | yes           |
| `com.apple.driver.ApplePMGR`                              | `1`              | `1`              | yes           |
| `com.apple.driver.AppleS8000AES`                          | `1`              | `1`              | yes           |
| `com.apple.driver.AppleSEPCredentialManager`              | `1.0`            | `1.0`            | yes           |
| `com.apple.driver.AppleSEPKeyStore`                       | `2`              | `2`              | yes           |
| `com.apple.driver.AppleSEPManager`                        | `1.0.1`          | `1.0.1`          | yes           |
| `com.apple.driver.AppleSMC`                               | `3.1.9`          | `3.1.9`          | yes           |
| `com.apple.driver.AppleSPU`                               | `1`              | `1`              | yes           |
| `com.apple.driver.AppleSamsungSerial`                     | `1.0.0d1`        | `1.0.0d1`        | yes           |
| `com.apple.driver.AppleSerialShim`                        | `1`              | `1`              | yes           |
| `com.apple.driver.AppleStorageDrivers`                    | `557`            | `557`            | yes           |
| `com.apple.driver.AppleTopCaseDriverV2`                   | `9110.2`         | `9110.2`         | yes           |
| `com.apple.driver.AppleTopCaseHIDEventDriver`             | `9110.2`         | `9110.2`         | yes           |
| `com.apple.driver.AppleTypeCPhy`                          | `1`              | `1`              | yes           |
| `com.apple.driver.AppleUSBCardReader`                     | `557`            | `557`            | yes           |
| `com.apple.driver.AppleUSBDeviceMux`                      | `1.0.0d1`        | `1.0.0d1`        | yes           |
| `com.apple.driver.AppleUSBDeviceNCM`                      | `5.0.0`          | `5.0.0`          | yes           |
| `com.apple.driver.AppleUSBEthernetHost`                   | `8.1.1`          | `8.1.1`          | yes           |
| `com.apple.driver.AppleUSBHostMergeProperties`            | `1.2`            | `1.2`            | yes           |
| `com.apple.driver.AppleUSBMassStorageInterfaceNub`        | `557`            | `557`            | yes           |
| `com.apple.driver.DiskImages`                             | `493.0.0`        | `493.0.0`        | yes           |
| `com.apple.driver.DiskImages.FileBackingStore`            | `493.0.0`        | `493.0.0`        | yes           |
| `com.apple.driver.DiskImages.KernelBacked`                | `493.0.0`        | `493.0.0`        | yes           |
| `com.apple.driver.DiskImages.RAMBackingStore`             | `493.0.0`        | `493.0.0`        | yes           |
| `com.apple.driver.DiskImages.ReadWriteDiskImage`          | `493.0.0`        | `493.0.0`        | yes           |
| `com.apple.driver.DiskImages.UDIFDiskImage`               | `493.0.0`        | `493.0.0`        | yes           |
| `com.apple.driver.ExclavesAudioKext`                      | `300.59`         | `300.59`         | yes           |
| `com.apple.driver.FairPlayIOKit`                          | `72.15.0`        | `72.15.0`        | yes           |
| `com.apple.driver.IISAudioIsolatedStreamECProxy`          | `520.2`          | `520.2`          | yes           |
| `com.apple.driver.IODARTFamily`                           | `1`              | `1`              | yes           |
| `com.apple.driver.IOSlaveProcessor`                       | `1`              | `1`              | yes           |
| `com.apple.driver.RTBuddy`                                | `1.0.0`          | `1.0.0`          | yes           |
| `com.apple.driver.SCSIDeviceSpecifics`                    | `557`            | `557`            | yes           |
| `com.apple.driver.USBStorageDeviceSpecifics`              | `557`            | `557`            | yes           |
| `com.apple.driver.mDNSOffloadUserClient-Embedded`         | `1.0.1b8`        | `1.0.1b8`        | yes           |
| `com.apple.driver.usb.AppleSynopsysUSBXHCI`               | `1`              | `1`              | yes           |
| `com.apple.driver.usb.AppleUSBCommon`                     | `1.0`            | `1.0`            | yes           |
| `com.apple.driver.usb.AppleUSBHostCompositeDevice`        | `1.2`            | `1.2`            | yes           |
| `com.apple.driver.usb.AppleUSBHostDeviceSupport`          | `1.0`            | `1.0`            | yes           |
| `com.apple.driver.usb.AppleUSBHostPacketFilter`           | `1.0`            | `1.0`            | yes           |
| `com.apple.driver.usb.AppleUSBHostPlatformProperties`     | `1.2`            | `1.2`            | yes           |
| `com.apple.driver.usb.AppleUSBHostiOSDevice`              | `1.0`            | `1.0`            | yes           |
| `com.apple.driver.usb.AppleUSBHub`                        | `1.2`            | `1.2`            | yes           |
| `com.apple.driver.usb.AppleUSBXHCI`                       | `1.2`            | `1.2`            | yes           |
| `com.apple.driver.usb.cdc`                                | `5.0.0`          | `5.0.0`          | yes           |
| `com.apple.driver.usb.cdc.ecm`                            | `5.0.0`          | `5.0.0`          | yes           |
| `com.apple.driver.usb.cdc.ncm`                            | `5.0.0`          | `5.0.0`          | yes           |
| `com.apple.driver.usb.ethernet.asix`                      | `5.0.0`          | `5.0.0`          | yes           |
| `com.apple.driver.usb.networking`                         | `5.0.0`          | `5.0.0`          | yes           |
| `com.apple.filesystems.apfs`                              | `2632.80.1`      | `2632.80.1`      | yes           |
| `com.apple.filesystems.hfs.kext`                          | `704.60.4`       | `704.60.4`       | yes           |
| `com.apple.filesystems.lifs`                              | `1`              | `1`              | yes           |
| `com.apple.filesystems.tmpfs`                             | `1`              | `1`              | yes           |
| `com.apple.iokit.AppleARMIISAudio`                        | `520.2`          | `520.2`          | yes           |
| `com.apple.iokit.CoreAnalyticsFamily`                     | `1`              | `1`              | yes           |
| `com.apple.iokit.IOAVFamily`                              | `1.0.0`          | `1.0.0`          | yes           |
| `com.apple.iokit.IOAccessoryManager`                      | `1.0.0`          | `1.0.0`          | yes           |
| `com.apple.iokit.IOAccessoryPortUSB`                      | `1.0.0`          | `1.0.0`          | yes           |
| `com.apple.iokit.IOAudio2Family`                          | `1.0`            | `1.0`            | yes           |
| `com.apple.iokit.IOCECFamily`                             | `1`              | `1`              | yes           |
| `com.apple.iokit.IOCryptoAcceleratorFamily`               | `1.0.1`          | `1.0.1`          | yes           |
| `com.apple.iokit.IOGPUFamily`                             | `129.3.2`        | `129.3.2`        | yes           |
| `com.apple.iokit.IOGameControllerFamily`                  | `13.3.1`         | `13.3.1`         | yes           |
| `com.apple.iokit.IOHDCPFamily`                            | `1.0.0`          | `1.0.0`          | yes           |
| `com.apple.iokit.IOHIDEventDriver`                        | `2.0.0`          | `2.0.0`          | yes           |
| `com.apple.iokit.IOHIDEventDriverSafeBoot`                | `2.0.0`          | `2.0.0`          | yes           |
| `com.apple.iokit.IOHIDFamily`                             | `2.0.0`          | `2.0.0`          | yes           |
| `com.apple.iokit.IOMobileGraphicsFamily`                  | `343.0.0`        | `343.0.0`        | yes           |
| `com.apple.iokit.IONetworkFamily`                         | `1.0`            | `1.0`            | yes           |
| `com.apple.iokit.IONetworkingFamily`                      | `3.4`            | `3.4`            | yes           |
| `com.apple.iokit.IOPCIFamily`                             | `2.9`            | `2.9`            | yes           |
| `com.apple.iokit.IOPortFamily`                            | `1.0`            | `1.0`            | yes           |
| `com.apple.iokit.IOReportFamily`                          | `47`             | `47`             | yes           |
| `com.apple.iokit.IOSCSIArchitectureModelFamily`           | `541.40.1`       | `541.40.1`       | yes           |
| `com.apple.iokit.IOSCSIBlockCommandsDevice`               | `541.40.1`       | `541.40.1`       | yes           |
| `com.apple.iokit.IOSerialFamily`                          | `11`             | `11`             | yes           |
| `com.apple.iokit.IOSkywalkFamily`                         | `1.0`            | `1.0`            | yes           |
| `com.apple.iokit.IOSlowAdaptiveClockingFamily`            | `1.0.0`          | `1.0.0`          | yes           |
| `com.apple.iokit.IOStorageFamily`                         | `2.1`            | `2.1`            | yes           |
| `com.apple.iokit.IOStreamFamily`                          | `1.1.0`          | `1.1.0`          | yes           |
| `com.apple.iokit.IOSurface`                               | `393.3.2`        | `393.3.2`        | yes           |
| `com.apple.iokit.IOTimeSyncFamily`                        | `1420.2`         | `1420.2`         | yes           |
| `com.apple.iokit.IOUSBDeviceFamily`                       | `2.0.0`          | `2.0.0`          | yes           |
| `com.apple.iokit.IOUSBHostFamily`                         | `1.2`            | `1.2`            | yes           |
| `com.apple.iokit.IOUSBMassStorageDriver`                  | `272.80.3`       | `272.80.3`       | yes           |
| `com.apple.iokit.IOUserEthernet`                          | `1.0.1`          | `1.0.1`          | yes           |
| `com.apple.kec.Compression`                               | `1.0`            | `1.0`            | yes           |
| `com.apple.kec.Libm`                                      | `1`              | `1`              | yes           |
| `com.apple.kec.corecrypto`                                | `26.0`           | `26.0`           | yes           |
| `com.apple.kec.pthread`                                   | `1`              | `1`              | yes           |
| `com.apple.kext.AppleMatch`                               | `1.0.0d1`        | `1.0.0d1`        | yes           |
| `com.apple.kext.CoreTrust`                                | `1`              | `1`              | yes           |
| `com.apple.kpi.bsd`                                       | `25.3.0`         | `25.3.0`         | yes           |
| `com.apple.kpi.dsep`                                      | `25.3.0`         | `25.3.0`         | yes           |
| `com.apple.kpi.iokit`                                     | `25.3.0`         | `25.3.0`         | yes           |
| `com.apple.kpi.libkern`                                   | `25.3.0`         | `25.3.0`         | yes           |
| `com.apple.kpi.mach`                                      | `25.3.0`         | `25.3.0`         | yes           |
| `com.apple.kpi.private`                                   | `25.3.0`         | `25.3.0`         | yes           |
| `com.apple.kpi.unsupported`                               | `25.3.0`         | `25.3.0`         | yes           |
| `com.apple.nke.l2tp`                                      | `1.9`            | `1.9`            | yes           |
| `com.apple.nke.ppp`                                       | `1.9`            | `1.9`            | yes           |
| `com.apple.plugin.IOgPTPPlugin`                           | `1420.2`         | `1420.2`         | yes           |
| `com.apple.security.AKSAnalytics`                         | `1`              | `1`              | yes           |
| `com.apple.security.AppleImage4`                          | `7.0.0`          | `7.0.0`          | yes           |
| `com.apple.security.sandbox`                              | `300.0`          | `300.0`          | yes           |


## Only vphone (VM / paravirt stack)


| Bundle ID                                              | Version  |
| ------------------------------------------------------ | -------- |
| `com.apple.driver.AppleARMGIC`                         | `1`      |
| `com.apple.driver.AppleM2ScalerParavirtDriver`         | `1.0.0`  |
| `com.apple.driver.ApplePVPanic`                        | `1`      |
| `com.apple.driver.AppleParavirtGPUIOGPUFamily`         | `15.0.0` |
| `com.apple.driver.AppleVPIOP`                          | `1.0.2`  |
| `com.apple.driver.AppleVideoToolboxParavirtualization` | `15.0.0` |
| `com.apple.driver.AppleVirtIO`                         | `248`    |
| `com.apple.driver.AppleVirtualPlatform`                | `1`      |
| `com.apple.driver.AvpFairPlayDriver`                   | `2.9.0`  |
| `com.apple.driver.driverkit.serial`                    | `6.0.0`  |
| `com.apple.driver.usb.AppleEmbeddedUSBXHCIPCI`         | `1`      |
| `com.apple.driver.usb.AppleUSBXHCIPCI`                 | `1.2`    |
| `com.apple.driver.usb.cdc.acm`                         | `5.0.0`  |
| `com.apple.driver.usb.serial`                          | `6.0.0`  |
| `com.apple.iokit.AppleParavirtIOSurface`               | `15.0.0` |
| `com.apple.iokit.AppleVirtIONeuralEngineDevice`        | `1.2.0`  |
| `com.apple.iokit.AppleVirtIOStorage`                   | `1.0.0`  |
| `com.apple.iokit.EndpointSecurity`                     | `1`      |


## Only iPhone hardware


| Bundle ID                                              | Version     |
| ------------------------------------------------------ | ----------- |
| `com.apple.AGXFirmwareKextG17PRTBuddy`                 | `1`         |
| `com.apple.AGXFirmwareKextRTBuddy64`                   | `345.20.1`  |
| `com.apple.AGXG17P`                                    | `345.20.1`  |
| `com.apple.EXBrightCalibrationConsumer`                | `1.0.0`     |
| `com.apple.EXBrightKext`                               | `1.0.0`     |
| `com.apple.ExclaveKextClient`                          | `1.0.0`     |
| `com.apple.driver.AOPAudio2`                           | `300.4`     |
| `com.apple.driver.AOPTouchKext`                        | `313`       |
| `com.apple.driver.ASIOKit`                             | `13.28`     |
| `com.apple.driver.AppleA7IOP-ASCWrap-v6`               | `1.0.2`     |
| `com.apple.driver.AppleALSColorSensor`                 | `1.0.0d1`   |
| `com.apple.driver.AppleAOP2`                           | `1`         |
| `com.apple.driver.AppleAOPAudio`                       | `500.14`    |
| `com.apple.driver.AppleAOPHaptics`                     | `930.11`    |
| `com.apple.driver.AppleAVD`                            | `908`       |
| `com.apple.driver.AppleAVE2`                           | `905.29.1`  |
| `com.apple.driver.AppleAstrisGpioProbe`                | `1.0.1`     |
| `com.apple.driver.AppleAuthCP`                         | `1.0.0`     |
| `com.apple.driver.AppleBasebandM20`                    | `1.0.0d1`   |
| `com.apple.driver.AppleBasebandPCI`                    | `1`         |
| `com.apple.driver.AppleBasebandPCIMAVControl`          | `1`         |
| `com.apple.driver.AppleBasebandPCIMAVPDP`              | `1`         |
| `com.apple.driver.AppleBluetoothDebug`                 | `1`         |
| `com.apple.driver.AppleBluetoothDebugService`          | `1`         |
| `com.apple.driver.AppleBluetoothModule`                | `1`         |
| `com.apple.driver.AppleC26Charger`                     | `1.0.1`     |
| `com.apple.driver.AppleCS42L79Audio`                   | `930.11`    |
| `com.apple.driver.AppleCSEmbeddedAudio`                | `930.11`    |
| `com.apple.driver.AppleConvergedIPCOLYBTControl`       | `1`         |
| `com.apple.driver.AppleConvergedPCI`                   | `1`         |
| `com.apple.driver.AppleDAPF`                           | `1`         |
| `com.apple.driver.AppleDCP`                            | `1`         |
| `com.apple.driver.AppleDCPDPTXProxy`                   | `1.0.0`     |
| `com.apple.driver.AppleDialogPMU`                      | `1.0.1`     |
| `com.apple.driver.AppleDisplayCrossbar`                | `1.0.0`     |
| `com.apple.driver.AppleDockChannel`                    | `1`         |
| `com.apple.driver.AppleEffaceableBlockDevice`          | `1.0`       |
| `com.apple.driver.AppleEmbeddedAudio`                  | `930.11`    |
| `com.apple.driver.AppleEmbeddedAudioResourceManager`   | `930.11`    |
| `com.apple.driver.AppleEmbeddedGPS`                    | `1.0.0d1`   |
| `com.apple.driver.AppleEmbeddedMikeyBus`               | `1.0.0d1`   |
| `com.apple.driver.AppleEmbeddedTouchEEPROM`            | `1`         |
| `com.apple.driver.AppleEpochManager`                   | `1`         |
| `com.apple.driver.AppleEventLogHandler`                | `1`         |
| `com.apple.driver.AppleEverestErrorHandler`            | `1`         |
| `com.apple.driver.AppleFAN53740`                       | `1`         |
| `com.apple.driver.AppleGPIOCanary`                     | `1.0.0`     |
| `com.apple.driver.AppleGPIOICController`               | `1.0.2`     |
| `com.apple.driver.AppleGenericMultitouch`              | `26.2`      |
| `com.apple.driver.AppleH10PearlCameraInterface`        | `22.303.0`  |
| `com.apple.driver.AppleH16ANEInterface`                | `9.300.0`   |
| `com.apple.driver.AppleH16CameraInterface`             | `5.311`     |
| `com.apple.driver.AppleH16PhotonDetector`              | `1.0`       |
| `com.apple.driver.AppleHIDALSService`                  | `1`         |
| `com.apple.driver.AppleHIDTransport`                   | `9100.29.1` |
| `com.apple.driver.AppleHIDTransportFIFO`               | `9100.29.1` |
| `com.apple.driver.AppleHIDTransportMailbox`            | `9100.29.1` |
| `com.apple.driver.AppleHIDTransportSCMCommon`          | `9100.29.1` |
| `com.apple.driver.AppleHIDTransportSPI`                | `9100.29.1` |
| `com.apple.driver.AppleHPM`                            | `3.4.4`     |
| `com.apple.driver.AppleHapticsSupportLEAP`             | `10.16`     |
| `com.apple.driver.AppleHapticsSupportNVM`              | `10.16`     |
| `com.apple.driver.AppleIDAMInterface`                  | `1`         |
| `com.apple.driver.AppleIDV`                            | `8.303`     |
| `com.apple.driver.AppleIOPADMAStream`                  | `300.8`     |
| `com.apple.driver.AppleIPAppender`                     | `1.0`       |
| `com.apple.driver.AppleInterruptControllerV3`          | `1.0.0d1`   |
| `com.apple.driver.AppleJPEGDriver`                     | `7.7.2`     |
| `com.apple.driver.AppleMikeyBusAudio`                  | `400.2.1`   |
| `com.apple.driver.AppleMobileDispH17P-DCP`             | `140.0`     |
| `com.apple.driver.AppleMultiFunctionManager`           | `1`         |
| `com.apple.driver.AppleOLYHAL`                         | `1`         |
| `com.apple.driver.ApplePMP`                            | `1`         |
| `com.apple.driver.ApplePMPFirmware`                    | `1`         |
| `com.apple.driver.ApplePPMCPMS`                        | `3.0`       |
| `com.apple.driver.ApplePTD`                            | `1.0.0`     |
| `com.apple.driver.AppleParrot`                         | `1`         |
| `com.apple.driver.ApplePearlSEPDriver`                 | `1`         |
| `com.apple.driver.ApplePhoneBTM`                       | `1.0.1`     |
| `com.apple.driver.ApplePhotonDetector`                 | `1.0`       |
| `com.apple.driver.AppleProResHW`                       | `501.4`     |
| `com.apple.driver.AppleProcessorTrace`                 | `1.0.0`     |
| `com.apple.driver.AppleProxDriver`                     | `49.4.2`    |
| `com.apple.driver.AppleS5L8920XPWM`                    | `1.0.0d1`   |
| `com.apple.driver.AppleS5L8940XI2C`                    | `1.0.0d2`   |
| `com.apple.driver.AppleS5L8960XNCO`                    | `1`         |
| `com.apple.driver.AppleS8000DWI`                       | `1.0.0d1`   |
| `com.apple.driver.AppleSARService`                     | `1`         |
| `com.apple.driver.AppleSART`                           | `1`         |
| `com.apple.driver.AppleSEPHDCPManager`                 | `1.0.1`     |
| `com.apple.driver.AppleSMCWirelessCharger`             | `1.0.1`     |
| `com.apple.driver.AppleSPIMC`                          | `1`         |
| `com.apple.driver.AppleSPMI`                           | `1.0.1`     |
| `com.apple.driver.AppleSPMIPMU`                        | `1.0.1`     |
| `com.apple.driver.AppleSPURose`                        | `1`         |
| `com.apple.driver.AppleSPUSphere`                      | `1`         |
| `com.apple.driver.AppleSSE`                            | `1.0`       |
| `com.apple.driver.AppleSmartBatteryManagerEmbedded`    | `1`         |
| `com.apple.driver.AppleSmartIO2`                       | `1`         |
| `com.apple.driver.AppleStockholmControl`               | `1.0.0`     |
| `com.apple.driver.AppleSynopsysMIPIDSI`                | `1.0.0`     |
| `com.apple.driver.AppleT6020PCIePIODMA`                | `1`         |
| `com.apple.driver.AppleT8030SOCTuner`                  | `1`         |
| `com.apple.driver.AppleT8103TypeCPhy`                  | `1`         |
| `com.apple.driver.AppleT8110DART`                      | `1`         |
| `com.apple.driver.AppleT8130TypeCPhy`                  | `1`         |
| `com.apple.driver.AppleT8140`                          | `1`         |
| `com.apple.driver.AppleT8140ANEHAL`                    | `9.300.3`   |
| `com.apple.driver.AppleT8140CLPC`                      | `1`         |
| `com.apple.driver.AppleT8140MCC`                       | `1`         |
| `com.apple.driver.AppleT8140PCIe`                      | `1`         |
| `com.apple.driver.AppleT8140PMGR`                      | `1`         |
| `com.apple.driver.AppleTemperatureSensor`              | `1.0.0d1`   |
| `com.apple.driver.AppleThunderboltDPAdapterFamily`     | `8.5.1`     |
| `com.apple.driver.AppleThunderboltDPInAdapter`         | `8.5.1`     |
| `com.apple.driver.AppleThunderboltDPOutAdapter`        | `8.5.1`     |
| `com.apple.driver.AppleThunderboltEDMService`          | `5.0.3`     |
| `com.apple.driver.AppleThunderboltEDMSource`           | `5.0.3`     |
| `com.apple.driver.AppleThunderboltIP`                  | `4.0.3`     |
| `com.apple.driver.AppleThunderboltNHI`                 | `7.2.81`    |
| `com.apple.driver.AppleThunderboltPCIDownAdapter`      | `4.1.1`     |
| `com.apple.driver.AppleThunderboltPCIUpAdapter`        | `4.1.1`     |
| `com.apple.driver.AppleThunderboltUSBDownAdapter`      | `1.0.4`     |
| `com.apple.driver.AppleThunderboltUSBType2DownAdapter` | `1.0.4`     |
| `com.apple.driver.AppleThunderboltUSBType2UpAdapter`   | `1.0.4`     |
| `com.apple.driver.AppleThunderboltUSBUpAdapter`        | `1.0.4`     |
| `com.apple.driver.AppleTriStar`                        | `1.0.0`     |
| `com.apple.driver.AppleTypeCPhyAUSBC`                  | `1`         |
| `com.apple.driver.AppleUSBAudio`                       | `830.31`    |
| `com.apple.driver.AppleUSBDeviceAudioController`       | `830.31`    |
| `com.apple.driver.AppleUSBEthernetDevice`              | `7.0`       |
| `com.apple.driver.AppleUSBLightningAdapter`            | `1`         |
| `com.apple.driver.AppleUSBMike`                        | `1.0.0d1`   |
| `com.apple.driver.AppleUSBTopCaseDriver`               | `9110.2`    |
| `com.apple.driver.AppleUSBXDCI`                        | `1.0`       |
| `com.apple.driver.AppleUSBXDCIARM`                     | `1.0`       |
| `com.apple.driver.AppleUVDM`                           | `1.0.0`     |
| `com.apple.driver.AppleUVDMDriver`                     | `1.0.0`     |
| `com.apple.driver.AudioDMACLLTEscalationDetector-Stub` | `530.10`    |
| `com.apple.driver.AudioDMAController-T8140`            | `530.10`    |
| `com.apple.driver.AudioDMAFamily`                      | `530.10`    |
| `com.apple.driver.AudioSharedDARTMapperProxy`          | `300.59`    |
| `com.apple.driver.DCPAVFamilyProxy`                    | `1`         |
| `com.apple.driver.DCPDPFamilyProxy`                    | `1`         |
| `com.apple.driver.DMAChannelProxy`                     | `530.10`    |
| `com.apple.driver.EXDisplayPipeH17P`                   | `1.0.0`     |
| `com.apple.driver.ExclaveSEPManagerProxy`              | `1`         |
| `com.apple.driver.IOAudioCodecs`                       | `1.0.0`     |
| `com.apple.driver.IOHIDPowerSource`                    | `1`         |
| `com.apple.driver.IOPAudioAssetManagerDevice`          | `300.21`    |
| `com.apple.driver.IOPAudioClientManagerDevice`         | `300.21`    |
| `com.apple.driver.IOPAudioHapticsLEAPControlDevice`    | `300.21`    |
| `com.apple.driver.IOPAudioIOBufferDevice`              | `300.21`    |
| `com.apple.driver.IOPAudioIsolatedIOBufferDevice`      | `300.21`    |
| `com.apple.driver.IOPAudioLEAPControlDevice`           | `300.21`    |
| `com.apple.driver.IOPAudioLPMicDevice`                 | `300.21`    |
| `com.apple.driver.IOPAudioPCMAssetManagerDevice`       | `300.21`    |
| `com.apple.driver.IOPAudioSpeaker`                     | `930.11`    |
| `com.apple.driver.IOPAudioVoiceTriggerDevice`          | `500.14`    |
| `com.apple.driver.IOPEmbeddedAudio`                    | `930.11`    |
| `com.apple.driver.IOPHaptics`                          | `930.11`    |
| `com.apple.driver.SecureRTBuddyProxy`                  | `1.0.0`     |
| `com.apple.driver.corecapture`                         | `1.0.4`     |
| `com.apple.driver.usb.AppleSynopsysUSB40XHCI`          | `1`         |
| `com.apple.driver.usb.AppleUSBHostBillboardDevice`     | `1.0`       |
| `com.apple.driver.usb.IOUSBHostHIDDevice`              | `1.2`       |
| `com.apple.driver.usb.IOUSBHostHIDDeviceSafeBoot`      | `1.2`       |
| `com.apple.iokit.AppleSEPGenericTransfer`              | `1`         |
| `com.apple.iokit.IOBiometricFamily`                    | `1`         |
| `com.apple.iokit.IODisplayPortFamily`                  | `1.0.0`     |
| `com.apple.iokit.IOMIPIFamily`                         | `1`         |
| `com.apple.iokit.IOMikeyBusFamily`                     | `1.0.0`     |
| `com.apple.iokit.IOMobileGraphicsFamily-DCP`           | `343.0.0`   |
| `com.apple.iokit.IONVMeFamily`                         | `2.1.0`     |
| `com.apple.iokit.IOPAudioDriverFamily`                 | `300.4`     |
| `com.apple.iokit.IOThunderboltFamily`                  | `9.3.3`     |
| `com.apple.kec.XrtHostedXnu`                           | `1`         |


