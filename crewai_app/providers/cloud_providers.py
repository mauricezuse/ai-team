from abc import ABC, abstractmethod
from typing import Dict, Any
from enum import Enum


class CloudProviderType(Enum):
    AZURE = "azure"
    AWS = "aws"


class CloudProviderError(Exception):
    """Base exception for cloud provider errors"""
    pass


class AzureProviderError(CloudProviderError):
    """Azure-specific provider errors"""
    pass


class AWSProviderError(CloudProviderError):
    """AWS-specific provider errors"""
    pass


class ConfigurationError(CloudProviderError):
    """Configuration-related errors"""
    pass


class CloudProvider(ABC):
    """Abstract base class for cloud provider implementations"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.provider_type = self._get_provider_type()
        self._validate_config()
    
    @abstractmethod
    def _get_provider_type(self) -> CloudProviderType:
        """Return the provider type"""
        pass
    
    @abstractmethod
    def _validate_config(self) -> None:
        """Validate provider-specific configuration"""
        pass
    
    @abstractmethod
    def get_llm_endpoint(self) -> str:
        """Get LLM endpoint URL"""
        pass
    
    @abstractmethod
    def get_vector_store_endpoint(self) -> str:
        """Get vector store endpoint URL"""
        pass
    
    @abstractmethod
    def get_database_endpoint(self) -> str:
        """Get database endpoint URL"""
        pass
    
    @abstractmethod
    def get_messaging_endpoint(self) -> str:
        """Get messaging endpoint URL"""
        pass
    
    @abstractmethod
    def get_storage_endpoint(self) -> str:
        """Get storage endpoint URL"""
        pass
    
    def get_credentials(self) -> Dict[str, str]:
        """Get provider-specific credentials"""
        return self.config.get('credentials', {})
    
    def get_region(self) -> str:
        """Get provider region"""
        return self.config.get('region', 'us-east-1')


class AzureProvider(CloudProvider):
    """Azure cloud provider implementation"""
    
    def _get_provider_type(self) -> CloudProviderType:
        return CloudProviderType.AZURE
    
    def _validate_config(self) -> None:
        required_keys = ['subscription_id', 'resource_group', 'credentials']
        for key in required_keys:
            if key not in self.config:
                raise ConfigurationError(f"Missing required Azure config: {key}")
    
    def get_llm_endpoint(self) -> str:
        return f"https://{self.config['openai_resource_name']}.openai.azure.com/"
    
    def get_vector_store_endpoint(self) -> str:
        return f"https://{self.config['search_service_name']}.search.windows.net/"
    
    def get_database_endpoint(self) -> str:
        return f"https://{self.config['sql_server_name']}.database.windows.net/"
    
    def get_messaging_endpoint(self) -> str:
        return f"https://{self.config['service_bus_namespace']}.servicebus.windows.net/"
    
    def get_storage_endpoint(self) -> str:
        return f"https://{self.config['storage_account']}.blob.core.windows.net/"


class AWSProvider(CloudProvider):
    """AWS cloud provider implementation"""
    
    def _get_provider_type(self) -> CloudProviderType:
        return CloudProviderType.AWS
    
    def _validate_config(self) -> None:
        required_keys = ['region', 'credentials']
        for key in required_keys:
            if key not in self.config:
                raise ConfigurationError(f"Missing required AWS config: {key}")
    
    def get_llm_endpoint(self) -> str:
        return f"https://bedrock-runtime.{self.get_region()}.amazonaws.com/"
    
    def get_vector_store_endpoint(self) -> str:
        return f"https://{self.config.get('opensearch_domain', 'search-domain')}.{self.get_region()}.es.amazonaws.com/"
    
    def get_database_endpoint(self) -> str:
        return f"https://rds.{self.get_region()}.amazonaws.com/"
    
    def get_messaging_endpoint(self) -> str:
        return f"https://sqs.{self.get_region()}.amazonaws.com/"
    
    def get_storage_endpoint(self) -> str:
        return f"https://s3.{self.get_region()}.amazonaws.com/"


class CloudProviderManager:
    """Manages cloud provider detection and configuration"""
    
    @staticmethod
    def detect_provider(config: Dict[str, Any]) -> CloudProviderType:
        """Detect cloud provider from configuration"""
        if not config:
            raise ConfigurationError("Empty configuration provided")
        
        if 'subscription_id' in config and 'resource_group' in config:
            return CloudProviderType.AZURE
        elif 'region' in config and 'credentials' in config:
            return CloudProviderType.AWS
        else:
            raise ConfigurationError("Unable to detect cloud provider from configuration")
    
    @staticmethod
    def create_provider(config: Dict[str, Any]) -> CloudProvider:
        """Create appropriate cloud provider instance"""
        provider_type = CloudProviderManager.detect_provider(config)
        
        if provider_type == CloudProviderType.AZURE:
            return AzureProvider(config)
        elif provider_type == CloudProviderType.AWS:
            return AWSProvider(config)
        else:
            raise ConfigurationError(f"Unsupported provider type: {provider_type}")
