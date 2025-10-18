import pytest
from unittest.mock import Mock, patch, MagicMock
from crewai_app.services.aws_bedrock_service import AWSBedrockService
from crewai_app.services.aws_opensearch_service import AWSOpenSearchService
from crewai_app.services.aws_rds_service import AWSRDSService
from crewai_app.services.aws_sqs_service import AWSSQSService
from crewai_app.services.aws_s3_service import AWSS3Service
from crewai_app.providers.cloud_providers import AWSProviderError

class TestAWSBedrockService:
    def test_bedrock_service_creation(self):
        """Test AWS Bedrock service creation"""
        config = {
            "region": "us-east-1",
            "credentials": {
                "aws_access_key_id": "test-key",
                "aws_secret_access_key": "test-secret"
            },
            "model_id": "anthropic.claude-3-sonnet-20240229-v1:0"
        }
        
        service = AWSBedrockService(config)
        assert service.region == "us-east-1"
        assert service.model_id == "anthropic.claude-3-sonnet-20240229-v1:0"
    
    @patch('boto3.client')
    def test_generate_text_success(self, mock_boto_client):
        """Test successful text generation"""
        config = {
            "region": "us-east-1",
            "credentials": {"aws_access_key_id": "test-key", "aws_secret_access_key": "test-secret"}
        }
        
        mock_client = Mock()
        mock_client.invoke_model.return_value = {'body': Mock()}
        mock_client.invoke_model.return_value['body'].read.return_value = b'{"content": "Test response"}'
        mock_boto_client.return_value = mock_client
        
        service = AWSBedrockService(config)
        service.client = mock_client
        
        result = service.generate_text("Test prompt")
        assert "Test response" in result
    
    @patch('boto3.client')
    def test_generate_text_error(self, mock_boto_client):
        """Test text generation error handling"""
        config = {
            "region": "us-east-1",
            "credentials": {"aws_access_key_id": "test-key", "aws_secret_access_key": "test-secret"}
        }
        
        mock_client = Mock()
        from botocore.exceptions import ClientError
        mock_client.invoke_model.side_effect = ClientError(
            {'Error': {'Code': 'ValidationException', 'Message': 'Bedrock error'}}, 
            'InvokeModel'
        )
        mock_boto_client.return_value = mock_client
        
        service = AWSBedrockService(config)
        service.client = mock_client
        
        with pytest.raises(AWSProviderError):
            service.generate_text("Test prompt")
    
    @patch('boto3.client')
    def test_get_available_models(self, mock_boto_client):
        """Test getting available models"""
        config = {
            "region": "us-east-1",
            "credentials": {"aws_access_key_id": "test-key", "aws_secret_access_key": "test-secret"}
        }
        
        mock_client = Mock()
        mock_client.list_foundation_models.return_value = {
            'modelSummaries': [{'modelId': 'model1'}, {'modelId': 'model2'}]
        }
        mock_boto_client.return_value = mock_client
        
        service = AWSBedrockService(config)
        service.client = mock_client
        
        models = service.get_available_models()
        assert len(models) == 2
        assert 'model1' in models
        assert 'model2' in models

class TestAWSOpenSearchService:
    def test_opensearch_service_creation(self):
        """Test AWS OpenSearch service creation"""
        config = {
            "region": "us-west-2",
            "credentials": {"aws_access_key_id": "test-key", "aws_secret_access_key": "test-secret"},
            "opensearch_domain": "test-domain"
        }
        
        service = AWSOpenSearchService(config)
        assert service.region == "us-west-2"
        assert service.domain == "test-domain"
        assert "test-domain.us-west-2.es.amazonaws.com" in service.endpoint
    
    @patch('requests.Session.put')
    def test_create_index_success(self, mock_put):
        """Test successful index creation"""
        config = {
            "region": "us-east-1",
            "credentials": {"aws_access_key_id": "test-key", "aws_secret_access_key": "test-secret"},
            "opensearch_domain": "test-domain"
        }
        
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_put.return_value = mock_response
        
        service = AWSOpenSearchService(config)
        result = service.create_index("test-index", {"mappings": {}})
        assert result is True
    
    @patch('requests.Session.put')
    def test_create_index_error(self, mock_put):
        """Test index creation error handling"""
        config = {
            "region": "us-east-1",
            "credentials": {"aws_access_key_id": "test-key", "aws_secret_access_key": "test-secret"},
            "opensearch_domain": "test-domain"
        }
        
        import requests
        mock_put.side_effect = requests.RequestException("OpenSearch error")
        
        service = AWSOpenSearchService(config)
        
        with pytest.raises(AWSProviderError):
            service.create_index("test-index", {"mappings": {}})
    
    @patch('requests.Session.post')
    def test_search_documents(self, mock_post):
        """Test document search"""
        config = {
            "region": "us-east-1",
            "credentials": {"aws_access_key_id": "test-key", "aws_secret_access_key": "test-secret"},
            "opensearch_domain": "test-domain"
        }
        
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            'hits': {'hits': [{'id': '1', 'source': {'content': 'test'}}]}
        }
        mock_post.return_value = mock_response
        
        service = AWSOpenSearchService(config)
        results = service.search_documents("test-index", {"query": {"match_all": {}}})
        assert len(results) == 1

