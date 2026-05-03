# Security bulletin ↔ vphone bundles ↔ macOS kext diff

Apple component names come from [APPLE_SECURITY_IOS_26_4.md](APPLE_SECURITY_IOS_26_4.md). Binary deltas are from `macOS_26_3_1_25D2128__vs_26_4_25E246` ([blacktop/ipsw-diffs](https://github.com/blacktop/ipsw-diffs)), files under `[KEXTS/](KEXTS/)`.

**Primary mapping (vphone `vm/` KC + full corpus):** [VPHONE_FIRMWARE_26_4_COVERAGE.md](VPHONE_FIRMWARE_26_4_COVERAGE.md).

Stock-iPhone DSC / restore KC inventory (non–vphone KC): [FULL_COMPONENT_MAP.md](FULL_COMPONENT_MAP.md).

## Bulletin component mapping

Only bulletin sections whose **Apple component title** lines up with a **single vphone-scoped kext bundle** that has a `KEXTS/*.md` in this folder are listed here (plus `com.apple.kernel` for all **Kernel** CVEs). Other CVEs (WebKit, libxpc, Security/Keychain, **WebKit Sandboxing**, etc.) are either speculative under the next table or not mapped to one bundle in this corpus.


| Apple component  | CVE IDs        | Impact (Apple)                                                                     | Fix (Apple description)                                               | Vphone bundle                | Diff                                        |
| ---------------- | -------------- | ---------------------------------------------------------------------------------- | --------------------------------------------------------------------- | ---------------------------- | ------------------------------------------- |
| Kernel           | CVE-2026-28868 | An app may be able to disclose kernel memory                                       | A logging issue was addressed with improved data redaction.           | `com.apple.kernel`           | [diff](KEXTS/com.apple.kernel.md)           |
| Kernel           | CVE-2026-28867 | An app may be able to leak sensitive kernel state                                  | This issue was addressed with improved authentication.                | `com.apple.kernel`           | [diff](KEXTS/com.apple.kernel.md)           |
| Kernel           | CVE-2026-20698 | An app may be able to cause unexpected system termination or corrupt kernel memory | The issue was addressed with improved memory handling.                | `com.apple.kernel`           | [diff](KEXTS/com.apple.kernel.md)           |
| Kernel           | CVE-2026-20687 | An app may be able to cause unexpected system termination or write kernel memory   | A use after free issue was addressed with improved memory management. | `com.apple.kernel`           | [diff](KEXTS/com.apple.kernel.md)           |
| Sandbox Profiles | CVE-2026-28863 | An app may be able to fingerprint the user                                         | A permissions issue was addressed with additional restrictions.       | `com.apple.security.sandbox` | [diff](KEXTS/com.apple.security.sandbox.md) |


## Related vphone bundles with a macOS 26.3.1→26.4 diff (Apple wording is userspace or unspecified)


| Notes                                                                                                                                                                       | Candidate vphone bundles (present in scope + diff present) | Diff                                                       |
| --------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------- | ---------------------------------------------------------- |
| Apple **Security** (Keychain) lists improved permissions checking—often touches Keychain stack; these kernel extensions are plausible attachment points on embedded builds. | `com.apple.driver.AppleMobileFileIntegrity`                | [diff](KEXTS/com.apple.driver.AppleMobileFileIntegrity.md) |
| »                                                                                                                                                                           | `com.apple.driver.AppleSEPKeyStore`                        | [diff](KEXTS/com.apple.driver.AppleSEPKeyStore.md)         |
| »                                                                                                                                                                           | `com.apple.driver.AppleSEPManager`                         | [diff](KEXTS/com.apple.driver.AppleSEPManager.md)          |
| »                                                                                                                                                                           | `com.apple.kec.corecrypto`                                 | [diff](KEXTS/com.apple.kec.corecrypto.md)                  |
| »                                                                                                                                                                           | `com.apple.security.AppleImage4`                           | [diff](KEXTS/com.apple.security.AppleImage4.md)            |
| Apple **Audio** CVEs reference web/content or memory handling; audio-related kexts below also changed in this macOS diff.                                                   | `com.apple.driver.AppleEmbeddedAudioLibs`                  | [diff](KEXTS/com.apple.driver.AppleEmbeddedAudioLibs.md)   |
| »                                                                                                                                                                           | `com.apple.driver.ExclavesAudioKext`                       | [diff](KEXTS/com.apple.driver.ExclavesAudioKext.md)        |
| »                                                                                                                                                                           | `com.apple.iokit.AppleARMIISAudio`                         | [diff](KEXTS/com.apple.iokit.AppleARMIISAudio.md)          |


## All vphone-scope bundles with `KEXTS/*.md` in this folder

- `[com.apple.AUC](KEXTS/com.apple.AUC.md)`
- `[com.apple.AppleFSCompression.AppleFSCompressionTypeZlib](KEXTS/com.apple.AppleFSCompression.AppleFSCompressionTypeZlib.md)`
- `[com.apple.IOTextEncryptionFamily](KEXTS/com.apple.IOTextEncryptionFamily.md)`
- `[com.apple.driver.AppleA7IOP](KEXTS/com.apple.driver.AppleA7IOP.md)`
- `[com.apple.driver.AppleARMPMU](KEXTS/com.apple.driver.AppleARMPMU.md)`
- `[com.apple.driver.AppleARMPlatform](KEXTS/com.apple.driver.AppleARMPlatform.md)`
- `[com.apple.driver.AppleARMWatchdogTimer](KEXTS/com.apple.driver.AppleARMWatchdogTimer.md)`
- `[com.apple.driver.AppleActuatorDriver](KEXTS/com.apple.driver.AppleActuatorDriver.md)`
- `[com.apple.driver.AppleAudioClockLibs](KEXTS/com.apple.driver.AppleAudioClockLibs.md)`
- `[com.apple.driver.AppleBSDKextStarter](KEXTS/com.apple.driver.AppleBSDKextStarter.md)`
- `[com.apple.driver.AppleCallbackPowerSource](KEXTS/com.apple.driver.AppleCallbackPowerSource.md)`
- `[com.apple.driver.AppleDiagnosticDataAccessReadOnly](KEXTS/com.apple.driver.AppleDiagnosticDataAccessReadOnly.md)`
- `[com.apple.driver.AppleDiskImages2](KEXTS/com.apple.driver.AppleDiskImages2.md)`
- `[com.apple.driver.AppleEffaceableStorage](KEXTS/com.apple.driver.AppleEffaceableStorage.md)`
- `[com.apple.driver.AppleEmbeddedAudioLibs](KEXTS/com.apple.driver.AppleEmbeddedAudioLibs.md)`
- `[com.apple.driver.AppleEmbeddedLightSensor](KEXTS/com.apple.driver.AppleEmbeddedLightSensor.md)`
- `[com.apple.driver.AppleEmbeddedPCIE](KEXTS/com.apple.driver.AppleEmbeddedPCIE.md)`
- `[com.apple.driver.AppleEmbeddedTempSensor](KEXTS/com.apple.driver.AppleEmbeddedTempSensor.md)`
- `[com.apple.driver.AppleEmbeddedUSBHost](KEXTS/com.apple.driver.AppleEmbeddedUSBHost.md)`
- `[com.apple.driver.AppleFirmwareKit](KEXTS/com.apple.driver.AppleFirmwareKit.md)`
- `[com.apple.driver.AppleFirmwareUpdateKext](KEXTS/com.apple.driver.AppleFirmwareUpdateKext.md)`
- `[com.apple.driver.AppleGameControllerPersonality](KEXTS/com.apple.driver.AppleGameControllerPersonality.md)`
- `[com.apple.driver.AppleHIDKeyboard](KEXTS/com.apple.driver.AppleHIDKeyboard.md)`
- `[com.apple.driver.AppleIISController](KEXTS/com.apple.driver.AppleIISController.md)`
- `[com.apple.driver.AppleInputDeviceSupport](KEXTS/com.apple.driver.AppleInputDeviceSupport.md)`
- `[com.apple.driver.AppleLockdownMode](KEXTS/com.apple.driver.AppleLockdownMode.md)`
- `[com.apple.driver.AppleM2ScalerCSCDriver](KEXTS/com.apple.driver.AppleM2ScalerCSCDriver.md)`
- `[com.apple.driver.AppleM68Buttons](KEXTS/com.apple.driver.AppleM68Buttons.md)`
- `[com.apple.driver.AppleMobileApNonce](KEXTS/com.apple.driver.AppleMobileApNonce.md)`
- `[com.apple.driver.AppleMobileFileIntegrity](KEXTS/com.apple.driver.AppleMobileFileIntegrity.md)`
- `[com.apple.driver.AppleMultitouchDriver](KEXTS/com.apple.driver.AppleMultitouchDriver.md)`
- `[com.apple.driver.AppleOnboardSerial](KEXTS/com.apple.driver.AppleOnboardSerial.md)`
- `[com.apple.driver.ApplePIODMA](KEXTS/com.apple.driver.ApplePIODMA.md)`
- `[com.apple.driver.ApplePMGR](KEXTS/com.apple.driver.ApplePMGR.md)`
- `[com.apple.driver.AppleS8000AES](KEXTS/com.apple.driver.AppleS8000AES.md)`
- `[com.apple.driver.AppleSEPKeyStore](KEXTS/com.apple.driver.AppleSEPKeyStore.md)`
- `[com.apple.driver.AppleSEPManager](KEXTS/com.apple.driver.AppleSEPManager.md)`
- `[com.apple.driver.AppleSMC](KEXTS/com.apple.driver.AppleSMC.md)`
- `[com.apple.driver.AppleSPU](KEXTS/com.apple.driver.AppleSPU.md)`
- `[com.apple.driver.AppleSamsungSerial](KEXTS/com.apple.driver.AppleSamsungSerial.md)`
- `[com.apple.driver.AppleSerialShim](KEXTS/com.apple.driver.AppleSerialShim.md)`
- `[com.apple.driver.AppleTopCaseHIDEventDriver](KEXTS/com.apple.driver.AppleTopCaseHIDEventDriver.md)`
- `[com.apple.driver.AppleTypeCPhy](KEXTS/com.apple.driver.AppleTypeCPhy.md)`
- `[com.apple.driver.AppleUSBCardReader](KEXTS/com.apple.driver.AppleUSBCardReader.md)`
- `[com.apple.driver.AppleUSBDeviceMux](KEXTS/com.apple.driver.AppleUSBDeviceMux.md)`
- `[com.apple.driver.AppleUSBDeviceNCM](KEXTS/com.apple.driver.AppleUSBDeviceNCM.md)`
- `[com.apple.driver.AppleUSBHostMergeProperties](KEXTS/com.apple.driver.AppleUSBHostMergeProperties.md)`
- `[com.apple.driver.AppleUSBMassStorageInterfaceNub](KEXTS/com.apple.driver.AppleUSBMassStorageInterfaceNub.md)`
- `[com.apple.driver.DiskImages](KEXTS/com.apple.driver.DiskImages.md)`
- `[com.apple.driver.DiskImages.FileBackingStore](KEXTS/com.apple.driver.DiskImages.FileBackingStore.md)`
- `[com.apple.driver.DiskImages.KernelBacked](KEXTS/com.apple.driver.DiskImages.KernelBacked.md)`
- `[com.apple.driver.DiskImages.RAMBackingStore](KEXTS/com.apple.driver.DiskImages.RAMBackingStore.md)`
- `[com.apple.driver.DiskImages.ReadWriteDiskImage](KEXTS/com.apple.driver.DiskImages.ReadWriteDiskImage.md)`
- `[com.apple.driver.DiskImages.UDIFDiskImage](KEXTS/com.apple.driver.DiskImages.UDIFDiskImage.md)`
- `[com.apple.driver.ExclavesAudioKext](KEXTS/com.apple.driver.ExclavesAudioKext.md)`
- `[com.apple.driver.FairPlayIOKit](KEXTS/com.apple.driver.FairPlayIOKit.md)`
- `[com.apple.driver.IISAudioIsolatedStreamECProxy](KEXTS/com.apple.driver.IISAudioIsolatedStreamECProxy.md)`
- `[com.apple.driver.IODARTFamily](KEXTS/com.apple.driver.IODARTFamily.md)`
- `[com.apple.driver.IOSlaveProcessor](KEXTS/com.apple.driver.IOSlaveProcessor.md)`
- `[com.apple.driver.RTBuddy](KEXTS/com.apple.driver.RTBuddy.md)`
- `[com.apple.driver.driverkit.serial](KEXTS/com.apple.driver.driverkit.serial.md)`
- `[com.apple.driver.usb.AppleEmbeddedUSBXHCIPCI](KEXTS/com.apple.driver.usb.AppleEmbeddedUSBXHCIPCI.md)`
- `[com.apple.driver.usb.AppleSynopsysUSBXHCI](KEXTS/com.apple.driver.usb.AppleSynopsysUSBXHCI.md)`
- `[com.apple.driver.usb.AppleUSBCommon](KEXTS/com.apple.driver.usb.AppleUSBCommon.md)`
- `[com.apple.driver.usb.AppleUSBHostCompositeDevice](KEXTS/com.apple.driver.usb.AppleUSBHostCompositeDevice.md)`
- `[com.apple.driver.usb.AppleUSBHostDeviceSupport](KEXTS/com.apple.driver.usb.AppleUSBHostDeviceSupport.md)`
- `[com.apple.driver.usb.AppleUSBHostPacketFilter](KEXTS/com.apple.driver.usb.AppleUSBHostPacketFilter.md)`
- `[com.apple.driver.usb.AppleUSBHostiOSDevice](KEXTS/com.apple.driver.usb.AppleUSBHostiOSDevice.md)`
- `[com.apple.driver.usb.AppleUSBHub](KEXTS/com.apple.driver.usb.AppleUSBHub.md)`
- `[com.apple.driver.usb.AppleUSBXHCI](KEXTS/com.apple.driver.usb.AppleUSBXHCI.md)`
- `[com.apple.driver.usb.AppleUSBXHCIPCI](KEXTS/com.apple.driver.usb.AppleUSBXHCIPCI.md)`
- `[com.apple.driver.usb.cdc](KEXTS/com.apple.driver.usb.cdc.md)`
- `[com.apple.driver.usb.cdc.acm](KEXTS/com.apple.driver.usb.cdc.acm.md)`
- `[com.apple.driver.usb.cdc.ecm](KEXTS/com.apple.driver.usb.cdc.ecm.md)`
- `[com.apple.driver.usb.cdc.ncm](KEXTS/com.apple.driver.usb.cdc.ncm.md)`
- `[com.apple.driver.usb.ethernet.asix](KEXTS/com.apple.driver.usb.ethernet.asix.md)`
- `[com.apple.driver.usb.networking](KEXTS/com.apple.driver.usb.networking.md)`
- `[com.apple.driver.usb.serial](KEXTS/com.apple.driver.usb.serial.md)`
- `[com.apple.filesystems.apfs](KEXTS/com.apple.filesystems.apfs.md)`
- `[com.apple.filesystems.hfs.kext](KEXTS/com.apple.filesystems.hfs.kext.md)`
- `[com.apple.filesystems.lifs](KEXTS/com.apple.filesystems.lifs.md)`
- `[com.apple.filesystems.tmpfs](KEXTS/com.apple.filesystems.tmpfs.md)`
- `[com.apple.iokit.AppleARMIISAudio](KEXTS/com.apple.iokit.AppleARMIISAudio.md)`
- `[com.apple.iokit.CoreAnalyticsFamily](KEXTS/com.apple.iokit.CoreAnalyticsFamily.md)`
- `[com.apple.iokit.EndpointSecurity](KEXTS/com.apple.iokit.EndpointSecurity.md)`
- `[com.apple.iokit.IOAVFamily](KEXTS/com.apple.iokit.IOAVFamily.md)`
- `[com.apple.iokit.IOAccessoryManager](KEXTS/com.apple.iokit.IOAccessoryManager.md)`
- `[com.apple.iokit.IOAccessoryPortUSB](KEXTS/com.apple.iokit.IOAccessoryPortUSB.md)`
- `[com.apple.iokit.IOAudio2Family](KEXTS/com.apple.iokit.IOAudio2Family.md)`
- `[com.apple.iokit.IOCECFamily](KEXTS/com.apple.iokit.IOCECFamily.md)`
- `[com.apple.iokit.IOCryptoAcceleratorFamily](KEXTS/com.apple.iokit.IOCryptoAcceleratorFamily.md)`
- `[com.apple.iokit.IOGPUFamily](KEXTS/com.apple.iokit.IOGPUFamily.md)`
- `[com.apple.iokit.IOGameControllerFamily](KEXTS/com.apple.iokit.IOGameControllerFamily.md)`
- `[com.apple.iokit.IOHDCPFamily](KEXTS/com.apple.iokit.IOHDCPFamily.md)`
- `[com.apple.iokit.IOHIDFamily](KEXTS/com.apple.iokit.IOHIDFamily.md)`
- `[com.apple.iokit.IOMobileGraphicsFamily](KEXTS/com.apple.iokit.IOMobileGraphicsFamily.md)`
- `[com.apple.iokit.IONetworkingFamily](KEXTS/com.apple.iokit.IONetworkingFamily.md)`
- `[com.apple.iokit.IOPCIFamily](KEXTS/com.apple.iokit.IOPCIFamily.md)`
- `[com.apple.iokit.IOReportFamily](KEXTS/com.apple.iokit.IOReportFamily.md)`
- `[com.apple.iokit.IOSCSIArchitectureModelFamily](KEXTS/com.apple.iokit.IOSCSIArchitectureModelFamily.md)`
- `[com.apple.iokit.IOSCSIBlockCommandsDevice](KEXTS/com.apple.iokit.IOSCSIBlockCommandsDevice.md)`
- `[com.apple.iokit.IOSerialFamily](KEXTS/com.apple.iokit.IOSerialFamily.md)`
- `[com.apple.iokit.IOSkywalkFamily](KEXTS/com.apple.iokit.IOSkywalkFamily.md)`
- `[com.apple.iokit.IOSlowAdaptiveClockingFamily](KEXTS/com.apple.iokit.IOSlowAdaptiveClockingFamily.md)`
- `[com.apple.iokit.IOStorageFamily](KEXTS/com.apple.iokit.IOStorageFamily.md)`
- `[com.apple.iokit.IOStreamFamily](KEXTS/com.apple.iokit.IOStreamFamily.md)`
- `[com.apple.iokit.IOSurface](KEXTS/com.apple.iokit.IOSurface.md)`
- `[com.apple.iokit.IOTimeSyncFamily](KEXTS/com.apple.iokit.IOTimeSyncFamily.md)`
- `[com.apple.iokit.IOUSBDeviceFamily](KEXTS/com.apple.iokit.IOUSBDeviceFamily.md)`
- `[com.apple.iokit.IOUSBHostFamily](KEXTS/com.apple.iokit.IOUSBHostFamily.md)`
- `[com.apple.iokit.IOUSBMassStorageDriver](KEXTS/com.apple.iokit.IOUSBMassStorageDriver.md)`
- `[com.apple.iokit.IOUserEthernet](KEXTS/com.apple.iokit.IOUserEthernet.md)`
- `[com.apple.kec.Compression](KEXTS/com.apple.kec.Compression.md)`
- `[com.apple.kec.Libm](KEXTS/com.apple.kec.Libm.md)`
- `[com.apple.kec.corecrypto](KEXTS/com.apple.kec.corecrypto.md)`
- `[com.apple.kec.pthread](KEXTS/com.apple.kec.pthread.md)`
- `[com.apple.kext.AppleMatch](KEXTS/com.apple.kext.AppleMatch.md)`
- `[com.apple.kext.CoreTrust](KEXTS/com.apple.kext.CoreTrust.md)`
- `[com.apple.nke.l2tp](KEXTS/com.apple.nke.l2tp.md)`
- `[com.apple.nke.ppp](KEXTS/com.apple.nke.ppp.md)`
- `[com.apple.plugin.IOgPTPPlugin](KEXTS/com.apple.plugin.IOgPTPPlugin.md)`
- `[com.apple.security.AppleImage4](KEXTS/com.apple.security.AppleImage4.md)`
- `[com.apple.security.sandbox](KEXTS/com.apple.security.sandbox.md)`

**Count:** 123 bundles with diffs.

## Vphone-scope bundles without a standalone diff file here

- `com.apple.driver.AppleARMGIC`
- `com.apple.driver.AppleBSDKextStarterTMPFS`
- `com.apple.driver.AppleBSDKextStarterVPN`
- `com.apple.driver.AppleEmbeddedUSB`
- `com.apple.driver.AppleHIDKeyboardEmbedded`
- `com.apple.driver.AppleM2ScalerParavirtDriver`
- `com.apple.driver.AppleMultitouchSPI`
- `com.apple.driver.AppleNANDConfigAccess`
- `com.apple.driver.ApplePVPanic`
- `com.apple.driver.AppleParavirtGPUIOGPUFamily`
- `com.apple.driver.AppleSEPCredentialManager`
- `com.apple.driver.AppleStorageDrivers`
- `com.apple.driver.AppleTopCaseDriverV2`
- `com.apple.driver.AppleUSBEthernetHost`
- `com.apple.driver.AppleVPIOP`
- `com.apple.driver.AppleVideoToolboxParavirtualization`
- `com.apple.driver.AppleVirtIO`
- `com.apple.driver.AppleVirtualPlatform`
- `com.apple.driver.AvpFairPlayDriver`
- `com.apple.driver.SCSIDeviceSpecifics`
- `com.apple.driver.USBStorageDeviceSpecifics`
- `com.apple.driver.mDNSOffloadUserClient-Embedded`
- `com.apple.driver.usb.AppleUSBHostPlatformProperties`
- `com.apple.iokit.AppleParavirtIOSurface`
- `com.apple.iokit.AppleVirtIONeuralEngineDevice`
- `com.apple.iokit.AppleVirtIOStorage`
- `com.apple.iokit.IOHIDEventDriver`
- `com.apple.iokit.IOHIDEventDriverSafeBoot`
- `com.apple.iokit.IONetworkFamily`
- `com.apple.iokit.IOPortFamily`
- `com.apple.kpi.bsd`
- `com.apple.kpi.dsep`
- `com.apple.kpi.iokit`
- `com.apple.kpi.libkern`
- `com.apple.kpi.mach`
- `com.apple.kpi.private`
- `com.apple.kpi.unsupported`
- `com.apple.security.AKSAnalytics`

**Count:** 38