"""
Tests for Component Configuration System

Tests the component configuration management including loading configs,
validation, and component creation templates.
"""

import os
import json
from tests.test_framework import TestFramework, assert_true, assert_not_none, assert_contains, assert_file_exists
from src.component_config_system import ComponentConfigManager, ComponentConfig


class TestComponentConfigSystem:
    """Test suite for Component Configuration System"""
    
    def __init__(self):
        self.framework = TestFramework()
        self.test_config_dir = "tests/test_results/test_component_templates"
        self.config_manager = None
        
        # Ensure test directory exists
        os.makedirs(self.test_config_dir, exist_ok=True)
    
    def setup_test_configs(self):
        """Create test configuration files"""
        try:
            # Create a simple test config
            test_config = {
                "name": "test-component",
                "schema_name": "AWS::EC2::Instance",
                "attributes": {
                    "/domain/Name": "test-instance",
                    "/domain/InstanceType": "t3.micro",
                    "/domain/ImageId": "ami-12345"
                }
            }
            
            test_config_file = os.path.join(self.test_config_dir, "test_config.json")
            with open(test_config_file, 'w') as f:
                json.dump([test_config], f, indent=2)
            
            # Create a more complex config with $source references
            complex_config = {
                "name": "test-complex-component",
                "schema_name": "AWS::EC2::Instance",
                "attributes": {
                    "/domain/Name": "complex-instance",
                    "/domain/InstanceType": "t3.small",
                    "/domain/ImageId": "ami-67890",
                    "/secrets/AWS Credential": {
                        "$source": {
                            "component": "aws-creds",
                            "path": "/secrets/AWS Credential"
                        }
                    },
                    "/domain/SubnetId": {
                        "$source": {
                            "component": "subnet-component",
                            "path": "/resource_value/SubnetId"
                        }
                    }
                }
            }
            
            complex_config_file = os.path.join(self.test_config_dir, "complex_config.json")
            with open(complex_config_file, 'w') as f:
                json.dump([complex_config], f, indent=2)
            
            return True
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def test_config_manager_initialization(self):
        """Test ComponentConfigManager initialization"""
        try:
            self.config_manager = ComponentConfigManager(config_dir=self.test_config_dir)
            assert_not_none(self.config_manager, "Config manager should not be None")
            assert_not_none(self.config_manager.config_dir, "Config directory should be set")
            
            return {
                "success": True,
                "config_dir": str(self.config_manager.config_dir),
                "configs_loaded": len(self.config_manager._configs)
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def test_load_configurations(self):
        """Test loading configurations from files"""
        # First setup test configs
        setup_result = self.setup_test_configs()
        if not setup_result:
            return setup_result
        
        try:
            # Reinitialize to load the new configs
            self.config_manager = ComponentConfigManager(config_dir=self.test_config_dir)
            
            configs = self.config_manager.list_configs()
            assert_not_none(configs, "Configs should not be None")
            assert_true(isinstance(configs, list), "Configs should be a list")
            assert_true(len(configs) >= 2, "Should load at least 2 test configs")
            
            # Check that configs have required fields
            for config in configs:
                assert_true(hasattr(config, 'name'), "Config should have name")
                assert_true(hasattr(config, 'schema_name'), "Config should have schema_name")
                assert_true(hasattr(config, 'attributes'), "Config should have attributes")
            
            return {
                "success": True,
                "configs_loaded": len(configs),
                "config_names": [config.name for config in configs],
                "sample_config": {
                    "name": configs[0].name,
                    "schema_name": configs[0].schema_name,
                    "attribute_count": len(configs[0].attributes) if configs[0].attributes else 0
                }
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def test_config_validation(self):
        """Test configuration validation"""
        if not self.config_manager:
            return {"success": False, "error": "Config manager not initialized"}
        
        try:
            configs = self.config_manager.list_configs()
            if not configs:
                return {"success": False, "error": "No configs to validate"}
            
            # Test validation of first config
            config_name = configs[0].name
            is_valid = self.config_manager.validate_config(config_name)
            
            # Should be valid since we created proper test configs
            assert_true(is_valid, f"Config {config_name} should be valid")
            
            # Test validation of all configs
            validation_results = {}
            for config in configs:
                validation_results[config.name] = self.config_manager.validate_config(config.name)
            
            return {
                "success": True,
                "configs_validated": len(validation_results),
                "validation_results": validation_results,
                "all_valid": all(validation_results.values())
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def test_create_component_request_format(self):
        """Test conversion to create component request format"""
        if not self.config_manager:
            return {"success": False, "error": "Config manager not initialized"}
        
        try:
            configs = self.config_manager.list_configs()
            if not configs:
                return {"success": False, "error": "No configs to test"}
            
            # Test conversion of first config
            config = configs[0]
            create_request = config.to_create_request()
            
            assert_not_none(create_request, "Create request should not be None")
            assert_contains(create_request, "name", "Create request should have name")
            assert_contains(create_request, "schemaName", "Create request should have schemaName")
            
            # Check attributes format
            if config.attributes:
                assert_contains(create_request, "attributes", "Create request should have attributes")
                attributes = create_request["attributes"]
                
                # Check for proper path format
                has_domain_paths = any(key.startswith('/domain/') for key in attributes.keys())
                has_secrets_paths = any(key.startswith('/secrets/') for key in attributes.keys())
                
                result_data = {
                    "success": True,
                    "config_name": config.name,
                    "schema_name": create_request["schemaName"],
                    "has_domain_paths": has_domain_paths,
                    "has_secrets_paths": has_secrets_paths,
                    "attribute_count": len(attributes),
                    "sample_attributes": list(attributes.keys())[:5]
                }
                
                # Check for $source references
                has_source_refs = any(
                    isinstance(v, dict) and '$source' in v 
                    for v in attributes.values()
                )
                result_data["has_source_references"] = has_source_refs
                
                return result_data
            else:
                return {
                    "success": True,
                    "config_name": config.name,
                    "schema_name": create_request["schemaName"],
                    "has_attributes": False
                }
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def test_component_config_structure(self):
        """Test ComponentConfig dataclass structure"""
        try:
            # Create a ComponentConfig instance
            test_config = ComponentConfig(
                name="test-structure",
                schema_name="AWS::S3::Bucket",
                attributes={
                    "/domain/BucketName": "test-bucket",
                    "/domain/PublicReadPolicy": False
                }
            )
            
            # Test required fields
            assert_true(hasattr(test_config, 'name'), "Should have name field")
            assert_true(hasattr(test_config, 'schema_name'), "Should have schema_name field")
            assert_true(hasattr(test_config, 'attributes'), "Should have attributes field")
            
            # Test optional fields
            optional_fields = ['domain', 'secrets', 'resource_id', 'view_name', 'connections', 'subscriptions', 'managed_by']
            for field in optional_fields:
                assert_true(hasattr(test_config, field), f"Should have optional field {field}")
            
            # Test to_create_request method
            create_request = test_config.to_create_request()
            assert_contains(create_request, "name", "Create request should have name")
            assert_contains(create_request, "schemaName", "Create request should have schemaName")
            
            return {
                "success": True,
                "config_created": True,
                "required_fields_present": True,
                "optional_fields_present": len(optional_fields),
                "create_request_format": create_request
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def run_all_tests(self):
        """Run all component config system tests"""
        self.framework.start_suite("Component Config System Tests")
        
        # Test manager initialization
        self.framework.run_test(
            "Config Manager Initialization",
            "Component Config System",
            self.test_config_manager_initialization
        )
        
        # Test loading configurations
        self.framework.run_test(
            "Load Configurations",
            "Component Config System",
            self.test_load_configurations
        )
        
        # Test config validation
        self.framework.run_test(
            "Config Validation",
            "Component Config System",
            self.test_config_validation
        )
        
        # Test create request format
        self.framework.run_test(
            "Create Component Request Format",
            "Component Config System",
            self.test_create_component_request_format
        )
        
        # Test ComponentConfig structure
        self.framework.run_test(
            "ComponentConfig Structure",
            "Component Config System",
            self.test_component_config_structure
        )
        
        # Print results and save
        self.framework.print_summary()
        results_file = self.framework.save_results("component_config_system_test_results.json")
        print(f"📄 Results saved to: {results_file}")
        
        return self.framework.results


if __name__ == "__main__":
    tester = TestComponentConfigSystem()
    tester.run_all_tests()