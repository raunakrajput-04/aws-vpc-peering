#!/usr/bin/env bash
# Automated SSH Configuration Script for Linux / macOS / WSL
# Configures ~/.ssh/config for Bastion Host & ProxyJump access.

set -e

if [ -z "$1" ]; then
    echo "Usage: ./setup_ssh_config.sh <BASTION_PUBLIC_IP> [PATH_TO_PEM_KEY]"
    echo "Example: ./setup_ssh_config.sh 13.232.45.10 ~/.ssh/ewb-lab.pem"
    exit 1
fi

BASTION_IP="$1"
KEY_PATH="${2:-$HOME/.ssh/ewb-lab.pem}"

mkdir -p "$HOME/.ssh"
chmod 700 "$HOME/.ssh"

if [ -f "$KEY_PATH" ]; then
    chmod 400 "$KEY_PATH"
    echo "[✓] Set permissions 400 on $KEY_PATH"
fi

CONFIG_FILE="$HOME/.ssh/config"

cat <<EOF >> "$CONFIG_FILE"

# ==========================================
# EWB AWS VPC Peering Lab Configuration
# ==========================================
Host ewb-bastion
    HostName $BASTION_IP
    User ec2-user
    IdentityFile $KEY_PATH
    IdentitiesOnly yes

Host ewb-app-a
    HostName 10.10.2.10
    User ec2-user
    IdentityFile $KEY_PATH
    IdentitiesOnly yes
    ProxyJump ewb-bastion

Host ewb-app-b
    HostName 10.20.1.10
    User ec2-user
    IdentityFile $KEY_PATH
    IdentitiesOnly yes
    ProxyJump ewb-bastion
# ==========================================
EOF

chmod 600 "$CONFIG_FILE"
echo "[✓] Successfully updated $CONFIG_FILE"
echo ""
echo "Test connection with:"
echo "  ssh ewb-bastion"
echo "  ssh ewb-app-a"
echo "  ssh ewb-app-b"
