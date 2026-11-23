#!/usr/bin/env bash
# manage-uniwill-hwmon.sh — Fan/RPM sensor for Uniwill/Tongfang ECs over ACPI-WMI
#
# Installs, inspects and removes the `uniwill-ec-hwmon-dkms` package, a
# read-only hwmon driver that exposes CPU/GPU fan RPM, temperatures and PWM on
# laptops whose BIOS does not provide the INOU0000 ACPI device required by the
# in-tree uniwill-laptop driver.
#
# The driver never writes to the EC. It is safe to remove at any time.
set -euo pipefail

PKG="uniwill-ec-hwmon-dkms"
MODULE="uniwill_ec_hwmon"
GUID="ABBC0F6F-8EA1-11D1-00A0-C90629100000"
HWMON_NAME="uniwill_ec"

ACTION="${1:---status}"

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m'

ok()   { echo -e "  ${GREEN}[OK]${NC} $*"; }
info() { echo -e "  ${BLUE}[INFO]${NC} $*"; }
warn() { echo -e "  ${YELLOW}[WARN]${NC} $*"; }
err()  { echo -e "  ${RED}[ERROR]${NC} $*"; }

log() {
    if declare -F runlog_event >/dev/null 2>&1; then
        runlog_event "$1" "$2" "${3:-}"
    fi
}

detect() {
    WMI_PRESENT=0
    INOU_PRESENT=0
    HWMON_PRESENT=0
    PKG_INSTALLED=0
    MOD_LOADED=0
    HWMON_PATH=""

    compgen -G "/sys/bus/wmi/devices/${GUID}-*" >/dev/null 2>&1 && WMI_PRESENT=1
    [ -e "/sys/bus/acpi/devices/INOU0000:00" ] && INOU_PRESENT=1

    local h
    for h in /sys/class/hwmon/hwmon*; do
        [ -r "$h/name" ] || continue
        if [ "$(cat "$h/name")" = "$HWMON_NAME" ]; then
            HWMON_PRESENT=1
            HWMON_PATH="$h"
        fi
    done

    pacman -Qq "$PKG" >/dev/null 2>&1 && PKG_INSTALLED=1
    grep -q "^${MODULE} " /proc/modules && MOD_LOADED=1
}

print_sensors() {
    if [ "$HWMON_PRESENT" = "1" ] && command -v sensors >/dev/null 2>&1; then
        sensors 2>/dev/null | sed -n "/${HWMON_NAME}/,+8p"
    fi
}

status() {
    echo -e "${BOLD}Uniwill EC fan sensor (${MODULE})${NC}"
    echo ""
    info "WMI EC bridge (${GUID}): $([ "$WMI_PRESENT" = 1 ] && echo present || echo MISSING)"
    info "INOU0000 ACPI device:      $([ "$INOU_PRESENT" = 1 ] && echo present || echo absent)"

    if [ "$INOU_PRESENT" = "1" ]; then
        warn "This BIOS exposes INOU0000: use the in-tree uniwill-laptop driver instead."
        log info "uniwill_hwmon_inou_present"
        echo ""
        return 0
    fi

    if [ "$WMI_PRESENT" = "0" ]; then
        warn "This machine does not expose the Uniwill WMI EC interface; unsupported."
        log warn "uniwill_hwmon_unsupported"
        echo ""
        return 0
    fi

    info "Package ${PKG}: $([ "$PKG_INSTALLED" = 1 ] && echo installed || echo not-installed)"
    info "Module ${MODULE}:    $([ "$MOD_LOADED" = 1 ] && echo loaded || echo not-loaded)"
    info "hwmon ${HWMON_NAME}:      $([ "$HWMON_PRESENT" = 1 ] && echo "${HWMON_PATH}" || echo absent)"

    if [ "$HWMON_PRESENT" = "1" ]; then
        ok "Fan RPM and temperatures are available to sensors/coolercontrol."
        if [ "$PKG_INSTALLED" = "0" ]; then
            warn "Module was loaded manually (insmod); run 'fan-sensor install' to persist across reboots."
        fi
        log ok "uniwill_hwmon_active" "${HWMON_PATH:-}"
        echo ""
        print_sensors
        echo ""
        return 0
    fi

    warn "Sensor is supported but not active. Install with:"
    echo "    ./bin/linux-wayland-config fan-sensor install"
    log warn "uniwill_hwmon_not_installed"
    echo ""
    return 0
}

require_supported() {
    if [ "$INOU_PRESENT" = "1" ]; then
        err "INOU0000 is present; the in-tree uniwill-laptop driver is the correct path."
        err "Do not install this module on top of it."
        log warn "uniwill_hwmon_refused_inou"
        exit 2
    fi
    if [ "$WMI_PRESENT" = "0" ]; then
        err "Uniwill WMI EC interface (${GUID}) not found; unsupported hardware."
        log err "uniwill_hwmon_unsupported"
        exit 2
    fi
}

