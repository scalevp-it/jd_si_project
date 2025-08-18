#!/usr/bin/env python3
"""
Fetch a specific schema template and save it to component_configs with .example extension
Enhanced with subscription information (input/output connections) and FULLY DYNAMIC required attributes detection
NO HARDCODED REQUIREMENTS - All requirements detected from actual schema definitions
"""

import sys
import os
import json
import re
from pathlib import Path

# Add parent directory to Python path so we can import from src
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.si_session import SISession
from system_initiative_api_client import SchemasApi


def detect_required_attributes_from_schema(session, schema_id, change_set_id, schema_name, quiet=False):
    """Dynamically detect required attributes from the actual schema definition - NO HARDCODING"""
    
    def quiet_print(msg):
        if not quiet:
            print(msg)
    
    quiet_print(f"🔍 Dynamically analyzing schema definition for required attributes: {schema_name}")
    
    try:
        from system_initiative_api_client import SchemasApi
        schemas_api = SchemasApi(session.api_client)
        
        required_attrs = {}
        
        # Method 1: Try to get schema definition directly
        try:
            schema_response = schemas_api.get_schema_without_preload_content(
                workspace_id=session.workspace_id,
                change_set_id=change_set_id,
                schema_id=schema_id
            )
            
            if hasattr(schema_response, 'data'):
                schema_raw = schema_response.data.decode('utf-8') if hasattr(schema_response.data, 'decode') else schema_response.data
                schema_data = json.loads(schema_raw) if isinstance(schema_raw, str) else schema_raw
                
                quiet_print(f"   ✅ Retrieved schema definition, analyzing for required fields...")
                
                # Look for required field indicators in the schema definition
                required_attrs.update(extract_required_from_schema_definition(schema_data, quiet))
                
        except Exception as e:
            quiet_print(f"   ⚠️  Could not get schema definition: {e}")
        
        # Method 2: Try to get default variant and analyze its structure
        try:
            variant_response = schemas_api.get_default_variant_without_preload_content(
                workspace_id=session.workspace_id,
                change_set_id=change_set_id,
                schema_id=schema_id
            )
            
            if hasattr(variant_response, 'data'):
                variant_raw = variant_response.data.decode('utf-8') if hasattr(variant_response.data, 'decode') else variant_response.data
                variant_data = json.loads(variant_raw) if isinstance(variant_raw, str) else variant_raw
                
                # Skip error responses
                if not (isinstance(variant_data, dict) and variant_data.get('statusCode', 0) >= 400):
                    quiet_print(f"   ✅ Retrieved variant definition, analyzing for required fields...")
                    required_attrs.update(extract_required_from_variant_definition(variant_data, quiet))
                
        except Exception as e:
            quiet_print(f"   ⚠️  Could not get variant definition: {e}")
        
        # Method 3: Try to analyze existing components of this schema type
        required_attrs.update(detect_required_from_existing_components(session, schema_name, change_set_id, quiet))
        
        required_count = len([attr for attr in required_attrs.values() if attr.get("required") == True])
        conditional_count = len([attr for attr in required_attrs.values() if attr.get("required") == "conditional"])
        
        quiet_print(f"   📊 Dynamic analysis found: {required_count} required + {conditional_count} conditional attributes")
        
        return required_attrs
        
    except Exception as e:
        quiet_print(f"   ❌ Error in dynamic schema analysis: {e}")
        if not quiet:
            import traceback
            print(f"   Full traceback: {traceback.format_exc()}")
        return {}


def extract_required_from_schema_definition(schema_data, quiet=False):
    """Extract required attributes from schema definition structure"""
    
    def quiet_print(msg):
        if not quiet:
            print(msg)
    
    required_attrs = {}
    
    if not isinstance(schema_data, dict):
        return required_attrs
    
    # Look for common schema definition patterns that indicate required fields
    patterns_to_check = [
        'required',
        'requiredProperties', 
        'mandatoryFields',
        'properties',
        'attributePrototypes',
        'props',
        'domainProps'
    ]
    
    for pattern in patterns_to_check:
        if pattern in schema_data:
            quiet_print(f"      🔍 Found '{pattern}' in schema definition")
            
            data = schema_data[pattern]
            
            if pattern == 'required' and isinstance(data, list):
                # Direct required field list
                for field_name in data:
                    path = f"/domain/{field_name}" if not field_name.startswith('/') else field_name
                    required_attrs[path] = {
                        "required": True,
                        "reason": f"Listed in schema required fields",
                        "source": "Schema Definition",
                        "detection_method": f"required_list_{pattern}"
                    }
                    quiet_print(f"         → {path}: REQUIRED (from required list)")
            
            elif isinstance(data, dict):
                # Analyze property definitions
                for prop_name, prop_def in data.items():
                    if isinstance(prop_def, dict):
                        is_required = analyze_property_for_required_status(prop_name, prop_def, quiet)
                        if is_required:
                            path = f"/domain/{prop_name}" if not prop_name.startswith('/') else prop_name
                            required_attrs[path] = {
                                "required": is_required,
                                "reason": f"Analyzed from property definition in {pattern}",
                                "source": "Schema Definition Analysis",
                                "detection_method": f"property_analysis_{pattern}"
                            }
                            req_type = "REQUIRED" if is_required == True else "CONDITIONAL"
                            quiet_print(f"         → {path}: {req_type} (from property analysis)")
    
    return required_attrs


def extract_required_from_variant_definition(variant_data, quiet=False):
    """Extract required attributes from variant definition structure"""
    
    def quiet_print(msg):
        if not quiet:
            print(msg)
    
    required_attrs = {}
    
    if not isinstance(variant_data, dict):
        return required_attrs
    
    # Look for variant-specific patterns
    variant_patterns = [
        'requiredInputSockets',
        'inputSockets',
        'props',
        'propTree',
        'attributeDefinitions'
    ]
    
    for pattern in variant_patterns:
        if pattern in variant_data:
            quiet_print(f"      🔍 Found '{pattern}' in variant definition")
            
            data = variant_data[pattern]
            
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict) and 'name' in item:
                        is_required = analyze_socket_for_required_status(item, quiet)
                        if is_required:
                            socket_name = item['name']
                            socket_kind = item.get('kind', 'domain')
                            path = f"/{socket_kind.lower()}/{socket_name}"
                            
                            required_attrs[path] = {
                                "required": is_required,
                                "reason": f"Required socket in variant definition",
                                "source": "Variant Definition Analysis", 
                                "detection_method": f"socket_analysis_{pattern}"
                            }
                            req_type = "REQUIRED" if is_required == True else "CONDITIONAL"
                            quiet_print(f"         → {path}: {req_type} (from socket analysis)")
    
    return required_attrs


