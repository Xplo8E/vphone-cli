# Build vphone_sb_shim.dylib — no-growth SpringBoard load shim.

NAME    := vphone_sb_shim
DYLIB   := $(NAME).dylib
SRC     := $(NAME).m
SDK     := $(shell xcrun --sdk iphoneos --show-sdk-path 2>/dev/null)
CC      := $(shell xcrun --sdk iphoneos --find clang 2>/dev/null)
TARGET  := arm64e-apple-ios15.0

SPRINGBOARD_FRAMEWORK := /System/Library/PrivateFrameworks/SpringBoard.framework/SpringBoard

CFLAGS  := -isysroot $(SDK) \
           -arch arm64e \
           -target $(TARGET) \
           -fobjc-arc \
           -fmodules \
           -Wall -Wextra \
           -O2

LDFLAGS := -dynamiclib \
           -install_name /v \
           -framework Foundation \
           -framework CoreFoundation \
           -lMobileGestalt \
           -Wl,-headerpad,0x400 \
           -Wl,-not_for_dyld_shared_cache

.PHONY: all clean verify

all: $(DYLIB)

$(DYLIB): $(SRC)
	@if [ -z "$(SDK)" ]; then \
		echo "[-] iPhoneOS SDK not found. Install Xcode + the iOS platform." >&2; \
		exit 1; \
	fi
	$(CC) $(CFLAGS) $(LDFLAGS) -o $@ $<
	../patchers/macho_reexport.py $@ $(SPRINGBOARD_FRAMEWORK)
	ldid -S $@

verify: $(DYLIB)
	@file $(DYLIB)
	@otool -L $(DYLIB)
	@otool -l $(DYLIB) | grep -A3 LC_REEXPORT_DYLIB || true
	@ldid -h $(DYLIB) | grep CDHash

clean:
	rm -f $(DYLIB)