class TestAWSRDSService:
    def test_rds_service_creation(self):
        """Test AWS RDS service creation"""
        config = {
            "region": "eu-west-1",
            "credentials": {"aws_access_key_id": "test-key", "aws_secret_access_key": "test-secret"}
        }
        
        service = AWSRDSService(config)
        assert service.region == "eu-west-1"
    
    @patch('boto3.client')
    def test_create_database_instance(self, mock_boto_client):
        """Test database instance creation"""
        config = {
            "region": "us-east-1",
            "credentials": {"aws_access_key_id": "test-key", "aws_secret_access_key": "test-secret"}
        }
        
        mock_client = Mock()
        mock_client.create_db_instance.return_value = {}
        mock_boto_client.return_value = mock_client
        
        service = AWSRDSService(config)
        service.client = mock_client
        
        result = service.create_database_instance("test-instance")
        assert result is True
    
    @patch('boto3.client')
    def test_get_database_endpoint(self, mock_boto_client):
        """Test getting database endpoint"""
        config = {
            "region": "us-east-1",
            "credentials": {"aws_access_key_id": "test-key", "aws_secret_access_key": "test-secret"}
        }
        
        mock_client = Mock()
        mock_client.describe_db_instances.return_value = {
            'DBInstances': [{'Endpoint': {'Address': 'test-endpoint.amazonaws.com'}}]
        }
        mock_boto_client.return_value = mock_client
        
        service = AWSRDSService(config)
        service.client = mock_client
        
        endpoint = service.get_database_endpoint("test-instance")
        assert endpoint == "test-endpoint.amazonaws.com"
    
    @patch('boto3.client')
    def test_get_database_status(self, mock_boto_client):
        """Test getting database status"""
        config = {
            "region": "us-east-1",
            "credentials": {"aws_access_key_id": "test-key", "aws_secret_access_key": "test-secret"}
        }
        
        mock_client = Mock()
        mock_client.describe_db_instances.return_value = {
            'DBInstances': [{'DBInstanceStatus': 'available'}]
        }
        mock_boto_client.return_value = mock_client
        
        service = AWSRDSService(config)
        service.client = mock_client
        
        status = service.get_database_status("test-instance")
        assert status == "available"

class TestAWSSQSService:
    def test_sqs_service_creation(self):
        """Test AWS SQS service creation"""
        config = {
            "region": "ap-southeast-1",
            "credentials": {"aws_access_key_id": "test-key", "aws_secret_access_key": "test-secret"}
        }
        
        service = AWSSQSService(config)
        assert service.region == "ap-southeast-1"
    
    @patch('boto3.client')
    def test_create_queue(self, mock_boto_client):
        """Test queue creation"""
        config = {
            "region": "us-east-1",
            "credentials": {"aws_access_key_id": "test-key", "aws_secret_access_key": "test-secret"}
        }
        
        mock_client = Mock()
        mock_client.create_queue.return_value = {'QueueUrl': 'https://sqs.us-east-1.amazonaws.com/123456789012/test-queue'}
        mock_boto_client.return_value = mock_client
        
        service = AWSSQSService(config)
        service.client = mock_client
        
        queue_url = service.create_queue("test-queue")
        assert "test-queue" in queue_url
    
    @patch('boto3.client')
    def test_send_message(self, mock_boto_client):
        """Test message sending"""
        config = {
            "region": "us-east-1",
            "credentials": {"aws_access_key_id": "test-key", "aws_secret_access_key": "test-secret"}
        }
        
        mock_client = Mock()
        mock_client.send_message.return_value = {}
        mock_boto_client.return_value = mock_client
        
        service = AWSSQSService(config)
        service.client = mock_client
        
        result = service.send_message("https://sqs.us-east-1.amazonaws.com/123456789012/test-queue", "test message")
        assert result is True
    
    @patch('boto3.client')
    def test_receive_messages(self, mock_boto_client):
        """Test message receiving"""
        config = {
            "region": "us-east-1",
            "credentials": {"aws_access_key_id": "test-key", "aws_secret_access_key": "test-secret"}
        }
        
        mock_client = Mock()
        mock_client.receive_message.return_value = {
            'Messages': [{'Body': 'test message', 'ReceiptHandle': 'test-handle'}]
        }
        mock_boto_client.return_value = mock_client
        
        service = AWSSQSService(config)
        service.client = mock_client
        
        messages = service.receive_messages("https://sqs.us-east-1.amazonaws.com/123456789012/test-queue")
        assert len(messages) == 1
        assert messages[0]['Body'] == 'test message'

