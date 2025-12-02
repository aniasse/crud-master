# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure("2") do |config|
  # Inject environment variables from .env file
  if File.exist?(".env")
    File.readlines(".env").each do |line|
      line.strip!
      if (line.length > 0 && !line.start_with?('#'))
        key, value = line.split('=', 2)
        ENV[key] = value
      end
    end
  end

  # Default Ubuntu box
  config.vm.box = "ubuntu/jammy64"

  # Common provisioning script
  config.vm.provision "shell", path: "scripts/common.sh"

  # API Gateway VM
  config.vm.define "gateway-vm" do |gateway|
    gateway.vm.hostname = "gateway-vm"
    gateway.vm.network "private_network", ip: "192.168.56.10"
    gateway.vm.provision "shell", path: "scripts/gateway.sh"
    # Forward port 8080 on host to 8080 on guest to access the gateway from host
    gateway.vm.network "forwarded_port", guest: 8080, host: 8080
  end

  # Inventory Service VM
  config.vm.define "inventory-vm" do |inventory|
    inventory.vm.hostname = "inventory-vm"
    inventory.vm.network "private_network", ip: ENV['INVENTORY_VM_IP'] || "192.168.56.11"
    inventory.vm.provision "shell", path: "scripts/inventory.sh"
  end

  # Billing Service VM
  config.vm.define "billing-vm" do |billing|
    billing.vm.hostname = "billing-vm"
    billing.vm.network "private_network", ip: ENV['BILLING_VM_IP'] || "192.168.56.12"
    billing.vm.provision "shell", path: "scripts/billing.sh"
    # Forward RabbitMQ management UI port
    billing.vm.network "forwarded_port", guest: 15672, host: 15672
  end

  # Synced folders for application code
  config.vm.synced_folder "srcs/api-gateway", "/home/vagrant/api-gateway"
  config.vm.synced_folder "srcs/inventory-app", "/home/vagrant/inventory-app"
  config.vm.synced_folder "srcs/billing-app", "/home/vagrant/billing-app"

  # Increase VM memory
  config.vm.provider "virtualbox" do |vb|
    vb.memory = "1024"
  end
end