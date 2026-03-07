#!/bin/bash
# setup_bin.sh — Build OEM tools from submodules and local super-tart, install to bin/.
#
# Prerequisites (macOS):
#   brew install automake autoconf libtool pkg-config \
#                libplist openssl@3 libimobiledevice-glue \
#                libimobiledevice libtatsu libzip curl
#
# Usage:
#   bash setup_bin.sh      # build everything (also sets up venv)
#
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BIN_DIR="${REPO_ROOT}/bin"
LOCAL_PREFIX="${REPO_ROOT}/.local"
OEMS_DIR="${REPO_ROOT}/oems"
SUPER_TART_DIR="${REPO_ROOT}/super-tart"
VENV_DIR="${REPO_ROOT}/.venv"
JOBS="$(sysctl -n hw.ncpu 2>/dev/null || echo 4)"

# ── helpers ──────────────────────────────────────────────────────────────────

log() { printf '\033[1;34m==>\033[0m %s\n' "$*"; }
ok() { printf '\033[1;32m  ✓\033[0m %s\n' "$*"; }
err() { printf '\033[1;31m  ✗\033[0m %s\n' "$*" >&2; }
die() {
	err "$@"
	exit 1
}

ensure_dir() { mkdir -p "$1"; }

# ── preflight ────────────────────────────────────────────────────────────────

