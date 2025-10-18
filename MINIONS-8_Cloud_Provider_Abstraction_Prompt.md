# MINIONS-8: Create Cloud Provider Abstraction
## Implementation Prompt for LLM

### **Task Overview**
You are implementing MINIONS-8: Create Cloud Provider Abstraction for the AI Team Multi-Agent System. This is the first story in Epic 1 (Platform-Agnostic Foundation) and establishes the foundation for cloud provider abstraction.

### **What You Need to Do**
Create a cloud provider abstraction layer that allows seamless switching between Azure and AWS without code changes. This will enable future migration from Azure to AWS when credits expire.

### **Files to Create**
1. `crewai_app/config/cloud_providers.py` - Main implementation
2. `crewai_app/services/cloud_provider_service.py` - Service layer
3. `crewai_app/tests/test_cloud_providers.py` - Unit tests

### **Core Requirements**
- Create abstract `CloudProvider` base class
- Implement `AzureProvider` and `AWSProvider` concrete classes
- Add provider detection and configuration logic
- Implement provider-specific error handling
- Create comprehensive unit tests
- Support configuration-driven provider selection

### **Implementation Steps**

#### **Step 1: Create the Base Class**
Create `crewai_app/config/cloud_providers.py` with this structure:

```python
from abc import ABC, abstractmethod
from typing import Dict, Any
from enum import Enum

class CloudProviderType(Enum):
    AZURE = "azure"
    AWS = "aws"

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
```

#### **Step 2: Add Azure Provider**
Add this class to the same file:

```python
class AzureProvider(CloudProvider):
    """Azure cloud provider implementation"""
    
    def _get_provider_type(self) -> CloudProviderType:
        return CloudProviderType.AZURE
    
    def _validate_config(self) -> None:
        required_keys = ['subscription_id', 'resource_group', 'credentials']
        for key in required_keys:
            if key not in self.config:
                raise ValueError(f"Missing required Azure config: {key}")
    
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
```

#### **Step 3: Add AWS Provider**
Add this class to the same file:

```python
class AWSProvider(CloudProvider):
    """AWS cloud provider implementation"""
    
    def _get_provider_type(self) -> CloudProviderType:
        return CloudProviderType.AWS
    
    def _validate_config(self) -> None:
        required_keys = ['region', 'credentials']
        for key in required_keys:
            if key not in self.config:
                raise ValueError(f"Missing required AWS config: {key}")
    
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
```

#### **Step 4: Add Provider Manager**
Add this class to the same file:

```python
class CloudProviderManager:
    """Manages cloud provider detection and configuration"""
    
    @staticmethod
    def detect_provider(config: Dict[str, Any]) -> CloudProviderType:
        """Detect cloud provider from configuration"""
        if 'subscription_id' in config and 'resource_group' in config:
            return CloudProviderType.AZURE
        elif 'region' in config and 'credentials' in config:
            return CloudProviderType.AWS
        else:
            raise ValueError("Unable to detect cloud provider from configuration")
    
    @staticmethod
    def create_provider(config: Dict[str, Any]) -> CloudProvider:
        """Create appropriate cloud provider instance"""
        provider_type = CloudProviderManager.detect_provider(config)
        
        if provider_type == CloudProviderType.AZURE:
            return AzureProvider(config)
        elif provider_type == CloudProviderType.AWS:
            return AWSProvider(config)
        else:
            raise ValueError(f"Unsupported provider type: {provider_type}")
```

#### **Step 5: Add Error Classes**
Add these exception classes to the same file:

```python
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
```

#### **Step 6: Create Unit Tests**
Create `crewai_app/tests/test_cloud_providers.py`:

```python
import pytest
from unittest.mock import Mock
from crewai_app.config.cloud_providers import (
    CloudProvider, AzureProvider, AWSProvider, 
    CloudProviderManager, CloudProviderType
)

class TestAzureProvider:
    def test_azure_provider_creation(self):
        config = {
            "subscription_id": "test-sub",
            "resource_group": "test-rg",
            "openai_resource_name": "test-openai",
            "search_service_name": "test-search",
            "sql_server_name": "test-sql",
            "service_bus_namespace": "test-sb",
            "storage_account": "test-storage",
            "credentials": {"client_id": "test-id"}
        }
        
        provider = AzureProvider(config)
        assert provider.provider_type == CloudProviderType.AZURE
        assert "test-openai.openai.azure.com" in provider.get_llm_endpoint()
        assert "test-search.search.windows.net" in provider.get_vector_store_endpoint()

class TestAWSProvider:
    def test_aws_provider_creation(self):
        config = {
            "region": "us-east-1",
            "credentials": {"aws_access_key_id": "test-key"}
        }
        
        provider = AWSProvider(config)
        assert provider.provider_type == CloudProviderType.AWS
        assert "bedrock-runtime.us-east-1.amazonaws.com" in provider.get_llm_endpoint()
        assert "s3.us-east-1.amazonaws.com" in provider.get_storage_endpoint()

class TestCloudProviderManager:
    def test_detect_azure_provider(self):
        config = {"subscription_id": "test", "resource_group": "test"}
        provider_type = CloudProviderManager.detect_provider(config)
        assert provider_type == CloudProviderType.AZURE
    
    def test_detect_aws_provider(self):
        config = {"region": "us-east-1", "credentials": {}}
        provider_type = CloudProviderManager.detect_provider(config)
        assert provider_type == CloudProviderType.AWS
    
    def test_create_azure_provider(self):
        config = {
            "subscription_id": "test-sub",
            "resource_group": "test-rg",
            "openai_resource_name": "test-openai",
            "search_service_name": "test-search",
            "sql_server_name": "test-sql",
            "service_bus_namespace": "test-sb",
            "storage_account": "test-storage",
            "credentials": {"client_id": "test-id"}
        }
        
        provider = CloudProviderManager.create_provider(config)
        assert isinstance(provider, AzureProvider)
    
    def test_create_aws_provider(self):
        config = {
            "region": "us-east-1",
            "credentials": {"aws_access_key_id": "test-key"}
        }
        
        provider = CloudProviderManager.create_provider(config)
        assert isinstance(provider, AWSProvider)
```

#### **Step 7: Create Service Layer**
Create `crewai_app/services/cloud_provider_service.py`:

```python
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
```

### **Testing Instructions**
1. Run the unit tests: `python -m pytest crewai_app/tests/test_cloud_providers.py -v`
2. Test Azure provider creation with valid config
3. Test AWS provider creation with valid config
4. Test provider detection logic
5. Test error handling for invalid configurations

### **Acceptance Criteria**
- [ ] All classes implement the required abstract methods
- [ ] Azure and AWS providers can be instantiated
- [ ] Provider detection works correctly
- [ ] All unit tests pass
- [ ] Error handling works for invalid configurations
- [ ] Service layer provides clean interface

### **Next Steps**
After completing this story, you can proceed to:
- MINIONS-9: Universal LLM Service
- MINIONS-10: Universal Vector Store Service  
- MINIONS-11: Universal Database Service