def analyze_property_for_required_status(prop_name, prop_def, quiet=False):
    """Analyze individual property definition to determine if it's required"""
    
    def quiet_print(msg):
        if not quiet:
            print(msg)
    
    # Look for indicators that a property is required
    required_indicators = [
        'required',
        'mandatory', 
        'isRequired',
        'minOccurs',
        'nullable'
    ]
    
    for indicator in required_indicators:
        if indicator in prop_def:
            value = prop_def[indicator]
            
            if indicator == 'required' and value == True:
                return True
            elif indicator == 'mandatory' and value == True:
                return True
            elif indicator == 'isRequired' and value == True:
                return True
            elif indicator == 'minOccurs' and isinstance(value, int) and value > 0:
                return True
            elif indicator == 'nullable' and value == False:
                return "conditional"  # Not nullable could mean conditionally required
    
    # Check for conditional requirements in descriptions or validation rules
    description_fields = ['description', 'docs', 'help', 'comment']
    for desc_field in description_fields:
        if desc_field in prop_def:
            desc = str(prop_def[desc_field]).lower()
            if 'required' in desc and 'optional' not in desc:
                return "conditional"
    
    return False


def analyze_socket_for_required_status(socket_def, quiet=False):
    """Analyze socket definition to determine if it's required"""
    
    def quiet_print(msg):
        if not quiet:
            print(msg)
    
    # Check for required indicators in socket definition
    if socket_def.get('required') == True:
        return True
    elif socket_def.get('optional') == False:
        return True
    elif socket_def.get('minOccurs', 0) > 0:
        return True
    elif socket_def.get('nullable') == False:
        return "conditional"
    
    return False


def detect_required_from_existing_components(session, schema_name, change_set_id, quiet=False):
    """Analyze existing components to detect commonly required fields"""
    
    def quiet_print(msg):
        if not quiet:
            print(msg)
    
    required_attrs = {}
    
    try:
        from system_initiative_api_client import ComponentsApi
        comp_api = ComponentsApi(session.api_client)
        
        # Get all components
        components_response = comp_api.list_components_without_preload_content(
            workspace_id=session.workspace_id,
            change_set_id=change_set_id
        )
        
        if not hasattr(components_response, 'data'):
            return required_attrs
        
        raw_data = components_response.data.decode('utf-8') if hasattr(components_response.data, 'decode') else components_response.data
        components_data = json.loads(raw_data) if isinstance(raw_data, str) else raw_data
        
        if not isinstance(components_data, dict) or 'components' not in components_data:
            return required_attrs
        
        # Find components of this schema type
        matching_components = []
        for comp in components_data['components']:
            if comp.get('schemaName') == schema_name:
                matching_components.append(comp)
        
        quiet_print(f"      📊 Found {len(matching_components)} existing components of type {schema_name}")
        
        if len(matching_components) >= 2:  # Need at least 2 to detect patterns
            # Analyze common attributes across components
            common_attrs = analyze_common_attributes_across_components(session, matching_components, change_set_id, quiet)
            required_attrs.update(common_attrs)
        
        return required_attrs
        
    except Exception as e:
        quiet_print(f"      ⚠️  Could not analyze existing components: {e}")
        return required_attrs


def analyze_common_attributes_across_components(session, components, change_set_id, quiet=False):
    """Find attributes that appear in ALL components (likely required)"""
    
    def quiet_print(msg):
        if not quiet:
            print(msg)
    
    required_attrs = {}
    
    try:
        from system_initiative_api_client import ComponentsApi
        comp_api = ComponentsApi(session.api_client)
        
        all_component_attrs = []
        
        # Get detailed info for each component
        for comp in components[:5]:  # Limit to first 5 to avoid too many API calls
            comp_id = comp.get('id')
            if not comp_id:
                continue
                
            try:
                detailed_comp_response = comp_api.get_component_without_preload_content(
                    workspace_id=session.workspace_id,
                    change_set_id=change_set_id,
                    component_id=comp_id
                )
                
                if hasattr(detailed_comp_response, 'data'):
                    detail_raw = detailed_comp_response.data.decode('utf-8') if hasattr(detailed_comp_response.data, 'decode') else detailed_comp_response.data
                    detailed_data = json.loads(detail_raw) if isinstance(detail_raw, str) else detail_raw
                    
                    # Extract all attribute paths from this component
                    comp_attrs = set()
                    for section in ['attributes', 'domain', 'secrets']:
                        if section in detailed_data and isinstance(detailed_data[section], dict):
                            for attr_name, attr_value in detailed_data[section].items():
                                if attr_value is not None and attr_value != "":  # Has a non-empty value
                                    if attr_name.startswith('/'):
                                        comp_attrs.add(attr_name)
                                    else:
                                        comp_attrs.add(f"/domain/{attr_name}")
                    
                    all_component_attrs.append(comp_attrs)
                    
            except Exception as e:
                quiet_print(f"         ⚠️  Could not analyze component {comp_id}: {e}")
                continue
        
        # Find attributes that appear in ALL components
        if all_component_attrs:
            common_attrs = set.intersection(*all_component_attrs) if len(all_component_attrs) > 1 else all_component_attrs[0]
            
            for attr_path in common_attrs:
                required_attrs[attr_path] = {
                    "required": "conditional",  # Conservative - mark as conditional since it's based on existing usage
                    "reason": f"Present in all {len(all_component_attrs)} analyzed components of this type",
                    "source": "Existing Component Analysis",
                    "detection_method": "common_usage_pattern"
                }
                quiet_print(f"         → {attr_path}: CONDITIONAL (common usage pattern)")
        
        return required_attrs
        
    except Exception as e:
        quiet_print(f"      ⚠️  Error in common attribute analysis: {e}")
        return required_attrs


def get_required_attributes_for_schema(session, schema_id, change_set_id, schema_name, quiet=False):
    """Get required attributes using ONLY dynamic detection - NO HARDCODING"""
    
    def quiet_print(msg):
        if not quiet:
            print(msg)
    
    quiet_print(f"🔍 Dynamically analyzing required attributes for: {schema_name}")
    
    # Use only dynamic detection methods - NO HARDCODED REQUIREMENTS
    required_attrs = detect_required_attributes_from_schema(session, schema_id, change_set_id, schema_name, quiet)
    
    required_count = len([attr for attr in required_attrs.values() if attr.get("required") == True])
    conditional_count = len([attr for attr in required_attrs.values() if attr.get("required") == "conditional"])
    
    if required_count > 0 or conditional_count > 0:
        quiet_print(f"   ✅ Dynamic analysis found {required_count} required + {conditional_count} conditional attributes")
        for path, info in required_attrs.items():
            req_type = "REQUIRED" if info.get("required") == True else "CONDITIONAL" 
            quiet_print(f"      → {path}: {req_type} - {info.get('reason', 'No reason specified')[:60]}...")
    else:
        quiet_print(f"   ℹ️  No required attributes detected through dynamic analysis")
    
    return required_attrs


