#!/bin/sh

# ============================================================
# WorkforceAI - Linux/macOS Installer
# Developed by issu321
# GitHub: github.com/issu321
# ============================================================

set -e

# =========================
# COLORS
# =========================

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m'

command -v clear >/dev/null 2>&1 && clear || true

# =========================
# ANIMATED TYPEWRITER EFFECT
# =========================

typewriter() {
    _text="$1"
    _delay="${2:-0.03}"
    _i=0
    _len=$(printf '%s' "$_text" | wc -c)
    while [ "$_i" -lt "$_len" ]; do
        _pos=$((_i + 1))
        _char=$(printf '%s' "$_text" | cut -c"$_pos")
        printf '%s' "$_char"
        sleep "$_delay"
        _i=$((_i + 1))
    done
}

# =========================
# HACKER RAIN EFFECT
# =========================

hacker_rain() {
    _cols=$(tput cols 2>/dev/null || echo 80)
    _r=0
    while [ "$_r" -lt 8 ]; do
        printf '\033[0;32m'
        _c=0
        while [ "$_c" -lt "$_cols" ]; do
            if [ $((RANDOM % 3)) -eq 0 ]; then
                if [ $((RANDOM % 2)) -eq 0 ]; then
                    printf '0'
                else
                    printf '1'
                fi
            else
                printf ' '
            fi
            _c=$((_c + 1))
        done
        printf '\n'
        sleep 0.03
        _r=$((_r + 1))
    done
    printf '\033[0m'
    command -v clear >/dev/null 2>&1 && clear || true
}

# =========================
# HACKER SCANLINE EFFECT
# =========================

scanline_effect() {
    _cols=$(tput cols 2>/dev/null || echo 80)
    printf '\033[0;32m'
    printf '▓'
    _i=1
    while [ "$_i" -lt $((_cols - 1)) ]; do
        printf '░'
        _i=$((_i + 1))
    done
    printf '▓\n'
    printf '\033[0m'
    sleep 0.1
}

# =========================
# LOADING BAR
# =========================

loading_bar() {
    printf "${CYAN}["
    i=0
    while [ $i -lt 40 ]
    do
        printf "="
        sleep 0.015
        i=$((i + 1))
    done
    printf "]${NC}\n"
}

# =========================
# SPINNER
# =========================

spinner() {
    pid=$1
    while kill -0 "$pid" 2>/dev/null
    do
        printf "\r${CYAN}[|] Processing...${NC}"
        sleep 0.1
        printf "\r${CYAN}[/] Processing...${NC}"
        sleep 0.1
        printf "\r${CYAN}[-] Processing...${NC}"
        sleep 0.1
        printf "\r${CYAN}[\\] Processing...${NC}"
        sleep 0.1
    done
    printf "\r${GREEN}[✓] Completed${NC}                    \n"
}

# =========================
# HACKER BOOT SEQUENCE
# =========================

hacker_boot() {
    command -v clear >/dev/null 2>&1 && clear || true
    printf '\033[0;32m'
    typewriter "[SYSTEM] Initializing core modules..." 0.02
    printf '\n'
    sleep 0.2
    typewriter "[KERNEL] Loading virtual environment protocols..." 0.02
    printf '\n'
    sleep 0.2
    typewriter "[DAEMON] Mounting dependency resolver..." 0.02
    printf '\n'
    sleep 0.2
    typewriter "[SECURE] Handshake with github.com/issu321 ..." 0.02
    printf '\n'
    sleep 0.3
    printf '\033[0m'
    command -v clear >/dev/null 2>&1 && clear || true
}

# =========================
# HEADER
# =========================

hacker_boot

hacker_rain

scanline_effect

printf '\033[0;32m'
typewriter "████████████████████████████████████████████████████████████" 0.005
printf '\n'
typewriter "██                                                        ██" 0.005
printf '\n'
typewriter "██   WORKFORCEAI  LINUX INSTALLER  v1.0                  ██" 0.005
printf '\n'
typewriter "██   Developed by: github.com/issu321                     ██" 0.005
printf '\n'
typewriter "██   Mode: STEALTH / HACKER                             ██" 0.005
printf '\n'
typewriter "██                                                        ██" 0.005
printf '\n'
typewriter "████████████████████████████████████████████████████████████" 0.005
printf '\n'
printf '\033[0m'

scanline_effect

printf '\033[0;36m'
echo ""
echo "██╗    ██╗ ██████╗ ██████╗ ██╗  ██╗███████╗ ██████╗ ██████╗ "
echo "██║    ██║██╔═══██╗██╔══██╗██║ ██╔╝██╔════╝██╔═══██╗██╔══██╗"
echo "██║ █╗ ██║██║   ██║██████╔╝█████╔╝ █████╗  ██║   ██║██████╔╝"
echo "██║███╗██║██║   ██║██╔══██╗██╔═██╗ ██╔══╝  ██║   ██║██╔══██╗"
echo "╚███╔███╔╝╚██████╔╝██║  ██║██║  ██╗███████╗╚██████╔╝██║  ██║"
echo " ╚══╝╚══╝  ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝ ╚═════╝ ╚═╝  ╚═╝"
printf '\033[0m'

echo ""
echo -e "${MAGENTA}=========================================================${NC}"
echo -e "${GREEN}             WorkforceAI Installer${NC}"
echo -e "${GREEN}             Developed by issu321${NC}"
echo -e "${MAGENTA}=========================================================${NC}"
echo ""

