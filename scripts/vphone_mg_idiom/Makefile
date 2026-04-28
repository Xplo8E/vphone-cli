# Build vphone_mg_idiom.dylib — MobileGestalt idiom interposer for iOS.
#
# Usage (from project root):
#   make -C scripts/vphone_mg_idiom
#
# Produces vphone_mg_idiom.dylib in this directory, cross-compiled for
# iPhoneOS arm64e and ad-hoc signed.
#
# Cross-compilation requires the iPhoneOS SDK to be installed via Xcode.
# If `xcrun --sdk iphoneos --show-sdk-path` fails, install Xcode's iPhoneOS
# platform or run `sudo xcode-select -s /Applications/Xcode.app`.

NAME         := vphone_mg_idiom
DYLIB        := $(NAME).dylib
SRC          := $(NAME).m

SDK          := $(shell xcrun --sdk iphoneos --show-sdk-path 2>/dev/null)
CC           := $(shell xcrun --sdk iphoneos --find clang 2>/dev/null)
TARGET       := arm64e-apple-ios15.0
CFLAGS       := -isysroot $(SDK) \
                -arch arm64e \
                -target $(TARGET) \
                -fobjc-arc \
                -fmodules \
                -Wall -Wextra \
                -O2
LDFLAGS      := -dynamiclib \
                -install_name /usr/lib/$(DYLIB) \
                -framework Foundation \
                -framework CoreFoundation \
                -lMobileGestalt \
                -Wl,-not_for_dyld_shared_cache

.PHONY: all clean verify

all: $(DYLIB)

$(DYLIB): $(SRC)
	@if [ -z "$(SDK)" ]; then \
		echo "[-] iPhoneOS SDK not found. Install Xcode + the iOS platform." >&2; \
		exit 1; \
	fi
	@echo "[*] Compiling $(SRC) for $(TARGET)"
	$(CC) $(CFLAGS) $(LDFLAGS) -o $@ $<
	@echo "[*] Signing $@ (ad-hoc, no entitlements — dylibs cannot carry entitlements on iOS)"
	ldid -S $@
	@echo "[+] $@ built and signed"

verify: $(DYLIB)
	@echo "[*] Mach-O header:"
	@otool -hv $(DYLIB) | head -5
	@echo "[*] __DATA,__interpose section:"
	@otool -s __DATA __interpose $(DYLIB) | head -20 || true
	@echo "[*] linked libraries:"
	@otool -L $(DYLIB)
	@echo "[*] ldid entitlements:"
	@ldid -e $(DYLIB) || true

clean:
	rm -f $(DYLIB)
