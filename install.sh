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
./.venv/bin/pip install -r requirements.txt || error "$MSG_PIP_FAIL"
success "$MSG_PYTHON_DEPS_INSTALLED"

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
cat > launch.sh << EOLSCRIPT
#!/bin/bash
INSTALL_DIR="${INSTALL_DIR}"
PYTHON_EXEC="\${INSTALL_DIR}/.venv/bin/python"
GRABTEXT_SCRIPT="\${INSTALL_DIR}/grabtext.py"

# Set language
DETECTED_LANG=\$(echo \$LANG | cut -d'.' -f1 | cut -d'_' -f1 | tr '[:upper:]' '[:lower:]')
export GRABTEXT_LANG="${GRABTEXT_LANG:-\${DETECTED_LANG:-pt}}"

# Set path to include common locations for required tools
export PATH=/usr/bin:/bin:/usr/local/bin:/usr/sbin:/sbin:\$HOME/.local/bin:\$PATH

# Check for GUI environment and tools
has_display() {
    # First check if DISPLAY is set
    [ -n "\$DISPLAY" ] || return 1
    
    # Then check if we can query X server
    if command -v xdpyinfo >/dev/null 2>&1; then
        xdpyinfo >/dev/null 2>&1
        return \$?
    elif command -v xhost >/dev/null 2>&1; then
        xhost >/dev/null 2>&1
        return \$?
    fi
    
    # If no X tools available, check Wayland
    [ -n "\$WAYLAND_DISPLAY" ]
    return \$?
}

has_gui_tools() {
    # Check if essential GUI tools are available
    command -v flameshot >/dev/null 2>&1 || return 1
    command -v notify-send >/dev/null 2>&1 || return 1
    return 0
}

# Debug information (if needed)
if [ "\$1" = "--debug" ]; then
    echo "Install directory: \$INSTALL_DIR"
    echo "Python executable: \$PYTHON_EXEC"
    echo "Script path: \$GRABTEXT_SCRIPT"
    echo "Current directory: \$(pwd)"
    echo "Display available: \$(has_display && echo 'yes' || echo 'no')"
    exit 0
fi

# Check installation directory
if [ ! -d "\$INSTALL_DIR" ]; then
    notify-send "GrabText Error" "Installation directory not found: \$INSTALL_DIR"
    exit 1
fi

# Check required files
if [ ! -f "\$PYTHON_EXEC" ]; then
    notify-send "GrabText Error" "Python environment not found. Try reinstalling GrabText."
    echo "Missing: \$PYTHON_EXEC" >&2
    exit 1
fi

if [ ! -f "\$GRABTEXT_SCRIPT" ]; then
    notify-send "GrabText Error" "Script not found. Try reinstalling GrabText."
    echo "Missing: \$GRABTEXT_SCRIPT" >&2
    exit 1
fi

# Execute command
if [ "\$1" = "grab" ] || [ "\$1" = "--gui" ]; then
    # Check GUI requirements
    if ! has_display; then
        echo "Error: No display available. X11 or Wayland is required for GUI operations." >&2
        exit 1
    fi

    if ! has_gui_tools; then
        echo "Error: Required GUI tools (flameshot, notify-send) are not installed." >&2
        exit 1
    fi

    # GUI Mode - Use temporary file to handle the screenshot
    TEMP_IMG=\$(mktemp -t grabtext-XXXXXX.png)
    cleanup() {
        rm -f "\$TEMP_IMG"
    }
    trap cleanup EXIT

    # Capture screenshot to temp file
    if flameshot gui --raw > "\$TEMP_IMG"; then
        if [ -s "\$TEMP_IMG" ]; then  # Check if file is not empty
            # Process the image with Python
            "\$PYTHON_EXEC" "\$GRABTEXT_SCRIPT" grab -i "\$TEMP_IMG" --clipboard
        else
            echo "No image captured." >&2
            exit 1
        fi
    fi
elif [ -z "\$1" ]; then
    # No arguments - show help
    "\$PYTHON_EXEC" "\$GRABTEXT_SCRIPT" help
else
    # CLI Mode - pass all arguments
    "\$PYTHON_EXEC" "\$GRABTEXT_SCRIPT" "\$@"
fi
EOLSCRIPT

# Set permissions
chmod +x launch.sh
success "$MSG_LAUNCH_SCRIPT_CREATED"

# Create CLI command
info "$MSG_CREATING_CLI_COMMAND"
mkdir -p "$HOME/.local/bin"
GRABTEXT_CLI="$HOME/.local/bin/grabtext"
ln -sf "$PWD/launch.sh" "$GRABTEXT_CLI"

# Add ~/.local/bin to PATH if not already present
if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
    SHELL_RC="$HOME/.$(basename $SHELL)rc"
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$SHELL_RC"
    info "$MSG_PATH_UPDATED"
fi

chmod +x grabtext.py
chmod +x launch.sh
success "$MSG_PERMISSIONS_ADJUSTED"

escape_path_with_single_quotes() {
  local IFS='/'
  read -ra parts <<< "$1"
  local escaped_path=""
  for part in "${parts[@]}"; do
    if [[ "$part" =~ [[:space:]] ]]; then
      escaped_path+="/'$part'"
    else
      escaped_path+="/$part"
    fi
  done
  echo "${escaped_path#/}"
}

echo ""
success "$MSG_INSTALL_COMPLETE"
info "$MSG_AUTO_SHORTCUT_SETUP"

# Install .desktop file
info "$MSG_DESKTOP_FILE_SETUP"
APPS_DIR="$HOME/.local/share/applications"
mkdir -p "$APPS_DIR"
cp "./grabtext.desktop" "$APPS_DIR/" || warning "$MSG_DESKTOP_FILE_COPY_FAIL"

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
            gsettings set org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:$KEY_PATH command "$PWD/launch.sh grab" &> /dev/null && \
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
            if xfconf-query -c xfce4-keyboard-shortcuts -p /commands/custom/Insert -n -t string -s "$PWD/launch.sh grab"; then
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
            kwriteconfig5 --file kglobalshortcutsrc --group "GrabText" --key "Grab Text" "$PWD/launch.sh grab,none,Grab Text" && \
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