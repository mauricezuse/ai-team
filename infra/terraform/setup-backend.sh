#!/bin/bash

# Setup Azure Storage Account for Terraform Remote State
# This script creates the storage account and container needed for remote state

set -e

echo "🔧 Setting up Azure Storage Account for Terraform Remote State..."

# Variables
RESOURCE_GROUP="minions-rg"
STORAGE_ACCOUNT="minionsterraform"
CONTAINER_NAME="tfstate"
LOCATION="West US 2"

# Check if resource group exists
if ! az group show --name $RESOURCE_GROUP &> /dev/null; then
    echo "📦 Creating resource group: $RESOURCE_GROUP"
    az group create --name $RESOURCE_GROUP --location "$LOCATION"
else
    echo "✅ Resource group $RESOURCE_GROUP already exists"
fi

# Check if storage account exists
if ! az storage account show --name $STORAGE_ACCOUNT --resource-group $RESOURCE_GROUP &> /dev/null; then
    echo "💾 Creating storage account: $STORAGE_ACCOUNT"
    az storage account create \
        --name $STORAGE_ACCOUNT \
        --resource-group $RESOURCE_GROUP \
        --location "$LOCATION" \
        --sku Standard_LRS \
        --kind StorageV2
else
    echo "✅ Storage account $STORAGE_ACCOUNT already exists"
fi

# Get storage account key
echo "🔑 Getting storage account key..."
STORAGE_KEY=$(az storage account keys list \
    --resource-group $RESOURCE_GROUP \
    --account-name $STORAGE_ACCOUNT \
    --query '[0].value' \
    --output tsv)

# Check if container exists
if ! az storage container show --name $CONTAINER_NAME --account-name $STORAGE_ACCOUNT --account-key $STORAGE_KEY &> /dev/null; then
    echo "📁 Creating container: $CONTAINER_NAME"
    az storage container create \
        --name $CONTAINER_NAME \
        --account-name $STORAGE_ACCOUNT \
        --account-key $STORAGE_KEY
else
    echo "✅ Container $CONTAINER_NAME already exists"
fi

echo ""
echo "✅ Remote state backend setup complete!"
echo ""
echo "📋 Backend Configuration:"
echo "   Resource Group: $RESOURCE_GROUP"
echo "   Storage Account: $STORAGE_ACCOUNT"
echo "   Container: $CONTAINER_NAME"
echo "   Location: $LOCATION"
echo ""
echo "🔧 Next steps:"
echo "   1. Run 'terraform init' to initialize with remote state"
echo "   2. Run 'terraform plan' to review the deployment"
echo "   3. Run 'terraform apply' to deploy the MySQL database"