def find_schema_in_all_pages(schemas_api, session, schema_name: str, change_set_id: str = "HEAD"):
    """Find a schema by searching through all paginated results and multiple sources"""
    print(f"🔍 Searching for schema '{schema_name}' across all sources...")
    
    approaches = [
        {"name": "HEAD changeset", "changeset": "HEAD"},
        {"name": "Current changeset", "changeset": change_set_id},
        {"name": "No changeset filter", "changeset": None}
    ]
    
    all_schemas = []
    
    for approach in approaches:
        try:
            print(f"   📄 Searching schemas using {approach['name']}...")
            
            cursor = None
            page = 1
            limit = "300"
            
            while True:
                print(f"      📄 Page {page}...")
                
                params = {
                    'workspace_id': session.workspace_id,
                    'limit': limit
                }
                
                if approach['changeset']:
                    params['change_set_id'] = approach['changeset']
                
                if cursor:
                    params['cursor'] = cursor
                
                try:
                    response = schemas_api.list_schemas_without_preload_content(**params)
                    
                    if not hasattr(response, 'data'):
                        break
                    
                    raw_data = response.data.decode('utf-8') if hasattr(response.data, 'decode') else response.data
                    data = json.loads(raw_data) if isinstance(raw_data, str) else raw_data
                    
                    if not isinstance(data, dict):
                        break
                    
                    page_schemas = data.get('schemas', [])
                    schemas_found = len(page_schemas)
                    print(f"         Found {schemas_found} schemas on this page")
                    all_schemas.extend(page_schemas)
                    
                    # Check for next page
                    next_cursor = data.get('nextCursor')
                    if not next_cursor:
                        break
                    
                    cursor = next_cursor
                    page += 1
                    
                    # Safety check
                    if page > 20:
                        break
                        
                except Exception as e:
                    print(f"         ❌ Error on page {page}: {e}")
                    break
                    
        except Exception as e:
            print(f"   ❌ Error with {approach['name']}: {e}")
    
    # Deduplicate schemas by ID
    seen_ids = set()
    unique_schemas = []
    for schema in all_schemas:
        schema_id = schema.get('schemaId') or schema.get('id')
        if schema_id and schema_id not in seen_ids:
            seen_ids.add(schema_id)
            unique_schemas.append(schema)
    
    print(f"\n📊 Total unique schemas found: {len(unique_schemas)}")
    
    # Search for target schema
    target_schema = None
    for schema in unique_schemas:
        schema_names_to_check = [
            schema.get('schemaName'),
            schema.get('name'),
            schema.get('displayName'),
            schema.get('title')
        ]
        
        for schema_name_field in schema_names_to_check:
            if schema_name_field and schema_name_field == schema_name:
                print(f"✅ Exact match found: {schema_name_field}")
                return schema
    
    print(f"❌ Schema '{schema_name}' not found!")
    return None


def extract_subscriptions(variant_data):
    """Extract subscription information from schema variant data"""
    subscriptions = {
        "input_subscriptions": [],
        "output_subscriptions": []
    }
    
    if isinstance(variant_data, dict):
        # Check for input socket definitions
        if 'inputSockets' in variant_data:
            for socket in variant_data['inputSockets']:
                input_sub = {
                    "name": socket.get('name'),
                    "kind": socket.get('kind'),
                    "connection_annotation": socket.get('connectionAnnotation'),
                    "definition": socket.get('definition'),
                    "ui_hidden": socket.get('uiHidden', False),
                    "attribute_path": socket.get('attributePath', f"/{socket.get('kind', 'domain').lower()}/{socket.get('name', 'unknown')}")
                }
                subscriptions["input_subscriptions"].append(input_sub)
        
        # Check for output socket definitions
        if 'outputSockets' in variant_data:
            for socket in variant_data['outputSockets']:
                output_sub = {
                    "name": socket.get('name'),
                    "kind": socket.get('kind'),
                    "connection_annotation": socket.get('connectionAnnotation'),
                    "definition": socket.get('definition'),
                    "ui_hidden": socket.get('uiHidden', False),
                    "attribute_path": socket.get('attributePath', f"/{socket.get('kind', 'domain').lower()}/{socket.get('name', 'unknown')}")
                }
                subscriptions["output_subscriptions"].append(output_sub)
    
    return subscriptions


def extract_attributes_from_existing_components(session, schema_name, change_set_id):
    """Extract attributes by finding existing components of this schema type"""
    from system_initiative_api_client import ComponentsApi
    
    print(f"🔍 Looking for existing components with schema '{schema_name}'...")
    
    try:
        comp_api = ComponentsApi(session.api_client)
        components_response = comp_api.list_components_without_preload_content(
            workspace_id=session.workspace_id,
            change_set_id=change_set_id
        )
        
        if not hasattr(components_response, 'data'):
            print(f"   ❌ No components data in response")
            return {}, 0
        
        raw_data = components_response.data.decode('utf-8') if hasattr(components_response.data, 'decode') else components_response.data
        components_data = json.loads(raw_data) if isinstance(raw_data, str) else raw_data
        
        if not isinstance(components_data, dict) or 'components' not in components_data:
            print(f"   ❌ Invalid components data structure")
            return {}, 0
        
        components = components_data['components']
        print(f"   ✅ Found {len(components)} total components in workspace")
        
        # Find components matching our schema
        matching_components = []
        for comp in components:
            comp_schema = comp.get('schemaName') or comp.get('schema', {}).get('name')
            if comp_schema == schema_name:
                matching_components.append(comp)
        
        print(f"   🎯 Found {len(matching_components)} components with schema '{schema_name}'")
        
        if len(matching_components) == 0:
            print(f"   ℹ️  No existing components found for this schema")
            return {}, 0
        
        # Extract attributes from the first matching component
        sample_component = matching_components[0]
        comp_id = sample_component.get('id')
        print(f"   📋 Extracting attributes from component: {comp_id}")
        
        # Get detailed component information
        detailed_comp_response = comp_api.get_component_without_preload_content(
            workspace_id=session.workspace_id,
            change_set_id=change_set_id,
            component_id=comp_id
        )
        
        if not hasattr(detailed_comp_response, 'data'):
            print(f"   ❌ No detailed component data")
            return {}, 0
        
        detail_raw = detailed_comp_response.data.decode('utf-8') if hasattr(detailed_comp_response.data, 'decode') else detailed_comp_response.data
        detailed_data = json.loads(detail_raw) if isinstance(detail_raw, str) else detail_raw
        
        print(f"   🔍 Detailed component keys: {list(detailed_data.keys()) if isinstance(detailed_data, dict) else 'Not a dict'}")
        
        # Extract attributes with full nested support
        attributes = {}
        attributes_found = 0
        
        def extract_nested_attributes(data, current_path_prefix, source_description):
            """Recursively extract nested attributes"""
            nonlocal attributes, attributes_found
            
            if not isinstance(data, dict):
                return
            
            for key, value in data.items():
                # Build the full attribute path
                attr_path = f"{current_path_prefix}/{key}"
                
                if isinstance(value, dict) and value:
                    # Check if this dict contains primitive values (leaf nodes) or more nested structures
                    has_primitive_children = any(not isinstance(v, dict) for v in value.values())
                    has_nested_children = any(isinstance(v, dict) for v in value.values())
                    
                    if has_primitive_children and not has_nested_children:
                        # This is a leaf dict with primitive values - treat as a single attribute
                        attributes[attr_path] = value
                        attributes_found += 1
                        print(f"      → {attr_path}: {type(value).__name__} (leaf object)")
                    elif has_nested_children:
                        # This has nested structure - recurse deeper
                        print(f"      🔍 Found nested structure at {attr_path}")
                        extract_nested_attributes(value, attr_path, f"{source_description} nested")
                    else:
                        # Empty dict or complex structure
                        attributes[attr_path] = value
                        attributes_found += 1
                        print(f"      → {attr_path}: {type(value).__name__} (complex object)")
                elif isinstance(value, list):
                    # Handle arrays properly
                    attributes[attr_path] = value
                    attributes_found += 1
                    print(f"      → {attr_path}: array with {len(value)} items")
                else:
                    # Primitive value - add it directly
                    attributes[attr_path] = value
                    attributes_found += 1
                    print(f"      → {attr_path}: {type(value).__name__} = {value}")
        
        attribute_sources = [
            ('attributes', 'Direct attributes'),
            ('domain', 'Domain attributes'), 
            ('secrets', 'Secret attributes')
        ]
        
        for source_key, description in attribute_sources:
            if source_key in detailed_data and isinstance(detailed_data[source_key], dict):
                source_attrs = detailed_data[source_key]
                print(f"   ✅ Found {len(source_attrs)} {description}")
                
                # Determine the path prefix based on source type
                if source_key == 'secrets':
                    path_prefix = "/secrets"
                    extract_nested_attributes(source_attrs, path_prefix, description)
                elif source_key == 'attributes':
                    # For attributes, check if they already have path prefixes
                    for attr_name, attr_value in source_attrs.items():
                        if attr_name.startswith('/'):
                            # Already a full path
                            attributes[attr_name] = attr_value
                            attributes_found += 1
                            print(f"      → {attr_name}: {type(attr_value).__name__}")
                        else:
                            # Need to add path prefix
                            full_path = f"/domain/{attr_name}"
                            attributes[full_path] = attr_value
                            attributes_found += 1
                            print(f"      → {full_path}: {type(attr_value).__name__}")
                else:
                    path_prefix = "/domain"
                    extract_nested_attributes(source_attrs, path_prefix, description)
        
        print(f"   ✅ Extracted {attributes_found} total attributes from existing component")
        return attributes, attributes_found
        
    except Exception as e:
        print(f"   ❌ Error extracting from existing components: {e}")
        import traceback
        print(f"   Full traceback: {traceback.format_exc()}")
        return {}, 0


