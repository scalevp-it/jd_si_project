"""
Component management helpers for System Initiative API
"""

from system_initiative_api_client import (
    ApiClient,
    ComponentsApi,
    SchemasApi,
    CreateComponentV1Request
)
from typing import Optional, Dict, Any, List

def add_component(
    session_or_client,
    change_set_id: str,
    schema_name: str,
    component_name: str,
    attributes: Optional[Dict[str, Any]] = None,
    domain: Optional[Dict[str, Any]] = None,
    secrets: Optional[Dict[str, Any]] = None,
    resource_id: Optional[str] = None,
    view_name: Optional[str] = None
) -> str:
    """
    Add a new component to the System Initiative workspace.
    
    Args:
        session_or_client: SISession instance or ApiClient (for backward compatibility)
        change_set_id: ID of the change set
        schema_name: Name of the schema to use for the component
        component_name: Name for the new component
        attributes: Optional dictionary of component attributes
        domain: Optional dictionary of domain-specific properties
        secrets: Optional dictionary of secrets for the component
        resource_id: Optional resource identifier
        view_name: Optional view name for the component
    
    Returns:
        str: The ID of the newly created component
        
    Raises:
        Exception: If component creation fails
    """
    # Handle both SISession and ApiClient for backward compatibility
    if hasattr(session_or_client, 'api_client'):
        # It's an SISession
        api_client = session_or_client.api_client
        workspace_id = session_or_client.workspace_id
    else:
        # It's an ApiClient (backward compatibility)
        api_client = session_or_client
        # workspace_id needs to be passed separately in this case
        raise ValueError("When using ApiClient directly, please use SISession instead")
    try:
        # Create the components API instance
        components_api = ComponentsApi(api_client)
        
        # Create the request object
        create_request = CreateComponentV1Request(
            name=component_name,
            schema_name=schema_name,
            attributes=attributes,
            domain=domain,
            secrets=secrets,
            resource_id=resource_id,
            view_name=view_name
        )
        
        # Create the component
        response = components_api.create_component(
            workspace_id=workspace_id,
            change_set_id=change_set_id,
            create_component_v1_request=create_request
        )
        
        component_id = response.component.id
        print(f"✓ Created component '{component_name}' with ID: {component_id}")
        
        return component_id
        
    except Exception as e:
        print(f"✗ Error creating component '{component_name}': {e}")
        raise

def list_available_schemas(
    session_or_client,
    workspace_id: str,
    change_set_id: str,
    limit: int = 50
) -> List[Dict[str, str]]:
    """
    List available schemas in the workspace.
    
    Args:
        session_or_client: SISession instance or ApiClient
        workspace_id: ID of the workspace
        change_set_id: ID of the change set
        limit: Maximum number of schemas to return
    
    Returns:
        List of dictionaries containing schema info (name, id)
    """
    # Handle both SISession and ApiClient
    if hasattr(session_or_client, 'api_client'):
        api_client = session_or_client.api_client
    else:
        api_client = session_or_client
        
    try:
        schemas_api = SchemasApi(api_client)
        response = schemas_api.list_schemas(
            workspace_id=workspace_id,
            change_set_id=change_set_id,
            limit=str(limit)
        )
        
        schemas = []
        total_found = len(response.schemas)
        print(f"Found {total_found} available schema(s):")
        
        for i, schema in enumerate(response.schemas, 1):
            schema_info = {
                "name": getattr(schema, 'name', 'Unnamed Schema'),
                "id": getattr(schema, 'id', 'N/A'),
                "category": getattr(schema, 'category', None)
            }
            schemas.append(schema_info)
            
            print(f"  {i:2d}. {schema_info['name']}")
            print(f"      ID: {schema_info['id']}")
            if schema_info['category']:
                print(f"      Category: {schema_info['category']}")
            print()
            
        return schemas
        
    except Exception as e:
        print(f"✗ Error listing schemas: {e}")
        raise

