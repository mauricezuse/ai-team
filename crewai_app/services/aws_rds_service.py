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
    
    def create_database_instance(self, instance_id: str, engine: str = 'postgres', 
                               instance_class: str = 'db.t3.micro', 
                               allocated_storage: int = 20,
                               master_username: str = 'admin',
                               master_password: str = 'password123') -> bool:
        """Create RDS database instance"""
        try:
            response = self.client.create_db_instance(
                DBInstanceIdentifier=instance_id,
                DBInstanceClass=instance_class,
                Engine=engine,
                MasterUsername=master_username,
                MasterUserPassword=master_password,
                AllocatedStorage=allocated_storage,
                BackupRetentionPeriod=7,
                MultiAZ=False,
                PubliclyAccessible=True,
                StorageEncrypted=True
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
    
    def get_database_status(self, instance_id: str) -> str:
        """Get RDS database status"""
        try:
            response = self.client.describe_db_instances(
                DBInstanceIdentifier=instance_id
            )
            return response['DBInstances'][0]['DBInstanceStatus']
        except (ClientError, BotoCoreError) as e:
            raise AWSProviderError(f"Failed to get RDS status: {str(e)}")
    
    def delete_database_instance(self, instance_id: str, skip_final_snapshot: bool = True) -> bool:
        """Delete RDS database instance"""
        try:
            self.client.delete_db_instance(
                DBInstanceIdentifier=instance_id,
                SkipFinalSnapshot=skip_final_snapshot
            )
            return True
        except (ClientError, BotoCoreError) as e:
            raise AWSProviderError(f"Failed to delete RDS instance: {str(e)}")
    
    def create_database_snapshot(self, instance_id: str, snapshot_id: str) -> bool:
        """Create RDS database snapshot"""
        try:
            self.client.create_db_snapshot(
                DBInstanceIdentifier=instance_id,
                DBSnapshotIdentifier=snapshot_id
            )
            return True
        except (ClientError, BotoCoreError) as e:
            raise AWSProviderError(f"Failed to create RDS snapshot: {str(e)}")
    
    def restore_database_from_snapshot(self, snapshot_id: str, instance_id: str) -> bool:
        """Restore RDS database from snapshot"""
        try:
            self.client.restore_db_instance_from_db_snapshot(
                DBInstanceIdentifier=instance_id,
                DBSnapshotIdentifier=snapshot_id
            )
            return True
        except (ClientError, BotoCoreError) as e:
            raise AWSProviderError(f"Failed to restore RDS from snapshot: {str(e)}")
    
    def list_database_instances(self) -> List[Dict[str, Any]]:
        """List all RDS database instances"""
        try:
            response = self.client.describe_db_instances()
            return response['DBInstances']
        except (ClientError, BotoCoreError) as e:
            raise AWSProviderError(f"Failed to list RDS instances: {str(e)}")
    
    def get_database_parameters(self, instance_id: str) -> List[Dict[str, Any]]:
        """Get database parameters"""
        try:
            response = self.client.describe_db_parameters(
                DBParameterGroupName=instance_id
            )
            return response['Parameters']
        except (ClientError, BotoCoreError) as e:
            raise AWSProviderError(f"Failed to get RDS parameters: {str(e)}")
    
    def modify_database_instance(self, instance_id: str, 
                               instance_class: Optional[str] = None,
                               allocated_storage: Optional[int] = None) -> bool:
        """Modify RDS database instance"""
        try:
            modify_params = {'DBInstanceIdentifier': instance_id}
            
            if instance_class:
                modify_params['DBInstanceClass'] = instance_class
            if allocated_storage:
                modify_params['AllocatedStorage'] = allocated_storage
            
            self.client.modify_db_instance(**modify_params)
            return True
        except (ClientError, BotoCoreError) as e:
            raise AWSProviderError(f"Failed to modify RDS instance: {str(e)}")
    
    def is_database_available(self, instance_id: str) -> bool:
        """Check if database is available"""
        try:
            status = self.get_database_status(instance_id)
            return status == 'available'
        except AWSProviderError:
            return False
