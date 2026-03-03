import AppKit
import UniformTypeIdentifiers

// MARK: - Connect Menu

extension VPhoneMenuController {
    func buildConnectMenu() -> NSMenuItem {
        let item = NSMenuItem()
        let menu = NSMenu(title: "Connect")
        menu.addItem(makeItem("File Browser", action: #selector(openFiles)))
        menu.addItem(makeItem("Install Package (.ipa) [WIP]", action: #selector(installPackage)))
        menu.addItem(makeItem("Install Package with Resign (.ipa) [WIP]", action: #selector(installPackageResign)))
        menu.addItem(makeItem("Upload Binary to Guest...", action: #selector(uploadBinary)))
        menu.addItem(NSMenuItem.separator())
        menu.addItem(makeItem("Developer Mode Status", action: #selector(devModeStatus)))
        menu.addItem(makeItem("Enable Developer Mode", action: #selector(devModeEnable)))
        menu.addItem(NSMenuItem.separator())
        menu.addItem(makeItem("Ping", action: #selector(sendPing)))
        menu.addItem(makeItem("Guest Version", action: #selector(queryGuestVersion)))
        item.submenu = menu
        return item
    }

    @objc func openFiles() {
        onFilesPressed?()
    }

    @objc func devModeStatus() {
        Task {
            do {
                let status = try await control.sendDevModeStatus()
                showAlert(
                    title: "Developer Mode",
                    message: status.enabled ? "Developer Mode is enabled." : "Developer Mode is disabled.",
                    style: .informational
                )
            } catch {
                showAlert(title: "Developer Mode", message: "\(error)", style: .warning)
            }
        }
    }

    @objc func devModeEnable() {
        Task {
            do {
                let result = try await control.sendDevModeEnable()
                showAlert(
                    title: "Developer Mode",
                    message: result.message.isEmpty
                        ? (result.alreadyEnabled ? "Developer Mode already enabled." : "Developer Mode enabled.")
                        : result.message,
                    style: .informational
                )
            } catch {
                showAlert(title: "Developer Mode", message: "\(error)", style: .warning)
            }
        }
    }

    @objc func sendPing() {
        Task {
            do {
                try await control.sendPing()
                showAlert(title: "Ping", message: "pong", style: .informational)
            } catch {
                showAlert(title: "Ping", message: "\(error)", style: .warning)
            }
        }
    }

    @objc func queryGuestVersion() {
        Task {
            do {
                let hash = try await control.sendVersion()
                showAlert(title: "Guest Version", message: "build: \(hash)", style: .informational)
            } catch {
                showAlert(title: "Guest Version", message: "\(error)", style: .warning)
            }
        }
    }

    // MARK: - IPA Install

    @objc func installPackage() {
        pickAndInstall(resign: false)
    }

    @objc func installPackageResign() {
        pickAndInstall(resign: true)
    }

    private func pickAndInstall(resign: Bool) {
        let panel = NSOpenPanel()
        panel.title = "Select IPA"
        panel.allowedContentTypes = [.init(filenameExtension: "ipa")!]
        panel.allowsMultipleSelection = false
        panel.canChooseDirectories = false

        guard panel.runModal() == .OK, let url = panel.url else { return }

        guard let installer = ipaInstaller else {
            showAlert(
                title: "Install Package",
                message: "IPA installer not available (bundled tools missing).",
                style: .warning
            )
            return
        }

        Task {
            do {
                try await installer.install(ipaURL: url, resign: resign)
                showAlert(
                    title: "Install Package",
                    message: "Successfully installed \(url.lastPathComponent).",
                    style: .informational
                )
            } catch {
                showAlert(
                    title: "Install Package",
                    message: "\(error)",
                    style: .warning
                )
            }
        }
    }

    // MARK: - Upload Binary

    @objc func uploadBinary() {
        let panel = NSOpenPanel()
        panel.title = "Select Binary to Upload"
        panel.allowsMultipleSelection = false
        panel.canChooseDirectories = false

        guard panel.runModal() == .OK, let url = panel.url else { return }

        let filename = url.lastPathComponent
        let remotePath = "/usr/bin/\(filename)"

        Task {
            do {
                let data = try Data(contentsOf: url)
                try await control.uploadFile(path: remotePath, data: data, permissions: "755")
                showAlert(
                    title: "Upload Binary",
                    message: "Uploaded \(filename) to \(remotePath) (\(data.count) bytes).",
                    style: .informational
                )
            } catch {
                showAlert(
                    title: "Upload Binary",
                    message: "\(error)",
                    style: .warning
                )
            }
        }
    }

    // MARK: - Alert

    private func showAlert(title: String, message: String, style: NSAlert.Style) {
        let alert = NSAlert()
        alert.messageText = title
        alert.informativeText = message
        alert.alertStyle = style
        if let window = NSApp.keyWindow {
            alert.beginSheetModal(for: window)
        } else {
            alert.runModal()
        }
    }
}