kernel_headers_package() {
    local kernel
    kernel="$(uname -r)"
    case "$kernel" in
        *-zen*)      echo "linux-zen-headers" ;;
        *-lts*)      echo "linux-lts-headers" ;;
        *-hardened*) echo "linux-hardened-headers" ;;
        *-rt*)       echo "linux-rt-headers" ;;
        *)           echo "linux-headers" ;;
    esac
}

install_sensor() {
    echo -e "${BOLD}Installing Uniwill EC fan sensor (${PKG})${NC}"
    echo ""

    require_supported

    if [ "$HWMON_PRESENT" = "1" ] && [ "$PKG_INSTALLED" = "1" ]; then
        ok "Already active at ${HWMON_PATH} and package installed; nothing to do."
        log ok "uniwill_hwmon_already_active" "${HWMON_PATH:-}"
        return 0
    fi

    if [ "$HWMON_PRESENT" = "1" ] && [ "$PKG_INSTALLED" = "0" ]; then
        warn "Module is loaded manually but the package is not installed; installing for persistence."
    fi

    if ! command -v dkms >/dev/null 2>&1; then
        info "Installing DKMS..."
        sudo pacman -S --needed --noconfirm dkms
    fi

    local hdr
    hdr="$(kernel_headers_package)"
    if [ ! -d "/lib/modules/$(uname -r)/build" ]; then
        info "Installing kernel headers (${hdr})..."
        sudo pacman -S --needed --noconfirm "$hdr"
    fi

    if [ "$PKG_INSTALLED" = "0" ]; then
        if [ "$(id -u)" = "0" ]; then
            err "Run as your user (not root); AUR helpers refuse to run as root."
            exit 1
        fi

        if command -v paru >/dev/null 2>&1; then
            info "Installing ${PKG} from AUR via paru..."
            paru -S --needed --noconfirm "$PKG"
        elif command -v yay >/dev/null 2>&1; then
            info "Installing ${PKG} from AUR via yay..."
            yay -S --needed --noconfirm "$PKG"
        elif sudo pacman -Si "$PKG" >/dev/null 2>&1; then
            info "Installing ${PKG} from pacman repositories..."
            sudo pacman -S --needed --noconfirm "$PKG"
        else
            err "Package ${PKG} is not available in configured repos and no AUR helper was found."
            err "Install an AUR helper (paru/yay) or build it manually."
            log err "uniwill_hwmon_package_missing"
            exit 1
        fi
    else
        info "${PKG} already installed; loading module..."
    fi

    sudo modprobe "$MODULE"
    detect

    if [ "$HWMON_PRESENT" = "1" ]; then
        ok "Sensor active at ${HWMON_PATH}."
        log ok "uniwill_hwmon_installed" "${HWMON_PATH:-}"
        echo ""
        print_sensors
        echo ""
        return 0
    fi

    err "Package installed but hwmon did not appear. Check: sudo dmesg | grep -i uniwill"
    log err "uniwill_hwmon_probe_failed"
    exit 1
}

uninstall_sensor() {
    echo -e "${BOLD}Removing Uniwill EC fan sensor (${PKG})${NC}"
    echo ""

    if [ "$PKG_INSTALLED" = "1" ]; then
        sudo pacman -Rns --noconfirm "$PKG"
        log ok "uniwill_hwmon_uninstalled"
    else
        sudo modprobe -r "$MODULE" 2>/dev/null || true
        log info "uniwill_hwmon_not_installed"
    fi

    detect
    if [ "$HWMON_PRESENT" = "1" ]; then
        warn "hwmon ${HWMON_NAME} still present; a reboot may be needed."
        exit 1
    fi

    ok "Sensor removed."
}

case "$ACTION" in
    --status|status)
        detect
        status
        ;;
    --install|install)
        detect
        install_sensor
        ;;
    --uninstall|uninstall|--remove|remove)
        detect
        uninstall_sensor
        ;;
    --help|-h|help)
        echo "Usage: manage-uniwill-hwmon.sh [status|install|uninstall]"
        echo ""
        echo "  status     Read-only check of hardware support, package and hwmon state."
        echo "  install    Installs ${PKG} via AUR helper and loads the module (sudo)."
        echo "  uninstall  Removes the package and the module (sudo)."
        ;;
    *)
        echo "Unknown action: $ACTION" >&2
        echo "Usage: manage-uniwill-hwmon.sh [status|install|uninstall]" >&2
        exit 1
        ;;
esac
