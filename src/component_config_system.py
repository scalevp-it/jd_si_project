"""
Component Configuration System for System Initiative
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ComponentConfig:
    """Configuration for creating a component"""
    name: str
    schema_name: str
    attributes: Optional[Dict[str, Any]] = None
    domain: Optional[Dict[str, Any]] = None
    secrets: Optional[Dict[str, Any]] = None
    resource_id: Optional[str] = None
    view_name: Optional[str] = None
    connections: Optional[List[Dict[str, Any]]] = None
    subscriptions: Optional[Dict[str, Dict[str, Any]]] = None
    managed_by: Optional[Dict[str, str]] = None
    
    def to_create_request(self) -> Dict[str, Any]:
        """Convert to CreateComponentV1Request format"""
        request_data = {
            "name": self.name,
            "schemaName": self.schema_name
        }
        
        # Always include attributes (even if empty) to avoid None validation errors
        request_data["attributes"] = self.attributes or {}
        
        # Add common optional fields with defaults to prevent None errors
        request_data["domain"] = self.domain or {}
        request_data["secrets"] = self.secrets or {}
        
        # Add other optional fields if they exist
        if self.resource_id:
            request_data["resourceId"] = self.resource_id
        if self.view_name:
            request_data["viewName"] = self.view_name
        if self.connections:
            request_data["connections"] = self.connections
        if self.subscriptions:
            request_data["subscriptions"] = self.subscriptions
        if self.managed_by:
            request_data["managedBy"] = self.managed_by
            
        return request_data


class ComponentConfigManager:
    """Manages component configurations and creation"""
    
    def __init__(self, config_dir: str = "component_configs/component_templates"):
        """
        Initialize the component config manager
        
        Args:
            config_dir: Directory containing component configuration files
        """
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self._configs: Dict[str, ComponentConfig] = {}
        self._load_configs()
    
    def _load_configs(self):
        """Load all configuration files from the config directory"""
        logger.info(f"Loading component configurations from {self.config_dir}")
        
        for config_file in self.config_dir.glob("*.json"):
            try:
                with open(config_file, 'r') as f:
                    config_data = json.load(f)
                
                # Handle both single config and list of configs in one file
                if isinstance(config_data, list):
                    for config in config_data:
                        self._add_config_from_dict(config, config_file.name)
                else:
                    self._add_config_from_dict(config_data, config_file.name)
                    
            except Exception as e:
                logger.error(f"Error loading config file {config_file}: {e}")
    
    def _add_config_from_dict(self, config_data: Dict[str, Any], filename: str):
        """Add a configuration from dictionary data"""
        try:
            config = ComponentConfig(**config_data)
            config_key = f"{filename}:{config.name}"
            self._configs[config_key] = config
            logger.info(f"Loaded config: {config.name} ({config.schema_name})")
        except Exception as e:
            logger.error(f"Error parsing config in {filename}: {e}")
    
    def get_config(self, name: str) -> Optional[ComponentConfig]:
        """Get a configuration by name"""
        # First try exact match
        for key, config in self._configs.items():
            if config.name == name:
                return config
        
        # Then try partial match
        for key, config in self._configs.items():
            if name.lower() in config.name.lower():
                return config
        
        return None
    
    def list_configs(self) -> List[ComponentConfig]:
        """List all available configurations"""
        return list(self._configs.values())
    
    def create_sample_configs(self):
        """Create sample configuration files for common components"""
        
        # AWS EC2 Instance Example
        ec2_config = {
            "name": "web-server-instance",
            "schema_name": "AWS EC2 Instance",
            "attributes": {
                "InstanceType": "t3.micro",
                "ImageId": "ami-0c02fb55956c7d316",  # Amazon Linux 2
                "KeyName": "my-keypair"
            },
            "domain": {
                "Name": "WebServer",
                "Environment": "development",
                "Owner": "devops-team"
            }
        }
        
        # AWS VPC Example
        vpc_config = {
            "name": "main-vpc",
            "schema_name": "AWS VPC", 
            "attributes": {
                "CidrBlock": "10.0.0.0/16",
                "EnableDnsHostnames": True,
                "EnableDnsSupport": True
            },
            "domain": {
                "Name": "MainVPC",
                "Environment": "production"
            }
        }
        
        # Docker Container Example
        docker_config = {
            "name": "web-app-container",
            "schema_name": "Docker Container",
            "attributes": {
                "Image": "nginx:latest",
                "Ports": ["80:80", "443:443"],
                "Environment": {
                    "NGINX_HOST": "localhost",
                    "NGINX_PORT": "80"
                }
            },
            "domain": {
                "Name": "WebApp",
                "Version": "1.0.0"
            }
        }
        
        # Kubernetes Deployment Example
        k8s_config = {
            "name": "api-deployment",
            "schema_name": "Kubernetes Deployment",
            "attributes": {
                "replicas": 3,
                "image": "myapp/api:v1.2.0",
                "ports": [{"containerPort": 8080}],
                "resources": {
                    "requests": {"memory": "256Mi", "cpu": "250m"},
                    "limits": {"memory": "512Mi", "cpu": "500m"}
                }
            },
            "domain": {
                "namespace": "production",
                "app": "api-service"
            }
        }
        
        # Save sample configs
        sample_configs = {
            "aws_examples.json.example": [ec2_config, vpc_config],
            "container_examples.json.example": [docker_config],
            "kubernetes_examples.json.example": [k8s_config]
        }
        
        for filename, configs in sample_configs.items():
            config_path = self.config_dir / filename
            if not config_path.exists():
                with open(config_path, 'w') as f:
                    json.dump(configs, f, indent=2)
                logger.info(f"Created sample config file: {filename}")
        
        # Reload configs after creating samples
        self._configs.clear()
        self._load_configs()
    
    def create_component_from_config(self, session, change_set_id: str, config_name: str) -> Optional[str]:
        """
        Create a component using a configuration
        
        Args:
            session: SISession instance
            change_set_id: ID of the change set
            config_name: Name of the configuration to use
            
        Returns:
            Component ID if successful, None otherwise
        """
        config = self.get_config(config_name)
        if not config:
            logger.error(f"Configuration '{config_name}' not found")
            return None
        
        try:
            from system_initiative_api_client import ComponentsApi, CreateComponentV1Request
            import json
            components_api = ComponentsApi(session.api_client)
            
            # Create the request object
            request_data = config.to_create_request()
            logger.info(f"Creating component '{config.name}' with schema '{config.schema_name}'")
            logger.info(f"Request data: {json.dumps(request_data, indent=2)}")
            
            # Create request object
            logger.info(f"Creating SDK request object...")
            create_request = CreateComponentV1Request(**request_data)
            logger.info(f"SDK request object created successfully")
            
            # Make the API call using raw method to bypass pydantic validation issues
            logger.info(f"Making API call...")
            response = components_api.create_component_without_preload_content(
                workspace_id=session.workspace_id,
                change_set_id=change_set_id,
                create_component_v1_request=create_request
            )
            
            # Handle raw response
            if hasattr(response, 'data'):
                raw_data = response.data.decode('utf-8') if hasattr(response.data, 'decode') else response.data
                response_data = json.loads(raw_data) if isinstance(raw_data, str) else raw_data
                
                # Extract component ID from response
                if isinstance(response_data, dict) and 'component' in response_data:
                    component_data = response_data['component']
                    if isinstance(component_data, dict) and 'id' in component_data:
                        component_id = component_data['id']
                        logger.info(f"✅ Successfully created component: {config.name} (ID: {component_id})")
                        return component_id
                
                logger.error(f"❌ Unexpected response format: {response_data}")
                return None
            else:
                logger.error(f"❌ No data in response: {response}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error creating component '{config.name}': {e}")
            import traceback
            logger.debug(f"Full traceback: {traceback.format_exc()}")
            return None
    
    def bulk_create_components(self, session, change_set_id: str, config_names: List[str]) -> Dict[str, Optional[str]]:
        """
        Create multiple components from configurations
        
        Args:
            session: SISession instance
            change_set_id: ID of the change set
            config_names: List of configuration names to create
            
        Returns:
            Dictionary mapping config names to component IDs (or None if failed)
        """
        results = {}
        
        for config_name in config_names:
            logger.info(f"Creating component from config: {config_name}")
            component_id = self.create_component_from_config(session, change_set_id, config_name)
            results[config_name] = component_id
            
            if component_id:
                logger.info(f"✅ Created: {config_name} -> {component_id}")
            else:
                logger.error(f"❌ Failed: {config_name}")
        
        return results
    
    def export_config(self, config_name: str, output_file: str) -> bool:
        """Export a configuration to a file"""
        config = self.get_config(config_name)
        if not config:
            logger.error(f"Configuration '{config_name}' not found")
            return False
        
        try:
            config_dict = asdict(config)
            with open(output_file, 'w') as f:
                json.dump(config_dict, f, indent=2)
            logger.info(f"Exported config '{config_name}' to {output_file}")
            return True
        except Exception as e:
            logger.error(f"Error exporting config: {e}")
            return False
    
    def validate_config(self, config_name: str) -> bool:
        """Validate a configuration"""
        config = self.get_config(config_name)
        if not config:
            logger.error(f"Configuration '{config_name}' not found")
            return False
        
        # Basic validation
        if not config.name:
            logger.error(f"Config '{config_name}' missing required field: name")
            return False
        
        if not config.schema_name:
            logger.error(f"Config '{config_name}' missing required field: schema_name")
            return False
        
        logger.info(f"✅ Configuration '{config_name}' is valid")
        return True


def create_config_template(schema_name: str, output_file: str):
    """Create a template configuration file for a given schema"""
    template = {
        "name": f"my-{schema_name.lower().replace(' ', '-')}",
        "schema_name": schema_name,
        "attributes": {
            "// Add schema-specific attributes here": "value"
        },
        "domain": {
            "Name": f"My{schema_name.replace(' ', '')}",
            "Environment": "development",
            "Owner": "team-name"
        }
    }
    
    try:
        with open(output_file, 'w') as f:
            json.dump(template, f, indent=2)
        logger.info(f"Created template for '{schema_name}' at {output_file}")
        return True
    except Exception as e:
        logger.error(f"Error creating template: {e}")
        return False


if __name__ == "__main__":
    # Example usage
    manager = ComponentConfigManager()
    
    # Create sample configs if directory is empty
    if not manager.list_configs():
        print("No configurations found. Creating sample configurations...")
        manager.create_sample_configs()
    
    # List available configurations
    print("\nAvailable configurations:")
    for config in manager.list_configs():
        print(f"  - {config.name} ({config.schema_name})")
    
    # Validate all configs
    print("\nValidating configurations...")
    for config in manager.list_configs():
        manager.validate_config(config.name)