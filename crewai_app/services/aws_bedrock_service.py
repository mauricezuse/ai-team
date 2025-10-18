import boto3
from typing import Dict, Any, List, Optional
from botocore.exceptions import ClientError, BotoCoreError
from crewai_app.providers.cloud_providers import AWSProviderError

class AWSBedrockService:
    """AWS Bedrock service for LLM operations"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.region = config.get('region', 'us-east-1')
        self.client = boto3.client(
            'bedrock-runtime',
            region_name=self.region,
            aws_access_key_id=config['credentials']['aws_access_key_id'],
            aws_secret_access_key=config['credentials']['aws_secret_access_key']
        )
        self.model_id = config.get('model_id', 'anthropic.claude-3-sonnet-20240229-v1:0')
    
    def generate_text(self, prompt: str, max_tokens: int = 1000) -> str:
        """Generate text using AWS Bedrock"""
        try:
            response = self.client.invoke_model(
                modelId=self.model_id,
                body={
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": max_tokens,
                    "messages": [{"role": "user", "content": prompt}]
                }
            )
            return response['body'].read().decode('utf-8')
        except (ClientError, BotoCoreError) as e:
            raise AWSProviderError(f"Bedrock text generation failed: {str(e)}")
    
    def get_available_models(self) -> List[str]:
        """Get list of available Bedrock models"""
        try:
            response = self.client.list_foundation_models()
            return [model['modelId'] for model in response['modelSummaries']]
        except (ClientError, BotoCoreError) as e:
            raise AWSProviderError(f"Failed to list Bedrock models: {str(e)}")
    
    def generate_text_with_parameters(self, prompt: str, max_tokens: int = 1000, 
                                    temperature: float = 0.7, top_p: float = 0.9) -> str:
        """Generate text with additional parameters"""
        try:
            response = self.client.invoke_model(
                modelId=self.model_id,
                body={
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                    "top_p": top_p,
                    "messages": [{"role": "user", "content": prompt}]
                }
            )
            return response['body'].read().decode('utf-8')
        except (ClientError, BotoCoreError) as e:
            raise AWSProviderError(f"Bedrock text generation with parameters failed: {str(e)}")
    
    def get_model_info(self, model_id: str) -> Dict[str, Any]:
        """Get information about a specific model"""
        try:
            response = self.client.get_foundation_model(modelIdentifier=model_id)
            return response['modelDetails']
        except (ClientError, BotoCoreError) as e:
            raise AWSProviderError(f"Failed to get model info: {str(e)}")
    
    def is_model_available(self, model_id: str) -> bool:
        """Check if a model is available in the current region"""
        try:
            available_models = self.get_available_models()
            return model_id in available_models
        except AWSProviderError:
            return False
