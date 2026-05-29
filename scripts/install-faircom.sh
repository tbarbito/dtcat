#!/usr/bin/env bash
# Assisted installer for FairCom DB Developer Edition (Linux / macOS).
#
# This script does NOT download FairCom for you (their site requires a form).
# It opens the sign-up form, asks where you saved the file, and configures
# environment variables.
#
# Usage:  ./scripts/install-faircom.sh [target-dir]
#         default target-dir: $HOME/faircom

set -euo pipefail

TARGET="${1:-$HOME/faircom}"
FORM_URL="https://www.faircom.com/download-ctreeace"
DOWNLOADS_URL="https://www.faircom.com/products/downloads"

OS=$(uname -s)
case "$OS" in
    Linux)   PLATFORM_HINT="Linux x86_64" ;;
    Darwin)  PLATFORM_HINT="macOS x86_64 (Apple Silicon: works under Rosetta 2)" ;;
    *)       echo "Unsupported OS: $OS"; exit 1 ;;
esac

cat <<EOF
================================================================
  FairCom DB Developer Edition — assisted installer for dtcat
================================================================

This script will help you install FairCom DB locally. It does NOT
redistribute any FairCom binaries — you download them yourself,
under FairCom's own license.

Steps:
  1. Open the sign-up form in your browser
  2. Fill in: name, email, company, country
  3. Open the email FairCom sends and download:
       ${PLATFORM_HINT}
  4. Come back here and tell me where you saved the file

Form URL:      ${FORM_URL}
All downloads: ${DOWNLOADS_URL}

EOF

read -rp "Press [Enter] to open the form in your browser, or [s] to skip: " ans
if [ "${ans,,}" != "s" ]; then
    if command -v xdg-open >/dev/null 2>&1; then xdg-open "$FORM_URL" >/dev/null 2>&1 &
    elif command -v open >/dev/null 2>&1; then open "$FORM_URL" >/dev/null 2>&1 &
    else echo "Could not open browser automatically. Visit: $FORM_URL"
    fi
fi

echo
read -rp "Full path to the downloaded archive (.tar.gz / .dmg): " ARCHIVE
ARCHIVE="${ARCHIVE/#~/$HOME}"

if [ ! -f "$ARCHIVE" ]; then
    echo "ERROR: file not found: $ARCHIVE" >&2
    exit 1
fi

mkdir -p "$TARGET"

case "$ARCHIVE" in
    *.tar.gz|*.tgz)
        echo "Extracting tarball to $TARGET ..."
        tar xzf "$ARCHIVE" -C "$TARGET" --strip-components=1
        ;;
    *.dmg)
        echo "Mounting DMG ..."
        MOUNT=$(hdiutil attach "$ARCHIVE" -nobrowse | tail -1 | awk '{print $3}')
        if [ -z "$MOUNT" ]; then echo "ERROR: failed to mount DMG"; exit 1; fi
        echo "Copying from $MOUNT to $TARGET ..."
        cp -R "$MOUNT"/* "$TARGET/"
        hdiutil detach "$MOUNT" >/dev/null
        ;;
    *)
        echo "ERROR: unsupported archive format. Expected .tar.gz or .dmg" >&2
        exit 1
        ;;
esac

LIB_VAR=$([ "$OS" = "Darwin" ] && echo "DYLD_LIBRARY_PATH" || echo "LD_LIBRARY_PATH")
SHELL_RC=$([ "$OS" = "Darwin" ] && echo "$HOME/.zshrc" || echo "$HOME/.bashrc")

if ! grep -q "FAIRCOM_HOME" "$SHELL_RC" 2>/dev/null; then
    cat >> "$SHELL_RC" << EOF

# Added by dtcat install-faircom.sh
export FAIRCOM_HOME="$TARGET"
export PATH="\$FAIRCOM_HOME/tools:\$PATH"
export ${LIB_VAR}="\$FAIRCOM_HOME/server:\$${LIB_VAR}"
EOF
    echo "Environment variables added to $SHELL_RC"
else
    echo "FAIRCOM_HOME already configured in $SHELL_RC — skipped"
fi

cat <<EOF

================================================================
  Installation complete
================================================================

dtcat uses FairCom's native Python driver — no unixODBC/DSN setup needed.

Next steps:
  1. Reload shell:      source $SHELL_RC
  2. Validate:          dtcat doctor
  3. Start the server:  dtcat server start
  4. Read a file:       dtcat info /path/to/file.dtc

See docs/setup-$([ "$OS" = "Darwin" ] && echo macos || echo linux).md for details.

EOF
