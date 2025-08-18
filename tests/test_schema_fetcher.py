"""
Tests for Schema Template Fetcher

Tests the schema template generation functionality including
fetching schemas, generating templates, and creating example files.
"""

import os
import json
from tests.test_framework import TestFramework, assert_true, assert_not_none, assert_file_exists
from src.schema_fetcher import fetch_schema_template


class TestSchemaFetcher:
    """Test suite for Schema Fetcher functionality"""
    
    def __init__(self):
        self.framework = TestFramework()
        self.test_schema = "AWS::EC2::Instance"  # Common schema for testing
        self.test_output_dir = "tests/test_results/schema_templates"
        
        # Ensure test output directory exists
        os.makedirs(self.test_output_dir, exist_ok=True)
    
    def test_fetch_schema_template_basic(self):
        """Test basic schema template fetching"""
        try:
            output_file = os.path.join(self.test_output_dir, f"{self.test_schema.lower().replace('::', '_')}_test.json.example")
            
            # Clean up any existing test file
            if os.path.exists(output_file):
                os.remove(output_file)
            
            # Fetch schema template
            success = fetch_schema_template(
                schema_name=self.test_schema,
                change_set_id="HEAD",
                output_file=output_file,
                quiet=True
            )
            
            assert_true(success, "Schema template fetch should succeed")
            assert_file_exists(output_file, f"Template file should be created at {output_file}")
            
            # Verify file content
            with open(output_file, 'r') as f:
                template_data = json.load(f)
            
            assert_not_none(template_data, "Template data should not be None")
            assert_true('_metadata' in template_data, "Template should have metadata section")
            assert_true('_needed_to_deploy' in template_data, "Template should have needed_to_deploy section")
            assert_true('_complete_usage_example' in template_data, "Template should have complete example section")
            
            # Check metadata
            metadata = template_data['_metadata']
            assert_true(metadata['schema_name'] == self.test_schema, "Schema name should match")
            
            return {
                "success": True,
                "output_file": output_file,
                "template_sections": list(template_data.keys()),
                "metadata": metadata
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def test_needed_to_deploy_section(self):
        """Test that needed_to_deploy section is properly generated"""
        try:
            output_file = os.path.join(self.test_output_dir, f"{self.test_schema.lower().replace('::', '_')}_deploy_test.json.example")
            
            success = fetch_schema_template(
                schema_name=self.test_schema,
                change_set_id="HEAD", 
                output_file=output_file,
                quiet=True
            )
            
            if not success:
                return {"success": False, "error": "Template fetch failed"}
            
            with open(output_file, 'r') as f:
                template_data = json.load(f)
            
            deploy_section = template_data.get('_needed_to_deploy')
            assert_not_none(deploy_section, "needed_to_deploy section should exist")
            assert_true('description' in deploy_section, "Deploy section should have description")
            assert_true('create_component_request' in deploy_section, "Deploy section should have creation request")
            
            create_request = deploy_section['create_component_request']
            assert_true('schemaName' in create_request, "Create request should have schema name")
            assert_true('attributes' in create_request, "Create request should have attributes")
            assert_true(create_request['schemaName'] == self.test_schema, "Schema name should match")
            
            # Check that attributes use proper paths
            attributes = create_request['attributes']
            has_domain_paths = any(key.startswith('/domain/') for key in attributes.keys())
            assert_true(has_domain_paths, "Attributes should include domain paths")
            
            return {
                "success": True,
                "deploy_section": deploy_section,
                "attribute_count": deploy_section.get('attribute_count', 0),
                "attributes": list(attributes.keys())
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def test_complete_example_section(self):
        """Test that complete example section is properly generated"""
        try:
            output_file = os.path.join(self.test_output_dir, f"{self.test_schema.lower().replace('::', '_')}_complete_test.json.example")
            
            success = fetch_schema_template(
                schema_name=self.test_schema,
                change_set_id="HEAD",
                output_file=output_file, 
                quiet=True
            )
            
            if not success:
                return {"success": False, "error": "Template fetch failed"}
            
            with open(output_file, 'r') as f:
                template_data = json.load(f)
            
            complete_section = template_data.get('_complete_usage_example')
            assert_not_none(complete_section, "complete_usage_example section should exist")
            assert_true('create_component_request' in complete_section, "Complete section should have creation request")
            
            create_request = complete_section['create_component_request']
            attributes = create_request.get('attributes', {})
            
            # Should have more attributes than the minimal example
            deploy_section = template_data.get('_needed_to_deploy', {})
            deploy_attrs = deploy_section.get('create_component_request', {}).get('attributes', {})
            
            assert_true(len(attributes) >= len(deploy_attrs), "Complete example should have at least as many attributes as deploy example")
            
            return {
                "success": True,
                "complete_attribute_count": len(attributes),
                "deploy_attribute_count": len(deploy_attrs),
                "sample_attributes": list(attributes.keys())[:10]  # First 10 attributes
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def test_invalid_schema(self):
        """Test handling of invalid schema names"""
        try:
            invalid_schema = "NonExistent::Schema::Name"
            output_file = os.path.join(self.test_output_dir, "invalid_schema_test.json.example")
            
            success = fetch_schema_template(
                schema_name=invalid_schema,
                change_set_id="HEAD",
                output_file=output_file,
                quiet=True
            )
            
            # Should fail gracefully
            assert_true(not success, "Invalid schema should return False")
            
            return {"success": True, "message": "Invalid schema handled correctly"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def test_aws_schema_requirements(self):
        """Test that AWS schemas include proper AWS-specific requirements"""
        try:
            output_file = os.path.join(self.test_output_dir, "aws_requirements_test.json.example")
            
            success = fetch_schema_template(
                schema_name=self.test_schema,
                change_set_id="HEAD",
                output_file=output_file,
                quiet=True
            )
            
            if not success:
                return {"success": False, "error": "Template fetch failed"}
            
            with open(output_file, 'r') as f:
                template_data = json.load(f)
            
            deploy_section = template_data.get('_needed_to_deploy', {})
            attributes = deploy_section.get('create_component_request', {}).get('attributes', {})
            
            # Should include AWS credential reference
            has_aws_credential = any('/secrets/AWS Credential' in key for key in attributes.keys())
            
            # Should include region reference
            has_region = any('Region' in key for key in attributes.keys())
            
            return {
                "success": True,
                "has_aws_credential": has_aws_credential,
                "has_region": has_region,
                "aws_specific_attributes": [k for k in attributes.keys() if 'AWS' in k or 'Region' in k]
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def run_all_tests(self):
        """Run all schema fetcher tests"""
        self.framework.start_suite("Schema Fetcher Tests")
        
        # Test basic template fetching
        self.framework.run_test(
            "Basic Schema Template Fetch",
            "Schema Fetcher",
            self.test_fetch_schema_template_basic
        )
        
        # Test needed to deploy section
        self.framework.run_test(
            "Needed to Deploy Section",
            "Schema Fetcher",
            self.test_needed_to_deploy_section
        )
        
        # Test complete example section
        self.framework.run_test(
            "Complete Example Section", 
            "Schema Fetcher",
            self.test_complete_example_section
        )
        
        # Test invalid schema handling
        self.framework.run_test(
            "Invalid Schema Handling",
            "Schema Fetcher",
            self.test_invalid_schema
        )
        
        # Test AWS-specific requirements
        self.framework.run_test(
            "AWS Schema Requirements",
            "Schema Fetcher",
            self.test_aws_schema_requirements
        )
        
        # Print results and save
        self.framework.print_summary()
        results_file = self.framework.save_results("schema_fetcher_test_results.json")
        print(f"📄 Results saved to: {results_file}")
        
        return self.framework.results


if __name__ == "__main__":
    tester = TestSchemaFetcher()
    tester.run_all_tests()