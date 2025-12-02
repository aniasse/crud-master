#!/bin/bash

set -e

echo "--- Provisioning Inventory VM ---"

# Source environment variables
export $(grep -v '^#' /vagrant/.env | xargs)

# Install PostgreSQL
echo "--- Installing PostgreSQL ---"
sudo apt-get update
sudo apt-get install -y postgresql postgresql-contrib

# Create PostgreSQL user and database
echo "--- Configuring Inventory Database (movies_db) ---"
sudo -u postgres psql <<EOF
CREATE DATABASE ${INVENTORY_DB_NAME};
CREATE USER ${INVENTORY_DB_USER} WITH PASSWORD '${INVENTORY_DB_PASSWORD}';
ALTER ROLE ${INVENTORY_DB_USER} SET client_encoding TO 'utf8';
ALTER ROLE ${INVENTORY_DB_USER} SET default_transaction_isolation TO 'read committed';
ALTER ROLE ${INVENTORY_DB_USER} SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE ${INVENTORY_DB_NAME} TO ${INVENTORY_DB_USER};
EOF

# Install Python dependencies
echo "--- Installing Python dependencies for Inventory App ---"
pip3 install --no-cache-dir -r /home/vagrant/inventory-app/requirements.txt

# Start the Inventory API with PM2
echo "--- Starting Inventory App with PM2 ---"
cd /home/vagrant/inventory-app
pm2 start --name inventory-api "python3 app.py"
pm2 save

echo "--- Inventory VM provisioning complete ---"
