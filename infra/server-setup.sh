#!/usr/bin/env bash
# One-time setup of a fresh Ubuntu 24.04 VM (Oracle Cloud Always Free, ARM64) for Librachieve.
# Run as the default "ubuntu" user:  bash server-setup.sh
# Idempotent: safe to re-run.
set -euo pipefail

REPO_URL="${REPO_URL:-https://github.com/alvaro219/librachieve.git}"
APP_DIR="$HOME/librachieve"

echo "==> Docker"
if ! command -v docker >/dev/null; then
  curl -fsSL https://get.docker.com | sudo sh
  sudo usermod -aG docker "$USER"
fi

echo "==> Firewall: open 80/443 (Oracle's Ubuntu images REJECT everything but SSH by default)"
for port in 80 443; do
  if ! sudo iptables -C INPUT -p tcp --dport "$port" -j ACCEPT 2>/dev/null; then
    sudo iptables -I INPUT 5 -p tcp --dport "$port" -m state --state NEW -j ACCEPT
  fi
done
if ! sudo iptables -C INPUT -p udp --dport 443 -j ACCEPT 2>/dev/null; then
  sudo iptables -I INPUT 5 -p udp --dport 443 -j ACCEPT  # HTTP/3
fi
sudo apt-get install -y -qq iptables-persistent >/dev/null 2>&1 || true
sudo netfilter-persistent save >/dev/null

echo "==> Swap (2 GB) so image builds never run out of memory"
if ! swapon --show | grep -q /swapfile; then
  sudo fallocate -l 2G /swapfile && sudo chmod 600 /swapfile
  sudo mkswap /swapfile >/dev/null && sudo swapon /swapfile
  echo "/swapfile none swap sw 0 0" | sudo tee -a /etc/fstab >/dev/null
fi

echo "==> Automatic security updates"
sudo apt-get install -y -qq unattended-upgrades >/dev/null

echo "==> Code"
if [ ! -d "$APP_DIR/.git" ]; then
  git clone --depth 1 "$REPO_URL" "$APP_DIR"
fi

if [ ! -f "$APP_DIR/.env" ]; then
  echo "!! Missing $APP_DIR/.env (copy the production .env before starting the stack)"
else
  echo "==> .env present"
fi
echo "Done. Log out and back in once so the docker group applies."
