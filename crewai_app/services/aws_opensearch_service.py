import boto3
import json
import requests
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
        
        # Initialize requests session for OpenSearch API calls
        self.session = requests.Session()
        self.session.auth = boto3.Session(
            aws_access_key_id=config['credentials']['aws_access_key_id'],
            aws_secret_access_key=config['credentials']['aws_secret_access_key'],
            region_name=self.region
        ).get_credentials()
    
    def create_index(self, index_name: str, mapping: Dict[str, Any]) -> bool:
        """Create OpenSearch index"""
        try:
            url = f"{self.endpoint}/{index_name}"
            headers = {'Content-Type': 'application/json'}
            
            response = self.session.put(url, json=mapping, headers=headers)
            response.raise_for_status()
            return True
        except (ClientError, BotoCoreError, requests.RequestException) as e:
            raise AWSProviderError(f"Failed to create OpenSearch index: {str(e)}")
    
    def index_document(self, index_name: str, document: Dict[str, Any], doc_id: str) -> bool:
        """Index document in OpenSearch"""
        try:
            url = f"{self.endpoint}/{index_name}/_doc/{doc_id}"
            headers = {'Content-Type': 'application/json'}
            
            response = self.session.put(url, json=document, headers=headers)
            response.raise_for_status()
            return True
        except (ClientError, BotoCoreError, requests.RequestException) as e:
            raise AWSProviderError(f"Failed to index document: {str(e)}")
    
    def search_documents(self, index_name: str, query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search documents in OpenSearch"""
        try:
            url = f"{self.endpoint}/{index_name}/_search"
            headers = {'Content-Type': 'application/json'}
            
            response = self.session.post(url, json=query, headers=headers)
            response.raise_for_status()
            
            result = response.json()
            return result.get('hits', {}).get('hits', [])
        except (ClientError, BotoCoreError, requests.RequestException) as e:
            raise AWSProviderError(f"Failed to search documents: {str(e)}")
    
    def delete_document(self, index_name: str, doc_id: str) -> bool:
        """Delete document from OpenSearch"""
        try:
            url = f"{self.endpoint}/{index_name}/_doc/{doc_id}"
            
            response = self.session.delete(url)
            response.raise_for_status()
            return True
        except (ClientError, BotoCoreError, requests.RequestException) as e:
            raise AWSProviderError(f"Failed to delete document: {str(e)}")
    
    def delete_index(self, index_name: str) -> bool:
        """Delete OpenSearch index"""
        try:
            url = f"{self.endpoint}/{index_name}"
            
            response = self.session.delete(url)
            response.raise_for_status()
            return True
        except (ClientError, BotoCoreError, requests.RequestException) as e:
            raise AWSProviderError(f"Failed to delete index: {str(e)}")
    
    def get_index_mapping(self, index_name: str) -> Dict[str, Any]:
        """Get index mapping"""
        try:
            url = f"{self.endpoint}/{index_name}/_mapping"
            
            response = self.session.get(url)
            response.raise_for_status()
            
            return response.json()
        except (ClientError, BotoCoreError, requests.RequestException) as e:
            raise AWSProviderError(f"Failed to get index mapping: {str(e)}")
    
    def bulk_index_documents(self, index_name: str, documents: List[Dict[str, Any]]) -> bool:
        """Bulk index multiple documents"""
        try:
            url = f"{self.endpoint}/_bulk"
            headers = {'Content-Type': 'application/x-ndjson'}
            
            bulk_data = []
            for doc in documents:
                bulk_data.append(json.dumps({"index": {"_index": index_name, "_id": doc.get("id")}}))
                bulk_data.append(json.dumps(doc))
            
            response = self.session.post(url, data='\n'.join(bulk_data), headers=headers)
            response.raise_for_status()
            return True
        except (ClientError, BotoCoreError, requests.RequestException) as e:
            raise AWSProviderError(f"Failed to bulk index documents: {str(e)}")
    
    def get_domain_info(self) -> Dict[str, Any]:
        """Get OpenSearch domain information"""
        try:
            response = self.client.describe_elasticsearch_domain(DomainName=self.domain)
            return response['DomainStatus']
        except (ClientError, BotoCoreError) as e:
            raise AWSProviderError(f"Failed to get domain info: {str(e)}")
    
    def is_domain_available(self) -> bool:
        """Check if OpenSearch domain is available"""
        try:
            domain_info = self.get_domain_info()
            return domain_info.get('Processing', False) == False
        except AWSProviderError:
            return False
