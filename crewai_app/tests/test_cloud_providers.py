import pytest
from unittest.mock import Mock
from crewai_app.config.cloud_providers import (
    CloudProvider, AzureProvider, AWSProvider, 
    CloudProviderManager, CloudProviderType,
    CloudProviderError, AzureProviderError, AWSProviderError, ConfigurationError
)
from crewai_app.services.cloud_provider_service import CloudProviderService


class TestAzureProvider:
    def test_azure_provider_creation(self):
        """Test Azure provider creation with valid configuration"""
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
        assert "test-sql.database.windows.net" in provider.get_database_endpoint()
        assert "test-sb.servicebus.windows.net" in provider.get_messaging_endpoint()
        assert "test-storage.blob.core.windows.net" in provider.get_storage_endpoint()
    
    def test_azure_provider_missing_config(self):
        """Test Azure provider with missing required configuration"""
        config = {
            "subscription_id": "test-sub",
            # Missing resource_group and credentials
        }
        
        with pytest.raises(ConfigurationError):
            AzureProvider(config)
    
    def test_azure_provider_credentials(self):
        """Test Azure provider credentials handling"""
        config = {
            "subscription_id": "test-sub",
            "resource_group": "test-rg",
            "openai_resource_name": "test-openai",
            "search_service_name": "test-search",
            "sql_server_name": "test-sql",
            "service_bus_namespace": "test-sb",
            "storage_account": "test-storage",
            "credentials": {"client_id": "test-id", "client_secret": "test-secret"}
        }
        
        provider = AzureProvider(config)
        credentials = provider.get_credentials()
        assert credentials["client_id"] == "test-id"
        assert credentials["client_secret"] == "test-secret"


class TestAWSProvider:
    def test_aws_provider_creation(self):
        """Test AWS provider creation with valid configuration"""
        config = {
            "region": "us-east-1",
            "credentials": {"aws_access_key_id": "test-key"}
        }
        
        provider = AWSProvider(config)
        assert provider.provider_type == CloudProviderType.AWS
        assert "bedrock-runtime.us-east-1.amazonaws.com" in provider.get_llm_endpoint()
        assert "s3.us-east-1.amazonaws.com" in provider.get_storage_endpoint()
        assert "sqs.us-east-1.amazonaws.com" in provider.get_messaging_endpoint()
        assert "rds.us-east-1.amazonaws.com" in provider.get_database_endpoint()
    
    def test_aws_provider_missing_config(self):
        """Test AWS provider with missing required configuration"""
        config = {
            "region": "us-east-1",
            # Missing credentials
        }
        
        with pytest.raises(ConfigurationError):
            AWSProvider(config)
    
    def test_aws_provider_credentials(self):
        """Test AWS provider credentials handling"""
        config = {
            "region": "us-west-2",
            "credentials": {
                "aws_access_key_id": "test-key",
                "aws_secret_access_key": "test-secret"
            }
        }
        
        provider = AWSProvider(config)
        credentials = provider.get_credentials()
        assert credentials["aws_access_key_id"] == "test-key"
        assert credentials["aws_secret_access_key"] == "test-secret"
        assert provider.get_region() == "us-west-2"
    
    def test_aws_provider_opensearch_domain(self):
        """Test AWS provider with custom OpenSearch domain"""
        config = {
            "region": "eu-west-1",
            "credentials": {"aws_access_key_id": "test-key"},
            "opensearch_domain": "custom-search-domain"
        }
        
        provider = AWSProvider(config)
        endpoint = provider.get_vector_store_endpoint()
        assert "custom-search-domain" in endpoint
        assert "eu-west-1" in endpoint


class TestCloudProviderManager:
    def test_detect_azure_provider(self):
        """Test detection of Azure provider from configuration"""
        config = {"subscription_id": "test", "resource_group": "test"}
        provider_type = CloudProviderManager.detect_provider(config)
        assert provider_type == CloudProviderType.AZURE
    
    def test_detect_aws_provider(self):
        """Test detection of AWS provider from configuration"""
        config = {"region": "us-east-1", "credentials": {}}
        provider_type = CloudProviderManager.detect_provider(config)
        assert provider_type == CloudProviderType.AWS
    
    def test_detect_provider_unknown(self):
        """Test detection with unknown configuration"""
        config = {"some_other_key": "value"}
        
        with pytest.raises(ConfigurationError):
            CloudProviderManager.detect_provider(config)
    
    def test_create_azure_provider(self):
        """Test creation of Azure provider through manager"""
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
        assert provider.provider_type == CloudProviderType.AZURE
    
    def test_create_aws_provider(self):
        """Test creation of AWS provider through manager"""
        config = {
            "region": "us-east-1",
            "credentials": {"aws_access_key_id": "test-key"}
        }
        
        provider = CloudProviderManager.create_provider(config)
        assert isinstance(provider, AWSProvider)
        assert provider.provider_type == CloudProviderType.AWS


