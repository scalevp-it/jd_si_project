"""
System Initiative Session Manager with Environment Variable Support
"""

import os
import json
from typing import Optional, List, Dict, Any
from system_initiative_api_client import ApiClient, Configuration


class SISession:
    """
    System Initiative API session manager with environment variable support.
    
    Uses the official System Initiative SDK for all API operations.
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
        
        # Setup the API client for all operations
        try:
            config = Configuration(host=self.si_host)
            config.verify_ssl = verify_ssl
            self.api_client = ApiClient(configuration=config)
            
            # Set the Authorization header directly on the API client
            if self.api_token:
                self.api_client.default_headers['Authorization'] = f"Bearer {self.api_token}"
                
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
        Test the connection to the System Initiative API using SDK.
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            from system_initiative_api_client import ChangeSetsApi
            changesets_api = ChangeSetsApi(self.api_client)
            
            # Try to list changesets as a connection test
            response = changesets_api.list_change_sets(workspace_id=self.workspace_id)
            return True  # If no exception, connection is good
        except Exception as e:
            print(f"Connection test failed: {e}")
            return False
    
    def get_change_sets(self) -> List[Dict[str, Any]]:
        """
        Get all change sets for the workspace using the SDK with fixed authentication.
        
        Returns:
            List of change set dictionaries
        """
        try:
            from system_initiative_api_client import ChangeSetsApi
            changesets_api = ChangeSetsApi(self.api_client)
            
            # Use the correct method name: list_change_sets (plural)
            response = changesets_api.list_change_sets(workspace_id=self.workspace_id)
            
            change_sets = []
            # Handle the response structure
            if hasattr(response, 'change_sets'):
                change_sets_data = response.change_sets
            elif hasattr(response, 'data'):
                change_sets_data = response.data
            elif isinstance(response, list):
                change_sets_data = response
            else:
                # Try to access as dictionary
                change_sets_data = response.get('changeSets', []) if hasattr(response, 'get') else []
            
            # Convert to list of dictionaries
            for cs in change_sets_data:
                if hasattr(cs, 'id'):
                    # SDK object with attributes
                    change_set_info = {
                        "id": getattr(cs, 'id', 'N/A'),
                        "name": getattr(cs, 'name', 'Unknown'),
                        "status": getattr(cs, 'status', 'unknown'),
                        "created_at": getattr(cs, 'created_at', None),
                    }
                else:
                    # Dictionary object
                    change_set_info = {
                        "id": cs.get('id', 'N/A'),
                        "name": cs.get('name', 'Unknown'),
                        "status": cs.get('status', 'unknown'),
                        "is_head": cs.get('isHead', False)
                    }
                change_sets.append(change_set_info)
            
            print(f"✅ Found {len(change_sets)} change set(s)")
            return change_sets
            
        except Exception as e:
            print(f"❌ Error getting change sets with SDK: {e}")
            import traceback
            print(f"Full traceback: {traceback.format_exc()}")
            return []
    
    def get_components(self, change_set_id: str) -> List[Dict[str, Any]]:
        """
        Get all components in a change set using the SDK, bypassing Pydantic validation.
        
        Args:
            change_set_id: The change set ID to query
            
        Returns:
            List of component dictionaries
        """
        try:
            from system_initiative_api_client import ComponentsApi
            components_api = ComponentsApi(self.api_client)
            
            # Use the _without_preload_content version to bypass Pydantic parsing issues
            response = components_api.list_components_without_preload_content(
                workspace_id=self.workspace_id,
                change_set_id=change_set_id
            )
            
            # Parse the raw response directly
            if hasattr(response, 'data'):
                # Parse the raw JSON response
                import json
                raw_data = response.data.decode('utf-8') if hasattr(response.data, 'decode') else response.data
                data = json.loads(raw_data) if isinstance(raw_data, str) else raw_data
                
                components = []
                
                # Handle the response structure
                if isinstance(data, dict) and 'components' in data:
                    components_data = data['components']
                elif isinstance(data, list):
                    components_data = data
                else:
                    components_data = data
                
                # Process each component
                for comp in components_data:
                    if isinstance(comp, str):
                        # Component ID only - get full details
                        try:
                            detail_response = components_api.get_component_without_preload_content(
                                workspace_id=self.workspace_id,
                                change_set_id=change_set_id,
                                component_id=comp
                            )
                            
                            if hasattr(detail_response, 'data'):
                                detail_raw = detail_response.data.decode('utf-8') if hasattr(detail_response.data, 'decode') else detail_response.data
                                detail_data = json.loads(detail_raw) if isinstance(detail_raw, str) else detail_raw
                                
                                # Extract component details from nested structure
                                if 'component' in detail_data:
                                    comp_data = detail_data['component']
                                    component_info = {
                                        "id": comp,
                                        "name": comp_data.get('name', comp),
                                        "display_name": comp_data.get('name', comp),
                                        "schema_id": comp_data.get('schemaId', 'N/A'),
                                        "schema_variant_id": comp_data.get('schemaVariantId', 'N/A'),
                                        "schema_name": self._get_schema_name(change_set_id, comp_data.get('schemaVariantId'), comp_data.get('schemaId')), # Pass schema_id as fallback),
                                        "resource_id": comp_data.get('resourceId', ''),
                                        "to_delete": comp_data.get('toDelete', False),
                                        "can_be_upgraded": comp_data.get('canBeUpgraded', False),
                                        "created_at": comp_data.get('createdAt', None),
                                    }
                                else:
                                    component_info = {
                                        "id": comp,
                                        "name": f"Component {comp[:8]}...",
                                        "display_name": f"Component {comp[:8]}...",
                                        "schema_name": "Unknown Schema"
                                    }
                            else:
                                component_info = {
                                    "id": comp,
                                    "name": f"Component {comp[:8]}...",
                                    "display_name": f"Component {comp[:8]}...",
                                    "schema_name": "Unknown Schema"
                                }
                        except Exception as detail_error:
                            print(f"Warning: Could not get details for component {comp}: {detail_error}")
                            component_info = {
                                "id": comp,
                                "name": f"Component {comp[:8]}...",
                                "display_name": f"Component {comp[:8]}...",
                                "schema_name": "Unknown Schema"
                            }
                    else:
                        # Component is already a dictionary/object
                        # FIXED: Use _get_schema_name instead of raw schemaName
                        schema_variant_id = comp.get('schemaVariantId') or comp.get('schema_variant_id')
                        resolved_schema_name = self._get_schema_name(change_set_id, schema_variant_id) if schema_variant_id else "Unknown Schema"
                        
                        component_info = {
                            "id": comp.get('id', 'N/A'),
                            "name": comp.get('name', comp.get('displayName', 'Unknown')),
                            "display_name": comp.get('name', comp.get('displayName', 'Unknown')),
                            "schema_name": resolved_schema_name,  # FIXED: Use resolved name
                            "created_at": comp.get('createdAt', None),
                        }
                    
                    components.append(component_info)
                
                print(f"✅ Found {len(components)} component(s) using raw SDK response")
                return components
            
            else:
                print(f"❌ Unexpected response format from SDK")
                return []
            
        except Exception as e:
            print(f"❌ Error getting components with SDK: {e}")
            print(f"Error type: {type(e)}")
            import traceback
            print(f"Full traceback: {traceback.format_exc()}")
            return []
    
    def _get_schema_name(self, change_set_id: str, schema_variant_id: str, schema_id: str = None) -> str:
        """
        Get the schema name from a schema variant ID, with fallback to schema ID.
        
        Args:
            change_set_id: The change set ID
            schema_variant_id: The schema variant ID to look up
            schema_id: Optional schema ID to use as fallback if variant lookup fails
            
        Returns:
            Schema name or "Unknown Schema" if not found
        """
        if not schema_variant_id or schema_variant_id == 'N/A':
            return "Unknown Schema"
        
        try:
            # Cache schemas to avoid repeated API calls
            if not hasattr(self, '_schema_cache'):
                self._schema_cache = {}
            
            cache_key = f"v3:{change_set_id}:{schema_variant_id}:{schema_id or 'none'}"
            if cache_key in self._schema_cache:
                return self._schema_cache[cache_key]
            
            from system_initiative_api_client import SchemasApi
            import json
            schemas_api = SchemasApi(self.api_client)
            
            # Method 1: Try to get schema by variant ID directly (keep your original method)
            try:
                schema_response = schemas_api.get_schema_without_preload_content(
                    workspace_id=self.workspace_id,
                    change_set_id=change_set_id,
                    schema_id=schema_variant_id  # Try using variant ID as schema ID
                )
                
                if hasattr(schema_response, 'data'):
                    raw_data = schema_response.data.decode('utf-8') if hasattr(schema_response.data, 'decode') else schema_response.data
                    schema_data = json.loads(raw_data) if isinstance(raw_data, str) else raw_data
                    
                    # Skip if error response
                    if not (isinstance(schema_data, dict) and schema_data.get('statusCode', 0) >= 400):
                        schema_name = schema_data.get('name', schema_data.get('displayName', 'Unknown Schema'))
                        self._schema_cache[cache_key] = schema_name
                        return schema_name
                        
            except Exception:
                pass  # Fall through to method 2
            
            # Method 2: Check each schema's default variant (existing working logic)
            try:
                schemas_response = schemas_api.list_schemas_without_preload_content(
                    workspace_id=self.workspace_id,
                    change_set_id=change_set_id
                )
                
                if hasattr(schemas_response, 'data'):
                    raw_data = schemas_response.data.decode('utf-8') if hasattr(schemas_response.data, 'decode') else schemas_response.data
                    schemas_data = json.loads(raw_data) if isinstance(raw_data, str) else raw_data
                    
                    # Handle different response structures
                    if isinstance(schemas_data, dict) and 'schemas' in schemas_data:
                        schemas_list = schemas_data['schemas']
                    elif isinstance(schemas_data, list):
                        schemas_list = schemas_data
                    else:
                        schemas_list = [schemas_data] if schemas_data else []
                    
                    # Check each schema's default variant for the target variant ID
                    for schema in schemas_list:
                        schema_id_from_list = schema.get('schemaId')
                        schema_name_from_list = schema.get('schemaName')
                        
                        if not schema_id_from_list or not schema_name_from_list:
                            continue
                        
                        try:
                            # Get the default variant for this schema
                            variant_response = schemas_api.get_default_variant_without_preload_content(
                                workspace_id=self.workspace_id,
                                change_set_id=change_set_id,
                                schema_id=schema_id_from_list
                            )
                            
                            if hasattr(variant_response, 'data'):
                                variant_raw = variant_response.data.decode('utf-8') if hasattr(variant_response.data, 'decode') else variant_response.data
                                variant_data = json.loads(variant_raw) if isinstance(variant_raw, str) else variant_raw
                                
                                # Skip if error response
                                if isinstance(variant_data, dict) and variant_data.get('statusCode', 0) >= 400:
                                    continue
                                
                                # Check all possible variant ID fields
                                possible_variant_fields = [
                                    'variantId',        # This is where your working variants were found!
                                    'id', 
                                    'schemaVariantId', 
                                    'variant_id',
                                    'defaultVariantId'
                                ]
                                
                                for field in possible_variant_fields:
                                    if isinstance(variant_data, dict) and field in variant_data:
                                        variant_id = str(variant_data[field])
                                        if variant_id == str(schema_variant_id):
                                            self._schema_cache[cache_key] = schema_name_from_list
                                            return schema_name_from_list
                                            
                        except Exception:
                            continue  # Continue to next schema if this one fails
                    
                    # Try non-default variants (your existing fallback logic)
                    for schema in schemas_list[:10]:  # Limit to first 10 to avoid too many API calls
                        schema_id_from_list = schema.get('schemaId')
                        schema_name_from_list = schema.get('schemaName')
                        
                        if not schema_id_from_list or not schema_name_from_list:
                            continue
                        
                        try:
                            # Try to get the specific variant directly
                            specific_variant = schemas_api.get_variant_without_preload_content(
                                workspace_id=self.workspace_id,
                                change_set_id=change_set_id,
                                schema_id=schema_id_from_list,
                                schema_variant_id=schema_variant_id
                            )
                            
                            if hasattr(specific_variant, 'data'):
                                specific_raw = specific_variant.data.decode('utf-8') if hasattr(specific_variant.data, 'decode') else specific_variant.data
                                specific_data = json.loads(specific_raw) if isinstance(specific_raw, str) else specific_raw
                                
                                # If no error, we found it!
                                if not (isinstance(specific_data, dict) and specific_data.get('statusCode', 0) >= 400):
                                    self._schema_cache[cache_key] = schema_name_from_list
                                    return schema_name_from_list
                                    
                        except Exception:
                            continue
            
            except Exception as e:
                pass  # Continue to Method 3
            
            # Method 3: NEW - Try using schema_id as fallback (THIS IS THE NEW FIX!)
            if schema_id:
                try:
                    schema_response = schemas_api.get_schema_without_preload_content(
                        workspace_id=self.workspace_id,
                        change_set_id=change_set_id,
                        schema_id=schema_id
                    )
                    
                    if hasattr(schema_response, 'data'):
                        raw_data = schema_response.data.decode('utf-8') if hasattr(schema_response.data, 'decode') else schema_response.data
                        schema_data = json.loads(raw_data) if isinstance(raw_data, str) else raw_data
                        
                        # Skip if error response
                        if not (isinstance(schema_data, dict) and schema_data.get('statusCode', 0) >= 400):
                            schema_name = schema_data.get('name', schema_data.get('displayName', schema_data.get('schemaName', 'Unknown Schema')))
                            self._schema_cache[cache_key] = schema_name
                            return schema_name
                            
                except Exception:
                    pass
            
            # Method 4: If all fails, return a descriptive message
            if schema_id:
                fallback_name = f"Missing Variant ({schema_variant_id[:8]}...)"
            else:
                fallback_name = f"Schema {schema_variant_id[:8]}..."
            
            self._schema_cache[cache_key] = fallback_name
            return fallback_name
            
        except Exception as e:
            print(f"Warning: Could not resolve schema name for {schema_variant_id}: {e}")
            return "Unknown Schema"
    
    def get_schemas(self, change_set_id: str) -> List[Dict[str, Any]]:
        """
        Get all available schemas using the SDK.
        
        Args:
            change_set_id: The change set ID to query
            
        Returns:
            List of schema dictionaries
        """
        try:
            from system_initiative_api_client import SchemasApi
            import json
            
            schemas_api = SchemasApi(self.api_client)
            
            # Use the raw response to avoid pydantic issues
            response = schemas_api.list_schemas_without_preload_content(
                workspace_id=self.workspace_id,
                change_set_id=change_set_id
            )
            
            if hasattr(response, 'data'):
                raw_data = response.data.decode('utf-8') if hasattr(response.data, 'decode') else response.data
                data = json.loads(raw_data) if isinstance(raw_data, str) else raw_data
                
                # Handle response structure
                if isinstance(data, dict) and 'schemas' in data:
                    schemas = data['schemas']
                elif isinstance(data, list):
                    schemas = data
                else:
                    schemas = []
                
                # Convert to consistent format
                schema_list = []
                for schema in schemas:
                    schema_info = {
                        "id": schema.get('schemaId', schema.get('id', 'N/A')),
                        "name": schema.get('schemaName', schema.get('name', 'Unknown')),
                        "display_name": schema.get('displayName', schema.get('name', 'Unknown')),
                        "installed": schema.get('installed', True)
                    }
                    schema_list.append(schema_info)
                
                print(f"✅ Found {len(schema_list)} schema(s) using SDK")
                return schema_list
            else:
                print(f"❌ No data in schema response")
                return []
                
        except Exception as e:
            print(f"❌ Error getting schemas with SDK: {e}")
            import traceback
            print(f"Full traceback: {traceback.format_exc()}")
            return []
    
    def create_change_set(self, name: str, base_change_set_id: Optional[str] = None) -> Optional[str]:
        """
        Create a new change set using the SDK.
        
        Args:
            name: Name for the new change set
            base_change_set_id: Optional base change set to branch from
            
        Returns:
            Change set ID if successful, None otherwise
        """
        try:
            from system_initiative_api_client import ChangeSetsApi, CreateChangeSetV1Request
            
            changesets_api = ChangeSetsApi(self.api_client)
            
            # Create the request object
            request_data = {"changeSetName": name}
            if base_change_set_id:
                request_data["baseChangeSetId"] = base_change_set_id
            
            create_request = CreateChangeSetV1Request(**request_data)
            
            # Make the API call
            response = changesets_api.create_change_set(
                workspace_id=self.workspace_id,
                create_change_set_v1_request=create_request
            )
            
            # Extract the change set ID from the response
            if hasattr(response, 'change_set') and hasattr(response.change_set, 'id'):
                changeset_id = response.change_set.id
                print(f"✅ Successfully created changeset '{name}' with ID: {changeset_id}")
                return changeset_id
            else:
                print(f"❌ Unexpected response format: {response}")
                return None
                
        except Exception as e:
            print(f"❌ Error creating change set with SDK: {e}")
            import traceback
            print(f"Full traceback: {traceback.format_exc()}")
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