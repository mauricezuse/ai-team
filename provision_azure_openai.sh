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
MODEL_NAMES[FRONTEND]="gpt-4.1"

typeset -A MODEL_VERSIONS
MODEL_VERSIONS[DEVELOPER]="2025-04-14"
MODEL_VERSIONS[REVIEWER]="2024-08-06"
MODEL_VERSIONS[ARCHITECT]="2025-04-14"
MODEL_VERSIONS[PM]="0125"
MODEL_VERSIONS[TESTER]="2024-08-06"
MODEL_VERSIONS[FRONTEND]="2025-04-14"

typeset -A DEPLOYMENT_NAMES
DEPLOYMENT_NAMES[DEVELOPER]="developer-gpt-4.1"
DEPLOYMENT_NAMES[REVIEWER]="reviewer-gpt-4o"
DEPLOYMENT_NAMES[ARCHITECT]="architect-gpt-4.1"
DEPLOYMENT_NAMES[PM]="pm-gpt-35-turbo"
DEPLOYMENT_NAMES[TESTER]="tester-gpt-4o"
DEPLOYMENT_NAMES[FRONTEND]="frontend-gpt-4.1"

typeset -A MODEL_SKUS
MODEL_SKUS[DEVELOPER]="GlobalStandard"
MODEL_SKUS[REVIEWER]="GlobalStandard"
MODEL_SKUS[ARCHITECT]="GlobalStandard"
MODEL_SKUS[PM]="Standard"
MODEL_SKUS[TESTER]="GlobalStandard"
MODEL_SKUS[FRONTEND]="GlobalStandard"

# Architect deployments for load balancing
ARCHITECT_DEPLOYMENTS=("architect-gpt-4.1-a" "architect-gpt-4.1-b" "architect-gpt-4.1-c")

# Embedding model config
EMBEDDING_MODEL_NAME="text-embedding-ada-002"
EMBEDDING_MODEL_VERSION="2"
EMBEDDING_DEPLOYMENT_NAME="text-embedding-ada-002"
EMBEDDING_MODEL_SKU="Standard"

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

# Deploy models (idempotent, supports multiple architect deployments)
echo "Deploying models..."
for role in DEVELOPER REVIEWER PM TESTER FRONTEND; do
  DEPLOYMENT_NAME="${DEPLOYMENT_NAMES[$role]}"
  echo "Checking if deployment $DEPLOYMENT_NAME exists..."
  STATE=$(az cognitiveservices account deployment show \
    --resource-group "$RESOURCE_GROUP" \
    --name "$OPENAI_RESOURCE" \
    --deployment-name "$DEPLOYMENT_NAME" \
    --query "properties.provisioningState" -o tsv 2>/dev/null || true)
  if [[ "$STATE" == "Succeeded" ]]; then
    echo "Deployment $DEPLOYMENT_NAME already exists. Skipping."
  else
    echo "Deploying ${MODEL_NAMES[$role]} (version ${MODEL_VERSIONS[$role]}) for $role as $DEPLOYMENT_NAME with SKU ${MODEL_SKUS[$role]} and capacity 1..."
    az cognitiveservices account deployment create \
      --resource-group "$RESOURCE_GROUP" \
      --name "$OPENAI_RESOURCE" \
      --deployment-name "$DEPLOYMENT_NAME" \
      --model-name "${MODEL_NAMES[$role]}" \
      --model-version "${MODEL_VERSIONS[$role]}" \
      --model-format OpenAI \
      --sku "${MODEL_SKUS[$role]}" \
      --sku-capacity 1
    sleep 2
  fi
done
# Architect role: deploy multiple for load balancing
for DEPLOYMENT_NAME in "${ARCHITECT_DEPLOYMENTS[@]}"; do
  echo "Checking if architect deployment $DEPLOYMENT_NAME exists..."
  STATE=$(az cognitiveservices account deployment show \
    --resource-group "$RESOURCE_GROUP" \
    --name "$OPENAI_RESOURCE" \
    --deployment-name "$DEPLOYMENT_NAME" \
    --query "properties.provisioningState" -o tsv 2>/dev/null || true)
  if [[ "$STATE" == "Succeeded" ]]; then
    echo "Architect deployment $DEPLOYMENT_NAME already exists. Skipping."
  else
    echo "Deploying architect-gpt-4.1 as $DEPLOYMENT_NAME with SKU GlobalStandard and capacity 1..."
    az cognitiveservices account deployment create \
      --resource-group "$RESOURCE_GROUP" \
      --name "$OPENAI_RESOURCE" \
      --deployment-name "$DEPLOYMENT_NAME" \
      --model-name "gpt-4.1" \
      --model-version "2025-04-14" \
      --model-format OpenAI \
      --sku "GlobalStandard" \
      --sku-capacity 1
    sleep 2
  fi