check_prerequisites() {
	log "checking prerequisites..."

	local missing=()
	for cmd in git make clang pkg-config automake autoconf libtool swift python3; do
		command -v "$cmd" >/dev/null 2>&1 || missing+=("$cmd")
	done

	if [ ${#missing[@]} -ne 0 ]; then
		die "missing commands: ${missing[*]}"
	fi

	# check brew packages via pkg-config
	local pkgs=(libplist-2.0 openssl libimobiledevice-glue-1.0
		libimobiledevice-1.0 libtatsu-1.0 libzip)
	local missing_pkgs=()
	for pkg in "${pkgs[@]}"; do
		pkg-config --exists "$pkg" 2>/dev/null || missing_pkgs+=("$pkg")
	done

	if [ ${#missing_pkgs[@]} -ne 0 ]; then
		err "missing pkg-config packages: ${missing_pkgs[*]}"
		echo "  install with:"
		echo "    brew install libplist openssl@3 libimobiledevice-glue libimobiledevice libtatsu libzip"
		die "install missing packages and re-run."
	fi

	ok "all prerequisites satisfied"
}

check_submodules() {
	log "checking submodules..."
	# Only init submodules we actually build from oems/ (super-tart is local at repo root).
	local build_modules=(libgeneral img4lib img4tool trustcache
		libirecovery idevicerestore)
	for mod in "${build_modules[@]}"; do
		local mod_path="${OEMS_DIR}/${mod}"
		git -C "${REPO_ROOT}" submodule update --init --recursive -- "oems/${mod}"
		# already cloned — clean build artifacts
		if [ -d "${mod_path}" ]; then
			git -C "${mod_path}" checkout . 2>/dev/null || true
			git -C "${mod_path}" clean -fdx 2>/dev/null || true
		fi
	done
	ok "required oems submodules ready"
}

check_local_super_tart() {
	log "checking local super-tart source..."
	[ -d "${SUPER_TART_DIR}" ] || die "missing local super-tart dir: ${SUPER_TART_DIR}"
	[ -f "${SUPER_TART_DIR}/Package.swift" ] || die "missing ${SUPER_TART_DIR}/Package.swift"
	[ -f "${SUPER_TART_DIR}/Resources/tart-prod.entitlements" ] || die "missing ${SUPER_TART_DIR}/Resources/tart-prod.entitlements"
	ok "local super-tart source ready: ${SUPER_TART_DIR}"
}

# ── python venv ──────────────────────────────────────────────────────────────

setup_venv() {
	log "setting up python venv..."
	if [ -d "${VENV_DIR}" ]; then
		ok "venv already exists at ${VENV_DIR}"
	else
		python3 -m venv "${VENV_DIR}"
		ok "created venv at ${VENV_DIR}"
	fi

	source "${VENV_DIR}/bin/activate"
	pip install --quiet --upgrade pip
	pip install --quiet -r "${REPO_ROOT}/requirements.txt"
	ok "python dependencies installed"
}

# ── prepare build dirs ───────────────────────────────────────────────────────

prepare() {
	log "preparing build directories..."
	ensure_dir "${BIN_DIR}"
	ensure_dir "${LOCAL_PREFIX}/bin"
	ensure_dir "${LOCAL_PREFIX}/lib/pkgconfig"
	ensure_dir "${LOCAL_PREFIX}/include"

	export PKG_CONFIG_PATH="${LOCAL_PREFIX}/lib/pkgconfig:${PKG_CONFIG_PATH:-}"
	export CFLAGS="-I${LOCAL_PREFIX}/include ${CFLAGS:-}"
	export CXXFLAGS="-I${LOCAL_PREFIX}/include ${CXXFLAGS:-}"
	export LDFLAGS="-L${LOCAL_PREFIX}/lib ${LDFLAGS:-}"
	export PATH="${LOCAL_PREFIX}/bin:${PATH}"
}

# ── build functions ──────────────────────────────────────────────────────────
# Build directly in oems/ submodule trees so autotools version detection
# (git rev-list --count HEAD) works correctly. Build artifacts are cleaned
# by check_submodules on subsequent runs.

build_libgeneral() {
	log "building libgeneral..."
	pushd "${OEMS_DIR}/libgeneral" >/dev/null
	./autogen.sh
	./configure --prefix="${LOCAL_PREFIX}"
	make -j"${JOBS}"
	make install
	popd >/dev/null
	ok "libgeneral installed to ${LOCAL_PREFIX}"
}

build_img4tool() {
	log "building img4tool..."
	pushd "${OEMS_DIR}/img4tool" >/dev/null
	mkdir -p m4
	if command -v glibtoolize >/dev/null 2>&1; then
		glibtoolize --copy --force
	elif command -v libtoolize >/dev/null 2>&1; then
		libtoolize --copy --force
	fi
	./autogen.sh
	./configure --prefix="${LOCAL_PREFIX}" \
		--without-libfwkeyfetch \
		--without-openssl
	make -j"${JOBS}"
	make install
	popd >/dev/null
	cp -f "${LOCAL_PREFIX}/bin/img4tool" "${BIN_DIR}/img4tool"
	ok "img4tool -> ${BIN_DIR}/img4tool"
}

build_img4lib() {
	log "building img4 (img4lib)..."
	pushd "${OEMS_DIR}/img4lib" >/dev/null
	make clean 2>/dev/null || true
	# macOS: CommonCrypto for crypto, libcompression for lzfse
	# /usr/lib/libcompression.dylib is in the shared cache on modern macOS,
	# so the Makefile wildcard check fails — override explicitly.
	make CC=clang \
		COMMONCRYPTO=1 \
		CFLAGS="-Wall -W -pedantic -Wno-variadic-macros -Wno-multichar \
                 -Wno-four-char-constants -Wno-unused-parameter -O2 -I. -g \
                 -DiOS10 -DDER_MULTIBYTE_TAGS=1 -DDER_TAG_SIZE=8 \
                 -D__unused=\"__attribute__((unused))\" \
                 -DUSE_COMMONCRYPTO -DUSE_LIBCOMPRESSION" \
		LDLIBS="-lcompression -framework Security -framework CoreFoundation" \
		-j"${JOBS}"
	popd >/dev/null
	cp -f "${OEMS_DIR}/img4lib/img4" "${BIN_DIR}/img4"
	ok "img4 -> ${BIN_DIR}/img4"
}

build_trustcache() {
	log "building trustcache..."
	local ssl_cflags ssl_libs
	ssl_cflags="$(pkg-config --cflags openssl)"
	ssl_libs="$(pkg-config --libs openssl)"

	pushd "${OEMS_DIR}/trustcache" >/dev/null
	make clean 2>/dev/null || true
	make OPENSSL=1 \
		CFLAGS="-DOPENSSL -DVERSION=2.0 ${ssl_cflags}" \
		LIBS="${ssl_libs}" \
		-j"${JOBS}"
	popd >/dev/null
	cp -f "${OEMS_DIR}/trustcache/trustcache" "${BIN_DIR}/trustcache"
	ok "trustcache -> ${BIN_DIR}/trustcache"
}

build_libirecovery() {
	log "building libirecovery (forked)..."
	pushd "${OEMS_DIR}/libirecovery" >/dev/null
	./autogen.sh
	./configure --prefix="${LOCAL_PREFIX}" --with-tools
	make -j"${JOBS}"
	make install
	popd >/dev/null
	cp -f "${LOCAL_PREFIX}/bin/irecovery" "${BIN_DIR}/irecovery"
	ok "irecovery -> ${BIN_DIR}/irecovery"
}

build_idevicerestore() {
	log "building idevicerestore..."
	pushd "${OEMS_DIR}/idevicerestore" >/dev/null
	./autogen.sh
	./configure --prefix="${LOCAL_PREFIX}"
	make -j"${JOBS}"
	make install
	popd >/dev/null
	cp -f "${LOCAL_PREFIX}/bin/idevicerestore" "${BIN_DIR}/idevicerestore"
	ok "idevicerestore -> ${BIN_DIR}/idevicerestore"
}

build_super_tart() {
	log "building super-tart (tart)..."
	local spm_root="${REPO_ROOT}/.swiftpm"
	local spm_home="${REPO_ROOT}/.swift-home"
	mkdir -p "${spm_root}/config" "${spm_root}/security" "${spm_root}/cache" "${spm_root}/xdg-cache" "${spm_home}"
	pushd "${SUPER_TART_DIR}" >/dev/null
	# Use repo-local SwiftPM caches and disable sandbox to avoid macOS sandbox/cache issues.
	SWIFTPM_CONFIG_PATH="${spm_root}/config" \
		SWIFTPM_SECURITY_PATH="${spm_root}/security" \
		SWIFTPM_CACHE_PATH="${spm_root}/cache" \
		XDG_CACHE_HOME="${spm_root}/xdg-cache" \
		HOME="${spm_home}" \
		swift build -c release --disable-sandbox 2>&1 | tail -5
	popd >/dev/null
	cp -f "${SUPER_TART_DIR}/.build/release/tart" "${BIN_DIR}/tart"
	# Sign with vphone prod entitlements
	codesign --sign - \
		--entitlements "${SUPER_TART_DIR}/Resources/tart-prod.entitlements" \
		--force "${BIN_DIR}/tart"
	ok "tart -> ${BIN_DIR}/tart (signed with vphone prod entitlements)"
}

install_homebrew_tools() {
	log "installing homebrew tools to bin/..."
	local tools=(ldid sshpass gtar iproxy)
	for tool in "${tools[@]}"; do
		local src
		src="$(command -v "$tool" 2>/dev/null || true)"
		if [ -z "$src" ]; then
			err "$tool not found — install with: brew install $tool"
			continue
		fi
		cp -f "$src" "${BIN_DIR}/$tool"
		chmod +x "${BIN_DIR}/$tool"
		ok "$tool -> ${BIN_DIR}/$tool"
	done
}

# ── main ─────────────────────────────────────────────────────────────────────

main() {
	log "setup_bin.sh — building tools from oems/ + local super-tart/"
	echo ""

	check_prerequisites
	check_submodules
	check_local_super_tart
	setup_venv
	prepare

	# build order matters: dependencies first
	build_libgeneral       # library (no deps)
	build_img4lib          # standalone (CommonCrypto)
	build_img4tool         # depends on libgeneral
	build_trustcache       # standalone (OpenSSL)
	build_libirecovery     # depends on libimobiledevice-glue
	build_idevicerestore   # depends on libirecovery + many libs
	build_super_tart       # Swift Package Manager
	install_homebrew_tools # ldid, sshpass, gtar, iproxy

	echo ""
	log "all tools built successfully:"
	ls -lh "${BIN_DIR}"/img4 "${BIN_DIR}"/img4tool "${BIN_DIR}"/trustcache \
		"${BIN_DIR}"/irecovery "${BIN_DIR}"/idevicerestore "${BIN_DIR}"/tart \
		"${BIN_DIR}"/ldid "${BIN_DIR}"/sshpass "${BIN_DIR}"/gtar \
		"${BIN_DIR}"/iproxy \
		2>/dev/null || true
	echo ""
	log "run 'source setup_env.sh' to activate the environment"
}

main "$@"