def generate_enhanced_schema_fallback(schema_name):
    """Generate enhanced fallback attributes based on schema name patterns and UI structure"""
    
    print(f"🎯 Generating enhanced fallback for schema: {schema_name}")
    
    base_attributes = {
        "/domain/Name": f"my-{schema_name.lower().replace('::', '-').replace(' ', '-').replace('_', '-')}",
        "/domain/Environment": "development",
        "/domain/Owner": "team-name"
    }
    
    # AWS-specific attributes
    if schema_name.startswith("AWS::"):
        base_attributes["/secrets/AWS Credential"] = {
            "$source": {
                "component": "my-aws-credential", 
                "path": "/secrets/AWS Credential"
            }
        }
        
        # EC2 Instance specific - based on UI screenshot structure
        if "EC2::Instance" in schema_name:
            base_attributes.update({
                # Core instance attributes
                "/domain/ImageId": "ami-0abcdef1234567890",
                "/domain/InstanceType": "t3.micro",
                "/domain/KeyName": "my-key-pair", 
                "/domain/UserData": "#!/bin/bash\necho 'Hello World'",
                
                # Nested attributes under /domain/extra/ (from UI screenshot)
                "/domain/extra/Region": "us-west-2",
                
                # Array attributes (from UI screenshot structure)
                "/domain/InstanceMetadataTags": [
                    {"Key": "Environment", "Value": "development"},
                    {"Key": "Project", "Value": "my-project"}
                ],
                "/domain/NetworkInterfaces": [
                    {
                        "DeviceIndex": 0,
                        "SubnetId": "subnet-12345678",
                        "SecurityGroupIds": ["sg-12345678"],
                        "AssociatePublicIpAddress": True
                    }
                ],
                "/domain/SecurityGroupIds": ["sg-12345678"],
                "/domain/SecurityGroups": [
                    {
                        "$source": {
                            "component": "my-security-group",
                            "path": "/domain/GroupId"
                        }
                    }
                ],
                "/domain/SsmAssociations": [
                    {
                        "DocumentName": "AWS-ConfigureAWSPackage",
                        "Parameters": {
                            "action": "Install",
                            "name": "AmazonCloudWatchAgent"
                        }
                    }
                ],
                "/domain/Tags": [
                    {"Key": "Name", "Value": "my-ec2-instance"},
                    {"Key": "Environment", "Value": "development"}
                ],
                "/domain/Volumes": [
                    {
                        "Device": "/dev/sda1",
                        "VolumeId": {
                            "$source": {
                                "component": "my-ebs-volume",
                                "path": "/domain/VolumeId"
                            }
                        }
                    }
                ],
                
                # IAM Instance Profile as source reference
                "/domain/IamInstanceProfile": {
                    "$source": {
                        "component": "my-instance-profile",
                        "path": "/domain/Arn"
                    }
                },
                
                # Private DNS Name Options (nested object from UI)
                "/domain/PrivateDnsNameOptions": {
                    "EnableResourceNameDnsARecord": True,
                    "EnableResourceNameDnsAAAARecord": False,
                    "HostnameType": "ip-name"
                },
                
                # Block Device Mappings
                "/domain/BlockDeviceMappings": [
                    {
                        "DeviceName": "/dev/sda1",
                        "Ebs": {
                            "VolumeSize": 20,
                            "VolumeType": "gp3",
                            "DeleteOnTermination": True
                        }
                    }
                ]
            })
        
        # Generic AWS resource fallback for other types
        else:
            # Add common AWS attributes that apply to most resources
            base_attributes.update({
                "/domain/extra/Region": "us-west-2"
            })
            
            # Add service-specific attributes based on general patterns
            if "RDS::" in schema_name:
                base_attributes.update({
                    "/domain/Engine": "postgres",
                    "/domain/DBInstanceClass": "db.t3.micro",
                    "/domain/EngineVersion": "14.9",
                    "/domain/AllocatedStorage": 20,
                    "/secrets/MasterUserPassword": "{{SECRET:replace_with_actual_password}}"
                })
            elif "S3::" in schema_name:
                base_attributes.update({
                    "/domain/BucketName": f"my-bucket-{schema_name.lower().replace('::', '-')}-{hash(schema_name) % 10000}",
                    "/domain/PublicAccessBlockConfiguration": {
                        "BlockPublicAcls": True,
                        "BlockPublicPolicy": True,
                        "IgnorePublicAcls": True,
                        "RestrictPublicBuckets": True
                    }
                })
            elif "Lambda::" in schema_name:
                base_attributes.update({
                    "/domain/Code": {
                        "ZipFile": "exports.handler = async (event) => { return 'Hello World'; };"
                    },
                    "/domain/Runtime": "nodejs18.x",
                    "/domain/Handler": "index.handler"
                })
            elif "IAM::" in schema_name:
                base_attributes.update({
                    "/domain/AssumeRolePolicyDocument": {
                        "Version": "2012-10-17",
                        "Statement": [
                            {
                                "Effect": "Allow",
                                "Principal": {"Service": "ec2.amazonaws.com"},
                                "Action": "sts:AssumeRole"
                            }
                        ]
                    }
                })
    
    print(f"   ✅ Generated {len(base_attributes)} enhanced fallback attributes")
    return base_attributes


