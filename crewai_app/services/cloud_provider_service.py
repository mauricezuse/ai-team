from typing import Dict, Any
from crewai_app.config.cloud_providers import CloudProviderManager, CloudProvider


class CloudProviderService:
    """Service layer for cloud provider management"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self._provider = None
    
    @property
    def provider(self) -> CloudProvider:
        """Get the current cloud provider instance"""
        if self._provider is None:
            self._provider = CloudProviderManager.create_provider(self.config)
        return self._provider
    
    def get_llm_endpoint(self) -> str:
        """Get LLM endpoint for current provider"""
        return self.provider.get_llm_endpoint()
    
    def get_vector_store_endpoint(self) -> str:
        """Get vector store endpoint for current provider"""
        return self.provider.get_vector_store_endpoint()
    
    def get_database_endpoint(self) -> str:
        """Get database endpoint for current provider"""
        return self.provider.get_database_endpoint()
    
    def get_messaging_endpoint(self) -> str:
        """Get messaging endpoint for current provider"""
        return self.provider.get_messaging_endpoint()
    
    def get_storage_endpoint(self) -> str:
        """Get storage endpoint for current provider"""
        return self.provider.get_storage_endpoint()
    
    def get_credentials(self) -> Dict[str, str]:
        """Get credentials for current provider"""
        return self.provider.get_credentials()
    
    def get_region(self) -> str:
        """Get region for current provider"""
        return self.provider.get_region()
    
    def get_provider_type(self) -> str:
        """Get the current provider type"""
        return self.provider.provider_type.value
