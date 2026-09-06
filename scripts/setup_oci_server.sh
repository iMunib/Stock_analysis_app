#!/usr/bin/env bash
# =============================================================================
# OCI Ubuntu 24.04 Bootstrap — Investment Stock Application
# VM.Standard.E2.1.Micro (AMD64, 1 OCPU, 1 GB RAM, 50 GB boot)
# Idempotent one-shot setup: swap + Docker + firewall + app directories.
# Run as:  chmod +x scripts/setup_oci_server.sh && ./scripts/setup_oci_server.sh
# =============================================================================
set -euo pipefail

echo "=== [1/5] 4 GB Swap Setup (critical for 1 GB RAM) ==="
if [ -f /swapfile ]; then
  echo "Swapfile already exists — skipping creation."
  sudo swapon --show | grep -q "/swapfile" || sudo swapon /swapfile || true
else
  echo "Creating 4 GB swapfile at /swapfile ..."
  sudo fallocate -l 4G /swapfile
  sudo chmod 600 /swapfile
  sudo mkswap /swapfile
  sudo swapon /swapfile
  echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
  echo "Swapfile created and enabled."
fi
# Tune swappiness for low-RAM host — prefer RAM, spill only under pressure.
sudo sysctl vm.swappiness=10
# Persist swappiness across reboots.
if grep -q "^vm.swappiness" /etc/sysctl.conf 2>/dev/null; then
  sudo sed -i 's/^vm.swappiness.*/vm.swappiness=10/' /etc/sysctl.conf
else
  echo 'vm.swappiness=10' | sudo tee -a /etc/sysctl.conf
fi
sudo swapon --show || true
free -h || true
echo ""

echo "=== [2/5] Package Updates & Prerequisites ==="
sudo apt-get update -y
sudo apt-get install -y ca-certificates curl gnupg git ufw iptables-persistent
echo ""

echo "=== [3/5] Docker Engine + Compose Plugin (official get.docker.com) ==="
if command -v docker >/dev/null 2>&1; then
  echo "Docker already installed: $(docker --version)"
else
  curl -fsSL https://get.docker.com -o get-docker.sh
  sudo sh get-docker.sh
  rm -f get-docker.sh
  echo "Docker installed: $(docker --version)"
fi
# Ensure Compose plugin is available (bundled with get.docker.com, verify)
docker compose version || echo "WARNING: docker compose plugin not found"

# Add ubuntu user to docker group (idempotent — no error if already member)
if id -nG ubuntu 2>/dev/null | grep -qw docker; then
  echo "User 'ubuntu' already in docker group."
else
  sudo usermod -aG docker ubuntu
  echo "Added 'ubuntu' to docker group (re-login or 'newgrp docker' required)."
fi
# Also handle current user if not ubuntu (e.g., opc)
CURRENT_USER="$(whoami)"
if [ "$CURRENT_USER" != "ubuntu" ] && ! id -nG "$CURRENT_USER" | grep -qw docker 2>/dev/null; then
  sudo usermod -aG docker "$CURRENT_USER" || true
fi
echo ""

echo "=== [4/5] Oracle Internal OS Firewall Unlock ==="
# Oracle Cloud Ubuntu images ship restrictive iptables INPUT chain that blocks
# 80/443/5173/8000 by default. Insert ACCEPT before the REJECT rule.
# Insert at position 6 is conventional for Oracle images; fall back gracefully.
echo "Inserting iptables ACCEPT for 80,443,5173,8000 ..."
if sudo iptables -C INPUT -m state --state NEW -p tcp -m multiport --dports 80,443,5173,8000 -j ACCEPT 2>/dev/null; then
  echo "iptables ACCEPT rule already present — skipping."
else
  # Try position 6 first (Oracle default), fall back to top if chain shorter.
  sudo iptables -I INPUT 6 -m state --state NEW -p tcp -m multiport --dports 80,443,5173,8000 -j ACCEPT 2>/dev/null \
    || sudo iptables -I INPUT 1 -m state --state NEW -p tcp -m multiport --dports 80,443,5173,8000 -j ACCEPT
  echo "iptables rule inserted."
fi
sudo iptables -L INPUT -v -n --line-numbers | head -n 20 || true
# Persist across reboots
sudo netfilter-persistent save || sudo iptables-save | sudo tee /etc/iptables/rules.v4 >/dev/null || true
echo "iptables rules persisted."

echo "Configuring UFW ..."
sudo ufw allow 22/tcp  || true
sudo ufw allow 80/tcp  || true
sudo ufw allow 443/tcp || true
sudo ufw allow 5173/tcp || true
sudo ufw allow 8000/tcp || true
sudo ufw --force enable
sudo ufw status verbose || true
echo ""

echo "=== [5/5] Application Directory Initialization ==="
mkdir -p /home/ubuntu/app/data /home/ubuntu/app/data/backups
# Also ensure current-user path if different from ubuntu
if [ "$HOME" != "/home/ubuntu" ]; then
  mkdir -p "$HOME/app/data" "$HOME/app/data/backups" || true
fi
echo "Directories ready:"
ls -ld /home/ubuntu/app/data /home/ubuntu/app/data/backups 2>/dev/null || true
echo ""

echo "=== Bootstrap complete ==="
echo "  Swap:      $(free -h | awk '/Swap:/{print $2}')"
echo "  Docker:    $(docker --version 2>/dev/null || echo 'pending relogin')"
echo "  Compose:   $(docker compose version 2>/dev/null || echo 'pending')"
echo "  UFW:       $(sudo ufw status | head -n1)"
echo "  App dir:   /home/ubuntu/app/data (+ backups/)"
echo ""
echo "Next: clone repo into /home/ubuntu/app and deploy:"
echo "  cd /home/ubuntu/app && git clone https://github.com/iMunib/Stock_analysis_app.git . || (git fetch origin main && git reset --hard origin/main)"
echo "  docker compose --profile frontend up --build -d"