done

# Embedding model deployment
echo "Checking if embedding deployment $EMBEDDING_DEPLOYMENT_NAME exists..."
STATE=$(az cognitiveservices account deployment show \
  --resource-group "$RESOURCE_GROUP" \
  --name "$OPENAI_RESOURCE" \
  --deployment-name "$EMBEDDING_DEPLOYMENT_NAME" \
  --query "properties.provisioningState" -o tsv 2>/dev/null || true)
if [[ "$STATE" == "Succeeded" ]]; then
  echo "Embedding deployment $EMBEDDING_DEPLOYMENT_NAME already exists. Skipping."
else
  echo "Deploying $EMBEDDING_MODEL_NAME (version $EMBEDDING_MODEL_VERSION) as $EMBEDDING_DEPLOYMENT_NAME with SKU $EMBEDDING_MODEL_SKU and capacity 1..."
  az cognitiveservices account deployment create \
    --resource-group "$RESOURCE_GROUP" \
    --name "$OPENAI_RESOURCE" \
    --deployment-name "$EMBEDDING_DEPLOYMENT_NAME" \
    --model-name "$EMBEDDING_MODEL_NAME" \
    --model-version "$EMBEDDING_MODEL_VERSION" \
    --model-format OpenAI \
    --sku "$EMBEDDING_MODEL_SKU" \
    --sku-capacity 1
  sleep 2
fi

# Output API keys and endpoint
API_KEY=$(az cognitiveservices account keys list \
  --name "$OPENAI_RESOURCE" \
  --resource-group "$RESOURCE_GROUP" \
  --query "key1" -o tsv)
ENDPOINT=$(az cognitiveservices account show \
  --name "$OPENAI_RESOURCE" \
  --resource-group "$RESOURCE_GROUP" \
  --query "properties.endpoint" -o tsv)

# Reminder for the user
echo "\n=== Azure OpenAI API Key: $API_KEY ==="
echo "=== Azure OpenAI Endpoint: $ENDPOINT ==="
echo "\nPlease manually update your .env file with the following values:"
echo "AZURE_OPENAI_API_KEY=$API_KEY"
echo "AZURE_OPENAI_ENDPOINT=$ENDPOINT"
echo "AZURE_OPENAI_DEPLOYMENT_ARCHITECT=$(IFS=, ; echo "${ARCHITECT_DEPLOYMENTS[*]}")"
echo "AZURE_OPENAI_DEPLOYMENT_DEVELOPER=${DEPLOYMENT_NAMES[DEVELOPER]}"
echo "AZURE_OPENAI_DEPLOYMENT_REVIEWER=${DEPLOYMENT_NAMES[REVIEWER]}"
echo "AZURE_OPENAI_DEPLOYMENT_PM=${DEPLOYMENT_NAMES[PM]}"
echo "AZURE_OPENAI_DEPLOYMENT_TESTER=${DEPLOYMENT_NAMES[TESTER]}"
echo "AZURE_OPENAI_DEPLOYMENT_FRONTEND=${DEPLOYMENT_NAMES[FRONTEND]}"
echo "\nOther environment variables (GitHub, Jira, etc.) should also be set as needed."

echo "\nDeployment names used:"
for role in DEVELOPER REVIEWER ARCHITECT PM TESTER FRONTEND; do
  echo "  $role: "
  echo "    Model: ${MODEL_NAMES[$role]}"
  echo "    Version: ${MODEL_VERSIONS[$role]}"
  echo "    Deployment: ${DEPLOYMENT_NAMES[$role]}"
  echo "    SKU: ${MODEL_SKUS[$role]}"
  echo "    Capacity: 1"
done 