#!/data/data/com.termux/files/usr/bin/bash
# ============================================================
#   AW FB Extractor — Termux Installer
#   github.com/ahmed-awad26
# ============================================================

set -u

RED='\033[0;31m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
BOLD='\033[1m'
NC='\033[0m'

REPO_URL="https://github.com/ahmed-awad26/AW-FB-Extractor"
RAW_BASE="https://raw.githubusercontent.com/ahmed-awad26/AW-FB-Extractor/main"
INSTALL_DIR="$HOME/AW-FB-Extractor"
LAUNCHER="$PREFIX/bin/fbx"

banner() {
  echo -e "${CYAN}"
  echo "  ╔══════════════════════════════════════════╗"
  echo "  ║   AW FB Extractor — Installer v1.1       ║"
  echo "  ║   github.com/ahmed-awad26                ║"
  echo "  ╚══════════════════════════════════════════╝"
  echo -e "${NC}"
}

step() { echo -e "${CYAN}[→]${NC} ${BOLD}$1${NC}"; }
ok() { echo -e "${GREEN}[✔]${NC} $1"; }
warn() { echo -e "${YELLOW}[!]${NC} $1"; }
fail() { echo -e "${RED}[✘]${NC} $1"; exit 1; }

run_or_warn() {
  "$@" || warn "Command failed but installer will continue: $*"
}

install_python_pkg() {
  local pkg="$1"
  python -m pip show "$pkg" >/dev/null 2>&1 || python -m pip install "$pkg" || return 1
}

banner

command -v pkg >/dev/null 2>&1 || fail "This installer is intended for Termux."

step "Updating Termux packages..."
run_or_warn pkg update -y
run_or_warn pkg upgrade -y
ok "Package index refreshed"

step "Installing system dependencies..."
pkg install -y \
  python \
  python-pip \
  git \
  clang \
  libxml2 \
  libxslt \
  libffi \
  openssl \
  pkg-config \
  rust \
  >/dev/null || fail "Failed to install required Termux packages"
ok "System dependencies installed"

step "Cloning or updating repository..."
if [ -d "$INSTALL_DIR/.git" ]; then
  cd "$INSTALL_DIR" || fail "Cannot access $INSTALL_DIR"
  if git pull --quiet; then
    ok "Updated existing installation"
  else
    warn "git pull failed; keeping local files"
  fi
else
  if git clone --quiet "$REPO_URL" "$INSTALL_DIR"; then
    ok "Repository cloned"
  else
    warn "git clone failed — creating local installation directory"
    mkdir -p "$INSTALL_DIR"
  fi
fi
cd "$INSTALL_DIR" || fail "Cannot access installation directory"

if [ ! -f "fb_extractor.py" ]; then
  step "Fetching core project files..."
  curl -fsSL "$RAW_BASE/fb_extractor.py" -o fb_extractor.py || fail "Could not download fb_extractor.py"
  curl -fsSL "$RAW_BASE/requirements.txt" -o requirements.txt || fail "Could not download requirements.txt"
  [ -f README.md ] || curl -fsSL "$RAW_BASE/README.md" -o README.md || true
  ok "Core files downloaded"
fi

step "Upgrading pip tooling..."
python -m pip install --upgrade pip setuptools wheel >/dev/null || warn "pip tooling upgrade had warnings"
ok "pip tooling ready"

step "Installing Python dependencies..."
if [ -f requirements.txt ]; then
  python -m pip install -r requirements.txt || warn "requirements.txt had package conflicts; applying targeted fixes"
else
  warn "requirements.txt not found — using targeted packages only"
fi

# Known compatibility fixes for Termux / Python 3.13 / requests-html / facebook-scraper
install_python_pkg rich || fail "Failed to install rich"
install_python_pkg requests || fail "Failed to install requests"
install_python_pkg pillow || fail "Failed to install Pillow"
install_python_pkg fpdf2 || warn "PDF export will be unavailable until fpdf2 is installed"
install_python_pkg lxml || fail "Failed to install lxml"
install_python_pkg lxml_html_clean || fail "Failed to install lxml_html_clean"
install_python_pkg facebook-scraper || fail "Failed to install facebook-scraper"
ok "Python dependencies installed"

step "Running self-checks..."
python - <<'PY' || fail "Python dependency self-check failed"
import importlib
mods = [
    'rich', 'requests', 'PIL', 'fpdf', 'lxml', 'lxml_html_clean', 'facebook_scraper'
]
for name in mods:
    importlib.import_module(name)
print('OK')
PY
ok "Self-check passed"

chmod +x fb_extractor.py 2>/dev/null || true
chmod +x *.sh 2>/dev/null || true

step "Installing launcher shortcut..."
cat > "$LAUNCHER" <<'LAUNCH'
#!/data/data/com.termux/files/usr/bin/bash
cd "$HOME/AW-FB-Extractor" || exit 1
python fb_extractor.py "$@"
LAUNCH
chmod +x "$LAUNCHER"
ok "Launcher installed → use: fbx"

echo ""
echo -e "${GREEN}${BOLD}╔══════════════════════════════════════╗${NC}"
echo -e "${GREEN}${BOLD}║   Installation complete! Run with:   ║${NC}"
echo -e "${GREEN}${BOLD}║                                      ║${NC}"
echo -e "${GREEN}${BOLD}║   ${CYAN}fbx${GREEN}   or   ${CYAN}python fb_extractor.py${GREEN}   ║${NC}"
echo -e "${GREEN}${BOLD}║                                      ║${NC}"
echo -e "${GREEN}${BOLD}╚══════════════════════════════════════╝${NC}"
echo ""
