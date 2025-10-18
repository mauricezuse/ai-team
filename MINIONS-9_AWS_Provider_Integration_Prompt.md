# Implementation Prompt for LLM
## Task Overview
You are implementing MINIONS-9: Implement AWS Provider Integration for the AI Team Multi-Agent System. This is the second story in Epic 1 (Platform-Agnostic Foundation) and builds upon the cloud provider abstraction layer established in MINIONS-8.

## What You Need to Do
Implement AWS-specific integrations and services to enable seamless operation with Amazon Web Services. This includes AWS Bedrock for LLM services, OpenSearch for vector storage, RDS for database, SQS for messaging, and S3 for file storage.

## Files to Create/Modify
- `crewai_app/services/aws_bedrock_service.py` - AWS Bedrock LLM integration
- `crewai_app/services/aws_opensearch_service.py` - AWS OpenSearch vector store integration  
- `crewai_app/services/aws_rds_service.py` - AWS RDS database integration
- `crewai_app/services/aws_sqs_service.py` - AWS SQS messaging integration
- `crewai_app/services/aws_s3_service.py` - AWS S3 storage integration
- `crewai_app/tests/test_aws_services.py` - Unit tests for AWS services
- `crewai_app/README.md` - Update documentation

## Core Requirements
- Implement AWS Bedrock service for LLM operations
- Implement AWS OpenSearch service for vector storage
- Implement AWS RDS service for database operations
- Implement AWS SQS service for messaging
- Implement AWS S3 service for file storage
- Add comprehensive error handling for AWS-specific errors
- Create unit tests for all AWS services
- Support configuration-driven AWS service selection
- Maintain compatibility with existing cloud provider abstraction

## Implementation Steps

### Step 1: Create AWS Bedrock Service
Create `crewai_app/services/aws_bedrock_service.py`:

```python
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
```

### Step 2: Create AWS OpenSearch Service
Create `crewai_app/services/aws_opensearch_service.py`:

```python
import boto3
from typing import Dict, Any, List, Optional
from botocore.exceptions import ClientError, BotoCoreError
from crewai_app.providers.cloud_providers import AWSProviderError

class AWSOpenSearchService:
    """AWS OpenSearch service for vector storage"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.region = config.get('region', 'us-east-1')
        self.domain = config.get('opensearch_domain', 'search-domain')
        self.endpoint = f"https://{self.domain}.{self.region}.es.amazonaws.com"
        
        # Initialize OpenSearch client
        self.client = boto3.client(
            'es',
            region_name=self.region,
            aws_access_key_id=config['credentials']['aws_access_key_id'],
            aws_secret_access_key=config['credentials']['aws_secret_access_key']
        )
    
    def create_index(self, index_name: str, mapping: Dict[str, Any]) -> bool:
        """Create OpenSearch index"""
        try:
            # Implementation for creating index
            return True
        except (ClientError, BotoCoreError) as e:
            raise AWSProviderError(f"Failed to create OpenSearch index: {str(e)}")
    
    def index_document(self, index_name: str, document: Dict[str, Any], doc_id: str) -> bool:
        """Index document in OpenSearch"""
        try:
            # Implementation for indexing document
            return True
        except (ClientError, BotoCoreError) as e:
            raise AWSProviderError(f"Failed to index document: {str(e)}")
    
    def search_documents(self, index_name: str, query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search documents in OpenSearch"""
        try:
            # Implementation for searching documents
            return []
        except (ClientError, BotoCoreError) as e:
            raise AWSProviderError(f"Failed to search documents: {str(e)}")
```

### Step 3: Create AWS RDS Service
Create `crewai_app/services/aws_rds_service.py`:

