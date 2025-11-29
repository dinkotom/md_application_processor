#!/usr/bin/env python3
"""
Ecomail API Integration Module
Handles communication with Ecomail API for contact list management
"""

import requests
import os
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

# Ecomail API base URL
ECOMAIL_API_BASE = "https://api2.ecomailapp.cz"


class EcomailClient:
    """Client for interacting with Ecomail API"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Ecomail client
        
        Args:
            api_key: Ecomail API key. If not provided, will try to get from environment
        """
        self.api_key = api_key or os.environ.get('ECOMAIL_API_KEY')
        if not self.api_key:
            raise ValueError("Ecomail API key not provided and not found in environment")
        
        self.headers = {
            'key': self.api_key,
            'Content-Type': 'application/json'
        }
    
    def get_lists(self) -> Dict:
        """
        Get all contact lists from Ecomail
        
        Returns:
            Dict containing lists data or error information
        """
        try:
            url = f"{ECOMAIL_API_BASE}/lists"
            logger.info(f"Fetching lists from: {url}")
            logger.info(f"Using API key: {self.api_key[:10]}...") # Log first 10 chars only
            
            response = requests.get(url, headers=self.headers, timeout=10)
            
            logger.info(f"Response status code: {response.status_code}")
            
            if response.status_code == 200:
                return {
                    'success': True,
                    'data': response.json()
                }
            else:
                logger.error(f"Ecomail API error: {response.status_code} - {response.text}")
                return {
                    'success': False,
                    'error': f"API returned status code {response.status_code}",
                    'details': response.text
                }
        except requests.exceptions.Timeout:
            logger.error("Ecomail API request timeout")
            return {
                'success': False,
                'error': 'Request timeout - Ecomail API did not respond in time'
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"Ecomail API request failed: {e}")
            return {
                'success': False,
                'error': f'Connection error: {str(e)}'
            }
        except Exception as e:
            logger.error(f"Unexpected error in get_lists: {e}")
            return {
                'success': False,
                'error': f'Unexpected error: {str(e)}'
            }
    
    def get_list_details(self, list_id: int) -> Dict:
        """
        Get details about a specific contact list
        
        Args:
            list_id: ID of the list to retrieve
            
        Returns:
            Dict containing list details or error information
        """
        try:
            url = f"{ECOMAIL_API_BASE}/lists/{list_id}"
            response = requests.get(url, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                return {
                    'success': True,
                    'data': response.json()
                }
            else:
                return {
                    'success': False,
                    'error': f"API returned status code {response.status_code}"
                }
        except Exception as e:
            logger.error(f"Error getting list details: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_list_subscribers(self, list_id: int) -> Dict:
        """
        Get all subscribers from a specific list
        
        Args:
            list_id: ID of the list
            
        Returns:
            Dict containing subscribers data or error information
        """
        try:
            url = f"{ECOMAIL_API_BASE}/lists/{list_id}/subscribers"
            response = requests.get(url, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                return {
                    'success': True,
                    'data': response.json()
                }
            else:
                return {
                    'success': False,
                    'error': f"API returned status code {response.status_code}"
                }
        except Exception as e:
            logger.error(f"Error getting list subscribers: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def test_connection(self) -> Dict:
        """
        Test the API connection by attempting to fetch lists
        
        Returns:
            Dict with success status and message
        """
        result = self.get_lists()
        if result['success']:
            return {
                'success': True,
                'message': 'Connection successful! API key is valid.'
            }
        else:
            return {
                'success': False,
                'message': f"Connection failed: {result.get('error', 'Unknown error')}"
            }

    def create_list(self, name: str, from_name: Optional[str] = None, from_email: Optional[str] = None, reply_to: Optional[str] = None) -> Dict:
        """
        Create a new contact list in Ecomail
        
        Args:
            name: Name of the new list
            from_name: Sender name
            from_email: Sender email
            reply_to: Reply-to email
            
        Returns:
            Dict containing new list data or error information
        """
        try:
            url = f"{ECOMAIL_API_BASE}/lists"
            payload = {
                'name': name
            }
            if from_name:
                payload['from_name'] = from_name
            if from_email:
                payload['from_email'] = from_email
            if reply_to:
                payload['reply_to'] = reply_to
                
            response = requests.post(url, headers=self.headers, json=payload, timeout=10)
            
            if response.status_code == 200 or response.status_code == 201:
                return {
                    'success': True,
                    'data': response.json()
                }
            else:
                logger.error(f"Ecomail API error: {response.status_code} - {response.text}")
                return {
                    'success': False,
                    'error': f"API returned status code {response.status_code}",
                    'details': response.text
                }
        except Exception as e:
            logger.error(f"Error creating list: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def add_subscriber(self, list_id: int, subscriber_data: Dict) -> Dict:
        """
        Add a subscriber to a contact list
        
        Args:
            list_id: ID of the list
            subscriber_data: Dictionary containing subscriber data (must include 'email')
            
        Returns:
            Dict containing result or error information
        """
        try:
            url = f"{ECOMAIL_API_BASE}/lists/{list_id}/subscribe"
            
            # Ensure email is present
            if 'email' not in subscriber_data:
                return {
                    'success': False,
                    'error': 'Email is required in subscriber data'
                }
                
            payload = {
                'subscriber_data': subscriber_data,
                'update_existing': True,
                'trigger_autoresponders': False,
                'resubscribe': True
            }
            
            response = requests.post(url, headers=self.headers, json=payload, timeout=10)
            
            if response.status_code == 200:
                return {
                    'success': True,
                    'data': response.json()
                }
            else:
                logger.error(f"Ecomail API error adding subscriber: {response.status_code} - {response.text}")
                return {
                    'success': False,
                    'error': f"API returned status code {response.status_code}",
                    'details': response.text
                }
        except Exception as e:
            logger.error(f"Error adding subscriber: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def get_subscriber(self, email: str) -> Dict:
        """
        Get subscriber data by email
        
        Args:
            email: Subscriber's email address
            
        Returns:
            Dict containing subscriber data or error information
        """
        try:
            url = f"{ECOMAIL_API_BASE}/subscribers/{email}"
            
            response = requests.get(url, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                return {
                    'success': True,
                    'data': response.json()
                }
            elif response.status_code == 404:
                return {
                    'success': False,
                    'error': 'Subscriber not found'
                }
            else:
                logger.error(f"Ecomail API error fetching subscriber: {response.status_code} - {response.text}")
                return {
                    'success': False,
                    'error': f"API returned status code {response.status_code}",
                    'details': response.text
                }
        except Exception as e:
            logger.error(f"Error fetching subscriber: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def create_subscriber(self, list_id: int, subscriber_data: Dict) -> Dict:
        """
        Create or update a subscriber in a specific list
        
        Args:
            list_id: ID of the contact list
            subscriber_data: Dictionary containing subscriber details
            
        Returns:
            Dict containing operation result
        """
        try:
            url = f"{ECOMAIL_API_BASE}/lists/{list_id}/subscribe"
            
            # Ensure email is present
            if 'email' not in subscriber_data:
                return {
                    'success': False,
                    'error': 'Email is required'
                }
            
            
            # Extract tags if present (they go at the top level, not in subscriber_data)
            tags = subscriber_data.pop('tags', [])
            
            payload = {
                'subscriber_data': subscriber_data,
                'trigger_autoresponders': True,
                'update_existing': True,
                'resubscribe': True
            }
            
            # Add tags at the top level if present
            if tags:
                payload['tags'] = tags
            
            response = requests.post(url, headers=self.headers, json=payload, timeout=10)
            
            if response.status_code == 200:
                return {
                    'success': True,
                    'data': response.json()
                }
            else:
                logger.error(f"Ecomail API error creating subscriber: {response.status_code} - {response.text}")
                return {
                    'success': False,
                    'error': f"API returned status code {response.status_code}",
                    'details': response.text
                }
        except Exception as e:
            logger.error(f"Error creating subscriber: {e}")
            return {
                'success': False,
                'error': str(e)
            }

