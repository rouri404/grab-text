#!/bin/bash

# --- GrabText - Installation Script ---

DETECTED_LANG=$(echo $LANG | cut -d'.' -f1 | cut -d'_' -f1 | tr '[:upper:]' '[:lower:]')
LANG_FILE=""

if [ -n "$GRABTEXT_LANG" ]; then
    if [ -f "./lang/${GRABTEXT_LANG}.sh" ]; then
        LANG_FILE="./lang/${GRABTEXT_LANG}.sh"
    fi
elif [ -f "./lang/${DETECTED_LANG}.sh" ]; then
    LANG_FILE="./lang/${DETECTED_LANG}.sh"
elif [ -f "./lang/pt.sh" ]; then
    LANG_FILE="./lang/pt.sh"
else
    echo "ERROR: Language files (e.g., lang/pt.sh or lang/en.sh) not found." >&2
    exit 1
fi

source "$LANG_FILE"

BLUE='\033[1;34m'; GREEN='\033[1;32m'; RED='\033[1;31m'; YELLOW='\033[1;33m'; NC='\033[0m'
info() { echo -e "${BLUE}[INFO]${NC} $1"; }
success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1" >&2; exit 1; }
warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }

info "$MSG_INSTALL_START"

info "$MSG_CHECK_PACKAGES"
if command -v pacman &> /dev/null; then
    sudo pacman -Syu --needed --noconfirm flameshot tesseract tesseract-data-por tesseract-data-eng xclip python-pip libnotify || error "$MSG_INSTALL_FAIL"
elif command -v apt &> /dev/null; then
    sudo apt update && sudo apt install -y flameshot tesseract-ocr tesseract-ocr-por tesseract-ocr-eng xclip python3-pip libnotify-bin || error "$MSG_INSTALL_FAIL"
elif command -v dnf &> /dev/null; then
    sudo dnf install -y flameshot tesseract langpacks-por langpacks-eng xclip python3-pip libnotify || error "$MSG_INSTALL_FAIL"
elif command -v zypper &> /dev/null; then
    sudo zypper install -y flameshot tesseract-ocr tesseract-ocr-por tesseract-ocr-eng xclip python3-pip libnotify-tools || error "$MSG_INSTALL_FAIL"
else
    error "$MSG_PKG_MGR_NOT_SUPPORTED"
fi
success "$MSG_DEPS_INSTALLED"

info "$MSG_SETUP_PYTHON_ENV"
python3 -m venv .venv || error "$MSG_VENV_FAIL"
./.venv/bin/pip install --upgrade pip || error "$MSG_PIP_FAIL"
./.venv/bin/pip install -r requirements.txt || error "$MSG_PIP_FAIL"
success "$MSG_PYTHON_DEPS_INSTALLED"

# Create initial configuration file
info "Criando arquivo de configuração inicial..."
cat > .grabtext_config << EOLCONFIG
language=pt
EOLCONFIG
if [ -f ".grabtext_config" ]; then
    success "Arquivo de configuração criado."
else
    warning "Falha ao criar arquivo de configuração."
fi

CONFIG_DIR="$HOME/.config/flameshot"
info "$MSG_CONFIG_FLAMESHOT"
mkdir -p "$CONFIG_DIR"
if [ -f "$CONFIG_DIR/flameshot.ini" ]; then mv "$CONFIG_DIR/flameshot.ini" "$CONFIG_DIR/flameshot.ini.bak"; fi
cp "./flameshot.ini" "$CONFIG_DIR/" || error "$MSG_COPY_CONFIG_FAIL"
success "$MSG_FLAMESHOT_CONFIG_APPLIED"

info "$MSG_CREATE_LAUNCH_SCRIPT"
# Get absolute path of installation directory
INSTALL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Create launch script
cat > launch.sh << 'EOLSCRIPT'
#!/bin/bash
SCRIPT_PATH="$(readlink -f "$0" 2>/dev/null || echo "$0")"
INSTALL_DIR="$(cd "$(dirname "$SCRIPT_PATH")" && pwd)"
PYTHON_EXEC="${INSTALL_DIR}/.venv/bin/python"
GRABTEXT_SCRIPT="${INSTALL_DIR}/grabtext.py"

# Ensure PATH has common locations
export PATH=/usr/bin:/bin:/usr/local/bin:/usr/sbin:/sbin:$HOME/.local/bin:$PATH

# Validate installation directory
if [ ! -d "$INSTALL_DIR" ]; then
	notify-send "GrabText Error" "Installation directory not found: $INSTALL_DIR" 2>/dev/null || true
	echo "Installation directory not found: $INSTALL_DIR" >&2
	exit 1
fi

# Validate Python venv
if [ ! -x "$PYTHON_EXEC" ]; then
	notify-send "GrabText Error" "Python environment not found. Run ./install.sh in $INSTALL_DIR" 2>/dev/null || true
	echo "Python environment not found at: $PYTHON_EXEC" >&2
	exit 1
fi

# Validate script
if [ ! -f "$GRABTEXT_SCRIPT" ]; then
	notify-send "GrabText Error" "Script not found. Expected: $GRABTEXT_SCRIPT" 2>/dev/null || true
	echo "Script not found: $GRABTEXT_SCRIPT" >&2
	exit 1
fi

