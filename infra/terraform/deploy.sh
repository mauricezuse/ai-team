#!/bin/bash

# Azure Database for MySQL Deployment Script
# This script deploys the MySQL database infrastructure using Terraform

set -e

echo "🚀 Starting Azure Database for MySQL deployment..."

# Check prerequisites
echo "📋 Checking prerequisites..."

# Check if Azure CLI is installed
if ! command -v az &> /dev/null; then
    echo "❌ Azure CLI is not installed. Please install it first."
    echo "   Visit: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli"
    exit 1
fi

# Check if Terraform is installed
if ! command -v terraform &> /dev/null; then
    echo "❌ Terraform is not installed. Please install it first."
    echo "   Visit: https://www.terraform.io/downloads"
    exit 1
fi

# Check if user is logged in to Azure
if ! az account show &> /dev/null; then
    echo "❌ Not logged in to Azure. Please run 'az login' first."
    exit 1
fi

echo "✅ Prerequisites check passed!"

# Check if terraform.tfvars exists
if [ ! -f "terraform.tfvars" ]; then
    echo "📝 Creating terraform.tfvars from example..."
    cp terraform.tfvars.example terraform.tfvars
    echo "⚠️  Please edit terraform.tfvars with your configuration before continuing."
    echo "   Especially update the mysql_admin_password!"
    read -p "Press Enter to continue after editing terraform.tfvars..."
fi

# Initialize Terraform
echo "🔧 Initializing Terraform..."
terraform init

# Plan the deployment
echo "📋 Planning deployment..."
terraform plan -out=tfplan

# Ask for confirmation
echo ""
echo "🔍 Review the plan above. This will create:"
echo "   - Resource Group: ai-team-rg"
echo "   - Virtual Network and Subnet"
echo "   - MySQL Flexible Server"
echo "   - Database: ai_team"
echo "   - Firewall rules"
echo ""
read -p "Do you want to proceed with the deployment? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Deployment cancelled."
    exit 1
fi

# Apply the configuration
echo "🚀 Deploying infrastructure..."
terraform apply tfplan

# Get outputs
echo ""
echo "✅ Deployment completed successfully!"
echo ""
echo "📊 Deployment Summary:"
echo "====================="

# Display key outputs
echo "MySQL Server Name: $(terraform output -raw mysql_server_name)"
echo "MySQL Server FQDN: $(terraform output -raw mysql_server_fqdn)"
echo "Database Name: $(terraform output -raw mysql_database_name)"
echo "Resource Group: $(terraform output -raw resource_group_name)"
echo "Location: $(terraform output -raw location)"

echo ""
echo "🔗 Connection Information:"
echo "========================="
echo "Host: $(terraform output -raw mysql_server_fqdn)"
echo "Port: 3306"
echo "Database: $(terraform output -raw mysql_database_name)"
echo "Username: $(terraform output -raw mysql_admin_username)"

echo ""
echo "📝 Next Steps:"
echo "=============="
echo "1. Update your application's DATABASE_URL environment variable"
echo "2. Install PyMySQL: pip install PyMySQL"
echo "3. Update your database configuration in crewai_app/database.py"
echo "4. Run database migrations"
echo ""
echo "🔧 Connection String Format:"
echo "mysql://username:password@host:port/database"
echo ""
echo "⚠️  Remember to:"
echo "   - Keep your credentials secure"
echo "   - Configure firewall rules for production"
echo "   - Enable monitoring and alerting"
echo "   - Set up automated backups"
echo ""
echo "🎉 MySQL database is ready for use!"
