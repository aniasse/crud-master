#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

echo "--- Provisioning common dependencies ---"

# Fix any potential dpkg issues and install dependencies
sudo dpkg --configure -a
sudo apt-get update
sudo apt-get install -f -y

# Remove old Node.js versions and conflicting packages to prevent conflicts
echo "--- Removing old Node.js packages ---"
sudo apt-get purge -y nodejs npm libnode-dev || true
sudo apt-get autoremove -y || true

# Update package list and install basic dependencies
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y python3-pip git curl

# Install Node.js v20.x and npm
echo "--- Installing Node.js v20 ---"
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y nodejs

# Install PM2 for process management
echo "--- Installing PM2 ---"
sudo npm install -g pm2
# Set PM2 to start on boot
echo "--- Configuring PM2 to start on boot ---"
sudo env PATH=$PATH:/usr/bin /usr/lib/node_modules/pm2/bin/pm2 startup systemd -u vagrant --hp /home/vagrant

echo "--- Common provisioning complete ---"