loading_bar

# =========================
# PYTHON CHECK
# =========================

printf '\033[0;32m'
typewriter "[SCAN] Detecting Python environment..." 0.03
printf '\n'
printf '\033[0m'

if ! command -v python3 >/dev/null 2>&1; then
    echo -e "${RED}[ERROR]${NC} Python3 not found."
    echo "Please install Python 3.11+ first."
    exit 1
fi

echo ""
echo -e "${GREEN}[OK]${NC} Python : $(python3 --version)"
echo ""

# =========================
# VENV NOTICE (DETAILED)
# =========================

printf '\033[0;33m'
typewriter "[ALERT] Virtual Environment Recommended" 0.03
printf '\n'
printf '\033[0m'

echo -e "${YELLOW}[IMPORTANT NOTICE]${NC}"
echo ""
echo "Using a Python Virtual Environment is VERY IMPORTANT and HIGHLY RECOMMENDED."
echo ""
echo "Why? Because it keeps your project dependencies isolated from your"
echo "system Python packages. This prevents version conflicts, keeps your"
echo "system clean, and makes your app portable and easy to deploy."
echo ""
echo "Without a virtual environment, packages may conflict with other"
echo "projects or system tools, causing crashes and broken installations."
echo ""
echo "Follow these steps to create and activate a virtual environment:"
echo ""
echo "-----------------------------------------"
echo "  Step 1: Create the virtual env"
echo "  $ python3 -m venv venv"
echo ""
echo "  Step 2: Activate the virtual env"
echo "  $ source venv/bin/activate"
echo ""
echo "  Step 3: Run the installer"
echo "  $ bash install.sh"
echo ""
echo "  Step 4: Deactivate when done"
echo "  $ deactivate"
echo "-----------------------------------------"
echo ""

printf '\033[0;36m'
typewriter ">>> Type yes  -> Continue (venv created)" 0.03
printf '\n'
typewriter ">>> Type no   -> Continue (no venv)" 0.03
printf '\n'
typewriter ">>> Type exit -> Stop installer" 0.03
printf '\n'
printf '\033[0m'

echo ""

read -r -p "Enter choice (yes/no/exit): " USER_INPUT

if [ "$USER_INPUT" = "exit" ]; then
    printf '\033[0;31m'
    typewriter "[ABORT] Installer terminated by user." 0.03
    printf '\n'
    printf '\033[0m'
    exit 1
fi

if [ "$USER_INPUT" != "yes" ] && [ "$USER_INPUT" != "no" ]; then
    printf '\033[0;31m'
    typewriter "[ERROR] Invalid input." 0.03
    printf '\n'
    printf '\033[0m'
    exit 1
fi

if [ "$USER_INPUT" = "yes" ]; then
    echo ""
    printf '\033[0;32m'
    typewriter "[ACCESS GRANTED] Proceeding with venv installation..." 0.03
    printf '\n'
    printf '\033[0m'
else
    echo ""
    printf '\033[0;33m'
    typewriter "[WARNING] Proceeding without virtual environment..." 0.03
    printf '\n'
    printf '\033[0m'
fi

echo ""

# =========================
# STEP 1
# =========================

printf '\033[0;34m'
typewriter "[1/4] Upgrading pip..." 0.03
printf '\n'
printf '\033[0m'

python3 -m pip install --upgrade pip


# =========================
# STEP 2
# =========================

echo ""
printf '\033[0;34m'
typewriter "[2/4] Installing dependencies..." 0.03
printf '\n'
printf '\033[0m'


python3 -m pip install -r requirements.txt




# =========================
# STEP 3
# =========================

echo ""
printf '\033[0;34m'
typewriter "[3/4] Creating application directories..." 0.03
printf '\n'
printf '\033[0m'

mkdir -p data uploads reports models



# =========================
# STEP 4
# =========================

echo ""
printf '\033[0;34m'
typewriter "[4/4] Finalizing installation..." 0.03
printf '\n'
printf '\033[0m'


# =========================
# COMPLETE
# =========================

echo ""
scanline_effect
printf '\033[0;32m'
typewriter "=========================================================" 0.005
printf '\n'
typewriter "              INSTALLATION COMPLETE" 0.005
printf '\n'
typewriter "=========================================================" 0.005
printf '\n'
printf '\033[0m'
scanline_effect

echo ""

printf '\033[0;32m'
typewriter "[SUCCESS] Dependencies Installed" 0.03
printf '\n'
typewriter "[SUCCESS] Application Directories Created" 0.03
printf '\n'
typewriter "[SUCCESS] WorkforceAI Ready" 0.03
printf '\n'
printf '\033[0m'

echo ""
echo "Default Login:"
echo "Username : admin"
echo "Password : admin123"
echo ""

printf '\033[0;35m'
typewriter "[LAUNCH] Preparing to start WorkforceAI..." 0.03
printf '\n'
printf '\033[0m'

echo ""

printf '\033[0;33m'
typewriter "Starting in 3..." 0.08
printf '\n'
sleep 0.5
typewriter "Starting in 2..." 0.08
printf '\n'
sleep 0.5
typewriter "Starting in 1..." 0.08
printf '\n'
sleep 0.5
printf '\033[0m'

echo ""
printf '\033[0;32m'
typewriter "[LAUNCH] Starting Application..." 0.03
printf '\n'
printf '\033[0m'
echo ""

python3 app.py
