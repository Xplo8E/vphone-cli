#!/bin/bash
# build_tart.sh — Build local super-tart and stage bin/tart.
# Mirrors the manual flow:
#   swift build -c release --disable-sandbox
#   codesign --force --sign - --entitlements Resources/tart-prod.entitlements .build/release/tart

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SUPER_TART_DIR="${REPO_ROOT}/super-tart"
BIN_DIR="${REPO_ROOT}/bin"
ENTITLEMENTS="${SUPER_TART_DIR}/Resources/tart-prod.entitlements"
TART_BIN="${SUPER_TART_DIR}/.build/release/tart"

log() { printf '\033[1;34m==>\033[0m %s\n' "$*"; }
ok()  { printf '\033[1;32m  ✓\033[0m %s\n' "$*"; }
err() { printf '\033[1;31m  ✗\033[0m %s\n' "$*" >&2; }
die() { err "$@"; exit 1; }

[ -d "${SUPER_TART_DIR}" ] || die "missing local super-tart dir: ${SUPER_TART_DIR}"
[ -f "${SUPER_TART_DIR}/Package.swift" ] || die "missing ${SUPER_TART_DIR}/Package.swift"
[ -f "${ENTITLEMENTS}" ] || die "missing entitlements: ${ENTITLEMENTS}"

log "building super-tart in ${SUPER_TART_DIR}..."
pushd "${SUPER_TART_DIR}" >/dev/null
swift build -c release --disable-sandbox
popd >/dev/null

[ -x "${TART_BIN}" ] || die "build output not found: ${TART_BIN}"

log "signing ${TART_BIN}..."
codesign --force --sign - --entitlements "${ENTITLEMENTS}" "${TART_BIN}"
ok "signed ${TART_BIN}"

mkdir -p "${BIN_DIR}"
cp -f "${TART_BIN}" "${BIN_DIR}/tart"
ok "staged ${BIN_DIR}/tart"

if strings "${TART_BIN}" 2>/dev/null | grep "_setCoprocessors" >/dev/null; then
	ok "binary check: vphone support marker present (_setCoprocessors)"
fi

log "done"
