#!/bin/bash
# setup_env.sh — Source this file to configure the build/runtime environment.
# Usage: source setup_env.sh

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
	echo "error: this script must be sourced, not executed."
	echo "usage: source setup_env.sh"
	exit 1
fi

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOCAL_PREFIX="${REPO_ROOT}/.local"
VENV_DIR="${REPO_ROOT}/.venv"

# --- Python virtual environment ---
if [ ! -d "${VENV_DIR}" ]; then
	echo "venv not found — creating with system python3..."
	python3 -m venv "${VENV_DIR}"
	source "${VENV_DIR}/bin/activate"
	pip install --quiet --upgrade pip
	pip install --quiet -r "${REPO_ROOT}/requirements.txt"
else
	source "${VENV_DIR}/bin/activate"
fi

# --- PATH ---
export PATH="${REPO_ROOT}/bin:${LOCAL_PREFIX}/bin:${PATH}"

# --- pkg-config ---
export PKG_CONFIG_PATH="${LOCAL_PREFIX}/lib/pkgconfig:${PKG_CONFIG_PATH:-}"

# --- dynamic linker ---
export DYLD_LIBRARY_PATH="${LOCAL_PREFIX}/lib:${DYLD_LIBRARY_PATH:-}"

# --- C/C++ include and lib search paths (for setup_bin.sh) ---
export CFLAGS="-I${LOCAL_PREFIX}/include ${CFLAGS:-}"
export CXXFLAGS="-I${LOCAL_PREFIX}/include ${CXXFLAGS:-}"
export LDFLAGS="-L${LOCAL_PREFIX}/lib ${LDFLAGS:-}"

# --- tart VM home (isolate VMs to repo directory) ---
export TART_HOME="${REPO_ROOT}/.tart"

# --- tool paths consumed by patch_fw.py ---
export IMG4TOOL="${REPO_ROOT}/bin/img4tool"
export IMG4="${REPO_ROOT}/bin/img4"
export TRUSTCACHE="${REPO_ROOT}/bin/trustcache"
export PYIMG4="$(command -v pyimg4)"

echo "environment configured (repo: ${REPO_ROOT})"
echo "  bin/        : ${REPO_ROOT}/bin"
echo "  .local/     : ${LOCAL_PREFIX}"
echo "  venv        : ${VENV_DIR} ($(python3 --version))"
echo "  TART_HOME   : ${TART_HOME}"
echo "  IMG4TOOL    : ${IMG4TOOL}"
echo "  IMG4        : ${IMG4}"
echo "  TRUSTCACHE  : ${TRUSTCACHE}"
echo "  PYIMG4      : ${PYIMG4}"
