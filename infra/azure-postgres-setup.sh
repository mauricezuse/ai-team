#!/bin/bash

# Azure Database for PostgreSQL Setup Script
# This script creates a PostgreSQL database in Azure for the AI Team project

set -e

# Configuration
RESOURCE_GROUP="ai-team-rg"
LOCATION="East US"
SERVER_NAME="ai-team-postgres-$(date +%s)"
ADMIN_USER="ai_team_admin"
ADMIN_PASSWORD="$(openssl rand -base64 32)"
DATABASE_NAME="ai_team_db"

echo "🚀 Setting up Azure Database for PostgreSQL for AI Team project..."

# Create resource group
echo "📦 Creating resource group: $RESOURCE_GROUP"
az group create \
    --name $RESOURCE_GROUP \
    --location "$LOCATION"

# Create PostgreSQL server
echo "🗄️ Creating PostgreSQL server: $SERVER_NAME"
az postgres flexible-server create \
    --resource-group $RESOURCE_GROUP \
    --name $SERVER_NAME \
    --location "$LOCATION" \
    --admin-user $ADMIN_USER \
    --admin-password "$ADMIN_PASSWORD" \
    --sku-name Standard_B1ms \
    --tier Burstable \
    --public-access 0.0.0.0 \
    --storage-size 32 \
    --version 15

# Create database
echo "📊 Creating database: $DATABASE_NAME"
az postgres flexible-server db create \
    --resource-group $RESOURCE_GROUP \
    --server-name $SERVER_NAME \
    --database-name $DATABASE_NAME

# Configure firewall rules
echo "🔥 Configuring firewall rules..."
az postgres flexible-server firewall-rule create \
    --resource-group $RESOURCE_GROUP \
    --name $SERVER_NAME \
    --rule-name "AllowAzureServices" \
    --start-ip-address 0.0.0.0 \
    --end-ip-address 0.0.0.0

# Get connection details
echo "🔗 Getting connection details..."
SERVER_FQDN=$(az postgres flexible-server show \
    --resource-group $RESOURCE_GROUP \
    --name $SERVER_NAME \
    --query "fullyQualifiedDomainName" \
    --output tsv)

echo ""
echo "✅ Azure Database for PostgreSQL setup complete!"
echo ""
echo "📋 Connection Details:"
echo "   Server: $SERVER_FQDN"
echo "   Database: $DATABASE_NAME"
echo "   Username: $ADMIN_USER"
echo "   Password: $ADMIN_PASSWORD"
echo ""
echo "🔧 Connection String:"
echo "   postgresql://$ADMIN_USER:$ADMIN_PASSWORD@$SERVER_FQDN:5432/$DATABASE_NAME"
echo ""
echo "⚠️  IMPORTANT: Save these credentials securely!"
echo "   Add them to your .env file as:"
echo "   DATABASE_URL=postgresql://$ADMIN_USER:$ADMIN_PASSWORD@$SERVER_FQDN:5432/$DATABASE_NAME"
echo ""
echo "🔧 Next steps:"
echo "   1. Update your .env file with the DATABASE_URL"
echo "   2. Install psycopg2: pip install psycopg2-binary"
echo "   3. Run database migrations"
echo "   4. Test the connection"
