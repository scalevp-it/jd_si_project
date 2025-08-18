"""
Comprehensive Test Runner for SI Component Management System

Runs all test suites and generates a consolidated report.
"""

import os
import sys
import json
from datetime import datetime
from tests.test_framework import TestFramework

# Import all test classes
from tests.test_si_session import TestSISession
from tests.test_schema_fetcher import TestSchemaFetcher
from tests.test_changeset_extractor import TestChangesetExtractor
from tests.test_component_config_system import TestComponentConfigSystem
from tests.test_component_generator import TestComponentGenerator


class ComprehensiveTestRunner:
    """Runs all test suites and consolidates results"""
    
    def __init__(self):
        self.results_dir = "tests/test_results"
        self.all_results = []
        self.start_time = None
        self.test_suites = [
            ("SI Session", TestSISession),
            ("Schema Fetcher", TestSchemaFetcher), 
            ("Changeset Extractor", TestChangesetExtractor),
            ("Component Config System", TestComponentConfigSystem),
            ("Component Generator", TestComponentGenerator)
        ]
        
        # Ensure results directory exists
        os.makedirs(self.results_dir, exist_ok=True)
    
    def check_prerequisites(self):
        """Check that required environment variables are set"""
        print("🔍 Checking Prerequisites")
        print("=" * 30)
        
        required_vars = ['SI_WORKSPACE_ID', 'SI_API_TOKEN']
        missing_vars = []
        
        for var in required_vars:
            value = os.getenv(var)
            if not value:
                missing_vars.append(var)
                print(f"❌ Missing: {var}")
            else:
                print(f"✅ Found: {var} ({'*' * (len(value) - 4) + value[-4:] if len(value) > 4 else '***'})")
        
        if missing_vars:
            print(f"\n⚠️  Missing required environment variables: {', '.join(missing_vars)}")
            print("Please set these variables before running tests.")
            return False
        
        print("✅ All prerequisites satisfied\n")
        return True
    
    def run_all_suites(self):
        """Run all test suites"""
        print("🚀 Starting Comprehensive Test Suite")
        print("=" * 60)
        self.start_time = datetime.now()
        print(f"⏰ Start time: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        suite_results = {}
        
        for suite_name, suite_class in self.test_suites:
            print(f"🧪 Running {suite_name} Tests...")
            print("-" * 40)
            
            try:
                # Create and run test suite
                tester = suite_class()
                results = tester.run_all_tests()
                
                # Store results
                suite_results[suite_name] = {
                    "results": results,
                    "total_tests": len(results),
                    "passed": sum(1 for r in results if r.status == "PASS"),
                    "failed": sum(1 for r in results if r.status == "FAIL"),
                    "errors": sum(1 for r in results if r.status == "ERROR"),
                    "skipped": sum(1 for r in results if r.status == "SKIP")
                }
                
                self.all_results.extend(results)
                
            except Exception as e:
                print(f"💥 Error running {suite_name} tests: {e}")
                suite_results[suite_name] = {
                    "error": str(e),
                    "results": [],
                    "total_tests": 0,
                    "passed": 0,
                    "failed": 0,
                    "errors": 1,
                    "skipped": 0
                }
            
            print("\n")
        
        return suite_results
    
    def generate_consolidated_report(self, suite_results):
        """Generate a comprehensive report of all test results"""
        end_time = datetime.now()
        total_duration = (end_time - self.start_time).total_seconds()
        
        # Calculate overall statistics
        total_tests = sum(suite["total_tests"] for suite in suite_results.values())
        total_passed = sum(suite["passed"] for suite in suite_results.values())
        total_failed = sum(suite["failed"] for suite in suite_results.values())
        total_errors = sum(suite["errors"] for suite in suite_results.values())
        total_skipped = sum(suite["skipped"] for suite in suite_results.values())
        
        # Create comprehensive report
        report = {
            "test_run_info": {
                "timestamp": end_time.isoformat(),
                "start_time": self.start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "total_duration": total_duration,
                "environment": {
                    "python_version": sys.version,
                    "working_directory": os.getcwd(),
                    "has_si_workspace_id": bool(os.getenv('SI_WORKSPACE_ID')),
                    "has_si_api_token": bool(os.getenv('SI_API_TOKEN'))
                }
            },
            "overall_summary": {
                "total_test_suites": len(self.test_suites),
                "total_tests": total_tests,
                "passed": total_passed,
                "failed": total_failed,
                "errors": total_errors,
                "skipped": total_skipped,
                "success_rate": (total_passed / total_tests * 100) if total_tests > 0 else 0
            },
            "suite_results": suite_results,
            "detailed_results": [
                {
                    "test_name": result.test_name,
                    "feature": result.feature,
                    "status": result.status,
                    "duration": result.duration,
                    "message": result.message,
                    "error_details": result.error_details,
                    "output_data": result.output_data
                }
                for result in self.all_results
            ]
        }
        
        # Save consolidated report
        timestamp = end_time.strftime("%Y%m%d_%H%M%S")
        report_file = os.path.join(self.results_dir, f"comprehensive_test_report_{timestamp}.json")
        
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        return report, report_file
    
    def print_final_summary(self, report):
        """Print a comprehensive summary of all test results"""
        print("📊 COMPREHENSIVE TEST RESULTS")
        print("=" * 60)
        
        overall = report["overall_summary"]
        print(f"🕒 Total Duration: {report['test_run_info']['total_duration']:.2f} seconds")
        print(f"📋 Total Test Suites: {overall['total_test_suites']}")
        print(f"🧪 Total Tests: {overall['total_tests']}")
        print(f"✅ Passed: {overall['passed']}")
        print(f"❌ Failed: {overall['failed']}")
        print(f"💥 Errors: {overall['errors']}")
        print(f"⏭️  Skipped: {overall['skipped']}")
        print(f"📈 Success Rate: {overall['success_rate']:.1f}%")
        
        print(f"\n🔍 Results by Test Suite:")
        print("-" * 40)
        
        for suite_name, suite_data in report["suite_results"].items():
            if "error" in suite_data:
                print(f"  💥 {suite_name}: ERROR - {suite_data['error']}")
            else:
                total = suite_data['total_tests']
                passed = suite_data['passed']
                success_rate = (passed / total * 100) if total > 0 else 0
                print(f"  📊 {suite_name}: {passed}/{total} ({success_rate:.1f}%)")
                
                # Show any failures or errors
                failed = suite_data['failed']
                errors = suite_data['errors']
                if failed > 0 or errors > 0:
                    issue_details = []
                    if failed > 0:
                        issue_details.append(f"{failed} failed")
                    if errors > 0:
                        issue_details.append(f"{errors} errors")
                    print(f"      ⚠️  Issues: {', '.join(issue_details)}")
        
        print(f"\n🎯 Feature Coverage Analysis:")
        print("-" * 30)
        
        # Analyze by feature
        feature_stats = {}
        for result in self.all_results:
            feature = result.feature
            if feature not in feature_stats:
                feature_stats[feature] = {"passed": 0, "failed": 0, "errors": 0, "skipped": 0, "total": 0}
            
            feature_stats[feature]["total"] += 1
            if result.status == "PASS":
                feature_stats[feature]["passed"] += 1
            elif result.status == "FAIL":
                feature_stats[feature]["failed"] += 1
            elif result.status == "ERROR":
                feature_stats[feature]["errors"] += 1
            elif result.status == "SKIP":
                feature_stats[feature]["skipped"] += 1
        
        for feature, stats in feature_stats.items():
            success_rate = (stats["passed"] / stats["total"] * 100) if stats["total"] > 0 else 0
            status_icon = "✅" if success_rate == 100 else "⚠️" if success_rate >= 80 else "❌"
            print(f"  {status_icon} {feature}: {stats['passed']}/{stats['total']} ({success_rate:.1f}%)")
        
        # Overall assessment
        print(f"\n🏆 OVERALL ASSESSMENT:")
        print("-" * 25)
        
        if overall["success_rate"] >= 95:
            print("🎉 EXCELLENT: All systems are functioning properly!")
        elif overall["success_rate"] >= 85:
            print("👍 GOOD: Most features working, minor issues detected")
        elif overall["success_rate"] >= 70:
            print("⚠️  NEEDS ATTENTION: Several issues need to be addressed")
        else:
            print("🚨 CRITICAL: Major issues detected, system may be unstable")
    
    def run_comprehensive_tests(self):
        """Run the complete test suite"""
        # Check prerequisites
        if not self.check_prerequisites():
            return False
        
        try:
            # Run all test suites
            suite_results = self.run_all_suites()
            
            # Generate consolidated report
            report, report_file = self.generate_consolidated_report(suite_results)
            
            # Print final summary
            self.print_final_summary(report)
            
            print(f"\n📄 Comprehensive report saved to: {report_file}")
            print(f"📁 Individual test results available in: {self.results_dir}/")
            
            return report["overall_summary"]["success_rate"] >= 80  # Return success if >= 80%
            
        except Exception as e:
            print(f"💥 Critical error during test execution: {e}")
            import traceback
            traceback.print_exc()
            return False


if __name__ == "__main__":
    runner = ComprehensiveTestRunner()
    success = runner.run_comprehensive_tests()
    
    if success:
        print("\n🎉 Test suite completed successfully!")
        exit(0)
    else:
        print("\n❌ Test suite completed with issues.")
        exit(1)