# Delegate to Python script
if [ $# -eq 0 ]; then
	"$PYTHON_EXEC" "$GRABTEXT_SCRIPT"
else
	"$PYTHON_EXEC" "$GRABTEXT_SCRIPT" "$@"
fi
EOLSCRIPT

# Set permissions
chmod +x launch.sh
success "$MSG_LAUNCH_SCRIPT_CREATED"

# Create CLI command
info "$MSG_CREATING_CLI_COMMAND"
mkdir -p "$HOME/.local/bin"
GRABTEXT_CLI="$HOME/.local/bin/grabtext"
ln -sf "$INSTALL_DIR/launch.sh" "$GRABTEXT_CLI"

# Add ~/.local/bin to PATH if not already present
if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
    SHELL_RC="$HOME/.$(basename $SHELL)rc"
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$SHELL_RC"
    info "$MSG_PATH_UPDATED"
fi

chmod +x grabtext.py
chmod +x launch.sh
success "$MSG_PERMISSIONS_ADJUSTED"

# Verify installation
info "Verificando instalação..."
MISSING_FILES=""
[ ! -f "grabtext.py" ] && MISSING_FILES="$MISSING_FILES grabtext.py"
[ ! -f "launch.sh" ] && MISSING_FILES="$MISSING_FILES launch.sh"
[ ! -f ".grabtext_config" ] && MISSING_FILES="$MISSING_FILES .grabtext_config"
[ ! -d ".venv" ] && MISSING_FILES="$MISSING_FILES .venv"
[ ! -f ".venv/bin/python" ] && MISSING_FILES="$MISSING_FILES .venv/bin/python"

if [ -n "$MISSING_FILES" ]; then
    error "Arquivos faltando na instalação:$MISSING_FILES"
else
    success "Todos os arquivos necessários foram criados."
fi


echo ""
success "$MSG_INSTALL_COMPLETE"
info "$MSG_AUTO_SHORTCUT_SETUP"

# Install .desktop file
info "$MSG_DESKTOP_FILE_SETUP"
APPS_DIR="$HOME/.local/share/applications"
mkdir -p "$APPS_DIR"

# Create .desktop file with correct path
cat > "$APPS_DIR/grabtext.desktop" << EOLDESKTOP
[Desktop Entry]
Version=1.0
Type=Application
Name=GrabText
Comment=Text extraction tool for Linux
Comment[pt]=Ferramenta de extração de texto para Linux
Exec=$INSTALL_DIR/launch.sh grab
Icon=document-save-as
Terminal=false
StartupNotify=true
Categories=Graphics;Photography;Utility;
Keywords=OCR;text;extraction;screenshot;tesseract;
Keywords[pt]=OCR;texto;extração;captura;tesseract;
MimeType=image/png;image/jpeg;image/jpg;
StartupWMClass=GrabText
EOLDESKTOP

if [ -f "$APPS_DIR/grabtext.desktop" ]; then
    success "Arquivo .desktop criado com sucesso"
else
    warning "$MSG_DESKTOP_FILE_COPY_FAIL"
fi

# Detect desktop environment
SESSION_TYPE="unknown"
if [ -n "$XDG_CURRENT_DESKTOP" ]; then
    SESSION_TYPE=$(echo "$XDG_CURRENT_DESKTOP" | tr '[:upper:]' '[:lower:]')
elif [ -n "$DESKTOP_SESSION" ]; then
    SESSION_TYPE=$(echo "$DESKTOP_SESSION" | tr '[:upper:]' '[:lower:]')
fi

# Configure shortcut based on desktop environment
case "$SESSION_TYPE" in
    *gnome*|*ubuntu*|*cinnamon*)
        info "$MSG_ATTEMPT_GNOME_SHORTCUT"
        if command -v gsettings > /dev/null; then
            KEY_PATH="/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/grabtext/"
            dconf reset -f /org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/grabtext/ &> /dev/null || true
            gsettings set org.gnome.settings-daemon.plugins.media-keys custom-keybindings "['$KEY_PATH']" &> /dev/null && \
            gsettings set org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:$KEY_PATH name 'GrabText' &> /dev/null && \
            gsettings set org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:$KEY_PATH command "$INSTALL_DIR/launch.sh grab" &> /dev/null && \
            gsettings set org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:$KEY_PATH binding 'Insert' &> /dev/null && \
            success "$MSG_SHORTCUT_SUCCESS" || warning "$MSG_SHORTCUT_FAIL"
        else
            warning "$MSG_NO_GSETTINGS"
        fi
        ;;
    *xfce*)
        info "$MSG_ATTEMPT_XFCE_SHORTCUT"
        if command -v xfconf-query > /dev/null; then
            xfconf-query -c xfce4-keyboard-shortcuts -p /commands/custom/Insert -r &> /dev/null || true
            if xfconf-query -c xfce4-keyboard-shortcuts -p /commands/custom/Insert -n -t string -s "$INSTALL_DIR/launch.sh grab"; then
                success "$MSG_SHORTCUT_SUCCESS"
            else
                warning "$MSG_SHORTCUT_FAIL"
            fi
        else
            warning "$MSG_NO_XFCONF"
        fi
        ;;
    *kde*|*plasma*)
        info "$MSG_ATTEMPT_KDE_SHORTCUT"
        if command -v kwriteconfig5 > /dev/null; then
            # Remove atalho existente se houver
            kwriteconfig5 --file kglobalshortcutsrc --group "GrabText" --delete &> /dev/null || true
            # Adicionar novo atalho
            kwriteconfig5 --file kglobalshortcutsrc --group "GrabText" --key "Grab Text" "$INSTALL_DIR/launch.sh grab,none,Grab Text" && \
            kwriteconfig5 --file kglobalshortcutsrc --group "GrabText" --key "_k_friendly_name" "GrabText" && \
            kwriteconfig5 --file kglobalshortcutsrc --group "GrabText" --key "_launch" "Insert,none,GrabText" && \
            success "$MSG_SHORTCUT_SUCCESS" || warning "$MSG_SHORTCUT_FAIL"
        else
            warning "$MSG_NO_KWRITECONFIG"
        fi
        ;;
    *)
        warning "$MSG_DESKTOP_NOT_DETECTED"
        ;;
esac
echo ""