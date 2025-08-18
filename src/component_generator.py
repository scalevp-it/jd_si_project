"""
Component Generator

Generates minimal component configuration files by combining:
1. Minimal required attributes from schema fetcher ("needed to deploy")
2. Real component references (AWS credentials, regions) from extracted components

This creates ready-to-use component templates with proper $source references.
"""

import json
import os
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path

from .schema_fetcher import fetch_schema_template
from .si_session import SISession


class ComponentGenerator:
    """Generate minimal component configuration files with real references"""
    
    def __init__(self, session: SISession):
        self.session = session
        self.current_components_dir = "component_configs/current_components"
        self.component_templates_dir = "component_configs/component_templates"
        self.extracted_components = None
        
        # Ensure directories exist
        os.makedirs(self.current_components_dir, exist_ok=True)
        os.makedirs(self.component_templates_dir, exist_ok=True)
    
    def generate_component_config(
        self,
        schema_name: str,
        component_name: str,
        change_set_id: str = "HEAD",
        output_dir: str = None
    ) -> Dict[str, Any]:
        """
        Generate a minimal component configuration file
        
        Args:
            schema_name: Schema to generate config for (e.g., "AWS::EC2::Instance")
            component_name: Name for the new component
            change_set_id: Changeset to use for template generation
            output_dir: Directory to save the config file (defaults to templates dir)
            
        Returns:
            Dict with generation result and metadata
        """
        if output_dir is None:
            output_dir = self.component_templates_dir
        
        print(f"🏗️  Generating component config for {schema_name}")
        
        try:
            # Step 1: Get minimal schema template
            print(f"  📋 Fetching minimal schema template...")
            schema_template = self._get_minimal_schema_template(schema_name, change_set_id)
            
            if not schema_template:
                return {"success": False, "error": f"Failed to fetch schema template for {schema_name}"}
            
            # Step 2: Load current component references
            print(f"  🔗 Loading current component references...")
            component_refs = self._load_current_component_references()
            
            # Step 3: Generate config with real references
            print(f"  ⚙️  Generating config with real references...")
            config = self._create_component_config(
                schema_name, 
                component_name, 
                schema_template, 
                component_refs
            )
            
            # Step 4: Save config file
            filename = f"{component_name.lower().replace(' ', '_').replace('-', '_')}.json"
            filepath = os.path.join(output_dir, filename)
            
            with open(filepath, 'w') as f:
                json.dump(config, f, indent=2)
            
            print(f"  ✅ Generated: {filename}")
            
            return {
                "success": True,
                "filename": filename,
                "filepath": filepath,
                "schema_name": schema_name,
                "component_name": component_name,
                "attributes_count": len(config.get("attributes", {})),
                "real_references_used": len([
                    attr for attr in config.get("attributes", {}).values()
                    if isinstance(attr, dict) and "$source" in attr
                ])
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _get_minimal_schema_template(self, schema_name: str, change_set_id: str) -> Optional[Dict[str, Any]]:
        """Get the minimal template from schema fetcher"""
        try:
            # Call fetch_schema_template which saves to default location
            success = fetch_schema_template(
                schema_name=schema_name,
                change_set_id=change_set_id,
                quiet=True
            )
            
            if not success:
                return None
            
            # The template is saved to component_configs/examples/ directory
            template_filename = f"{schema_name.lower().replace('::', '_').replace(' ', '_')}_template.json.example"
            template_filepath = os.path.join("component_configs", "examples", template_filename)
            
            if not os.path.exists(template_filepath):
                print(f"    ❌ Template file not found: {template_filepath}")
                return None
            
            # Load and extract the minimal template
            with open(template_filepath, 'r') as f:
                template_data = json.load(f)
            
            # Extract the "needed to deploy" section
            needed_to_deploy = template_data.get("_needed_to_deploy", {})
            return needed_to_deploy.get("create_component_request", {})
            
        except Exception as e:
            print(f"    ❌ Error fetching schema template: {e}")
            return None
    
    def _load_current_component_references(self) -> Dict[str, Dict[str, Any]]:
        """Load references from current extracted components"""
        if self.extracted_components is not None:
            return self.extracted_components
        
        component_refs = {
            "aws_credentials": [],
            "regions": [],
            "vpcs": [],
            "subnets": [],
            "security_groups": [],
            "other": []
        }
        
        try:
            # Load all current component files
            current_components_path = Path(self.current_components_dir)
            
            if not current_components_path.exists():
                print(f"    ⚠️  No current components directory found")
                return component_refs
            
            for comp_file in current_components_path.glob("*.json"):
                if comp_file.name.startswith("extraction_summary"):
                    continue
                
                try:
                    with open(comp_file, 'r') as f:
                        comp_data = json.load(f)
                    
                    extracted_comp = comp_data.get("extracted_component", {})
                    create_request = extracted_comp.get("create_component_request", {})
                    schema_name = create_request.get("schemaName", "")
                    component_name = create_request.get("name", "")
                    
                    # Categorize components by type
                    if schema_name == "AWS Credential":
                        component_refs["aws_credentials"].append({
                            "name": component_name,
                            "schema_name": schema_name,
                            "reference": {
                                "$source": {
                                    "component": component_name,
                                    "path": "/secrets/AWS Credential"
                                }
                            }
                        })
                    elif schema_name == "Region":
                        component_refs["regions"].append({
                            "name": component_name,
                            "schema_name": schema_name,
                            "reference": {
                                "$source": {
                                    "component": component_name,
                                    "path": "/domain/region"
                                }
                            }
                        })
                    elif schema_name == "AWS::EC2::VPC":
                        component_refs["vpcs"].append({
                            "name": component_name,
                            "schema_name": schema_name,
                            "vpc_id_reference": {
                                "$source": {
                                    "component": component_name,
                                    "path": "/resource_value/VpcId"
                                }
                            }
                        })
                    elif schema_name == "AWS::EC2::Subnet":
                        component_refs["subnets"].append({
                            "name": component_name,
                            "schema_name": schema_name,
                            "subnet_id_reference": {
                                "$source": {
                                    "component": component_name,
                                    "path": "/resource_value/SubnetId"
                                }
                            }
                        })
                    elif schema_name == "AWS::EC2::SecurityGroup":
                        component_refs["security_groups"].append({
                            "name": component_name,
                            "schema_name": schema_name,
                            "group_id_reference": {
                                "$source": {
                                    "component": component_name,
                                    "path": "/resource_value/GroupId"
                                }
                            }
                        })
                    else:
                        component_refs["other"].append({
                            "name": component_name,
                            "schema_name": schema_name
                        })
                
                except Exception as e:
                    print(f"    ⚠️  Error loading {comp_file.name}: {e}")
                    continue
            
            self.extracted_components = component_refs
            return component_refs
            
        except Exception as e:
            print(f"    ❌ Error loading current components: {e}")
            return component_refs
    
    def _create_component_config(
        self,
        schema_name: str,
        component_name: str,
        schema_template: Dict[str, Any],
        component_refs: Dict[str, List[Dict[str, Any]]]
    ) -> Dict[str, Any]:
        """Create the final component configuration with real references"""
        
        # Start with the minimal schema template
        config = {
            "name": component_name,
            "schema_name": schema_name,
            "attributes": schema_template.get("attributes", {}).copy()
        }
        
        # Replace placeholder values with real component references
        self._inject_real_references(config["attributes"], schema_name, component_refs)
        
        # Ensure AWS resources have required credentials and region
        if schema_name.startswith("AWS::"):
            self._ensure_aws_requirements(config["attributes"], component_refs)
        
        return config
    
    def _inject_real_references(
        self,
        attributes: Dict[str, Any],
        schema_name: str,
        component_refs: Dict[str, List[Dict[str, Any]]]
    ):
        """Inject real component references into attributes"""
        
        # AWS Credential injection
        if "/secrets/AWS Credential" in attributes:
            if component_refs["aws_credentials"]:
                cred = component_refs["aws_credentials"][0]  # Use first available
                attributes["/secrets/AWS Credential"] = cred["reference"]
                print(f"    🔗 Using AWS credential: {cred['name']}")
        
        # Region injection
        region_keys = ["/domain/extra/Region", "/domain/Region", "/domain/AvailabilityZone"]
        for region_key in region_keys:
            if region_key in attributes:
                if component_refs["regions"]:
                    region = component_refs["regions"][0]  # Use first available
                    attributes[region_key] = region["reference"]
                    print(f"    🌍 Using region: {region['name']}")
                break
        
        # Schema-specific reference injection
        if schema_name.startswith("AWS::EC2::"):
            self._inject_aws_ec2_references(attributes, schema_name, component_refs)
    
    def _ensure_aws_requirements(
        self,
        attributes: Dict[str, Any],
        component_refs: Dict[str, List[Dict[str, Any]]]
    ):
        """Ensure AWS resources have required credentials and region references"""
        
        # Always add AWS credential if not present
        if "/secrets/AWS Credential" not in attributes:
            if component_refs["aws_credentials"]:
                cred = component_refs["aws_credentials"][0]
                attributes["/secrets/AWS Credential"] = cred["reference"]
                print(f"    ➕ Added required AWS credential: {cred['name']}")
            else:
                # Add placeholder if no real credential available
                attributes["/secrets/AWS Credential"] = {
                    "$source": {
                        "component": "my-aws-credential",
                        "path": "/secrets/AWS Credential"
                    }
                }
                print(f"    ➕ Added placeholder AWS credential reference")
        
        # Always add region if not present
        region_keys = ["/domain/extra/Region", "/domain/Region"]
        has_region = any(key in attributes for key in region_keys)
        
        if not has_region:
            if component_refs["regions"]:
                region = component_refs["regions"][0]
                attributes["/domain/extra/Region"] = region["reference"]
                print(f"    ➕ Added required region: {region['name']}")
            else:
                # Add placeholder if no real region available
                attributes["/domain/extra/Region"] = {
                    "$source": {
                        "component": "my-region",
                        "path": "/domain/region"
                    }
                }
                print(f"    ➕ Added placeholder region reference")
    
    def _inject_aws_ec2_references(
        self,
        attributes: Dict[str, Any],
        schema_name: str,
        component_refs: Dict[str, List[Dict[str, Any]]]
    ):
        """Inject AWS EC2-specific references"""
        
        # VPC references for subnets, security groups, etc.
        vpc_keys = ["/domain/VpcId", "/domain/Vpc"]
        for vpc_key in vpc_keys:
            if vpc_key in attributes and component_refs["vpcs"]:
                vpc = component_refs["vpcs"][0]  # Use first available
                attributes[vpc_key] = vpc["vpc_id_reference"]
                print(f"    🏗️  Using VPC: {vpc['name']}")
                break
        
        # Subnet references for EC2 instances
        subnet_keys = ["/domain/SubnetId", "/domain/SubnetIds"]
        for subnet_key in subnet_keys:
            if subnet_key in attributes and component_refs["subnets"]:
                subnet = component_refs["subnets"][0]  # Use first available
                if subnet_key.endswith("Ids"):  # Array format
                    attributes[subnet_key] = [subnet["subnet_id_reference"]]
                else:
                    attributes[subnet_key] = subnet["subnet_id_reference"]
                print(f"    🌐 Using subnet: {subnet['name']}")
                break
        
        # Security Group references
        sg_keys = ["/domain/SecurityGroupIds", "/domain/SecurityGroups"]
        for sg_key in sg_keys:
            if sg_key in attributes and component_refs["security_groups"]:
                sg = component_refs["security_groups"][0]  # Use first available
                if sg_key.endswith("Ids"):
                    attributes[sg_key] = [sg["group_id_reference"]]
                else:
                    attributes[sg_key] = [sg["group_id_reference"]]
                print(f"    🛡️  Using security group: {sg['name']}")
                break
    
    def _generate_reference_info(self, component_refs: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """Generate information about available references"""
        return {
            "description": "Available component references that were used or can be used",
            "aws_credentials_available": len(component_refs["aws_credentials"]),
            "regions_available": len(component_refs["regions"]),
            "vpcs_available": len(component_refs["vpcs"]),
            "subnets_available": len(component_refs["subnets"]),
            "security_groups_available": len(component_refs["security_groups"]),
            "other_components_available": len(component_refs["other"]),
            "note": "These references are automatically injected based on available extracted components"
        }


def generate_component_config(
    schema_name: str,
    component_name: str,
    change_set_id: str = "HEAD",
    output_dir: str = None,
    quiet: bool = False
) -> Dict[str, Any]:
    """
    Convenience function to generate a component configuration
    
    Args:
        schema_name: Schema to generate config for
        component_name: Name for the new component  
        change_set_id: Changeset to use
        output_dir: Output directory
        quiet: Suppress output
        
    Returns:
        Dict with generation result
    """
    if not quiet:
        print(f"🚀 Starting component config generation")
        print(f"   Schema: {schema_name}")
        print(f"   Component name: {component_name}")
        print(f"   Output directory: {output_dir or 'component_configs/component_templates'}")
    
    try:
        session = SISession.from_env()
        generator = ComponentGenerator(session)
        
        result = generator.generate_component_config(
            schema_name=schema_name,
            component_name=component_name,
            change_set_id=change_set_id,
            output_dir=output_dir
        )
        
        if not quiet:
            if result["success"]:
                print(f"✅ Component config generated successfully")
                print(f"📁 File: {result['filename']}")
                print(f"🔗 Real references used: {result['real_references_used']}")
            else:
                print(f"❌ Generation failed: {result['error']}")
        
        return result
        
    except Exception as e:
        error_result = {
            "success": False,
            "error": str(e),
            "schema_name": schema_name,
            "component_name": component_name
        }
        
        if not quiet:
            print(f"❌ Generation failed: {e}")
        
        return error_result