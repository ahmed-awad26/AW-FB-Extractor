#!/data/data/com.termux/files/usr/bin/bash
# ============================================================
#   AW FB Extractor — Termux Installer
#   github.com/ahmed-awad26
# ============================================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
BOLD='\033[1m'
NC='\033[0m'

REPO_URL="https://github.com/ahmed-awad26/AW-FB-Extractor"
INSTALL_DIR="$HOME/AW-FB-Extractor"

banner() {
  echo -e "${CYAN}"
  echo "  ╔══════════════════════════════════════════╗"
  echo "  ║   AW FB Extractor — Installer v1.0       ║"
  echo "  ║   github.com/ahmed-awad26                ║"
  echo "  ╚══════════════════════════════════════════╝"
  echo -e "${NC}"
}

step() {
  echo -e "${CYAN}[→]${NC} ${BOLD}$1${NC}"
}

ok() {
  echo -e "${GREEN}[✔]${NC} $1"
}

warn() {
  echo -e "${YELLOW}[!]${NC} $1"
}

err() {
  echo -e "${RED}[✘]${NC} $1"
  exit 1
}

banner

# ── Update packages ──
step "Updating Termux packages..."
pkg update -y -q 2>/dev/null || warn "pkg update had warnings (continuing)"
pkg upgrade -y -q 2>/dev/null || warn "pkg upgrade had warnings (continuing)"
ok "Packages updated"

# ── Install system deps ──
step "Installing system dependencies..."
pkg install -y python python-pip git clang libffi openssl 2>/dev/null
ok "System deps installed"

# ── Clone or update repo ──
if [ -d "$INSTALL_DIR/.git" ]; then
  step "Updating existing installation..."
  cd "$INSTALL_DIR"
  git pull --quiet
  ok "Updated to latest version"
else
  step "Cloning AW FB Extractor from GitHub..."
  if git clone --quiet "$REPO_URL" "$INSTALL_DIR" 2>/dev/null; then
    ok "Cloned successfully"
  else
    warn "GitHub clone failed — using local files instead"
    mkdir -p "$INSTALL_DIR"
  fi
fi

cd "$INSTALL_DIR"

# ── Python deps ──
step "Installing Python dependencies..."
pip install --quiet --upgrade pip 2>/dev/null || true
pip install --quiet -r requirements.txt
ok "Python packages installed"

# ── Make executable ──
chmod +x fb_extractor.py

# ── Launcher shortcut ──
LAUNCHER="$HOME/../usr/bin/fbx"
cat > "$LAUNCHER" << 'LAUNCH'
#!/data/data/com.termux/files/usr/bin/bash
cd "$HOME/AW-FB-Extractor"
python fb_extractor.py "$@"
LAUNCH
chmod +x "$LAUNCHER"
ok "Launcher 'fbx' installed → type: fbx"

echo ""
echo -e "${GREEN}${BOLD}╔══════════════════════════════════════╗${NC}"
echo -e "${GREEN}${BOLD}║   Installation complete! Run with:   ║${NC}"
echo -e "${GREEN}${BOLD}║                                      ║${NC}"
echo -e "${GREEN}${BOLD}║   ${CYAN}fbx${GREEN}   or   ${CYAN}python fb_extractor.py${GREEN}   ║${NC}"
echo -e "${GREEN}${BOLD}║                                      ║${NC}"
echo -e "${GREEN}${BOLD}╚══════════════════════════════════════╝${NC}"
echo ""
