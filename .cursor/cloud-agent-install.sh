#!/usr/bin/env bash
# Idempotent Cloud Agent bootstrap for ns-3 (waf + examples, no Python bindings).
set -euo pipefail

export DEBIAN_FRONTEND=noninteractive
export CXXFLAGS_EXTRA="${CXXFLAGS_EXTRA:--Wno-error}"

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

apt_install() {
  sudo apt-get update -qq
  if ! dpkg -s python3.11 >/dev/null 2>&1; then
    sudo apt-get install -y -qq software-properties-common
    sudo add-apt-repository -y ppa:deadsnakes/ppa
    sudo apt-get update -qq
  fi
  sudo apt-get install -y -qq \
    python3.11 \
    g++ \
    python3-dev \
    pkg-config \
    libsqlite3-dev \
    libxml2-dev \
    libc6-dev
}

ensure_python() {
  sudo ln -sf /usr/bin/python3.11 /usr/local/bin/python
  export PATH="/usr/local/bin:${PATH}"
  python --version
}

patch_waf() {
  ./waf --version >/dev/null 2>&1 || true
  python3 "${REPO_ROOT}/.cursor/patch-waf-py312.py"
}

configure_ns3() {
  ./waf configure --enable-examples --disable-python
}

build_ns3() {
  ./waf build -j"$(nproc)"
}

apt_install
ensure_python
patch_waf
configure_ns3
build_ns3
