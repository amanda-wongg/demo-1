"""
Redash API Client for Cash Completeness Monitor
Handles all interactions with Redash for query execution and result retrieval.
"""

import requests
import time
import logging
from typing import Dict, Any, Optional
from urllib.parse import urljoin

logger = logging.getLogger(__name__)


class RedashClient:
    """Client for interacting with Redash API."""
    
    def __init__(self, base_url: str, api_key: str, timeout: int = 300):
        """
        Initialize Redash client.
        
        Args:
            base_url: Base URL of the Redash instance
            api_key: API key for authentication
            timeout: Query execution timeout in seconds
        """
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Key {api_key}',
            'Content-Type': 'application/json'
        })
        
        logger.info(f"Redash client initialized for {self.base_url}")
    
    def execute_query(self, query_id: int, parameters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute a query and return the results.
        
        Args:
            query_id: ID of the query to execute
            parameters: Query parameters to pass
            
        Returns:
            Query results as dictionary with columns and rows
        """
        logger.info(f"Executing query {query_id} with parameters: {parameters}")
        
        try:
            # Trigger query execution
            job_id = self._trigger_query_execution(query_id, parameters)
            
            # Wait for completion and get results
            result = self._wait_for_query_completion(job_id)
            
            logger.info(f"Query {query_id} executed successfully")
            return result
            
        except Exception as e:
            logger.error(f"Failed to execute query {query_id}: {str(e)}")
            raise
    
    def _trigger_query_execution(self, query_id: int, parameters: Optional[Dict[str, Any]] = None) -> str:
        """Trigger query execution and return job ID."""
        url = urljoin(self.base_url, f'/api/queries/{query_id}/results')
        
        payload = {}
        if parameters:
            payload['parameters'] = parameters
        
        response = self.session.post(url, json=payload)
        response.raise_for_status()
        
        job_data = response.json()
        job_id = job_data['job']['id']
        
        logger.debug(f"Query execution triggered, job ID: {job_id}")
        return job_id
    
    def _wait_for_query_completion(self, job_id: str) -> Dict[str, Any]:
        """Wait for query completion and return results."""
        url = urljoin(self.base_url, f'/api/jobs/{job_id}')
        
        start_time = time.time()
        
        while time.time() - start_time < self.timeout:
            response = self.session.get(url)
            response.raise_for_status()
            
            job_data = response.json()
            status = job_data['job']['status']
            
            if status == 3:  # Success
                logger.debug(f"Query job {job_id} completed successfully")
                return self._get_query_results(job_data['job']['query_result_id'])
            
            elif status == 4:  # Failed
                error_msg = job_data['job'].get('error', 'Unknown error')
                raise Exception(f"Query execution failed: {error_msg}")
            
            elif status in [1, 2]:  # Pending or Started
                logger.debug(f"Query job {job_id} still running (status: {status})")
                time.sleep(2)  # Poll every 2 seconds
            
            else:
                raise Exception(f"Unknown job status: {status}")
        
        raise TimeoutError(f"Query execution timed out after {self.timeout} seconds")
    
    def _get_query_results(self, result_id: int) -> Dict[str, Any]:
        """Retrieve query results by result ID."""
        url = urljoin(self.base_url, f'/api/query_results/{result_id}')
        
        response = self.session.get(url)
        response.raise_for_status()
        
        result_data = response.json()
        
        # Extract and format the results
        query_result = result_data['query_result']
        
        return {
            'columns': query_result['data']['columns'],
            'rows': query_result['data']['rows'],
            'metadata': {
                'id': result_id,
                'retrieved_at': query_result['retrieved_at'],
                'runtime': query_result['runtime'],
                'data_source_id': query_result['data_source_id']
            }
        }
    
    def test_connection(self) -> bool:
        """Test the connection to Redash."""
        try:
            url = urljoin(self.base_url, '/api/session')
            response = self.session.get(url)
            response.raise_for_status()
            
            logger.info("Redash connection test successful")
            return True
            
        except Exception as e:
            logger.error(f"Redash connection test failed: {str(e)}")
            return False
    
    def get_query_info(self, query_id: int) -> Dict[str, Any]:
        """Get information about a specific query."""
        try:
            url = urljoin(self.base_url, f'/api/queries/{query_id}')
            response = self.session.get(url)
            response.raise_for_status()
            
            query_data = response.json()
            
            return {
                'id': query_data['id'],
                'name': query_data['name'],
                'description': query_data.get('description', ''),
                'data_source_id': query_data['data_source_id'],
                'created_at': query_data['created_at'],
                'updated_at': query_data['updated_at']
            }
            
        except Exception as e:
            logger.error(f"Failed to get query info for {query_id}: {str(e)}")
            raise