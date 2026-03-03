import AppKit
import Foundation

// MARK: - IPA Installer

/// Host-side IPA installer. Re-signs with bundled ldid + signcert.p12,
/// then installs via ideviceinstaller over USB/usbmuxd.
@MainActor
class VPhoneIPAInstaller {
    private let macosDir: URL
    private let resourcesDir: URL

    private var ldidURL: URL { macosDir.appendingPathComponent("ldid") }
    private var ideviceInstallerURL: URL { macosDir.appendingPathComponent("ideviceinstaller") }
    private var ideviceIdURL: URL { macosDir.appendingPathComponent("idevice_id") }
    private var signcertURL: URL { resourcesDir.appendingPathComponent("signcert.p12") }

    init?() {
        guard let execURL = Bundle.main.executableURL else { return nil }
        macosDir = execURL.deletingLastPathComponent()
        resourcesDir = macosDir
            .deletingLastPathComponent()
            .appendingPathComponent("Resources")
    }

    // MARK: - Public API

    /// Install an IPA. If `resign` is true, re-sign all Mach-O binaries
    /// preserving their original entitlements before installing.
    func install(ipaURL: URL, resign: Bool) async throws {
        let udid = try await getUDID()
        print("[ipa] device UDID: \(udid)")

        var installURL = ipaURL
        var tempDir: URL?

        if resign {
            let dir = FileManager.default.temporaryDirectory
                .appendingPathComponent("vphone-cli-resign-\(UUID().uuidString)")
            tempDir = dir
            installURL = try await resignIPA(ipaURL: ipaURL, tempDir: dir)
        }

        defer {
            if let tempDir {
                try? FileManager.default.removeItem(at: tempDir)
            }
        }

        print("[ipa] installing \(installURL.lastPathComponent) to \(udid)...")
        let result = try await run(
            ideviceInstallerURL,
            arguments: ["-u", udid, "install", installURL.path]
        )
        guard result.status == 0 else {
            let msg = result.stderr.isEmpty ? result.stdout : result.stderr
            throw IPAError.installFailed(msg.trimmingCharacters(in: .whitespacesAndNewlines))
        }
        print("[ipa] installed successfully")
    }

    // MARK: - UDID Discovery

    private func getUDID() async throws -> String {
        let result = try await run(ideviceIdURL, arguments: ["-l"])
        guard result.status == 0 else {
            throw IPAError.noDevice
        }
        let udids = result.stdout
            .components(separatedBy: .newlines)
            .map { $0.trimmingCharacters(in: .whitespaces) }
            .filter { !$0.isEmpty }
        guard let first = udids.first else {
            throw IPAError.noDevice
        }
        return first
    }

    // MARK: - Re-sign

    private func resignIPA(ipaURL: URL, tempDir: URL) async throws -> URL {
        let fm = FileManager.default
        try fm.createDirectory(at: tempDir, withIntermediateDirectories: true)

        // Unzip
        print("[ipa] extracting \(ipaURL.lastPathComponent)...")
        let unzip = try await run(
            URL(fileURLWithPath: "/usr/bin/unzip"),
            arguments: ["-o", ipaURL.path, "-d", tempDir.path]
        )
        guard unzip.status == 0 else {
            throw IPAError.extractFailed(unzip.stderr)
        }

        // Remove macOS resource fork files that break iOS installd
        _ = try? await run(
            URL(fileURLWithPath: "/usr/bin/find"),
            arguments: [tempDir.path, "-name", "._*", "-delete"]
        )
        _ = try? await run(
            URL(fileURLWithPath: "/usr/bin/find"),
            arguments: [tempDir.path, "-name", ".DS_Store", "-delete"]
        )

        // Find Payload/*.app
        let payloadDir = tempDir.appendingPathComponent("Payload")
        guard fm.fileExists(atPath: payloadDir.path) else {
            throw IPAError.invalidIPA("no Payload directory")
        }
        let contents = try fm.contentsOfDirectory(atPath: payloadDir.path)
        guard let appName = contents.first(where: { $0.hasSuffix(".app") }) else {
            throw IPAError.invalidIPA("no .app bundle in Payload")
        }
        let appDir = payloadDir.appendingPathComponent(appName)

        // Walk and re-sign all Mach-O files
        let machoFiles = findMachOFiles(in: appDir)
        print("[ipa] re-signing \(machoFiles.count) Mach-O binaries...")

        let ldid = ldidURL.path
        let cert = signcertURL.path

        for file in machoFiles {
            // Extract existing entitlements
            let entsResult = try await run(
                ldidURL,
                arguments: ["-e", file.path]
            )
            let entsXML = entsResult.stdout.trimmingCharacters(in: .whitespacesAndNewlines)

            // Build ldid arguments
            var args: [String]
            if !entsXML.isEmpty, entsXML.hasPrefix("<?xml") || entsXML.hasPrefix("<!DOCTYPE") {
                // Write entitlements to temp file
                let entsFile = tempDir.appendingPathComponent("ents-\(UUID().uuidString).plist")
                try entsXML.write(to: entsFile, atomically: true, encoding: .utf8)
                args = ["-S\(entsFile.path)", "-M", "-K\(cert)", file.path]
            } else {
                args = ["-S", "-M", "-K\(cert)", file.path]
            }

            let sign = try await run(ldidURL, arguments: args)
            if sign.status != 0 {
                print("[ipa] warning: failed to sign \(file.lastPathComponent): \(sign.stderr)")
            } else {
                print("[ipa] signed \(file.lastPathComponent)")
            }
        }

        // Re-zip (use zip from the temp dir so Payload/ is at the root)
        let outputIPA = tempDir.appendingPathComponent("resigned.ipa")
        print("[ipa] re-packaging...")
        let zip = try await run(
            URL(fileURLWithPath: "/usr/bin/zip"),
            arguments: ["-r", "-y", outputIPA.path, "Payload"],
            currentDirectory: tempDir
        )
        guard zip.status == 0 else {
            throw IPAError.repackFailed(zip.stderr)
        }

        return outputIPA
    }