```python
import boto3
from typing import Dict, Any, List, Optional
from botocore.exceptions import ClientError, BotoCoreError
from crewai_app.providers.cloud_providers import AWSProviderError

class AWSRDSService:
    """AWS RDS service for database operations"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.region = config.get('region', 'us-east-1')
        self.client = boto3.client(
            'rds',
            region_name=self.region,
            aws_access_key_id=config['credentials']['aws_access_key_id'],
            aws_secret_access_key=config['credentials']['aws_secret_access_key']
        )
    
    def create_database_instance(self, instance_id: str, engine: str = 'postgres') -> bool:
        """Create RDS database instance"""
        try:
            response = self.client.create_db_instance(
                DBInstanceIdentifier=instance_id,
                DBInstanceClass='db.t3.micro',
                Engine=engine,
                MasterUsername='admin',
                MasterUserPassword='password123',
                AllocatedStorage=20
            )
            return True
        except (ClientError, BotoCoreError) as e:
            raise AWSProviderError(f"Failed to create RDS instance: {str(e)}")
    
    def get_database_endpoint(self, instance_id: str) -> str:
        """Get RDS database endpoint"""
        try:
            response = self.client.describe_db_instances(
                DBInstanceIdentifier=instance_id
            )
            return response['DBInstances'][0]['Endpoint']['Address']
        except (ClientError, BotoCoreError) as e:
            raise AWSProviderError(f"Failed to get RDS endpoint: {str(e)}")
```

### Step 4: Create AWS SQS Service
Create `crewai_app/services/aws_sqs_service.py`:

```python
import boto3
from typing import Dict, Any, List, Optional
from botocore.exceptions import ClientError, BotoCoreError
from crewai_app.providers.cloud_providers import AWSProviderError

class AWSSQSService:
    """AWS SQS service for messaging"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.region = config.get('region', 'us-east-1')
        self.client = boto3.client(
            'sqs',
            region_name=self.region,
            aws_access_key_id=config['credentials']['aws_access_key_id'],
            aws_secret_access_key=config['credentials']['aws_secret_access_key']
        )
    
    def create_queue(self, queue_name: str) -> str:
        """Create SQS queue"""
        try:
            response = self.client.create_queue(QueueName=queue_name)
            return response['QueueUrl']
        except (ClientError, BotoCoreError) as e:
            raise AWSProviderError(f"Failed to create SQS queue: {str(e)}")
    
    def send_message(self, queue_url: str, message: str) -> bool:
        """Send message to SQS queue"""
        try:
            self.client.send_message(QueueUrl=queue_url, MessageBody=message)
            return True
        except (ClientError, BotoCoreError) as e:
            raise AWSProviderError(f"Failed to send SQS message: {str(e)}")
    
    def receive_messages(self, queue_url: str, max_messages: int = 10) -> List[Dict[str, Any]]:
        """Receive messages from SQS queue"""
        try:
            response = self.client.receive_message(
                QueueUrl=queue_url,
                MaxNumberOfMessages=max_messages
            )
            return response.get('Messages', [])
        except (ClientError, BotoCoreError) as e:
            raise AWSProviderError(f"Failed to receive SQS messages: {str(e)}")
```

### Step 5: Create AWS S3 Service
Create `crewai_app/services/aws_s3_service.py`:

```python
import boto3
from typing import Dict, Any, List, Optional
from botocore.exceptions import ClientError, BotoCoreError
from crewai_app.providers.cloud_providers import AWSProviderError

class AWSS3Service:
    """AWS S3 service for file storage"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.region = config.get('region', 'us-east-1')
        self.client = boto3.client(
            's3',
            region_name=self.region,
            aws_access_key_id=config['credentials']['aws_access_key_id'],
            aws_secret_access_key=config['credentials']['aws_secret_access_key']
        )
    
    def create_bucket(self, bucket_name: str) -> bool:
        """Create S3 bucket"""
        try:
            self.client.create_bucket(Bucket=bucket_name)
            return True
        except (ClientError, BotoCoreError) as e:
            raise AWSProviderError(f"Failed to create S3 bucket: {str(e)}")
    
    def upload_file(self, bucket_name: str, file_path: str, object_key: str) -> bool:
        """Upload file to S3"""
        try:
            self.client.upload_file(file_path, bucket_name, object_key)
            return True
        except (ClientError, BotoCoreError) as e:
            raise AWSProviderError(f"Failed to upload file to S3: {str(e)}")
    
    def download_file(self, bucket_name: str, object_key: str, file_path: str) -> bool:
        """Download file from S3"""
        try:
            self.client.download_file(bucket_name, object_key, file_path)
            return True
        except (ClientError, BotoCoreError) as e:
            raise AWSProviderError(f"Failed to download file from S3: {str(e)}")
    
    def list_objects(self, bucket_name: str, prefix: str = '') -> List[Dict[str, Any]]:
        """List objects in S3 bucket"""
        try:
            response = self.client.list_objects_v2(Bucket=bucket_name, Prefix=prefix)
            return response.get('Contents', [])
        except (ClientError, BotoCoreError) as e:
            raise AWSProviderError(f"Failed to list S3 objects: {str(e)}")
```

