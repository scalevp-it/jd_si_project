"""
Tests for SI Session Management

Tests the core SI API session functionality including authentication,
changeset operations, and component retrieval.
"""

import os
from tests.test_framework import TestFramework, assert_true, assert_not_none, assert_contains
from src.si_session import SISession


class TestSISession:
    """Test suite for SI Session functionality"""
    
    def __init__(self):
        self.framework = TestFramework()
        self.session = None
    
    def test_environment_variables(self):
        """Test that required environment variables are present"""
        required_vars = ['SI_WORKSPACE_ID', 'SI_API_TOKEN']
        
        for var in required_vars:
            value = os.getenv(var)
            assert_not_none(value, f"Environment variable {var} must be set")
            assert_true(len(value) > 10, f"Environment variable {var} appears too short")
        
        return True
    
    def test_session_creation(self):
        """Test SI session creation from environment"""
        try:
            self.session = SISession.from_env()
            assert_not_none(self.session, "Session should not be None")
            assert_not_none(self.session.workspace_id, "Workspace ID should be set")
            assert_not_none(self.session.api_client, "API client should be initialized")
            return True
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def test_get_change_sets(self):
        """Test retrieving change sets"""
        if not self.session:
            return {"success": False, "error": "Session not initialized"}
        
        try:
            change_sets = self.session.get_change_sets()
            assert_not_none(change_sets, "Change sets should not be None")
            assert_true(isinstance(change_sets, list), "Change sets should be a list")
            
            if len(change_sets) > 0:
                cs = change_sets[0]
                assert_contains(cs, 'id', "Change set should have an ID")
                assert_contains(cs, 'name', "Change set should have a name")
                assert_contains(cs, 'status', "Change set should have a status")
            
            return {
                "success": True, 
                "change_sets_found": len(change_sets),
                "sample_changeset": change_sets[0] if change_sets else None
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def test_get_components(self):
        """Test retrieving components from changeset"""
        if not self.session:
            return {"success": False, "error": "Session not initialized"}
        
        try:
            # Try to get components from HEAD changeset
            components = self.session.get_components("HEAD")
            assert_not_none(components, "Components should not be None")
            assert_true(isinstance(components, list), "Components should be a list")
            
            result = {
                "success": True,
                "components_found": len(components)
            }
            
            if len(components) > 0:
                comp = components[0]
                assert_contains(comp, 'id', "Component should have an ID")
                assert_contains(comp, 'display_name', "Component should have a display name")
                assert_contains(comp, 'schema_name', "Component should have a schema name")
                result["sample_component"] = comp
            
            return result
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def test_get_schemas(self):
        """Test retrieving schemas"""
        if not self.session:
            return {"success": False, "error": "Session not initialized"}
        
        try:
            schemas = self.session.get_schemas("HEAD")
            assert_not_none(schemas, "Schemas should not be None")
            assert_true(isinstance(schemas, list), "Schemas should be a list")
            
            result = {
                "success": True,
                "schemas_found": len(schemas)
            }
            
            if len(schemas) > 0:
                schema = schemas[0]
                result["sample_schema"] = schema
                # Check for common AWS schemas
                aws_schemas = [s for s in schemas if s.get('name', '').startswith('AWS::')]
                result["aws_schemas_found"] = len(aws_schemas)
            
            return result
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def run_all_tests(self):
        """Run all SI session tests"""
        self.framework.start_suite("SI Session Tests")
        
        # Test environment setup
        self.framework.run_test(
            "Environment Variables Check",
            "SI Session",
            self.test_environment_variables
        )
        
        # Test session creation
        self.framework.run_test(
            "Session Creation",
            "SI Session", 
            self.test_session_creation
        )
        
        # Test change sets
        self.framework.run_test(
            "Get Change Sets",
            "SI Session",
            self.test_get_change_sets
        )
        
        # Test components
        self.framework.run_test(
            "Get Components",
            "SI Session",
            self.test_get_components
        )
        
        # Test schemas
        self.framework.run_test(
            "Get Schemas", 
            "SI Session",
            self.test_get_schemas
        )
        
        # Print results and save
        self.framework.print_summary()
        results_file = self.framework.save_results("si_session_test_results.json")
        print(f"📄 Results saved to: {results_file}")
        
        return self.framework.results


if __name__ == "__main__":
    tester = TestSISession()
    tester.run_all_tests()