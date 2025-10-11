# Azure Database for MySQL - Flexible Server
terraform {
  required_version = ">= 1.0"
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
  }
  
  backend "azurerm" {
    resource_group_name  = "minions-rg"
    storage_account_name = "minionsterraform"
    container_name       = "tfstate"
    key                  = "mysql.tfstate"
  }
}

provider "azurerm" {
  features {}
}

# Resource Group
resource "azurerm_resource_group" "ai_team" {
  name     = "minions-rg"
  location = "West US 2"
  
  tags = {
    Environment = "Production"
    Project     = "AI Team"
  }
}

# Virtual Network
resource "azurerm_virtual_network" "ai_team" {
  name                = "ai-team-vnet"
  address_space       = ["10.0.0.0/16"]
  location            = azurerm_resource_group.ai_team.location
  resource_group_name = azurerm_resource_group.ai_team.name
}

# Subnet for MySQL
resource "azurerm_subnet" "mysql" {
  name                 = "mysql-subnet"
  resource_group_name  = azurerm_resource_group.ai_team.name
  virtual_network_name = azurerm_virtual_network.ai_team.name
  address_prefixes     = ["10.0.1.0/24"]
  
  delegation {
    name = "mysql-delegation"
    service_delegation {
      name = "Microsoft.DBforMySQL/flexibleServers"
      actions = [
        "Microsoft.Network/virtualNetworks/subnets/join/action",
      ]
    }
  }
}

# MySQL Flexible Server
resource "azurerm_mysql_flexible_server" "ai_team" {
  name                   = "ai-team-mysql-${random_string.suffix.result}"
  resource_group_name    = azurerm_resource_group.ai_team.name
  location              = azurerm_resource_group.ai_team.location
  administrator_login   = var.mysql_admin_username
  administrator_password = var.mysql_admin_password
  backup_retention_days  = 7
  geo_redundant_backup_enabled = false
  sku_name              = "GP_Standard_D2ds_v4"
  version               = "8.0.21"
  # zone                  = "1"  # Commented out - let Azure choose available zone
  
  storage {
    auto_grow_enabled  = true
    iops               = 360
    size_gb            = 20
  }
  
  high_availability {
    mode = "SameZone"
  }
  
  maintenance_window {
    day_of_week  = 0
    start_hour    = 8
    start_minute  = 0
  }
  
  depends_on = [azurerm_subnet.mysql]
}

# MySQL Database
resource "azurerm_mysql_flexible_database" "ai_team" {
  name                = "ai_team"
  resource_group_name = azurerm_resource_group.ai_team.name
  server_name        = azurerm_mysql_flexible_server.ai_team.name
  charset            = "utf8"
  collation          = "utf8_unicode_ci"
}

# MySQL Firewall Rule - Allow Azure Services
resource "azurerm_mysql_flexible_server_firewall_rule" "azure_services" {
  name                = "AllowAzureServices"
  resource_group_name = azurerm_resource_group.ai_team.name
  server_name        = azurerm_mysql_flexible_server.ai_team.name
  start_ip_address   = "0.0.0.0"
  end_ip_address     = "0.0.0.0"
}

# MySQL Firewall Rule - Allow All (for development)
resource "azurerm_mysql_flexible_server_firewall_rule" "allow_all" {
  name                = "AllowAll"
  resource_group_name = azurerm_resource_group.ai_team.name
  server_name        = azurerm_mysql_flexible_server.ai_team.name
  start_ip_address   = "0.0.0.0"
  end_ip_address     = "255.255.255.255"
}

# Random string for unique naming
resource "random_string" "suffix" {
  length  = 8
  special = false
  upper   = false
}

# Outputs are defined in outputs.tf
