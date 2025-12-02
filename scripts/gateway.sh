#!/bin/bash

set -e

echo "--- Provisioning API Gateway VM ---"

# Install Python dependencies
echo "--- Installing Python dependencies for API Gateway ---"
pip3 install -r /home/vagrant/api-gateway/requirements.txt

# Start the API Gateway with PM2
echo "--- Starting API Gateway with PM2 ---"
cd /home/vagrant/api-gateway
pm2 start --name api-gateway "python3 app.py"
pm2 save

echo "--- API Gateway VM provisioning complete ---"
