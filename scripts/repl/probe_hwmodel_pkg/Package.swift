// swift-tools-version:5.10
import PackageDescription
let package = Package(
  name: "ProbeHWModel",
  platforms: [.macOS(.v13)],
  targets: [
    .target(name: "VirtualizationPrivate", dependencies: [], path: "Sources/VirtualizationPrivate"),
    .executableTarget(name: "ProbeHWModel", dependencies: ["VirtualizationPrivate"], path: "Sources/ProbeHWModel"),
  ]
)