def extract_schema_definition_directly(session, schema_id, change_set_id):
    """Extract schema structure directly from schema definition API"""
    from system_initiative_api_client import SchemasApi
    
    print(f"🔍 Attempting direct schema definition extraction...")
    
    try:
        schemas_api = SchemasApi(session.api_client)
        
        # Try to get the schema definition directly
        schema_response = schemas_api.get_schema_without_preload_content(
            workspace_id=session.workspace_id,
            change_set_id=change_set_id,
            schema_id=schema_id
        )
        
        if not hasattr(schema_response, 'data'):
            print(f"   ❌ No schema definition data")
            return {}, 0
        
        schema_raw = schema_response.data.decode('utf-8') if hasattr(schema_response.data, 'decode') else schema_response.data
        schema_data = json.loads(schema_raw) if isinstance(schema_raw, str) else schema_raw
        
        print(f"   🔍 Schema definition keys: {list(schema_data.keys()) if isinstance(schema_data, dict) else 'Not a dict'}")
        
        # Look for attribute definitions in schema structure
        attributes = {}
        attributes_found = 0
        
        # Check various places where attribute definitions might be stored
        attribute_locations = [
            'attributePrototypes',
            'props',
            'properties', 
            'attributes',
            'domain',
            'domainProps'
        ]
        
        for location in attribute_locations:
            if location in schema_data and schema_data[location]:
                print(f"   ✅ Found attribute definitions in: {location}")
                
                attr_defs = schema_data[location]
                if isinstance(attr_defs, list):
                    for attr_def in attr_defs:
                        if isinstance(attr_def, dict):
                            attr_name = attr_def.get('name') or attr_def.get('key')
                            attr_path = attr_def.get('path') or attr_def.get('attributePath')
                            
                            if attr_name:
                                # Build proper attribute path
                                if attr_path:
                                    full_path = attr_path
                                elif attr_name.startswith('/'):
                                    full_path = attr_name
                                else:
                                    full_path = f"/domain/{attr_name}"
                                
                                # Determine default value based on type
                                attr_type = attr_def.get('type', 'string')
                                if attr_type == 'array':
                                    default_value = []
                                elif attr_type == 'object':
                                    default_value = {}
                                elif attr_type == 'boolean':
                                    default_value = False
                                elif attr_type == 'number':
                                    default_value = 0
                                else:
                                    default_value = f"example-{attr_name.lower()}"
                                
                                attributes[full_path] = default_value
                                attributes_found += 1
                                print(f"      → {full_path}: {attr_type}")
                
                elif isinstance(attr_defs, dict):
                    for attr_name, attr_def in attr_defs.items():
                        if attr_name.startswith('/'):
                            full_path = attr_name
                        else:
                            full_path = f"/domain/{attr_name}"
                        
                        if isinstance(attr_def, dict):
                            attributes[full_path] = attr_def
                        else:
                            attributes[full_path] = f"example-{attr_name.lower()}"
                        
                        attributes_found += 1
                        print(f"      → {full_path}")
        
        print(f"   ✅ Extracted {attributes_found} attributes from schema definition")
        return attributes, attributes_found
        
    except Exception as e:
        print(f"   ❌ Error in direct schema definition extraction: {e}")
        import traceback
        print(f"   Full traceback: {traceback.format_exc()}")
        return {}, 0


