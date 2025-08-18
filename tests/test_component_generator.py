"""
Tests for Component Generator

Tests the component generation functionality including minimal config generation,
real reference injection, and component config creation.
"""

import os
import json
from tests.test_framework import TestFramework, assert_true, assert_not_none, assert_file_exists, assert_contains
from src.component_generator import generate_component_config, ComponentGenerator
from src.si_session import SISession


class TestComponentGenerator:
    """Test suite for Component Generator functionality"""
    
    def __init__(self):
        self.framework = TestFramework()
        self.test_output_dir = "tests/test_results/generated_configs"
        self.session = None
        
        # Ensure test directory exists
        os.makedirs(self.test_output_dir, exist_ok=True)
    
    def setup_session(self):
        """Setup SI session for testing"""
        try:
            self.session = SISession.from_env()
            return True
        except Exception as e:
            return {"success": False, "error": f"Failed to create session: {e}"}
    
    def test_basic_component_generation(self):
        """Test basic component config generation"""
        if not self.session:
            setup_result = self.setup_session()
            if not setup_result:
                return setup_result
        
        try:
            # Generate a basic component config
            result = generate_component_config(
                schema_name="AWS::EC2::Instance",
                component_name="test-ec2-instance",
                change_set_id="HEAD",
                output_dir=self.test_output_dir,
                quiet=True
            )
            
            assert_not_none(result, "Generation result should not be None")
            assert_true(result["success"], "Generation should succeed")
            assert_contains(result, "filename", "Result should contain filename")
            assert_contains(result, "filepath", "Result should contain filepath")
            
            # Check that file was created
            assert_file_exists(result["filepath"], f"Generated file should exist: {result['filename']}")
            
            return {
                "success": True,
                "filename": result["filename"],
                "attributes_count": result["attributes_count"],
                "real_references_used": result["real_references_used"]
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def test_generated_config_structure(self):
        """Test that generated configs have proper structure"""
        try:
            # Generate config
            result = generate_component_config(
                schema_name="AWS::S3::Bucket",
                component_name="test-s3-bucket",
                change_set_id="HEAD",
                output_dir=self.test_output_dir,
                quiet=True
            )
            
            if not result["success"]:
                return {"success": False, "error": f"Generation failed: {result.get('error')}"}
            
            # Load and verify structure
            with open(result["filepath"], 'r') as f:
                config_data = json.load(f)
            
            # Check required top-level fields
            assert_contains(config_data, "name", "Config should have name")
            assert_contains(config_data, "schema_name", "Config should have schema_name")
            assert_contains(config_data, "attributes", "Config should have attributes")
            assert_contains(config_data, "_generation_metadata", "Config should have generation metadata")
            assert_contains(config_data, "_available_references", "Config should have available references")
            
            # Check metadata structure
            metadata = config_data["_generation_metadata"]
            assert_contains(metadata, "generated_from", "Metadata should have generated_from")
            assert_contains(metadata, "generated_at", "Metadata should have generated_at")
            assert_contains(metadata, "schema_name", "Metadata should have schema_name")
            assert_true(metadata["based_on_minimal_template"], "Should be based on minimal template")
            
            # Check that attributes use proper path format
            attributes = config_data["attributes"]
            has_proper_paths = any(key.startswith('/domain/') or key.startswith('/secrets/') for key in attributes.keys())
            assert_true(has_proper_paths, "Attributes should use proper path format")
            
            return {
                "success": True,
                "config_structure_valid": True,
                "attribute_count": len(attributes),
                "attribute_paths": list(attributes.keys()),
                "metadata_complete": True
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def test_real_reference_injection(self):
        """Test that real component references are properly injected"""
        if not self.session:
            return {"success": False, "error": "Session not initialized"}
        
        try:
            # Generate component that should have real references
            result = generate_component_config(
                schema_name="AWS::EC2::Instance",
                component_name="test-ec2-with-refs",
                change_set_id="HEAD",
                output_dir=self.test_output_dir,
                quiet=True
            )
            
            if not result["success"]:
                return {"success": False, "error": f"Generation failed: {result.get('error')}"}
            
            # Load and check for real references
            with open(result["filepath"], 'r') as f:
                config_data = json.load(f)
            
            attributes = config_data["attributes"]
            real_references = []
            
            # Check for $source references
            for attr_name, attr_value in attributes.items():
                if isinstance(attr_value, dict) and "$source" in attr_value:
                    real_references.append({
                        "attribute": attr_name,
                        "component": attr_value["$source"].get("component"),
                        "path": attr_value["$source"].get("path")
                    })
            
            return {
                "success": True,
                "real_references_found": len(real_references),
                "references": real_references,
                "has_aws_credential": any("/secrets/AWS Credential" in ref["attribute"] for ref in real_references),
                "has_region": any("Region" in ref["attribute"] for ref in real_references)
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def test_component_reference_loading(self):
        """Test loading of current component references"""
        if not self.session:
            return {"success": False, "error": "Session not initialized"}
        
        try:
            generator = ComponentGenerator(self.session)
            component_refs = generator._load_current_component_references()
            
            assert_not_none(component_refs, "Component references should not be None")
            assert_contains(component_refs, "aws_credentials", "Should have AWS credentials category")
            assert_contains(component_refs, "regions", "Should have regions category")
            assert_contains(component_refs, "vpcs", "Should have VPCs category")
            assert_contains(component_refs, "subnets", "Should have subnets category")
            assert_contains(component_refs, "security_groups", "Should have security groups category")
            assert_contains(component_refs, "other", "Should have other category")
            
            # Count available references
            total_refs = sum(len(refs) for refs in component_refs.values())
            
            return {
                "success": True,
                "total_references_loaded": total_refs,
                "aws_credentials": len(component_refs["aws_credentials"]),
                "regions": len(component_refs["regions"]),
                "vpcs": len(component_refs["vpcs"]),
                "subnets": len(component_refs["subnets"]),
                "security_groups": len(component_refs["security_groups"]),
                "other": len(component_refs["other"])
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def test_batch_generation(self):
        """Test batch generation of multiple configs"""
        if not self.session:
            return {"success": False, "error": "Session not initialized"}
        
        try:
            schemas = ["AWS::S3::Bucket", "AWS::EC2::SecurityGroup"]
            generated_configs = []
            
            for i, schema in enumerate(schemas):
                component_name = f"test-batch-{i+1}"
                result = generate_component_config(
                    schema_name=schema,
                    component_name=component_name,
                    change_set_id="HEAD",
                    output_dir=self.test_output_dir,
                    quiet=True
                )
                
                generated_configs.append({
                    "schema": schema,
                    "component_name": component_name,
                    "success": result["success"],
                    "filename": result.get("filename") if result["success"] else None,
                    "error": result.get("error") if not result["success"] else None
                })
            
            # Check results
            successful_configs = [config for config in generated_configs if config["success"]]
            
            return {
                "success": True,
                "total_schemas": len(schemas),
                "successful_generations": len(successful_configs),
                "failed_generations": len(schemas) - len(successful_configs),
                "generated_configs": generated_configs
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def test_schema_specific_references(self):
        """Test that schema-specific references are properly handled"""
        if not self.session:
            return {"success": False, "error": "Session not initialized"}
        
        try:
            # Test AWS EC2 instance which should get VPC, subnet references
            result = generate_component_config(
                schema_name="AWS::EC2::Instance",
                component_name="test-ec2-refs",
                change_set_id="HEAD",
                output_dir=self.test_output_dir,
                quiet=True
            )
            
            if not result["success"]:
                return {"success": False, "error": f"Generation failed: {result.get('error')}"}
            
            # Load and check for schema-specific references
            with open(result["filepath"], 'r') as f:
                config_data = json.load(f)
            
            attributes = config_data["attributes"]
            
            # Check for AWS EC2-specific references
            has_vpc_ref = any("VpcId" in attr_name for attr_name in attributes.keys())
            has_subnet_ref = any("SubnetId" in attr_name for attr_name in attributes.keys())
            has_sg_ref = any("SecurityGroup" in attr_name for attr_name in attributes.keys())
            
            # Count $source references
            source_refs = sum(
                1 for attr_value in attributes.values()
                if isinstance(attr_value, dict) and "$source" in attr_value
            )
            
            return {
                "success": True,
                "schema_name": "AWS::EC2::Instance",
                "has_vpc_reference": has_vpc_ref,
                "has_subnet_reference": has_subnet_ref,
                "has_security_group_reference": has_sg_ref,
                "total_source_references": source_refs,
                "sample_attributes": list(attributes.keys())[:5]
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def run_all_tests(self):
        """Run all component generator tests"""
        self.framework.start_suite("Component Generator Tests")
        
        # Test basic generation
        self.framework.run_test(
            "Basic Component Generation",
            "Component Generator",
            self.test_basic_component_generation
        )
        
        # Test config structure
        self.framework.run_test(
            "Generated Config Structure",
            "Component Generator",
            self.test_generated_config_structure
        )
        
        # Test real reference injection
        self.framework.run_test(
            "Real Reference Injection",
            "Component Generator",
            self.test_real_reference_injection
        )
        
        # Test component reference loading
        self.framework.run_test(
            "Component Reference Loading",
            "Component Generator",
            self.test_component_reference_loading
        )
        
        # Test batch generation
        self.framework.run_test(
            "Batch Generation",
            "Component Generator",
            self.test_batch_generation
        )
        
        # Test schema-specific references
        self.framework.run_test(
            "Schema-Specific References",
            "Component Generator",
            self.test_schema_specific_references
        )
        
        # Print results and save
        self.framework.print_summary()
        results_file = self.framework.save_results("component_generator_test_results.json")
        print(f"📄 Results saved to: {results_file}")
        
        return self.framework.results


if __name__ == "__main__":
    tester = TestComponentGenerator()
    tester.run_all_tests()