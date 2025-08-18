"""
Changeset Component Extractor

Extracts all components from a changeset and saves them as JSON files
for analysis, backup, or reuse.
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
from system_initiative_api_client.api.components_api import ComponentsApi

from .si_session import SISession


class ChangesetExtractor:
    """Extract and save changeset components as JSON files"""
    
    def __init__(self, session: SISession):
        self.session = session
        self.components_api = ComponentsApi(session.api_client)
        
    def extract_changeset_components(
        self, 
        change_set_id: str, 
        output_dir: str = "component_configs/current_components"
    ) -> Dict[str, Any]:
        """
        Extract all components from a changeset and save as JSON files
        
        Args:
            change_set_id: The changeset ID to extract from
            output_dir: Directory to save component JSON files
            
        Returns:
            Dict with extraction summary and metadata
        """
        print(f"🔄 Extracting components from changeset...")
        
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        # Get all components in the changeset
        components = self._get_all_components_paginated(change_set_id)
        
        if not components:
            print("🔭 No components found in this changeset")
            return {
                "success": True,
                "component_count": 0,
                "files_created": [],
                "changeset_id": change_set_id,
                "extracted_at": datetime.now().isoformat()
            }
        
        print(f"📋 Found {len(components)} components to extract")
        
        # Extract detailed data for each component
        extraction_results = []
        files_created = []
        
        for i, component in enumerate(components, 1):
            component_id = component["id"]
            component_name = component["display_name"]
            schema_name = component["schema_name"]
            
            print(f"  {i}/{len(components)} Extracting: {component_name} ({schema_name})")
            
            try:
                # Get detailed component data
                detailed_component = self._get_component_details(change_set_id, component_id)
                
                if detailed_component:
                    # Create filename
                    safe_name = self._make_safe_filename(component_name)
                    filename = f"{safe_name}_{component_id[:8]}.json"
                    filepath = os.path.join(output_dir, filename)
                    
                    # Save component data
                    self._save_component_data(detailed_component, filepath, change_set_id)
                    
                    files_created.append(filename)
                    extraction_results.append({
                        "component_id": component_id,
                        "component_name": component_name,
                        "schema_name": schema_name,
                        "filename": filename,
                        "success": True
                    })
                else:
                    extraction_results.append({
                        "component_id": component_id,
                        "component_name": component_name,
                        "schema_name": schema_name,
                        "success": False,
                        "error": "Failed to get detailed component data"
                    })
                    
            except Exception as e:
                print(f"    ❌ Error extracting {component_name}: {e}")
                extraction_results.append({
                    "component_id": component_id,
                    "component_name": component_name,
                    "schema_name": schema_name,
                    "success": False,
                    "error": str(e)
                })
        
        # Create extraction summary
        successful_extractions = [r for r in extraction_results if r["success"]]
        failed_extractions = [r for r in extraction_results if not r["success"]]
        
        summary = {
            "success": True,
            "changeset_id": change_set_id,
            "extracted_at": datetime.now().isoformat(),
            "component_count": len(components),
            "successful_extractions": len(successful_extractions),
            "failed_extractions": len(failed_extractions),
            "files_created": files_created,
            "output_directory": output_dir,
            "extraction_details": extraction_results
        }
        
        # Save extraction summary
        summary_file = os.path.join(output_dir, f"extraction_summary_{change_set_id[:8]}.json")
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        print(f"✅ Extraction completed:")
        print(f"   Successfully extracted: {len(successful_extractions)} components")
        if failed_extractions:
            print(f"   Failed extractions: {len(failed_extractions)} components")
        print(f"   Files saved to: {output_dir}")
        print(f"   Summary saved: {os.path.basename(summary_file)}")
        
        return summary
    
    def _get_all_components_paginated(self, change_set_id: str) -> List[Dict[str, Any]]:
        """Get all components using the session's get_components method"""
        try:
            # Use the existing SI session method which handles API response parsing correctly
            components = self.session.get_components(change_set_id)
            print(f"    📋 Found {len(components)} components")
            return components
        except Exception as e:
            print(f"❌ Error fetching components: {e}")
            return []
    
    def _get_component_details(self, change_set_id: str, component_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed component data including attributes and connections"""
        try:
            # Use the raw API method with preload bypassing like in si_session.py
            response = self.components_api.get_component_without_preload_content(
                workspace_id=self.session.workspace_id,
                change_set_id=change_set_id,
                component_id=component_id
            )
            
            if hasattr(response, 'data'):
                import json
                raw_data = response.data.decode('utf-8') if hasattr(response.data, 'decode') else response.data
                data = json.loads(raw_data) if isinstance(raw_data, str) else raw_data
                return data
            
            return None
            
        except Exception as e:
            print(f"    ❌ Error getting component details: {e}")
            return None
    
    def _save_component_data(
        self, 
        component_data: Dict[str, Any], 
        filepath: str, 
        change_set_id: str
    ):
        """Save component data to JSON file with metadata in template format"""
        
        # Extract component info
        component = component_data.get("component", {})
        component_name = component.get("name", "unknown")
        schema_name = self._get_schema_name_from_component(component)
        
        # Transform to template format
        template_data = self._transform_to_template_format(component_data, component_name, schema_name)
        
        # Add extraction metadata
        output_data = {
            "_extraction_metadata": {
                "extracted_from": "System Initiative Changeset",
                "changeset_id": change_set_id,
                "extracted_at": datetime.now().isoformat(),
                "extractor_version": "1.0.0",
                "component_id": component.get("id", "unknown"),
                "original_component_name": component_name,
                "schema_name": schema_name,
                "note": "This file contains component data transformed to template format for reuse"
            },
            **template_data
        }
        
        with open(filepath, 'w') as f:
            json.dump(output_data, f, indent=2)
    
    def _transform_to_template_format(
        self, 
        component_data: Dict[str, Any], 
        component_name: str, 
        schema_name: str
    ) -> Dict[str, Any]:
        """Transform raw component data to template format"""
        
        component = component_data.get("component", {})
        raw_attributes = component.get("attributes", {})
        
        # Transform attributes to template format
        template_attributes = {}
        
        # Process each raw attribute
        for attr_path, attr_value in raw_attributes.items():
            # Skip SI internal and runtime attributes
            if attr_path.startswith("/si/"):
                continue
            if attr_path.startswith("/qualification/"):
                continue
            if attr_path.startswith("/resource/"):
                continue  # Skip runtime resource data
            if attr_path.startswith("/resource_value/"):
                continue  # Skip resource output values
            if attr_path.startswith("/code/"):
                continue  # Skip generated code
                
            # Transform common attribute paths
            if attr_path.startswith("/root/"):
                # Transform /root/ paths to /domain/ paths
                new_path = attr_path.replace("/root/", "/domain/")
                template_attributes[new_path] = attr_value
            elif attr_path.startswith("/secrets/"):
                # Keep secrets paths as-is but transform values to $source format if they reference other components
                if isinstance(attr_value, str) and len(attr_value) > 20:  # Likely a component reference
                    # Look for connection that might provide this value
                    connections = component.get("connections", [])
                    source_component = self._find_source_component_for_secret(attr_path, connections)
                    
                    if source_component:
                        template_attributes[attr_path] = {
                            "$source": {
                                "component": source_component.get("name", "component-name"),
                                "path": attr_path
                            }
                        }
                    else:
                        # Keep as placeholder value
                        template_attributes[attr_path] = f"<{attr_path.split('/')[-1].lower().replace(' ', '_')}>"
                else:
                    template_attributes[attr_path] = attr_value
            else:
                # Use attribute as-is but ensure it has proper domain prefix if it doesn't have a path prefix
                if not attr_path.startswith("/"):
                    new_path = f"/domain/{attr_path}"
                    template_attributes[new_path] = attr_value
                else:
                    template_attributes[attr_path] = attr_value
        
        # Add standard SI attributes if not present
        if "/domain/Name" not in template_attributes:
            template_attributes["/domain/Name"] = component_name
            
        # Generate reference examples for this component
        reference_examples = self._generate_reference_examples(component, schema_name, component_name)
        
        # Build the template structure like the .example files
        return {
            "extracted_component": {
                "description": f"Component extracted from changeset and transformed to template format",
                "original_component_id": component.get("id", "unknown"),
                "schema_name": schema_name,
                "create_component_request": {
                    "schemaName": schema_name,
                    "name": component_name,
                    "attributes": template_attributes
                }
            },
            "_reference_examples": reference_examples
        }
    
    def _get_schema_name_from_component(self, component: Dict[str, Any]) -> str:
        """Extract schema name from component data"""
        schema_id = component.get("schemaId", "")
        schema_variant_id = component.get("schemaVariantId", "")
        
        # Try to use the session's schema name lookup method (similar to si_session.py)
        try:
            # Use the session's _get_schema_name method if available
            if hasattr(self.session, '_get_schema_name'):
                return self.session._get_schema_name("HEAD", schema_variant_id, schema_id)
        except Exception as e:
            print(f"    ⚠️  Could not resolve schema name: {e}")
        
        # Fallback to ID-based name
        return f"Schema-{schema_id[:8]}" if schema_id else "Unknown"
    
    def _generate_reference_examples(
        self, 
        component: Dict[str, Any], 
        schema_name: str, 
        component_name: str
    ) -> Dict[str, Any]:
        """Generate examples showing how other components can reference this component"""
        
        # Analyze the component's sockets to determine what it provides
        sockets = component.get("sockets", [])
        output_sockets = [s for s in sockets if s.get("direction") == "output"]
        
        reference_examples = {
            "description": f"Examples of how to reference this {schema_name} component in other component templates",
            "component_name": component_name,
            "schema_name": schema_name
        }
        
        # Generate reference patterns based on schema type and available outputs
        if output_sockets:
            reference_examples["available_outputs"] = []
            reference_examples["usage_examples"] = {}
            
            for socket in output_sockets:
                socket_name = socket.get("name", "unknown")
                socket_path = f"/secrets/{socket_name}" if socket_name in ["AWS Credential"] else f"/domain/{socket_name}"
                
                reference_examples["available_outputs"].append({
                    "socket_name": socket_name,
                    "path": socket_path,
                    "description": f"Reference to {socket_name} from {component_name}"
                })
                
                # Create usage example
                safe_socket_name = socket_name.lower().replace(" ", "_").replace("::", "_")
                reference_examples["usage_examples"][f"reference_{safe_socket_name}"] = {
                    socket_path: {
                        "$source": {
                            "component": component_name,
                            "path": socket_path
                        }
                    }
                }
        
        # Add schema-specific reference patterns
        reference_examples.update(self._get_schema_specific_references(schema_name, component_name))
        
        return reference_examples
    
    def _get_schema_specific_references(self, schema_name: str, component_name: str) -> Dict[str, Any]:
        """Get schema-specific reference patterns"""
        
        schema_references = {}
        
        # AWS EC2 VPC references
        if schema_name == "AWS::EC2::VPC":
            schema_references["common_references"] = {
                "vpc_id_reference": {
                    "description": "Reference VPC ID for subnet creation",
                    "example": {
                        "/domain/VpcId": {
                            "$source": {
                                "component": component_name,
                                "path": "/resource_value/VpcId"
                            }
                        }
                    }
                }
            }
        
        # AWS EC2 Subnet references  
        elif schema_name == "AWS::EC2::Subnet":
            schema_references["common_references"] = {
                "subnet_id_reference": {
                    "description": "Reference Subnet ID for EC2 instances or other resources",
                    "example": {
                        "/domain/SubnetId": {
                            "$source": {
                                "component": component_name,
                                "path": "/resource_value/SubnetId"
                            }
                        }
                    }
                }
            }
        
        # AWS Credential references
        elif schema_name == "AWS Credential":
            schema_references["common_references"] = {
                "aws_credential_reference": {
                    "description": "Reference AWS credentials for any AWS resource",
                    "example": {
                        "/secrets/AWS Credential": {
                            "$source": {
                                "component": component_name,
                                "path": "/secrets/AWS Credential"
                            }
                        }
                    }
                }
            }
        
        # Region references
        elif schema_name == "Region":
            schema_references["common_references"] = {
                "region_reference": {
                    "description": "Reference region for AWS resources",
                    "example": {
                        "/domain/extra/Region": {
                            "$source": {
                                "component": component_name,
                                "path": "/domain/region"
                            }
                        }
                    }
                }
            }
        
        # AWS EC2 SecurityGroup references
        elif schema_name == "AWS::EC2::SecurityGroup":
            schema_references["common_references"] = {
                "security_group_reference": {
                    "description": "Reference Security Group for EC2 instances",
                    "example": {
                        "/domain/SecurityGroupIds": [
                            {
                                "$source": {
                                    "component": component_name,
                                    "path": "/resource_value/GroupId"
                                }
                            }
                        ]
                    }
                }
            }
        
        # Generic reference for other schemas
        else:
            schema_references["generic_reference"] = {
                "description": f"Generic reference pattern for {schema_name}",
                "note": "Check component sockets and resource values for specific reference paths",
                "example": {
                    "/domain/SomeAttribute": {
                        "$source": {
                            "component": component_name,
                            "path": "/domain/attribute_name"
                        }
                    }
                }
            }
        
        return schema_references
    
    def _find_source_component_for_secret(
        self, 
        secret_path: str, 
        connections: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """Find the source component that provides a secret value"""
        # This would analyze connections to find which component provides the secret
        # For now, return None to use placeholder format
        return None
    
    def _make_safe_filename(self, name: str) -> str:
        """Convert component name to safe filename"""
        # Remove or replace unsafe characters
        safe_name = name.replace(' ', '_')
        safe_name = ''.join(c for c in safe_name if c.isalnum() or c in '_-.')
        return safe_name.lower()


def extract_changeset_components(
    change_set_id: str, 
    output_dir: str = "component_configs/current_components",
    quiet: bool = False
) -> Dict[str, Any]:
    """
    Convenience function to extract changeset components
    
    Args:
        change_set_id: The changeset ID to extract from
        output_dir: Directory to save component JSON files
        quiet: If True, suppress most output
        
    Returns:
        Dict with extraction summary
    """
    if not quiet:
        print(f"🚀 Starting changeset component extraction")
        print(f"   Changeset ID: {change_set_id}")
        print(f"   Output directory: {output_dir}")
    
    try:
        session = SISession.from_env()
        extractor = ChangesetExtractor(session)
        
        result = extractor.extract_changeset_components(change_set_id, output_dir)
        
        if not quiet:
            if result["successful_extractions"] > 0:
                print(f"✅ Extraction completed successfully")
                print(f"📁 Component files saved to: {output_dir}")
            else:
                print(f"⚠️  Extraction completed but no components were successfully extracted")
        
        return result
        
    except Exception as e:
        error_result = {
            "success": False,
            "error": str(e),
            "changeset_id": change_set_id,
            "extracted_at": datetime.now().isoformat()
        }
        
        if not quiet:
            print(f"❌ Extraction failed: {e}")
        
        return error_result