def create_temp_component_for_extraction(session, schema_name, change_set_id):
    """Create a temporary component to extract complete attribute structure, then delete it"""
    from system_initiative_api_client import ComponentsApi, ChangeSetsApi, CreateChangeSetV1Request
    from system_initiative_api_client.models.create_component_v1_request import CreateComponentV1Request
    
    print(f"🗂️  Creating temporary component to extract complete attributes...")
    
    temp_changeset_id = None
    temp_comp_id = None
    
    try:
        # Step 1: Create a temporary changeset if we're on HEAD
        if change_set_id == "HEAD":
            print(f"   📝 Creating temporary changeset (can't modify HEAD)...")
            changeset_api = ChangeSetsApi(session.api_client)
            
            temp_changeset_request = CreateChangeSetV1Request(
                changeSetName=f"temp-schema-extraction-{schema_name.replace('::', '-').lower()}"
            )
            
            changeset_response = changeset_api.create_change_set(
                workspace_id=session.workspace_id,
                create_change_set_v1_request=temp_changeset_request
            )
            
            temp_changeset_id = changeset_response.change_set.id
            working_changeset = temp_changeset_id
            print(f"   ✅ Created temporary changeset: {temp_changeset_id}")
        else:
            working_changeset = change_set_id
        
        # Step 2: Create the temporary component with enhanced error handling
        comp_api = ComponentsApi(session.api_client)
        temp_name = f"temp-extract-{schema_name.lower().replace('::', '-').replace(' ', '-')}"
        
        print(f"   📋 Creating temporary component: {temp_name}")
        
        try:
            # Create the request object
            create_request = CreateComponentV1Request(
                schema_name=schema_name,
                name=temp_name
            )
            
            create_response = comp_api.create_component(
                workspace_id=session.workspace_id,
                change_set_id=working_changeset,
                create_component_v1_request=create_request
            )
            
            if not hasattr(create_response, 'component') or not create_response.component:
                print(f"   ❌ Failed to create temporary component - no component in response")
                return {}, 0, None, temp_changeset_id
            
            temp_comp_id = create_response.component.id
            print(f"   ✅ Created temporary component with ID: {temp_comp_id}")
            
        except Exception as create_error:
            error_msg = str(create_error)
            print(f"   ❌ Error creating temporary component: {create_error}")
            
            # Handle specific pydantic validation errors
            if "Input should be a valid dictionary" in error_msg and "ComponentPropViewV1" in error_msg:
                print("   🔍 Detected ComponentPropViewV1 validation error:")
                print("      This indicates the schema has properties with null values that break pydantic validation")
                print("      The schema variant likely has incomplete property definitions")
                print("      Falling back to enhanced fallback attributes...")
                
                fallback_attributes = generate_enhanced_schema_fallback(schema_name)
                return fallback_attributes, len(fallback_attributes), None, temp_changeset_id
            
            # Handle WorkspaceSnapshotGraph node not found errors
            elif "Node with ID" in error_msg and "not found" in error_msg:
                print("   🔍 Detected WorkspaceSnapshotGraph node error:")
                print("      The schema exists but its variant is not accessible in the current workspace snapshot")
                print("      This can happen with newly added or uninstalled schemas")
                print("      Falling back to enhanced fallback attributes...")
                
                fallback_attributes = generate_enhanced_schema_fallback(schema_name)
                return fallback_attributes, len(fallback_attributes), None, temp_changeset_id
            
            # Re-raise other unexpected errors
            else:
                print("   Full traceback:")
                import traceback
                print(traceback.format_exc())
                return {}, 0, None, temp_changeset_id
        
        # Step 3: Get the detailed component information
        print(f"   📋 Extracting attributes from temporary component...")
        
        try:
            detailed_comp_response = comp_api.get_component_without_preload_content(
                workspace_id=session.workspace_id,
                change_set_id=working_changeset,
                component_id=temp_comp_id
            )
            
            if not hasattr(detailed_comp_response, 'data'):
                print(f"   ❌ No detailed component data")
                return {}, 0, temp_comp_id, temp_changeset_id
            
            detail_raw = detailed_comp_response.data.decode('utf-8') if hasattr(detailed_comp_response.data, 'decode') else detailed_comp_response.data
            detailed_data = json.loads(detail_raw) if isinstance(detail_raw, str) else detail_raw
            
            print(f"   🔍 Detailed component keys: {list(detailed_data.keys()) if isinstance(detailed_data, dict) else 'Not a dict'}")
            
            # Step 4: Extract attributes using nested extraction logic
            attributes = {}
            attributes_found = 0
            
            def extract_nested_attributes(data, current_path_prefix, source_description):
                """Recursively extract nested attributes like /domain/extra/region"""
                nonlocal attributes, attributes_found
                
                if not isinstance(data, dict):
                    return
                
                for key, value in data.items():
                    # Build the full attribute path
                    attr_path = f"{current_path_prefix}/{key}"
                    
                    if isinstance(value, dict) and value:
                        # Check if this dict contains primitive values (leaf nodes) or more nested structures
                        has_primitive_children = any(not isinstance(v, dict) for v in value.values())
                        has_nested_children = any(isinstance(v, dict) for v in value.values())
                        
                        if has_primitive_children and not has_nested_children:
                            # This is a leaf dict with primitive values - treat as a single attribute
                            attributes[attr_path] = value
                            attributes_found += 1
                            print(f"      → {attr_path}: {type(value).__name__} (leaf object)")
                        elif has_nested_children:
                            # This has nested structure - recurse deeper
                            print(f"      🔍 Found nested structure at {attr_path}")
                            extract_nested_attributes(value, attr_path, f"{source_description} nested")
                        else:
                            # Empty dict or complex structure
                            attributes[attr_path] = value
                            attributes_found += 1
                            print(f"      → {attr_path}: {type(value).__name__} (complex object)")
                    elif isinstance(value, list):
                        # Handle arrays properly
                        attributes[attr_path] = value
                        attributes_found += 1
                        print(f"      → {attr_path}: array with {len(value)} items")
                    else:
                        # Primitive value - add it directly
                        attributes[attr_path] = value
                        attributes_found += 1
                        print(f"      → {attr_path}: {type(value).__name__} = {value}")
            
            attribute_sources = [
                ('attributes', 'Direct attributes'),
                ('domain', 'Domain attributes'), 
                ('secrets', 'Secret attributes'),
                ('domainProps', 'Domain Properties'),
                ('props', 'Properties')
            ]
            
            for source_key, description in attribute_sources:
                if source_key in detailed_data and isinstance(detailed_data[source_key], dict):
                    source_attrs = detailed_data[source_key]
                    print(f"   ✅ Found {len(source_attrs)} {description}")
                    
                    # Determine the path prefix based on source type
                    if source_key == 'secrets':
                        path_prefix = "/secrets"
                        extract_nested_attributes(source_attrs, path_prefix, description)
                    elif source_key == 'attributes':
                        # For attributes, check if they already have path prefixes
                        for attr_name, attr_value in source_attrs.items():
                            if attr_name.startswith('/'):
                                # Already a full path
                                attributes[attr_name] = attr_value
                                attributes_found += 1
                                print(f"      → {attr_name}: {type(attr_value).__name__}")
                            else:
                                # Need to add path prefix
                                full_path = f"/domain/{attr_name}"
                                attributes[full_path] = attr_value
                                attributes_found += 1
                                print(f"      → {full_path}: {type(attr_value).__name__}")
                    else:
                        path_prefix = "/domain"
                        extract_nested_attributes(source_attrs, path_prefix, description)
            
            print(f"   ✅ Extracted {attributes_found} total attributes from temporary component")
            return attributes, attributes_found, temp_comp_id, temp_changeset_id
            
        except Exception as extraction_error:
            print(f"   ❌ Error during attribute extraction: {extraction_error}")
            import traceback
            print(f"   Full traceback: {traceback.format_exc()}")
            
            # Fall back to enhanced schema fallback
            fallback_attributes = generate_enhanced_schema_fallback(schema_name)
            return fallback_attributes, len(fallback_attributes), temp_comp_id, temp_changeset_id
        
    except Exception as e:
        print(f"   ❌ Unexpected error in temp component creation: {e}")
        import traceback
        print(f"   Full traceback: {traceback.format_exc()}")
        return {}, 0, temp_comp_id, temp_changeset_id


def cleanup_temp_component(session, temp_comp_id, temp_changeset_id, change_set_id):
    """Delete the temporary component and changeset we created for extraction"""
    
    try:
        # Delete component first if it exists
        if temp_comp_id:
            from system_initiative_api_client import ComponentsApi
            comp_api = ComponentsApi(session.api_client)
            
            working_changeset = temp_changeset_id if temp_changeset_id else change_set_id
            
            print(f"   🧹 Deleting temporary component: {temp_comp_id}")
            
            comp_api.delete_component(
                workspace_id=session.workspace_id,
                change_set_id=working_changeset,
                component_id=temp_comp_id
            )
            
            print(f"   ✅ Temporary component deleted successfully")
        
        # Delete temporary changeset if we created one
        if temp_changeset_id:
            from system_initiative_api_client import ChangeSetsApi
            changeset_api = ChangeSetsApi(session.api_client)
            
            print(f"   🧹 Deleting temporary changeset: {temp_changeset_id}")
            
            changeset_api.abandon_change_set(
                workspace_id=session.workspace_id,
                change_set_id=temp_changeset_id
            )
            
            print(f"   ✅ Temporary changeset deleted successfully")
        
    except Exception as e:
        print(f"   ⚠️  Warning: Could not clean up temporary resources: {e}")
        if temp_comp_id:
            print(f"      You may need to manually delete component {temp_comp_id}")
        if temp_changeset_id:
            print(f"      You may need to manually delete changeset {temp_changeset_id}")


