import boto3
import json
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
    
    def create_queue(self, queue_name: str, attributes: Optional[Dict[str, str]] = None) -> str:
        """Create SQS queue"""
        try:
            queue_attributes = attributes or {}
            response = self.client.create_queue(QueueName=queue_name, Attributes=queue_attributes)
            return response['QueueUrl']
        except (ClientError, BotoCoreError) as e:
            raise AWSProviderError(f"Failed to create SQS queue: {str(e)}")
    
    def get_queue_url(self, queue_name: str) -> str:
        """Get SQS queue URL"""
        try:
            response = self.client.get_queue_url(QueueName=queue_name)
            return response['QueueUrl']
        except (ClientError, BotoCoreError) as e:
            raise AWSProviderError(f"Failed to get SQS queue URL: {str(e)}")
    
    def send_message(self, queue_url: str, message: str, 
                    message_attributes: Optional[Dict[str, Any]] = None,
                    delay_seconds: int = 0) -> bool:
        """Send message to SQS queue"""
        try:
            send_params = {
                'QueueUrl': queue_url,
                'MessageBody': message,
                'DelaySeconds': delay_seconds
            }
            
            if message_attributes:
                send_params['MessageAttributes'] = message_attributes
            
            self.client.send_message(**send_params)
            return True
        except (ClientError, BotoCoreError) as e:
            raise AWSProviderError(f"Failed to send SQS message: {str(e)}")
    
    def send_message_batch(self, queue_url: str, messages: List[Dict[str, Any]]) -> bool:
        """Send multiple messages to SQS queue"""
        try:
            entries = []
            for i, message in enumerate(messages):
                entry = {
                    'Id': str(i),
                    'MessageBody': message.get('body', ''),
                }
                if 'attributes' in message:
                    entry['MessageAttributes'] = message['attributes']
                entries.append(entry)
            
            self.client.send_message_batch(QueueUrl=queue_url, Entries=entries)
            return True
        except (ClientError, BotoCoreError) as e:
            raise AWSProviderError(f"Failed to send SQS message batch: {str(e)}")
    
    def receive_messages(self, queue_url: str, max_messages: int = 10, 
                        wait_time_seconds: int = 0,
                        visibility_timeout: int = 30) -> List[Dict[str, Any]]:
        """Receive messages from SQS queue"""
        try:
            response = self.client.receive_message(
                QueueUrl=queue_url,
                MaxNumberOfMessages=max_messages,
                WaitTimeSeconds=wait_time_seconds,
                VisibilityTimeout=visibility_timeout
            )
            return response.get('Messages', [])
        except (ClientError, BotoCoreError) as e:
            raise AWSProviderError(f"Failed to receive SQS messages: {str(e)}")
    
    def delete_message(self, queue_url: str, receipt_handle: str) -> bool:
        """Delete message from SQS queue"""
        try:
            self.client.delete_message(
                QueueUrl=queue_url,
                ReceiptHandle=receipt_handle
            )
            return True
        except (ClientError, BotoCoreError) as e:
            raise AWSProviderError(f"Failed to delete SQS message: {str(e)}")
    
    def delete_message_batch(self, queue_url: str, messages: List[Dict[str, str]]) -> bool:
        """Delete multiple messages from SQS queue"""
        try:
            entries = []
            for i, message in enumerate(messages):
                entries.append({
                    'Id': str(i),
                    'ReceiptHandle': message['receipt_handle']
                })
            
            self.client.delete_message_batch(QueueUrl=queue_url, Entries=entries)
            return True
        except (ClientError, BotoCoreError) as e:
            raise AWSProviderError(f"Failed to delete SQS message batch: {str(e)}")
    
    def purge_queue(self, queue_url: str) -> bool:
        """Purge all messages from SQS queue"""
        try:
            self.client.purge_queue(QueueUrl=queue_url)
            return True
        except (ClientError, BotoCoreError) as e:
            raise AWSProviderError(f"Failed to purge SQS queue: {str(e)}")
    
    def delete_queue(self, queue_url: str) -> bool:
        """Delete SQS queue"""
        try:
            self.client.delete_queue(QueueUrl=queue_url)
            return True
        except (ClientError, BotoCoreError) as e:
            raise AWSProviderError(f"Failed to delete SQS queue: {str(e)}")
    
    def get_queue_attributes(self, queue_url: str, 
                           attribute_names: Optional[List[str]] = None) -> Dict[str, str]:
        """Get SQS queue attributes"""
        try:
            if attribute_names is None:
                attribute_names = ['All']
            
            response = self.client.get_queue_attributes(
                QueueUrl=queue_url,
                AttributeNames=attribute_names
            )
            return response['Attributes']
        except (ClientError, BotoCoreError) as e:
            raise AWSProviderError(f"Failed to get SQS queue attributes: {str(e)}")
    
    def set_queue_attributes(self, queue_url: str, attributes: Dict[str, str]) -> bool:
        """Set SQS queue attributes"""
        try:
            self.client.set_queue_attributes(QueueUrl=queue_url, Attributes=attributes)
            return True
        except (ClientError, BotoCoreError) as e:
            raise AWSProviderError(f"Failed to set SQS queue attributes: {str(e)}")
    
    def list_queues(self, queue_name_prefix: Optional[str] = None) -> List[str]:
        """List SQS queues"""
        try:
            params = {}
            if queue_name_prefix:
                params['QueueNamePrefix'] = queue_name_prefix
            
            response = self.client.list_queues(**params)
            return response.get('QueueUrls', [])
        except (ClientError, BotoCoreError) as e:
            raise AWSProviderError(f"Failed to list SQS queues: {str(e)}")
    
    def get_queue_arn(self, queue_url: str) -> str:
        """Get SQS queue ARN"""
        try:
            attributes = self.get_queue_attributes(queue_url, ['QueueArn'])
            return attributes['QueueArn']
        except (ClientError, BotoCoreError) as e:
            raise AWSProviderError(f"Failed to get SQS queue ARN: {str(e)}")
