"""
Test Framework for SI Component Management System

Provides base classes and utilities for testing SI features.
"""

import json
import os
import traceback
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict


@dataclass
class TestResult:
    """Individual test result"""
    test_name: str
    feature: str
    status: str  # "PASS", "FAIL", "SKIP", "ERROR"
    duration: float
    message: str = ""
    error_details: Optional[str] = None
    output_data: Optional[Dict[str, Any]] = None


@dataclass
class TestSuiteResult:
    """Complete test suite results"""
    suite_name: str
    start_time: str
    end_time: str
    total_duration: float
    total_tests: int
    passed: int
    failed: int
    errors: int
    skipped: int
    results: List[TestResult]


class TestFramework:
    """Base framework for SI component tests"""
    
    def __init__(self, results_dir: str = "tests/test_results"):
        self.results_dir = results_dir
        self.results: List[TestResult] = []
        self.start_time = None
        self.suite_name = "SI_Component_Tests"
        
        # Ensure results directory exists
        os.makedirs(self.results_dir, exist_ok=True)
    
    def run_test(self, test_name: str, feature: str, test_func, *args, **kwargs) -> TestResult:
        """Run a single test and capture results"""
        print(f"🧪 Running {test_name}...")
        
        start_time = datetime.now()
        
        try:
            result = test_func(*args, **kwargs)
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            if result is True:
                test_result = TestResult(
                    test_name=test_name,
                    feature=feature,
                    status="PASS",
                    duration=duration,
                    message="Test passed successfully"
                )
                print(f"   ✅ PASS ({duration:.2f}s)")
                
            elif isinstance(result, dict) and result.get("success", False):
                test_result = TestResult(
                    test_name=test_name,
                    feature=feature,
                    status="PASS",
                    duration=duration,
                    message=result.get("message", "Test passed successfully"),
                    output_data=result
                )
                print(f"   ✅ PASS ({duration:.2f}s)")
                
            else:
                test_result = TestResult(
                    test_name=test_name,
                    feature=feature,
                    status="FAIL",
                    duration=duration,
                    message=str(result) if result else "Test returned False/None",
                    output_data=result if isinstance(result, dict) else None
                )
                print(f"   ❌ FAIL ({duration:.2f}s): {test_result.message}")
                
        except Exception as e:
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            test_result = TestResult(
                test_name=test_name,
                feature=feature,
                status="ERROR",
                duration=duration,
                message=str(e),
                error_details=traceback.format_exc()
            )
            print(f"   💥 ERROR ({duration:.2f}s): {e}")
        
        self.results.append(test_result)
        return test_result
    
    def save_results(self, filename: Optional[str] = None) -> str:
        """Save test results to JSON file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"test_results_{timestamp}.json"
        
        filepath = os.path.join(self.results_dir, filename)
        
        # Calculate summary statistics
        total_tests = len(self.results)
        passed = sum(1 for r in self.results if r.status == "PASS")
        failed = sum(1 for r in self.results if r.status == "FAIL")
        errors = sum(1 for r in self.results if r.status == "ERROR")
        skipped = sum(1 for r in self.results if r.status == "SKIP")
        
        total_duration = sum(r.duration for r in self.results)
        
        suite_result = TestSuiteResult(
            suite_name=self.suite_name,
            start_time=self.start_time.isoformat() if self.start_time else "",
            end_time=datetime.now().isoformat(),
            total_duration=total_duration,
            total_tests=total_tests,
            passed=passed,
            failed=failed,
            errors=errors,
            skipped=skipped,
            results=self.results
        )
        
        with open(filepath, 'w') as f:
            json.dump(asdict(suite_result), f, indent=2, default=str)
        
        return filepath
    
    def print_summary(self):
        """Print test summary to console"""
        total_tests = len(self.results)
        passed = sum(1 for r in self.results if r.status == "PASS")
        failed = sum(1 for r in self.results if r.status == "FAIL")
        errors = sum(1 for r in self.results if r.status == "ERROR")
        skipped = sum(1 for r in self.results if r.status == "SKIP")
        
        print(f"\n📊 Test Suite Summary")
        print(f"=" * 50)
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"💥 Errors: {errors}")
        print(f"⏭️  Skipped: {skipped}")
        
        if total_tests > 0:
            success_rate = (passed / total_tests) * 100
            print(f"📈 Success Rate: {success_rate:.1f}%")
        
        print(f"\n🔍 Results by Feature:")
        features = {}
        for result in self.results:
            feature = result.feature
            if feature not in features:
                features[feature] = {"passed": 0, "failed": 0, "errors": 0, "skipped": 0}
            
            if result.status == "PASS":
                features[feature]["passed"] += 1
            elif result.status == "FAIL":
                features[feature]["failed"] += 1
            elif result.status == "ERROR":
                features[feature]["errors"] += 1
            elif result.status == "SKIP":
                features[feature]["skipped"] += 1
        
        for feature, stats in features.items():
            total_feature = sum(stats.values())
            feature_success = (stats["passed"] / total_feature) * 100 if total_feature > 0 else 0
            print(f"  {feature}: {stats['passed']}/{total_feature} ({feature_success:.1f}%)")
    
    def start_suite(self, suite_name: str = "SI_Component_Tests"):
        """Start test suite execution"""
        self.suite_name = suite_name
        self.start_time = datetime.now()
        print(f"🚀 Starting {suite_name}")
        print(f"⏰ Start time: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"=" * 60)


def assert_equals(actual, expected, message=""):
    """Simple assertion helper"""
    if actual != expected:
        raise AssertionError(f"{message}. Expected: {expected}, Got: {actual}")


def assert_true(condition, message=""):
    """Assert that condition is true"""
    if not condition:
        raise AssertionError(f"{message}. Expected: True, Got: {condition}")


def assert_not_none(value, message=""):
    """Assert that value is not None"""
    if value is None:
        raise AssertionError(f"{message}. Expected: not None, Got: None")


def assert_contains(container, item, message=""):
    """Assert that container contains item"""
    if item not in container:
        raise AssertionError(f"{message}. Expected '{item}' to be in {type(container).__name__}")


def assert_file_exists(filepath, message=""):
    """Assert that file exists"""
    if not os.path.exists(filepath):
        raise AssertionError(f"{message}. File not found: {filepath}")