class TestCloudProviderService:
    def test_azure_service_creation(self):
        """Test CloudProviderService with Azure configuration"""
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
        
        service = CloudProviderService(config)
        assert service.get_provider_type() == "azure"
        assert "test-openai.openai.azure.com" in service.get_llm_endpoint()
        assert "test-search.search.windows.net" in service.get_vector_store_endpoint()
    
    def test_aws_service_creation(self):
        """Test CloudProviderService with AWS configuration"""
        config = {
            "region": "us-west-2",
            "credentials": {"aws_access_key_id": "test-key"}
        }
        
        service = CloudProviderService(config)
        assert service.get_provider_type() == "aws"
        assert "bedrock-runtime.us-west-2.amazonaws.com" in service.get_llm_endpoint()
        assert "s3.us-west-2.amazonaws.com" in service.get_storage_endpoint()
    
    def test_service_lazy_loading(self):
        """Test that service creates provider only when needed"""
        config = {
            "region": "us-east-1",
            "credentials": {"aws_access_key_id": "test-key"}
        }
        
        service = CloudProviderService(config)
        # Provider should not be created yet
        assert service._provider is None
        
        # Accessing provider should create it
        provider = service.provider
        assert provider is not None
        assert service._provider is provider  # Should be cached
    
    def test_service_all_endpoints(self):
        """Test that service provides all required endpoints"""
        config = {
            "region": "us-east-1",
            "credentials": {"aws_access_key_id": "test-key"}
        }
        
        service = CloudProviderService(config)
        
        # Test all endpoint methods
        llm_endpoint = service.get_llm_endpoint()
        vector_endpoint = service.get_vector_store_endpoint()
        db_endpoint = service.get_database_endpoint()
        messaging_endpoint = service.get_messaging_endpoint()
        storage_endpoint = service.get_storage_endpoint()
        
        assert llm_endpoint.startswith("https://")
        assert vector_endpoint.startswith("https://")
        assert db_endpoint.startswith("https://")
        assert messaging_endpoint.startswith("https://")
        assert storage_endpoint.startswith("https://")
        
        # Test credentials and region
        credentials = service.get_credentials()
        region = service.get_region()
        
        assert isinstance(credentials, dict)
        assert isinstance(region, str)


class TestErrorHandling:
    def test_azure_provider_error_inheritance(self):
        """Test that Azure provider errors inherit from base class"""
        assert issubclass(AzureProviderError, CloudProviderError)
    
    def test_aws_provider_error_inheritance(self):
        """Test that AWS provider errors inherit from base class"""
        assert issubclass(AWSProviderError, CloudProviderError)
    
    def test_configuration_error_inheritance(self):
        """Test that configuration errors inherit from base class"""
        assert issubclass(ConfigurationError, CloudProviderError)
    
    def test_error_raising(self):
        """Test that appropriate errors are raised"""
        # Test configuration error
        with pytest.raises(ConfigurationError):
            AzureProvider({"invalid": "config"})
        
        with pytest.raises(ConfigurationError):
            AWSProvider({"invalid": "config"})
        
        with pytest.raises(ConfigurationError):
            CloudProviderManager.detect_provider({"invalid": "config"})


class TestProviderTypeEnum:
    def test_provider_type_values(self):
        """Test that provider type enum has correct values"""
        assert CloudProviderType.AZURE.value == "azure"
        assert CloudProviderType.AWS.value == "aws"
    
    def test_provider_type_comparison(self):
        """Test provider type comparison"""
        azure_type = CloudProviderType.AZURE
        aws_type = CloudProviderType.AWS
        
        assert azure_type != aws_type
        assert azure_type == CloudProviderType.AZURE
        assert aws_type == CloudProviderType.AWS