### Step 6: Create Unit Tests
Create `crewai_app/tests/test_aws_services.py`:

```python
import pytest
from unittest.mock import Mock, patch
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
        mock_client.invoke_model.side_effect = Exception("Bedrock error")
        mock_boto_client.return_value = mock_client
        
        service = AWSBedrockService(config)
        service.client = mock_client
        
        with pytest.raises(AWSProviderError):
            service.generate_text("Test prompt")

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

class TestAWSRDSService:
    def test_rds_service_creation(self):
        """Test AWS RDS service creation"""
        config = {
            "region": "eu-west-1",
            "credentials": {"aws_access_key_id": "test-key", "aws_secret_access_key": "test-secret"}
        }
        
        service = AWSRDSService(config)
        assert service.region == "eu-west-1"

class TestAWSSQSService:
    def test_sqs_service_creation(self):
        """Test AWS SQS service creation"""
        config = {
            "region": "ap-southeast-1",
            "credentials": {"aws_access_key_id": "test-key", "aws_secret_access_key": "test-secret"}
        }
        
        service = AWSSQSService(config)
        assert service.region == "ap-southeast-1"

class TestAWSS3Service:
    def test_s3_service_creation(self):
        """Test AWS S3 service creation"""
        config = {
            "region": "ca-central-1",
            "credentials": {"aws_access_key_id": "test-key", "aws_secret_access_key": "test-secret"}
        }
        
        service = AWSS3Service(config)
        assert service.region == "ca-central-1"
```

### Step 7: Update README Documentation
Update `crewai_app/README.md` to include AWS services documentation:

```markdown
### AWS Services Integration
Comprehensive AWS service integration for production-ready cloud operations:

- **AWS Bedrock**: LLM operations with Claude and other foundation models
- **AWS OpenSearch**: Vector storage and semantic search capabilities
- **AWS RDS**: Managed database services with PostgreSQL/MySQL support
- **AWS SQS**: Message queuing for asynchronous processing
- **AWS S3**: Object storage for files, artifacts, and backups

#### AWS Service Usage
```python
from crewai_app.services.aws_bedrock_service import AWSBedrockService
from crewai_app.services.aws_s3_service import AWSS3Service

# AWS Bedrock for LLM operations
bedrock_config = {
    "region": "us-east-1",
    "credentials": {"aws_access_key_id": "your-key", "aws_secret_access_key": "your-secret"},
    "model_id": "anthropic.claude-3-sonnet-20240229-v1:0"
}
bedrock_service = AWSBedrockService(bedrock_config)
response = bedrock_service.generate_text("Your prompt here")

# AWS S3 for file storage
s3_config = {
    "region": "us-east-1",
    "credentials": {"aws_access_key_id": "your-key", "aws_secret_access_key": "your-secret"}
}
s3_service = AWSS3Service(s3_config)
s3_service.upload_file("my-bucket", "local-file.txt", "remote-file.txt")
```
```

## Testing Instructions
1. Run unit tests: `python -m pytest crewai_app/tests/test_aws_services.py -v`
2. Test AWS service creation with valid configurations
3. Test error handling for invalid AWS credentials
4. Test service integration with cloud provider abstraction
5. Verify all services work with existing cloud provider service

## Acceptance Criteria
- All AWS services implement required methods
- AWS services integrate with cloud provider abstraction
- Comprehensive error handling for AWS-specific errors
- All unit tests pass
- Documentation updated with AWS service usage
- Services support configuration-driven setup
- Maintain compatibility with existing Azure services

## Dependencies
- `boto3` - AWS SDK for Python
- `botocore` - Low-level AWS service access
- Existing cloud provider abstraction from MINIONS-8

## Environment Variables
```bash
# AWS Configuration
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_OPENSEARCH_DOMAIN=your-opensearch-domain
AWS_S3_BUCKET=your-s3-bucket
AWS_SQS_QUEUE_URL=your-sqs-queue-url
AWS_RDS_INSTANCE_ID=your-rds-instance
```
