#!/bin/bash

# --- GrabText - Uninstallation Script ---

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
warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }

info "$MSG_UNINSTALL_START"
read -p "$MSG_CONFIRM_UNINSTALL" response
if [[ "$response" =~ ^([yY])$ ]]; then
    # Remove CLI command
    info "$MSG_REMOVING_CLI"
    GRABTEXT_CLI="$HOME/.local/bin/grabtext"
    if [ -L "$GRABTEXT_CLI" ]; then
        rm -f "$GRABTEXT_CLI"
        success "$MSG_CLI_REMOVED"
    fi

    info "\n$MSG_REMOVE_SHORTCUT_ATTEMPT"
    if [ -n "$XDG_CURRENT_DESKTOP" ]; then DESKTOP_ENV="$XDG_CURRENT_DESKTOP"; elif [ -n "$GDMSESSION" ]; then DESKTOP_ENV="$GDMSESSION"; else DESKTOP_ENV="$DESKTOP_SESSION"; fi
    DESKTOP_ENV=$(echo "$DESKTOP_ENV" | tr '[:upper:]' '[:lower:]')

    case "$DESKTOP_ENV" in
      *gnome*|*cinnamon*)
        KEY_PATH="/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/custom0/"
        if gsettings get org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:$KEY_PATH name &> /dev/null | grep -q "GrabText"; then
            CURRENT_KEYBINDINGS=$(gsettings get org.gnome.settings-daemon.plugins.media-keys custom-keybindings)
            NEW_KEYBINDINGS=$(echo "$CURRENT_KEYBINDINGS" | sed "s#,'$KEY_PATH'##g;s#'$KEY_PATH',##g;s#\[\'$KEY_PATH\'\]#@as []#") # Remove custom0 from the array
            gsettings set org.gnome.settings-daemon.plugins.media-keys custom-keybindings "$NEW_KEYBINDINGS" &> /dev/null
            
            gsettings reset org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:$KEY_PATH name &> /dev/null
            gsettings reset org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:$KEY_PATH command &> /dev/null
            gsettings reset org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:$KEY_PATH binding &> /dev/null
            success "$MSG_SHORTCUT_RESET_GNOME"
        else
            warning "$MSG_NO_SHORTCUT_FOUND"
        fi
        ;;
      *xfce*)
        if xfconf-query -c xfce4-keyboard-shortcuts -p /commands/custom/Insert &> /dev/null; then
            xfconf-query -c xfce4-keyboard-shortcuts -p /commands/custom/Insert -r
            success "$MSG_SHORTCUT_REMOVED_XFCE"
        else
             warning "$MSG_NO_SHORTCUT_FOUND"
        fi
        ;;
      *)
        warning "$MSG_COULD_NOT_REMOVE_SHORTCUT"
        ;;
    esac

    CONFIG_DIR="$HOME/.config/flameshot"
    if [ -f "$CONFIG_DIR/flameshot.ini.bak" ]; then mv "$CONFIG_DIR/flameshot.ini.bak" "$CONFIG_DIR/flameshot.ini"; success "$MSG_FLAMESHOT_RESTORED"; else rm -f "$CONFIG_DIR/flameshot.ini"; fi
    rm -rf .venv
    rm -f launch.sh
    rm -f grabtext.log
    success "$MSG_VENV_LAUNCH_LOG_REMOVED"

    warning "\n$MSG_REMINDER_PKG_REMOVAL"
    info "$MSG_REMOVE_PACKAGES_PROMPT"

    if command -v pacman &> /dev/null; then
        echo -e "${YELLOW}   sudo pacman -Rsn flameshot tesseract tesseract-data-por tesseract-data-eng xclip python-pip libnotify${NC}"
    elif command -v apt &> /dev/null; then
        echo -e "${YELLOW}   sudo apt remove --purge flameshot tesseract-ocr tesseract-ocr-por tesseract-ocr-eng xclip python3-pip libnotify-bin${NC}"
    elif command -v dnf &> /dev/null; then
        echo -e "${YELLOW}   sudo dnf remove flameshot tesseract langpacks-por langpacks-eng xclip python3-pip libnotify${NC}"
    elif command -v zypper &> /dev/null; then
        echo -e "${YELLOW}   sudo zypper remove flameshot tesseract-ocr tesseract-ocr-por tesseract-ocr-eng xclip python3-pip libnotify-tools${NC}"
    fi
    
    echo ""
    read -p "$MSG_CONFIRM_FOLDER_DELETE" del_response
    if [[ "$del_response" =~ ^([yY])$ ]]; then
        PROJECT_DIR_NAME=${PWD##*/} 
        info "$(echo "$MSG_REMOVING_PROJECT_FOLDER" | sed "s/{PROJECT_DIR_NAME}/$PROJECT_DIR_NAME/")"
        cd .. && rm -rf "$PROJECT_DIR_NAME"
        success "$MSG_PROJECT_FOLDER_REMOVED"
    fi
    success "$MSG_UNINSTALL_COMPLETE"

else
    info "$MSG_UNINSTALL_CANCELLED"
fi