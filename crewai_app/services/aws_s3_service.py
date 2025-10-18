import boto3
import os
from typing import Dict, Any, List, Optional, BinaryIO
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
    
    def create_bucket(self, bucket_name: str, region: Optional[str] = None) -> bool:
        """Create S3 bucket"""
        try:
            if region and region != 'us-east-1':
                self.client.create_bucket(
                    Bucket=bucket_name,
                    CreateBucketConfiguration={'LocationConstraint': region}
                )
            else:
                self.client.create_bucket(Bucket=bucket_name)
            return True
        except (ClientError, BotoCoreError) as e:
            raise AWSProviderError(f"Failed to create S3 bucket: {str(e)}")
    
    def upload_file(self, bucket_name: str, file_path: str, object_key: str,
                   extra_args: Optional[Dict[str, Any]] = None) -> bool:
        """Upload file to S3"""
        try:
            upload_params = {
                'Filename': file_path,
                'Bucket': bucket_name,
                'Key': object_key
            }
            
            if extra_args:
                upload_params['ExtraArgs'] = extra_args
            
            self.client.upload_file(**upload_params)
            return True
        except (ClientError, BotoCoreError) as e:
            raise AWSProviderError(f"Failed to upload file to S3: {str(e)}")
    
    def upload_fileobj(self, bucket_name: str, file_obj: BinaryIO, object_key: str,
                      extra_args: Optional[Dict[str, Any]] = None) -> bool:
        """Upload file object to S3"""
        try:
            upload_params = {
                'Fileobj': file_obj,
                'Bucket': bucket_name,
                'Key': object_key
            }
            
            if extra_args:
                upload_params['ExtraArgs'] = extra_args
            
            self.client.upload_fileobj(**upload_params)
            return True
        except (ClientError, BotoCoreError) as e:
            raise AWSProviderError(f"Failed to upload file object to S3: {str(e)}")
    
    def download_file(self, bucket_name: str, object_key: str, file_path: str) -> bool:
        """Download file from S3"""
        try:
            self.client.download_file(bucket_name, object_key, file_path)
            return True
        except (ClientError, BotoCoreError) as e:
            raise AWSProviderError(f"Failed to download file from S3: {str(e)}")
    
    def download_fileobj(self, bucket_name: str, object_key: str, file_obj: BinaryIO) -> bool:
        """Download file object from S3"""
        try:
            self.client.download_fileobj(bucket_name, object_key, file_obj)
            return True
        except (ClientError, BotoCoreError) as e:
            raise AWSProviderError(f"Failed to download file object from S3: {str(e)}")
    
    def get_object(self, bucket_name: str, object_key: str) -> Dict[str, Any]:
        """Get object from S3"""
        try:
            response = self.client.get_object(Bucket=bucket_name, Key=object_key)
            return response
        except (ClientError, BotoCoreError) as e:
            raise AWSProviderError(f"Failed to get object from S3: {str(e)}")
    
    def put_object(self, bucket_name: str, object_key: str, body: bytes,
                  content_type: Optional[str] = None,
                  metadata: Optional[Dict[str, str]] = None) -> bool:
        """Put object to S3"""
        try:
            put_params = {
                'Bucket': bucket_name,
                'Key': object_key,
                'Body': body
            }
            
            if content_type:
                put_params['ContentType'] = content_type
            if metadata:
                put_params['Metadata'] = metadata
            
            self.client.put_object(**put_params)
            return True
        except (ClientError, BotoCoreError) as e:
            raise AWSProviderError(f"Failed to put object to S3: {str(e)}")
    
    def delete_object(self, bucket_name: str, object_key: str) -> bool:
        """Delete object from S3"""
        try:
            self.client.delete_object(Bucket=bucket_name, Key=object_key)
            return True
        except (ClientError, BotoCoreError) as e:
            raise AWSProviderError(f"Failed to delete object from S3: {str(e)}")
    
    def delete_objects(self, bucket_name: str, object_keys: List[str]) -> bool:
        """Delete multiple objects from S3"""
        try:
            objects = [{'Key': key} for key in object_keys]
            self.client.delete_objects(
                Bucket=bucket_name,
                Delete={'Objects': objects}
            )
            return True
        except (ClientError, BotoCoreError) as e:
            raise AWSProviderError(f"Failed to delete objects from S3: {str(e)}")
    
    def list_objects(self, bucket_name: str, prefix: str = '', 
                    max_keys: int = 1000) -> List[Dict[str, Any]]:
        """List objects in S3 bucket"""
        try:
            response = self.client.list_objects_v2(
                Bucket=bucket_name,
                Prefix=prefix,
                MaxKeys=max_keys
            )
            return response.get('Contents', [])
        except (ClientError, BotoCoreError) as e:
            raise AWSProviderError(f"Failed to list S3 objects: {str(e)}")
    
    def list_buckets(self) -> List[Dict[str, Any]]:
        """List all S3 buckets"""
        try:
            response = self.client.list_buckets()
            return response.get('Buckets', [])
        except (ClientError, BotoCoreError) as e:
            raise AWSProviderError(f"Failed to list S3 buckets: {str(e)}")
    
    def bucket_exists(self, bucket_name: str) -> bool:
        """Check if S3 bucket exists"""
        try:
            self.client.head_bucket(Bucket=bucket_name)
            return True
        except (ClientError, BotoCoreError):
            return False
    
    def object_exists(self, bucket_name: str, object_key: str) -> bool:
        """Check if S3 object exists"""
        try:
            self.client.head_object(Bucket=bucket_name, Key=object_key)
            return True
        except (ClientError, BotoCoreError):
            return False
    
    def get_object_metadata(self, bucket_name: str, object_key: str) -> Dict[str, Any]:
        """Get object metadata from S3"""
        try:
            response = self.client.head_object(Bucket=bucket_name, Key=object_key)
            return response
        except (ClientError, BotoCoreError) as e:
            raise AWSProviderError(f"Failed to get object metadata from S3: {str(e)}")
    
    def copy_object(self, source_bucket: str, source_key: str, 
                   dest_bucket: str, dest_key: str) -> bool:
        """Copy object within S3"""
        try:
            copy_source = {'Bucket': source_bucket, 'Key': source_key}
            self.client.copy_object(
                CopySource=copy_source,
                Bucket=dest_bucket,
                Key=dest_key
            )
            return True
        except (ClientError, BotoCoreError) as e:
            raise AWSProviderError(f"Failed to copy object in S3: {str(e)}")
    
    def generate_presigned_url(self, bucket_name: str, object_key: str,
                              expiration: int = 3600, http_method: str = 'GET') -> str:
        """Generate presigned URL for S3 object"""
        try:
            response = self.client.generate_presigned_url(
                'get_object',
                Params={'Bucket': bucket_name, 'Key': object_key},
                ExpiresIn=expiration
            )
            return response
        except (ClientError, BotoCoreError) as e:
            raise AWSProviderError(f"Failed to generate presigned URL: {str(e)}")
    
    def set_bucket_policy(self, bucket_name: str, policy: str) -> bool:
        """Set S3 bucket policy"""
        try:
            self.client.put_bucket_policy(Bucket=bucket_name, Policy=policy)
            return True
        except (ClientError, BotoCoreError) as e:
            raise AWSProviderError(f"Failed to set S3 bucket policy: {str(e)}")
    
    def get_bucket_policy(self, bucket_name: str) -> str:
        """Get S3 bucket policy"""
        try:
            response = self.client.get_bucket_policy(Bucket=bucket_name)
            return response['Policy']
        except (ClientError, BotoCoreError) as e:
            raise AWSProviderError(f"Failed to get S3 bucket policy: {str(e)}")
    
    def delete_bucket(self, bucket_name: str) -> bool:
        """Delete S3 bucket"""
        try:
            self.client.delete_bucket(Bucket=bucket_name)
            return True
        except (ClientError, BotoCoreError) as e:
            raise AWSProviderError(f"Failed to delete S3 bucket: {str(e)}")
