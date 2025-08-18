"""
Tests for Changeset Component Extractor

Tests the changeset extraction functionality including component extraction,
template transformation, and reference example generation.
"""

import os
import json
from tests.test_framework import TestFramework, assert_true, assert_not_none, assert_file_exists, assert_contains
from src.changeset_extractor import extract_changeset_components, ChangesetExtractor
from src.si_session import SISession


class TestChangesetExtractor:
    """Test suite for Changeset Extractor functionality"""
    
    def __init__(self):
        self.framework = TestFramework()
        self.test_output_dir = "tests/test_results/extracted_components"
        self.session = None
        
        # Ensure test output directory exists
        os.makedirs(self.test_output_dir, exist_ok=True)
    
    def setup_session(self):
        """Setup SI session for testing"""
        try:
            self.session = SISession.from_env()
            return True
        except Exception as e:
            return {"success": False, "error": f"Failed to create session: {e}"}
    
    def test_basic_extraction(self):
        """Test basic component extraction from changeset"""
        if not self.session:
            setup_result = self.setup_session()
            if not setup_result:
                return setup_result
        
        try:
            # Extract components from HEAD changeset
            result = extract_changeset_components(
                change_set_id="HEAD",
                output_dir=self.test_output_dir,
                quiet=True
            )
            
            assert_not_none(result, "Extraction result should not be None")
            assert_true(result["success"], "Extraction should succeed")
            assert_contains(result, "component_count", "Result should contain component count")
            assert_contains(result, "successful_extractions", "Result should contain successful extraction count")
            assert_contains(result, "files_created", "Result should contain list of created files")
            
            # Check that files were created
            files_created = result["files_created"]
            for filename in files_created:
                filepath = os.path.join(self.test_output_dir, filename)
                assert_file_exists(filepath, f"Extracted file should exist: {filename}")
            
            return {
                "success": True,
                "components_extracted": result["successful_extractions"],
                "files_created": len(files_created),
                "sample_files": files_created[:3]  # Show first 3 files
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def test_template_format_transformation(self):
        """Test that extracted components are in proper template format"""
        try:
            # First ensure we have extracted components
            result = extract_changeset_components(
                change_set_id="HEAD",
                output_dir=self.test_output_dir,
                quiet=True
            )
            
            if not result["success"] or not result["files_created"]:
                return {"success": False, "error": "No components extracted for testing"}
            
            # Check the format of the first extracted file
            first_file = result["files_created"][0]
            filepath = os.path.join(self.test_output_dir, first_file)
            
            with open(filepath, 'r') as f:
                component_data = json.load(f)
            
            # Check required top-level sections
            assert_contains(component_data, "_extraction_metadata", "Should have extraction metadata")
            assert_contains(component_data, "extracted_component", "Should have extracted component section")
            assert_contains(component_data, "_reference_examples", "Should have reference examples section")
            
            # Check extracted component format
            extracted_comp = component_data["extracted_component"]
            assert_contains(extracted_comp, "create_component_request", "Should have create component request")
            
            create_request = extracted_comp["create_component_request"]
            assert_contains(create_request, "schemaName", "Should have schema name")
            assert_contains(create_request, "name", "Should have component name")
            assert_contains(create_request, "attributes", "Should have attributes")
            
            # Check that attributes use proper path format
            attributes = create_request["attributes"]
            has_proper_paths = any(key.startswith('/domain/') or key.startswith('/secrets/') for key in attributes.keys())
            assert_true(has_proper_paths, "Attributes should use proper path format")
            
            return {
                "success": True,
                "file_tested": first_file,
                "schema_name": create_request["schemaName"],
                "attribute_count": len(attributes),
                "attribute_paths": list(attributes.keys())
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def test_reference_examples_generation(self):
        """Test that reference examples are properly generated"""
        try:
            # Get extraction results
            result = extract_changeset_components(
                change_set_id="HEAD",
                output_dir=self.test_output_dir,
                quiet=True
            )
            
            if not result["success"] or not result["files_created"]:
                return {"success": False, "error": "No components extracted for testing"}
            
            # Check reference examples in the first file
            first_file = result["files_created"][0]
            filepath = os.path.join(self.test_output_dir, first_file)
            
            with open(filepath, 'r') as f:
                component_data = json.load(f)
            
            ref_examples = component_data["_reference_examples"]
            assert_contains(ref_examples, "description", "Reference examples should have description")
            assert_contains(ref_examples, "component_name", "Reference examples should have component name")
            assert_contains(ref_examples, "schema_name", "Reference examples should have schema name")
            
            # Check for available outputs or common references
            has_outputs = "available_outputs" in ref_examples
            has_common_refs = "common_references" in ref_examples
            has_usage_examples = "usage_examples" in ref_examples
            
            assert_true(has_outputs or has_common_refs, "Should have either outputs or common references")
            
            result_data = {
                "success": True,
                "file_tested": first_file,
                "has_available_outputs": has_outputs,
                "has_common_references": has_common_refs,
                "has_usage_examples": has_usage_examples,
                "schema_name": ref_examples["schema_name"]
            }
            
            if has_outputs:
                outputs = ref_examples["available_outputs"]
                result_data["output_count"] = len(outputs)
                result_data["sample_output"] = outputs[0] if outputs else None
            
            return result_data
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def test_schema_specific_references(self):
        """Test that schema-specific reference patterns are generated"""
        try:
            # Extract and check for AWS-specific references
            result = extract_changeset_components(
                change_set_id="HEAD",
                output_dir=self.test_output_dir,
                quiet=True
            )
            
            if not result["success"] or not result["files_created"]:
                return {"success": False, "error": "No components extracted for testing"}
            
            # Look for AWS components and check their reference patterns
            aws_components = []
            credential_components = []
            
            for filename in result["files_created"]:
                filepath = os.path.join(self.test_output_dir, filename)
                with open(filepath, 'r') as f:
                    component_data = json.load(f)
                
                schema_name = component_data["_reference_examples"]["schema_name"]
                
                if schema_name.startswith("AWS::"):
                    aws_components.append({
                        "filename": filename,
                        "schema_name": schema_name,
                        "references": component_data["_reference_examples"]
                    })
                elif schema_name == "AWS Credential":
                    credential_components.append({
                        "filename": filename,
                        "schema_name": schema_name,
                        "references": component_data["_reference_examples"]
                    })
            
            return {
                "success": True,
                "aws_components_found": len(aws_components),
                "credential_components_found": len(credential_components),
                "aws_schemas": [comp["schema_name"] for comp in aws_components],
                "sample_aws_component": aws_components[0] if aws_components else None
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def test_extraction_summary(self):
        """Test that extraction summary is properly generated"""
        try:
            result = extract_changeset_components(
                change_set_id="HEAD",
                output_dir=self.test_output_dir,
                quiet=True
            )
            
            if not result["success"]:
                return {"success": False, "error": "Extraction failed"}
            
            # Check for summary file
            summary_file = os.path.join(self.test_output_dir, "extraction_summary_HEAD.json")
            assert_file_exists(summary_file, "Extraction summary file should exist")
            
            with open(summary_file, 'r') as f:
                summary_data = json.load(f)
            
            # Check summary structure
            required_fields = [
                "success", "changeset_id", "extracted_at", "component_count",
                "successful_extractions", "failed_extractions", "files_created",
                "extraction_details"
            ]
            
            for field in required_fields:
                assert_contains(summary_data, field, f"Summary should contain {field}")
            
            return {
                "success": True,
                "summary_file": "extraction_summary_HEAD.json",
                "components_in_summary": summary_data["component_count"],
                "successful_extractions": summary_data["successful_extractions"],
                "extraction_timestamp": summary_data["extracted_at"]
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def run_all_tests(self):
        """Run all changeset extractor tests"""
        self.framework.start_suite("Changeset Extractor Tests")
        
        # Test basic extraction
        self.framework.run_test(
            "Basic Component Extraction",
            "Changeset Extractor",
            self.test_basic_extraction
        )
        
        # Test template format
        self.framework.run_test(
            "Template Format Transformation",
            "Changeset Extractor",
            self.test_template_format_transformation
        )
        
        # Test reference examples
        self.framework.run_test(
            "Reference Examples Generation",
            "Changeset Extractor", 
            self.test_reference_examples_generation
        )
        
        # Test schema-specific references
        self.framework.run_test(
            "Schema-Specific References",
            "Changeset Extractor",
            self.test_schema_specific_references
        )
        
        # Test extraction summary
        self.framework.run_test(
            "Extraction Summary Generation",
            "Changeset Extractor",
            self.test_extraction_summary
        )
        
        # Print results and save
        self.framework.print_summary()
        results_file = self.framework.save_results("changeset_extractor_test_results.json")
        print(f"📄 Results saved to: {results_file}")
        
        return self.framework.results


if __name__ == "__main__":
    tester = TestChangesetExtractor()
    tester.run_all_tests()