def create_template_from_attributes(schema_name, schema_id, attributes, attributes_found, input_count, output_count, change_set_id, is_installed, required_attributes, quiet=False):
    """Create and save template from extracted attributes with DYNAMIC required attribute analysis"""
    
    def quiet_print(msg):
        if not quiet:
            print(msg)
    
    template = {
        "name": f"my-{schema_name.lower().replace('::', '-').replace(' ', '-').replace('_', '-')}",
        "schema_name": schema_name,
        "attributes": attributes
    }
    
    quiet_print(f"   ✅ Created template with {attributes_found} attributes")
    
    # Analyze which required attributes are present/missing
    required_analysis = {
        "required_attributes_found": [],
        "required_attributes_missing": [],
        "conditional_attributes_found": [],
        "conditional_attributes_missing": []
    }
    
    for req_path, req_info in required_attributes.items():
        is_required = req_info.get("required") == True
        is_conditional = req_info.get("required") == "conditional"
        is_present = req_path in attributes
        
        if is_required:
            if is_present:
                required_analysis["required_attributes_found"].append({
                    "path": req_path,
                    "reason": req_info.get("reason", ""),
                    "value": attributes[req_path],
                    "detection_method": req_info.get("detection_method", "dynamic_analysis")
                })
            else:
                required_analysis["required_attributes_missing"].append({
                    "path": req_path,
                    "reason": req_info.get("reason", ""),
                    "source": req_info.get("source", ""),
                    "detection_method": req_info.get("detection_method", "dynamic_analysis")
                })
        elif is_conditional:
            if is_present:
                required_analysis["conditional_attributes_found"].append({
                    "path": req_path,
                    "reason": req_info.get("reason", ""),
                    "value": attributes[req_path],
                    "detection_method": req_info.get("detection_method", "dynamic_analysis")
                })
            else:
                required_analysis["conditional_attributes_missing"].append({
                    "path": req_path,
                    "reason": req_info.get("reason", ""),
                    "source": req_info.get("source", ""),
                    "detection_method": req_info.get("detection_method", "dynamic_analysis")
                })
    
    # Save template to file
    quiet_print(f"\n5. Saving template to file...")
    
    safe_name = schema_name.replace('::', '_').replace(' ', '_').lower()
    filename = f"component_configs/{safe_name}_template.json.example"
    
    Path("component_configs").mkdir(exist_ok=True)
    
    template_data = [template]
    
    complete_example = {
        "schemaName": schema_name,
        "name": "demo-component", 
        "attributes": attributes
    }
    
    final_data = {
        "_metadata": {
            "schema_name": schema_name,
            "schema_id": schema_id,
            "generated_from": "System Initiative API",
            "generated_at": "auto-generated",
            "note": "This template uses NEW UI format with attribute paths and $source references - DYNAMIC REQUIREMENTS DETECTION",
            "ui_format": "new",
            "schema_installed": is_installed,
            "input_subscriptions_count": input_count,
            "output_subscriptions_count": output_count,
            "required_attributes_analysis": required_analysis,
            "requirements_source": "Dynamic Schema Definition Analysis (NO HARDCODING)"
        },
        "_required_attributes_info": {
            "description": "Analysis of required vs optional attributes based on DYNAMIC schema definition analysis",
            "detection_method": "Dynamic schema analysis - NO hardcoded requirements",
            "note": "Requirements are detected dynamically from actual schema definitions",
            "required_count": len(required_analysis["required_attributes_found"]) + len(required_analysis["required_attributes_missing"]),
            "conditional_count": len(required_analysis["conditional_attributes_found"]) + len(required_analysis["conditional_attributes_missing"]),
            "coverage": {
                "required_present": len(required_analysis["required_attributes_found"]),
                "required_missing": len(required_analysis["required_attributes_missing"]),
                "conditional_present": len(required_analysis["conditional_attributes_found"]),
                "conditional_missing": len(required_analysis["conditional_attributes_missing"])
            }
        },
        "_complete_usage_example": {
            "description": "Complete ready-to-use example with all available attributes",
            "copy_paste_ready": True,
            "create_component_request": complete_example
        },
        "templates": template_data
    }
    
    with open(filename, 'w') as f:
        json.dump(final_data, f, indent=2)
    
    quiet_print(f"   ✅ Template saved to: {filename}")
    
    # Show summary with required attributes analysis
    installation_status = "✅ INSTALLED" if is_installed else "⚠️  NOT INSTALLED"
    req_found = len(required_analysis["required_attributes_found"])
    req_missing = len(required_analysis["required_attributes_missing"])
    cond_found = len(required_analysis["conditional_attributes_found"])
    cond_missing = len(required_analysis["conditional_attributes_missing"])
    
    quiet_print(f"\n📋 Template Summary (NEW UI FORMAT + DYNAMIC REQUIREMENTS DETECTION):")
    quiet_print(f"   Schema: {schema_name} ({installation_status})")
    quiet_print(f"   Template name: {template['name']}")  
    quiet_print(f"   Attribute paths: {attributes_found}")
    quiet_print(f"   Input Subscriptions: {input_count}")
    quiet_print(f"   Output Subscriptions: {output_count}")
    quiet_print(f"   Required Attributes: {req_found} found, {req_missing} missing (DYNAMIC DETECTION)")
    quiet_print(f"   Conditional Attributes: {cond_found} found, {cond_missing} missing (DYNAMIC DETECTION)") 
    quiet_print(f"   File: {filename}")
    
    # Show missing required attributes as warnings
    if req_missing > 0:
        quiet_print(f"\n⚠️  MISSING REQUIRED ATTRIBUTES (from dynamic schema analysis):")
        for missing in required_analysis["required_attributes_missing"]:
            quiet_print(f"   ❌ {missing['path']}: {missing['reason'][:80]}...")
    
    return True