class TestAWSS3Service:
    def test_s3_service_creation(self):
        """Test AWS S3 service creation"""
        config = {
            "region": "ca-central-1",
            "credentials": {"aws_access_key_id": "test-key", "aws_secret_access_key": "test-secret"}
        }
        
        service = AWSS3Service(config)
        assert service.region == "ca-central-1"
    
    @patch('boto3.client')
    def test_create_bucket(self, mock_boto_client):
        """Test bucket creation"""
        config = {
            "region": "us-east-1",
            "credentials": {"aws_access_key_id": "test-key", "aws_secret_access_key": "test-secret"}
        }
        
        mock_client = Mock()
        mock_client.create_bucket.return_value = {}
        mock_boto_client.return_value = mock_client
        
        service = AWSS3Service(config)
        service.client = mock_client
        
        result = service.create_bucket("test-bucket")
        assert result is True
    
    @patch('boto3.client')
    def test_upload_file(self, mock_boto_client):
        """Test file upload"""
        config = {
            "region": "us-east-1",
            "credentials": {"aws_access_key_id": "test-key", "aws_secret_access_key": "test-secret"}
        }
        
        mock_client = Mock()
        mock_client.upload_file.return_value = None
        mock_boto_client.return_value = mock_client
        
        service = AWSS3Service(config)
        service.client = mock_client
        
        result = service.upload_file("test-bucket", "local-file.txt", "remote-file.txt")
        assert result is True
    
    @patch('boto3.client')
    def test_download_file(self, mock_boto_client):
        """Test file download"""
        config = {
            "region": "us-east-1",
            "credentials": {"aws_access_key_id": "test-key", "aws_secret_access_key": "test-secret"}
        }
        
        mock_client = Mock()
        mock_client.download_file.return_value = None
        mock_boto_client.return_value = mock_client
        
        service = AWSS3Service(config)
        service.client = mock_client
        
        result = service.download_file("test-bucket", "remote-file.txt", "local-file.txt")
        assert result is True
    
    @patch('boto3.client')
    def test_list_objects(self, mock_boto_client):
        """Test object listing"""
        config = {
            "region": "us-east-1",
            "credentials": {"aws_access_key_id": "test-key", "aws_secret_access_key": "test-secret"}
        }
        
        mock_client = Mock()
        mock_client.list_objects_v2.return_value = {
            'Contents': [{'Key': 'file1.txt'}, {'Key': 'file2.txt'}]
        }
        mock_boto_client.return_value = mock_client
        
        service = AWSS3Service(config)
        service.client = mock_client
        
        objects = service.list_objects("test-bucket")
        assert len(objects) == 2
        assert objects[0]['Key'] == 'file1.txt'
    
    @patch('boto3.client')
    def test_bucket_exists(self, mock_boto_client):
        """Test bucket existence check"""
        config = {
            "region": "us-east-1",
            "credentials": {"aws_access_key_id": "test-key", "aws_secret_access_key": "test-secret"}
        }
        
        mock_client = Mock()
        mock_client.head_bucket.return_value = {}
        mock_boto_client.return_value = mock_client
        
        service = AWSS3Service(config)
        service.client = mock_client
        
        exists = service.bucket_exists("test-bucket")
        assert exists is True
    
    @patch('boto3.client')
    def test_bucket_not_exists(self, mock_boto_client):
        """Test bucket non-existence check"""
        config = {
            "region": "us-east-1",
            "credentials": {"aws_access_key_id": "test-key", "aws_secret_access_key": "test-secret"}
        }
        
        mock_client = Mock()
        from botocore.exceptions import ClientError
        mock_client.head_bucket.side_effect = ClientError(
            {'Error': {'Code': 'NoSuchBucket', 'Message': 'Bucket not found'}}, 
            'HeadBucket'
        )
        mock_boto_client.return_value = mock_client
        
        service = AWSS3Service(config)
        service.client = mock_client
        
        exists = service.bucket_exists("test-bucket")
        assert exists is False

class TestAWSProviderError:
    def test_aws_provider_error_creation(self):
        """Test AWS provider error creation"""
        error = AWSProviderError("Test error message")
        assert str(error) == "Test error message"
        assert isinstance(error, Exception)

# Integration tests
class TestAWSServicesIntegration:
    def test_all_services_creation(self):
        """Test that all AWS services can be created with valid config"""
        config = {
            "region": "us-east-1",
            "credentials": {
                "aws_access_key_id": "test-key",
                "aws_secret_access_key": "test-secret"
            },
            "opensearch_domain": "test-domain"
        }
        
        # Test all services can be instantiated
        bedrock_service = AWSBedrockService(config)
        opensearch_service = AWSOpenSearchService(config)
        rds_service = AWSRDSService(config)
        sqs_service = AWSSQSService(config)
        s3_service = AWSS3Service(config)
        
        assert bedrock_service.region == "us-east-1"
        assert opensearch_service.region == "us-east-1"
        assert rds_service.region == "us-east-1"
        assert sqs_service.region == "us-east-1"
        assert s3_service.region == "us-east-1"
    
    def test_services_with_different_regions(self):
        """Test services with different regions"""
        regions = ["us-west-2", "eu-west-1", "ap-southeast-1"]
        
        for region in regions:
            config = {
                "region": region,
                "credentials": {
                    "aws_access_key_id": "test-key",
                    "aws_secret_access_key": "test-secret"
                }
            }
            
            bedrock_service = AWSBedrockService(config)
            assert bedrock_service.region == region
