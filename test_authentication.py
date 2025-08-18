"""
System Initiative Session Manager with Environment Variable Support
"""

import os
import requests
import json
from typing import Optional, List, Dict, Any
from system_initiative_api_client import ApiClient, Configuration


class SISession:
    """
    System Initiative API session manager with environment variable support.
    
    This version uses direct HTTP requests for operations that have auth issues,
    while still providing a clean interface.
    """
    
    def __init__(
        self, 
        si_host: Optional[str] = None,
        workspace_id: Optional[str] = None,
        api_token: Optional[str] = None,
        verify_ssl: bool = True
    ):
        """
        Initialize the System Initiative session.
        
        Args:
            si_host: URL of the System Initiative server. 
                    Defaults to "https://api.systeminit.com" or SI_HOST env var
            workspace_id: ID of the workspace to work with.
                         Defaults to SI_WORKSPACE_ID env var
            api_token: API token for authentication.
                      Defaults to SI_API_TOKEN env var
            verify_ssl: Whether to verify SSL certificates
        """
        # Set defaults from environment variables
        self.si_host = si_host or os.getenv('SI_HOST', 'https://api.systeminit.com')
        self.workspace_id = workspace_id or os.getenv('SI_WORKSPACE_ID')
        self.api_token = api_token or os.getenv('SI_API_TOKEN')
        self.verify_ssl = verify_ssl
        
        # Validate required parameters
        if not self.workspace_id:
            raise ValueError(
                "workspace_id is required. Provide it as an argument or set SI_WORKSPACE_ID environment variable."
            )
        
        # Setup HTTP session for direct API calls
        self.session = requests.Session()
        if self.api_token:
            self.session.headers.update({
                'Authorization': f'Bearer {self.api_token}',
                'Content-Type': 'application/json'
            })
        self.session.verify = verify_ssl
        
        # Also setup the original API client for operations that work
        try:
            config = Configuration(host=self.si_host)
            if self.api_token:
                config.access_token = self.api_token
            config.verify_ssl = verify_ssl
            self.api_client = ApiClient(configuration=config)
        except Exception as e:
            print(f"Warning: Could not initialize API client: {e}")
            self.api_client = None
    
    @classmethod
    def from_env(cls) -> 'SISession':
        """
        Create a session using only environment variables.
        
        Returns:
            SISession configured from environment variables
            
        Raises:
            ValueError: If required environment variables are missing
        """
        return cls()
    
    def test_connection(self) -> bool:
        """
        Test the connection to the System Initiative API.
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            url = f"{self.si_host}/v1/workspaces/{self.workspace_id}/change-sets"
            response = self.session.get(url)
            return response.status_code == 200
        except Exception as e:
            print(f"Connection test failed: {e}")
            return False
    
    def get_change_sets(self) -> List[Dict[str, Any]]:
        """
        Get all change sets for the workspace using direct HTTP (SDK auth is broken).
        
        Returns:
            List of change set dictionaries
        """
        try:
            # Use direct HTTP since SDK auth is broken
            url = f"{self.si_host}/workspaces/{self.workspace_id}/changeSets"
            response = self.session.get(url)
            
            if response.status_code == 200:
                data = response.json()
                
                # Convert the response format to match what the app expects
                change_sets = []
                changesets_data = data.get('changeSets', [])
                
                for cs in changesets_data:
                    change_set_info = {
                        "id": cs.get('id', 'N/A'),
                        "name": cs.get('name', 'Unknown'),
                        "status": cs.get('status', 'unknown'),
                        "is_head": cs.get('isHead', False)
                    }
                    change_sets.append(change_set_info)
                
                print(f"✅ Found {len(change_sets)} change set(s)")
                return change_sets
            else:
                print(f"❌ Failed to get change sets: {response.status_code} {response.text}")
                return []
                
        except Exception as e:
            print(f"❌ Error getting change sets: {e}")
            return []
    
    def get_components(self, change_set_id: str) -> List[Dict[str, Any]]:
        """
        Get all components in a change set using direct HTTP.
        
        Args:
            change_set_id: The change set ID to query
            
        Returns:
            List of component dictionaries
        """
        try:
            url = f"{self.si_host}/v1/workspaces/{self.workspace_id}/change-sets/{change_set_id}/components"
            response = self.session.get(url)
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Failed to get components: {response.status_code} {response.text}")
                return []
        except Exception as e:
            print(f"Error getting components: {e}")
            return []
    
    def get_schemas(self, change_set_id: str) -> List[Dict[str, Any]]:
        """
        Get all available schemas using direct HTTP.
        
        Args:
            change_set_id: The change set ID to query
            
        Returns:
            List of schema dictionaries
        """
        try:
            url = f"{self.si_host}/v1/workspaces/{self.workspace_id}/change-sets/{change_set_id}/schemas"
            response = self.session.get(url)
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Failed to get schemas: {response.status_code} {response.text}")
                return []
        except Exception as e:
            print(f"Error getting schemas: {e}")
            return []
    
    def create_change_set(self, name: str, base_change_set_id: Optional[str] = None) -> Optional[str]:
        """
        Create a new change set.
        
        Args:
            name: Name for the new change set
            base_change_set_id: Optional base change set to branch from
            
        Returns:
            Change set ID if successful, None otherwise
        """
        try:
            url = f"{self.si_host}/v1/workspaces/{self.workspace_id}/change-sets"
            
            payload = {"name": name}
            if base_change_set_id:
                payload["base_change_set_id"] = base_change_set_id
            
            response = self.session.post(url, json=payload)
            
            if response.status_code == 200:
                result = response.json()
                return result.get("id")
            else:
                print(f"Failed to create change set: {response.status_code} {response.text}")
                return None
        except Exception as e:
            print(f"Error creating change set: {e}")
            return None
    
    def find_components_by_name(self, change_set_id: str, name_pattern: str) -> List[Dict[str, Any]]:
        """
        Find components matching a name pattern.
        
        Args:
            change_set_id: The change set ID to search in
            name_pattern: Pattern to match (case-insensitive substring)
            
        Returns:
            List of matching components
        """
        components = self.get_components(change_set_id)
        pattern_lower = name_pattern.lower()
        
        return [
            comp for comp in components 
            if pattern_lower in comp.get("display_name", "").lower()
        ]
    
    @staticmethod
    def check_env_vars():
        """
        Check and display the status of SI environment variables.
        Useful for debugging configuration.
        """
        env_vars = {
            'SI_HOST': os.getenv('SI_HOST'),
            'SI_WORKSPACE_ID': os.getenv('SI_WORKSPACE_ID'), 
            'SI_API_TOKEN': os.getenv('SI_API_TOKEN')
        }
        
        print("System Initiative Environment Variables:")
        print("-" * 40)
        
        for var_name, var_value in env_vars.items():
            if var_value:
                if 'TOKEN' in var_name:
                    display_value = f"***{var_value[-4:]}" if len(var_value) > 4 else "***"
                else:
                    display_value = var_value
                print(f"✓ {var_name} = {display_value}")
            else:
                print(f"✗ {var_name} = (not set)")
        
        print("-" * 40)
        print("Defaults:")
        print(f"  SI_HOST defaults to: https://api.systeminit.com")
        print(f"  SI_WORKSPACE_ID: (required - no default)")
        print(f"  SI_API_TOKEN: (optional for local development)")

    def __str__(self) -> str:
        """String representation of the session"""
        auth_status = "authenticated" if self.api_token else "no auth"
        return f"SISession(host={self.si_host}, workspace={self.workspace_id}, {auth_status})"

    def __repr__(self) -> str:
        """Detailed representation of the session"""
        return (f"SISession(si_host='{self.si_host}', workspace_id='{self.workspace_id}', "
                f"api_token={'***' if self.api_token else 'None'}, verify_ssl={self.verify_ssl})")


class SISessionManager:
    """
    Manage multiple SI sessions for different environments
    """
    
    def __init__(self):
        self.sessions: Dict[str, SISession] = {}
        self.default_session: Optional[str] = None
    
    def add_session(self, name: str, session: SISession):
        """Add a named session"""
        self.sessions[name] = session
        if self.default_session is None:
            self.default_session = name
    
    def get_session(self, name: Optional[str] = None) -> Optional[SISession]:
        """Get a session by name, or the default session"""
        if name is None:
            name = self.default_session
        return self.sessions.get(name)
    
    def set_default(self, name: str):
        """Set the default session"""
        if name in self.sessions:
            self.default_session = name
        else:
            raise ValueError(f"Session '{name}' not found")
    
    def list_sessions(self) -> List[str]:
        """List all session names"""
        return list(self.sessions.keys())