def fetch_schema_template(schema_name: str, change_set_id: str = "HEAD", quiet: bool = True):
    """Fetch schema template with subscriptions and save to component_configs directory - DYNAMIC REQUIREMENTS ONLY"""
    
    # Initialize cleanup variables early to ensure proper scope
    temp_comp_id = None
    temp_changeset_id = None
    
    def quiet_print(msg, force=False):
        """Print only if not in quiet mode, or if force=True"""
        if not quiet or force:
            print(msg)
    
    try:
        session = SISession.from_env()
        schemas_api = SchemasApi(session.api_client)
        
        if not quiet:
            print(f"🎯 Fetching schema template: {schema_name}")
            print(f"📋 Workspace: {session.workspace_id}")
            print(f"📄 Change set: {change_set_id}")
            print("-" * 60)
        else:
            # Show simple progress bar
            import sys
            progress_chars = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
            progress_idx = 0
            
            def show_progress(step_name):
                nonlocal progress_idx
                char = progress_chars[progress_idx % len(progress_chars)]
                progress_idx += 1
                sys.stdout.write(f'\r{char} {step_name}...')
                sys.stdout.flush()
            
            show_progress("Searching for schema")
        
        # Step 1: Find the schema
        target_schema = find_schema_in_all_pages(schemas_api, session, schema_name, change_set_id)
        
        if not target_schema:
            quiet_print(f"\n❌ STOPPING: Schema '{schema_name}' not found anywhere!", force=True)
            return False
        
        schema_id = target_schema.get('schemaId')
        is_installed = target_schema.get('installed', True)
        
        if quiet:
            show_progress("Schema found, analyzing attributes")
        else:
            print(f"✅ Found schema! ID: {schema_id}")
            print(f"📦 Schema installed: {is_installed}")
        
        # Step 1.5: Get required attributes using ONLY dynamic detection - NO HARDCODING
        required_attributes = get_required_attributes_for_schema(session, schema_id, change_set_id, schema_name, quiet)
        
        # Step 2: Get variant data (try regardless of installation status)
        if quiet:
            show_progress("Getting schema variant data")
        else:
            print(f"\n2. Getting schema variant for attributes...")
        variant_data = {}
        
        try:
            variant_response = schemas_api.get_default_variant_without_preload_content(
                workspace_id=session.workspace_id,
                change_set_id=change_set_id,
                schema_id=schema_id
            )
            
            if hasattr(variant_response, 'data'):
                variant_raw = variant_response.data.decode('utf-8') if hasattr(variant_response.data, 'decode') else variant_response.data
                variant_data = json.loads(variant_raw) if isinstance(variant_raw, str) else variant_raw
                
                if isinstance(variant_data, dict) and 'statusCode' in variant_data:
                    quiet_print(f"   ❌ Default variant error: {variant_data.get('message')}")
                    variant_data = {}
                else:
                    quiet_print(f"   ✅ Default variant retrieved successfully")
                    
        except Exception as variant_error:
            quiet_print(f"   ❌ Default variant error: {variant_error}")
            variant_data = {}

        # Step 3: Extract attributes (try multiple approaches)
        if quiet:
            show_progress("Extracting attributes")
        else:
            print(f"\n3. 🔧 Extracting attributes...")
        
        attributes = {}
        attributes_found = 0
        
        # Try 1: Extract from existing components
        if is_installed:
            if quiet:
                show_progress("Checking existing components")
            else:
                print(f"   🔍 Trying existing components first (schema is installed)...")
            existing_attrs, existing_count = extract_attributes_from_existing_components(
                session, schema_name, change_set_id
            )
            attributes.update(existing_attrs)
            attributes_found += existing_count
        
        # Try 2: Extract directly from schema definition
        if attributes_found == 0:
            if quiet:
                show_progress("Analyzing schema definition")
            else:
                print(f"   🔍 Trying direct schema definition extraction...")
            direct_attrs, direct_count = extract_schema_definition_directly(
                session, schema_id, change_set_id
            )
            attributes.update(direct_attrs)
            attributes_found += direct_count
        
        # Try 3: Create temporary component
        if attributes_found == 0:
            if quiet:
                show_progress("Creating temporary component")
            else:
                print(f"   🗂️  Trying temporary component approach...")
            
            extracted_attrs, extracted_count, temp_comp_id, temp_changeset_id = create_temp_component_for_extraction(
                session, schema_name, change_set_id
            )
            
            attributes.update(extracted_attrs)
            attributes_found += extracted_count
        
        # Try 4: Use enhanced fallback if all else fails
        if attributes_found == 0:
            if quiet:
                show_progress("Using fallback attributes")
            else:
                print(f"   ⚠️  All extraction methods failed, using enhanced fallback attributes...")
            
            fallback_attributes = generate_enhanced_schema_fallback(schema_name)
            attributes.update(fallback_attributes)
            attributes_found = len(attributes)
        
        # Step 4: Extract subscriptions and generate attribute paths from them
        subscriptions = extract_subscriptions(variant_data)
        input_count = len(subscriptions["input_subscriptions"])
        output_count = len(subscriptions["output_subscriptions"])
        
        quiet_print(f"   🔍 Found {input_count} input subscriptions, {output_count} output subscriptions")
        
        # Generate attribute paths from subscription sockets
        subscription_attributes = {}
        if input_count > 0:
            quiet_print(f"   📡 Generating attribute paths from input subscriptions...")
            for sub in subscriptions["input_subscriptions"]:
                socket_name = sub.get('name', 'Unknown')
                socket_kind = sub.get('kind', 'domain')
                
                if socket_kind.lower() == 'secrets':
                    attr_path = f"/secrets/{socket_name}"
                else:
                    attr_path = f"/domain/extra/{socket_name}"
                
                example_component = f"my-{socket_name.lower().replace(' ', '-')}"
                example_source_path = f"/{socket_kind.lower()}/{socket_name.lower()}"
                
                subscription_attributes[attr_path] = {
                    "$source": {
                        "component": example_component,
                        "path": example_source_path
                    }
                }
                
                quiet_print(f"      → Generated: {attr_path} from {socket_name} socket")
        
        # Merge subscription-derived attributes with extracted attributes
        if subscription_attributes:
            quiet_print(f"   ✅ Adding {len(subscription_attributes)} subscription-derived attributes")
            attributes.update(subscription_attributes)
            attributes_found += len(subscription_attributes)
        
        # Step 5: Create and save template with DYNAMIC required attributes analysis
        if quiet:
            show_progress("Saving template file")
            
        result = create_template_from_attributes(
            schema_name, schema_id, attributes, attributes_found, 
            input_count, output_count, change_set_id, is_installed, required_attributes, quiet
        )
        
        # Show final result in quiet mode
        if quiet and result:
            import sys
            safe_name = schema_name.replace('::', '_').replace(' ', '_').lower()
            filename = f"component_configs/{safe_name}_template.json.example"
            sys.stdout.write(f'\r✅ Template saved to: {filename}\n')
            sys.stdout.flush()
        
        return result
        
    except Exception as e:
        quiet_print(f"❌ Error: {e}", force=True)
        if not quiet:
            import traceback
            print(f"Full traceback: {traceback.format_exc()}")
        return False
        
    finally:
        # Clean up temporary resources
        if temp_comp_id or temp_changeset_id:
            if not quiet:
                print(f"\n🧹 Cleaning up temporary resources...")
            cleanup_temp_component(session, temp_comp_id, temp_changeset_id, change_set_id)


def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Fetch Schema Template with DYNAMIC Required Attributes Detection (NO HARDCODING)")
    parser.add_argument("schema_name", help="Schema name to fetch (e.g., 'AWS::RDS::DBInstance')")
    parser.add_argument("--changeset", "-c", default="HEAD", help="Change set ID (default: HEAD)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show detailed output (default is quiet mode)")
    
    args = parser.parse_args()
    
    # Only show banner in verbose mode
    if args.verbose:
        print("🚀 Enhanced Schema Template Fetcher & Saver (DYNAMIC Requirements Detection)")
        print("=" * 80)
    
    success = fetch_schema_template(args.schema_name, args.changeset, quiet=not args.verbose)
    
    if success:
        if args.verbose:
            print(f"\n✅ Enhanced schema template (DYNAMIC requirements) completed!")
            print(f"💡 The template uses NEW UI format with attribute paths and $source references")
            print(f"🔍 Required attributes detected DYNAMICALLY from actual schema definitions")
            print(f"📝 Copy/rename to .json to use it in your component configurations")
            print(f"🔗 Connection examples show how to link components with $source references")
            print(f"⚠️  Check metadata for missing required attributes before deployment")
    else:
        if args.verbose:
            print(f"\n❌ Schema template fetch failed!")
        else:
            print(f"❌ Failed to fetch schema template for '{args.schema_name}'")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())