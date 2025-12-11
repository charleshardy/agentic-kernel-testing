#!/usr/bin/env python3
"""Deployment validation script for Agentic AI Testing System."""

import requests
import time
import sys
import argparse
import json
from typing import Dict, List, Optional, Tuple
from urllib.parse import urljoin


class DeploymentValidator:
    """Validates deployment health and functionality."""
    
    def __init__(self, base_url: str = "http://localhost", timeout: int = 30):
        self.base_url = base_url
        self.timeout = timeout
        self.services = {
            "api": 8000,
            "orchestrator": 8001,
            "execution": 8002,
            "analysis": 8003,
            "ai-generator": 8004,
            "dashboard": 3000
        }
        self.results: Dict[str, Dict] = {}
        
    def check_service_health(self, service: str, port: int) -> Tuple[bool, str, Dict]:
        """Check if a service is healthy."""
        if service == "dashboard":
            # Dashboard doesn't have a health endpoint, just check if it responds
            url = f"{self.base_url}:{port}/"
            try:
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    return True, "OK", {"status": "healthy"}
                else:
                    return False, f"HTTP {response.status_code}", {}
            except Exception as e:
                return False, str(e), {}
        else:
            # Other services have /health endpoints
            health_url = f"{self.base_url}:{port}/health"
            try:
                response = requests.get(health_url, timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    status = data.get("status", "unknown")
                    if status == "healthy":
                        return True, "OK", data
                    else:
                        return False, f"Status: {status}", data
                else:
                    return False, f"HTTP {response.status_code}", {}
            except requests.exceptions.ConnectionError:
                return False, "Connection refused", {}
            except requests.exceptions.Timeout:
                return False, "Timeout", {}
            except Exception as e:
                return False, str(e), {}
                
    def check_api_endpoints(self) -> Dict[str, bool]:
        """Check critical API endpoints."""
        api_url = f"{self.base_url}:8000"
        endpoints = {
            "/api/v1/health": "GET",
            "/api/v1/tests": "GET",
            "/api/v1/status": "GET",
            "/docs": "GET"
        }
        
        results = {}
        for endpoint, method in endpoints.items():
            url = urljoin(api_url, endpoint)
            try:
                if method == "GET":
                    response = requests.get(url, timeout=5)
                else:
                    response = requests.request(method, url, timeout=5)
                    
                results[endpoint] = response.status_code < 400
            except Exception:
                results[endpoint] = False
                
        return results
        
    def check_database_connectivity(self) -> Tuple[bool, str]:
        """Check database connectivity through API."""
        api_url = f"{self.base_url}:8000/api/v1/health"
        try:
            response = requests.get(api_url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                components = data.get("components", {})
                db_status = components.get("database", {}).get("status")
                if db_status == "healthy":
                    return True, "Connected"
                else:
                    return False, f"Database status: {db_status}"
            else:
                return False, f"API not responding: {response.status_code}"
        except Exception as e:
            return False, f"Error: {e}"
            
    def check_llm_connectivity(self) -> Tuple[bool, str]:
        """Check LLM API connectivity."""
        api_url = f"{self.base_url}:8004/health"
        try:
            response = requests.get(api_url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                components = data.get("components", {})
                llm_status = components.get("llm", {}).get("status")
                if llm_status == "healthy":
                    return True, "Connected"
                else:
                    return False, f"LLM status: {llm_status}"
            else:
                return False, f"AI Generator not responding: {response.status_code}"
        except Exception as e:
            return False, f"Error: {e}"
            
    def test_basic_workflow(self) -> Tuple[bool, str]:
        """Test a basic workflow end-to-end."""
        api_url = f"{self.base_url}:8000"
        
        try:
            # 1. Submit a test
            test_data = {
                "name": "Deployment Validation Test",
                "type": "unit",
                "subsystem": "core",
                "description": "Test to validate deployment"
            }
            
            response = requests.post(
                f"{api_url}/api/v1/tests",
                json=test_data,
                timeout=10
            )
            
            if response.status_code != 201:
                return False, f"Failed to submit test: {response.status_code}"
                
            test_id = response.json().get("id")
            if not test_id:
                return False, "No test ID returned"
                
            # 2. Check test status
            time.sleep(2)  # Give it a moment to process
            
            response = requests.get(
                f"{api_url}/api/v1/tests/{test_id}",
                timeout=5
            )
            
            if response.status_code != 200:
                return False, f"Failed to get test status: {response.status_code}"
                
            return True, f"Basic workflow successful (test ID: {test_id})"
            
        except Exception as e:
            return False, f"Workflow error: {e}"
            
    def wait_for_services(self, max_wait: int = 60) -> bool:
        """Wait for all services to become healthy."""
        print(f"Waiting up to {max_wait} seconds for services to start...")
        
        start_time = time.time()
        while time.time() - start_time < max_wait:
            all_healthy = True
            
            for service, port in self.services.items():
                healthy, _, _ = self.check_service_health(service, port)
                if not healthy:
                    all_healthy = False
                    break
                    
            if all_healthy:
                return True
                
            time.sleep(5)
            print(".", end="", flush=True)
            
        print()
        return False
        
    def run_validation(self, wait_for_services: bool = True) -> bool:
        """Run complete deployment validation."""
        print("🚀 Starting deployment validation...")
        print()
        
        # Wait for services if requested
        if wait_for_services:
            if not self.wait_for_services():
                print("❌ Services did not start within timeout period")
                return False
            print("✅ All services started successfully")
            print()
            
        # Check individual service health
        print("🔍 Checking service health...")
        all_services_healthy = True
        
        for service, port in self.services.items():
            healthy, message, data = self.check_service_health(service, port)
            status_icon = "✅" if healthy else "❌"
            print(f"  {status_icon} {service:12} ({port}): {message}")
            
            self.results[service] = {
                "healthy": healthy,
                "message": message,
                "data": data
            }
            
            if not healthy:
                all_services_healthy = False
                
        print()
        
        # Check API endpoints
        print("🔍 Checking API endpoints...")
        api_results = self.check_api_endpoints()
        all_endpoints_ok = True
        
        for endpoint, ok in api_results.items():
            status_icon = "✅" if ok else "❌"
            print(f"  {status_icon} {endpoint}")
            if not ok:
                all_endpoints_ok = False
                
        print()
        
        # Check database connectivity
        print("🔍 Checking database connectivity...")
        db_ok, db_message = self.check_database_connectivity()
        status_icon = "✅" if db_ok else "❌"
        print(f"  {status_icon} Database: {db_message}")
        print()
        
        # Check LLM connectivity
        print("🔍 Checking LLM connectivity...")
        llm_ok, llm_message = self.check_llm_connectivity()
        status_icon = "✅" if llm_ok else "❌"
        print(f"  {status_icon} LLM API: {llm_message}")
        print()
        
        # Test basic workflow
        print("🔍 Testing basic workflow...")
        workflow_ok, workflow_message = self.test_basic_workflow()
        status_icon = "✅" if workflow_ok else "❌"
        print(f"  {status_icon} Workflow: {workflow_message}")
        print()
        
        # Summary
        all_ok = (all_services_healthy and all_endpoints_ok and 
                 db_ok and llm_ok and workflow_ok)
        
        if all_ok:
            print("🎉 Deployment validation PASSED!")
            print()
            print("Your Agentic AI Testing System is ready to use:")
            print(f"  • Web Dashboard: {self.base_url}:3000")
            print(f"  • API Documentation: {self.base_url}:8000/docs")
            print(f"  • API Health: {self.base_url}:8000/api/v1/health")
        else:
            print("❌ Deployment validation FAILED!")
            print()
            print("Issues found:")
            if not all_services_healthy:
                print("  • Some services are not healthy")
            if not all_endpoints_ok:
                print("  • Some API endpoints are not responding")
            if not db_ok:
                print("  • Database connectivity issues")
            if not llm_ok:
                print("  • LLM API connectivity issues")
            if not workflow_ok:
                print("  • Basic workflow test failed")
                
        return all_ok
        
    def export_results(self, filename: str) -> None:
        """Export validation results to JSON file."""
        with open(filename, 'w') as f:
            json.dump(self.results, f, indent=2)
        print(f"Results exported to {filename}")


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Validate Agentic AI Testing System deployment")
    parser.add_argument("--base-url", default="http://localhost", 
                       help="Base URL for services (default: http://localhost)")
    parser.add_argument("--timeout", type=int, default=30,
                       help="Timeout for service startup (default: 30s)")
    parser.add_argument("--no-wait", action="store_true",
                       help="Don't wait for services to start")
    parser.add_argument("--export", help="Export results to JSON file")
    parser.add_argument("--quiet", action="store_true",
                       help="Only show final result")
    
    args = parser.parse_args()
    
    validator = DeploymentValidator(args.base_url, args.timeout)
    
    if args.quiet:
        # Redirect stdout to suppress output
        import io
        import contextlib
        
        f = io.StringIO()
        with contextlib.redirect_stdout(f):
            success = validator.run_validation(not args.no_wait)
    else:
        success = validator.run_validation(not args.no_wait)
    
    if args.export:
        validator.export_results(args.export)
        
    if args.quiet:
        if success:
            print("✅ PASSED")
        else:
            print("❌ FAILED")
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()