    // MARK: - Mach-O Detection

    /// Recursively find all Mach-O files in a directory.
    private func findMachOFiles(in directory: URL) -> [URL] {
        let fm = FileManager.default
        guard let enumerator = fm.enumerator(
            at: directory,
            includingPropertiesForKeys: [.isRegularFileKey],
            options: [.skipsHiddenFiles]
        ) else { return [] }

        var results: [URL] = []
        for case let url as URL in enumerator {
            guard let values = try? url.resourceValues(forKeys: [.isRegularFileKey]),
                  values.isRegularFile == true,
                  Self.isMachO(at: url)
            else { continue }
            results.append(url)
        }
        return results
    }

    private static func isMachO(at url: URL) -> Bool {
        guard let fh = try? FileHandle(forReadingFrom: url) else { return false }
        defer { try? fh.close() }
        guard let data = try? fh.read(upToCount: 4), data.count == 4 else { return false }
        let magic = data.withUnsafeBytes { $0.load(as: UInt32.self) }
        return magic == 0xFEEDFACF  // MH_MAGIC_64
            || magic == 0xCFFAEDFE  // MH_CIGAM_64
            || magic == 0xFEEDFACE  // MH_MAGIC
            || magic == 0xCEFAEDFE  // MH_CIGAM
            || magic == 0xCAFEBABE  // FAT_MAGIC
            || magic == 0xBEBAFECA  // FAT_CIGAM
    }

    // MARK: - Process Runner

    private struct ProcessResult: Sendable {
        let stdout: String
        let stderr: String
        let status: Int32
    }

    /// Run an external process and return its output.
    private func run(
        _ executable: URL,
        arguments: [String],
        currentDirectory: URL? = nil
    ) async throws -> ProcessResult {
        let execPath = executable.path
        let args = arguments
        let dirPath = currentDirectory?.path

        return try await Task.detached {
            let process = Process()
            process.executableURL = URL(fileURLWithPath: execPath)
            process.arguments = args
            if let dirPath {
                process.currentDirectoryURL = URL(fileURLWithPath: dirPath)
            }

            let stdoutPipe = Pipe()
            let stderrPipe = Pipe()
            process.standardOutput = stdoutPipe
            process.standardError = stderrPipe

            try process.run()
            process.waitUntilExit()

            let outData = stdoutPipe.fileHandleForReading.readDataToEndOfFile()
            let errData = stderrPipe.fileHandleForReading.readDataToEndOfFile()

            return ProcessResult(
                stdout: String(data: outData, encoding: .utf8) ?? "",
                stderr: String(data: errData, encoding: .utf8) ?? "",
                status: process.terminationStatus
            )
        }.value
    }

    // MARK: - Errors

    enum IPAError: Error, CustomStringConvertible {
        case noDevice
        case extractFailed(String)
        case invalidIPA(String)
        case repackFailed(String)
        case installFailed(String)

        var description: String {
            switch self {
            case .noDevice: "no device found (is the VM running?)"
            case let .extractFailed(msg): "failed to extract IPA: \(msg)"
            case let .invalidIPA(msg): "invalid IPA: \(msg)"
            case let .repackFailed(msg): "failed to repackage IPA: \(msg)"
            case let .installFailed(msg): "install failed: \(msg)"
            }
        }
    }
}
