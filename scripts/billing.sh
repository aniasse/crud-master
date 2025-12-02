#!/bin/bash

set -e

echo "--- Provisioning Billing VM ---"

# Source environment variables from .env file in the synced /vagrant folder
export $(grep -v '^#' /vagrant/.env | xargs)

# --- Install PostgreSQL ---
echo "--- Installing PostgreSQL ---"
sudo apt-get update
sudo apt-get install -y postgresql postgresql-contrib

# --- Configure Billing Database (billing_db) ---
echo "--- Configuring Billing Database ---"
sudo -u postgres psql <<EOF
CREATE DATABASE ${BILLING_DB_NAME};
CREATE USER ${BILLING_DB_USER} WITH PASSWORD '${BILLING_DB_PASSWORD}';
GRANT ALL PRIVILEGES ON DATABASE ${BILLING_DB_NAME} TO ${BILLING_DB_USER};
EOF

# --- Install RabbitMQ ---
echo "--- Installing RabbitMQ Server ---"
sudo apt-get install -y rabbitmq-server
# Enable RabbitMQ Management Plugin
sudo rabbitmq-plugins enable rabbitmq_management

# --- Configure RabbitMQ ---
echo "--- Configuring RabbitMQ ---"
# Add user
sudo rabbitmqctl add_user ${RABBITMQ_USER} ${RABBITMQ_PASSWORD} || echo "User already exists."
# Set user tags to enable management UI access
sudo rabbitmqctl set_user_tags ${RABBITMQ_USER} administrator
# Add vhost
sudo rabbitmqctl add_vhost ${RABBITMQ_VHOST} || echo "Vhost already exists."
# Set user permissions for the vhost
sudo rabbitmqctl set_permissions -p ${RABBITMQ_VHOST} ${RABBITMQ_USER} ".*" ".*" ".*"

# Install Python dependencies
echo "--- Installing Python dependencies for Billing App ---"
pip3 install -r /home/vagrant/billing-app/requirements.txt

# Start the Billing Consumer with PM2
echo "--- Starting Billing Consumer with PM2 ---"
cd /home/vagrant/billing-app
pm2 start --name billing-consumer "python3 consumer.py"
pm2 save

echo "--- Billing VM provisioning complete ---"
