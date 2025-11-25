"""
Mocked Ecomail API integration module.
This module simulates the Ecomail API for testing purposes.
"""
import time
from typing import Dict

def export_to_ecomail(applicant_data: Dict[str, str]) -> Dict[str, any]:
    """
    Simulates exporting an applicant to Ecomail.
    
    Args:
        applicant_data: Dictionary containing applicant information
        
    Returns:
        Dictionary with success status and message
    """
    # Simulate API delay
    time.sleep(0.5)
    
    # Log the export (in real implementation, this would make an API call)
    print(f"[MOCK] Exporting to Ecomail:")
    print(f"  Email: {applicant_data.get('email')}")
    print(f"  Name: {applicant_data.get('first_name')} {applicant_data.get('last_name')}")
    print(f"  Membership ID: {applicant_data.get('membership_id')}")
    
    # Simulate successful response
    return {
        "success": True,
        "message": "Successfully exported to Ecomail",
        "subscriber_id": f"mock_{applicant_data.get('id', '0')}"
    }
