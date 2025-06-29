#!/bin/zsh

# === CONFIGURATION ===
SUBSCRIPTION="96f783d6-efe3-4f05-9353-746e66439033"  # <-- Set your subscription here
RESOURCE_GROUP="negishi-ai-prod"
LOCATION="eastus"  # Change if needed
OPENAI_RESOURCE="negishi-openai-prod"
ENV_FILE=".env"

# === MODEL ASSIGNMENTS (based on your Azure availability) ===
typeset -A MODEL_NAMES
MODEL_NAMES[DEVELOPER]="gpt-4.1"
MODEL_NAMES[REVIEWER]="gpt-4o"
MODEL_NAMES[ARCHITECT]="gpt-4.1"
MODEL_NAMES[PM]="gpt-35-turbo"
MODEL_NAMES[TESTER]="gpt-4o"

typeset -A MODEL_VERSIONS
MODEL_VERSIONS[DEVELOPER]="2025-04-14"
MODEL_VERSIONS[REVIEWER]="2024-08-06"
MODEL_VERSIONS[ARCHITECT]="2025-04-14"
MODEL_VERSIONS[PM]="0125"
MODEL_VERSIONS[TESTER]="2024-08-06"

typeset -A DEPLOYMENT_NAMES
DEPLOYMENT_NAMES[DEVELOPER]="developer-gpt-4.1"
DEPLOYMENT_NAMES[REVIEWER]="reviewer-gpt-4o"
DEPLOYMENT_NAMES[ARCHITECT]="architect-gpt-4.1"
DEPLOYMENT_NAMES[PM]="pm-gpt-35-turbo"
DEPLOYMENT_NAMES[TESTER]="tester-gpt-4o"

typeset -A MODEL_SKUS
MODEL_SKUS[DEVELOPER]="GlobalStandard"
MODEL_SKUS[REVIEWER]="GlobalStandard"
MODEL_SKUS[ARCHITECT]="GlobalStandard"
MODEL_SKUS[PM]="Standard"
MODEL_SKUS[TESTER]="GlobalStandard"

set -e

# Set subscription
echo "Setting subscription..."
az account set --subscription "$SUBSCRIPTION"

# Create resource group
echo "Creating resource group..."
az group create --name "$RESOURCE_GROUP" --location "$LOCATION"

# Create Azure OpenAI resource
echo "Creating Azure OpenAI resource..."
az cognitiveservices account create \
  --name "$OPENAI_RESOURCE" \
  --resource-group "$RESOURCE_GROUP" \
  --kind OpenAI \
  --sku S0 \
  --location "$LOCATION" \
  --yes

# Deploy models
echo "Deploying models..."
for role in DEVELOPER REVIEWER ARCHITECT PM TESTER; do
  echo "Deploying ${MODEL_NAMES[$role]} (version ${MODEL_VERSIONS[$role]}) for $role as ${DEPLOYMENT_NAMES[$role]} with SKU ${MODEL_SKUS[$role]} and capacity 1..."
  az cognitiveservices account deployment create \
    --resource-group "$RESOURCE_GROUP" \
    --name "$OPENAI_RESOURCE" \
    --deployment-name "${DEPLOYMENT_NAMES[$role]}" \
    --model-name "${MODEL_NAMES[$role]}" \
    --model-version "${MODEL_VERSIONS[$role]}" \
    --model-format OpenAI \
    --sku "${MODEL_SKUS[$role]}" \
    --sku-capacity 1
  sleep 2
done

# Output API keys and endpoint
API_KEY=$(az cognitiveservices account keys list \
  --name "$OPENAI_RESOURCE" \
  --resource-group "$RESOURCE_GROUP" \
  --query "key1" -o tsv)
ENDPOINT=$(az cognitiveservices account show \
  --name "$OPENAI_RESOURCE" \
  --resource-group "$RESOURCE_GROUP" \
  --query "properties.endpoint" -o tsv)

# Write to .env
echo "Writing to $ENV_FILE..."
cat > $ENV_FILE <<EOF
# Azure OpenAI Service
AZURE_OPENAI_API_KEY=$API_KEY
AZURE_OPENAI_ENDPOINT=$ENDPOINT
AZURE_OPENAI_DEPLOYMENT=${DEPLOYMENT_NAMES[DEVELOPER]}
AZURE_OPENAI_DEPLOYMENT_DEVELOPER=${DEPLOYMENT_NAMES[DEVELOPER]}
AZURE_OPENAI_DEPLOYMENT_REVIEWER=${DEPLOYMENT_NAMES[REVIEWER]}
AZURE_OPENAI_DEPLOYMENT_ARCHITECT=${DEPLOYMENT_NAMES[ARCHITECT]}
AZURE_OPENAI_DEPLOYMENT_PM=${DEPLOYMENT_NAMES[PM]}
AZURE_OPENAI_DEPLOYMENT_TESTER=${DEPLOYMENT_NAMES[TESTER]}

# Environment
ENVIRONMENT=production

# (Optional) GitHub Integration
GITHUB_TOKEN=your-github-token
GITHUB_REPO=your-org/your-repo

# (Optional) Jira Integration
JIRA_API_TOKEN=your-jira-api-token
JIRA_BASE_URL=https://your-domain.atlassian.net
JIRA_EMAIL=your-email@example.com
EOF

echo "\n=== Azure OpenAI API Key and Endpoint saved to $ENV_FILE ==="
echo "\nDeployment names used:"
for role in DEVELOPER REVIEWER ARCHITECT PM TESTER; do
  echo "  $role: "
  echo "    Model: ${MODEL_NAMES[$role]}"
  echo "    Version: ${MODEL_VERSIONS[$role]}"
  echo "    Deployment: ${DEPLOYMENT_NAMES[$role]}"
  echo "    SKU: ${MODEL_SKUS[$role]}"
  echo "    Capacity: 1"
done 