def get_component_by_name(
    session_or_client,
    workspace_id: str,
    change_set_id: str,
    component_name: str
) -> Optional[Dict[str, Any]]:
    """
    Find a component by name.
    
    Args:
        session_or_client: SISession instance or ApiClient
        workspace_id: ID of the workspace
        change_set_id: ID of the change set
        component_name: Name of the component to find
    
    Returns:
        Component information if found, None otherwise
    """
    # Handle both SISession and ApiClient
    if hasattr(session_or_client, 'api_client'):
        api_client = session_or_client.api_client
    else:
        api_client = session_or_client
        
    try:
        components_api = ComponentsApi(api_client)
        response = components_api.find_component(
            workspace_id=workspace_id,
            change_set_id=change_set_id,
            component=component_name
        )
        
        if response.component:
            component_info = {
                "id": getattr(response.component, 'id', 'N/A'),
                "name": getattr(response.component, 'name', component_name),
                "schema_name": getattr(response.component, 'schema_name', 'Unknown')
            }
            print(f"✓ Found component '{component_name}':")
            print(f"    ID: {component_info['id']}")
            print(f"    Schema: {component_info['schema_name']}")
            return component_info
        else:
            print(f"✗ Component '{component_name}' not found")
            return None
            
    except Exception as e:
        print(f"✗ Error finding component '{component_name}': {e}")
        return None

def list_components(
    session_or_client,
    workspace_id: str,
    change_set_id: str,
    limit: int = 50
) -> List[Dict[str, Any]]:
    """
    List all components in the workspace.
    
    Args:
        session_or_client: SISession instance or ApiClient 
        workspace_id: ID of the workspace
        change_set_id: ID of the change set
        limit: Maximum number of components to return
    
    Returns:
        List of component information dictionaries
    """
    # Handle both SISession and ApiClient
    if hasattr(session_or_client, 'api_client'):
        api_client = session_or_client.api_client
    else:
        api_client = session_or_client
    
    try:
        components_api = ComponentsApi(api_client)
        response = components_api.list_components(
            workspace_id=workspace_id,
            change_set_id=change_set_id,
            limit=str(limit)
        )
        
        components = []
        total_found = len(response.components)
        print(f"Found {total_found} component(s):")
        
        if total_found == 0:
            print("  (No components in this workspace)")
            return components
        
        for i, component in enumerate(response.components, 1):
            # Safely extract component information
            component_info = {
                "id": getattr(component, 'id', 'N/A'),
                "name": getattr(component, 'name', 'Unnamed'),
                "schema_name": getattr(component, 'schema_name', 'Unknown Schema'),
                "created_at": getattr(component, 'created_at', None),
                "updated_at": getattr(component, 'updated_at', None),
            }
            
            # Add any additional fields that might be present
            if hasattr(component, 'component_type'):
                component_info['component_type'] = component.component_type
            if hasattr(component, 'change_status'):
                component_info['change_status'] = component.change_status
            
            components.append(component_info)
            
            # Print component info with better formatting
            name = component_info['name']
            schema = component_info['schema_name'] 
            comp_id = component_info['id']
            
            print(f"  {i:2d}. {name}")
            print(f"      Schema: {schema}")
            print(f"      ID: {comp_id}")
            
            # Show additional info if available
            if component_info.get('component_type'):
                print(f"      Type: {component_info['component_type']}")
            if component_info.get('change_status'):
                print(f"      Status: {component_info['change_status']}")
            
            print()  # Empty line between components
            
        return components
        
    except Exception as e:
        print(f"✗ Error listing components: {e}")
        raise

def test_imports():
    """Test function to verify all imports are working"""
    try:
        print("✓ ApiClient imported successfully")
        print("✓ ComponentsApi imported successfully")
        print("✓ SchemasApi imported successfully")
        print("✓ CreateComponentV1Request imported successfully")
        print("✓ All imports working correctly!")
        return True
    except Exception as e:
        print(f"✗ Import error: {e}")
        return False