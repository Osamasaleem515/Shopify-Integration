#!/usr/bin/env python
"""
Docker Setup Verification Script
Run this script to verify that your Docker setup is working correctly.
"""

import requests
import subprocess
import sys
import time
import os

def run_command(command):
    """Run a shell command and return the result."""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def check_docker_installation():
    """Check if Docker and Docker Compose are installed."""
    print("🔍 Checking Docker Installation...")
    
    # Check Docker
    success, stdout, stderr = run_command("docker --version")
    if success:
        print(f"✅ Docker: {stdout.strip()}")
    else:
        print("❌ Docker not found or not running")
        return False
    
    # Check Docker Compose
    success, stdout, stderr = run_command("docker-compose --version")
    if success:
        print(f"✅ Docker Compose: {stdout.strip()}")
    else:
        print("❌ Docker Compose not found")
        return False
    
    return True

def check_containers_status():
    """Check if all containers are running."""
    print("\n🔍 Checking Container Status...")
    
    success, stdout, stderr = run_command("docker-compose ps")
    if success:
        print("✅ Container Status:")
        print(stdout)
        
        # Check if all services are running
        if "Up" in stdout and "Exit" not in stdout:
            print("✅ All containers are running")
            return True
        else:
            print("❌ Some containers are not running properly")
            return False
    else:
        print("❌ Failed to check container status")
        return False

def check_web_service():
    """Check if the web service is responding."""
    print("\n🔍 Checking Web Service...")
    
    try:
        # Wait a bit for the service to start
        time.sleep(5)
        
        response = requests.get("http://localhost:8000/admin/", timeout=10)
        if response.status_code == 200:
            print("✅ Web service is responding")
            return True
        else:
            print(f"❌ Web service returned status code: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to web service (port 8000)")
        return False
    except Exception as e:
        print(f"❌ Error checking web service: {e}")
        return False

def check_database():
    """Check if the database is accessible."""
    print("\n🔍 Checking Database...")
    
    success, stdout, stderr = run_command("docker-compose exec -T web python manage.py check --database default")
    if success:
        print("✅ Database connection is working")
        return True
    else:
        print("❌ Database connection failed")
        print(f"Error: {stderr}")
        return False

def check_redis():
    """Check if Redis is accessible."""
    print("\n🔍 Checking Redis...")
    
    success, stdout, stderr = run_command("docker-compose exec -T redis redis-cli ping")
    if success and "PONG" in stdout:
        print("✅ Redis is responding")
        return True
    else:
        print("❌ Redis is not responding")
        return False

def run_migrations():
    """Run database migrations."""
    print("\n🔍 Running Database Migrations...")
    
    success, stdout, stderr = run_command("docker-compose exec -T web python manage.py migrate")
    if success:
        print("✅ Migrations completed successfully")
        return True
    else:
        print("❌ Migrations failed")
        print(f"Error: {stderr}")
        return False

def create_test_data():
    """Create test data for verification."""
    print("\n🔍 Creating Test Data...")
    
    # Create a test product via management command
    success, stdout, stderr = run_command("docker-compose exec -T web python manage.py create_test_data --count 5")
    if success:
        print("✅ Test data created successfully")
        return True
    else:
        print("❌ Failed to create test data")
        print(f"Error: {stderr}")
        return False

def main():
    """Main verification function."""
    print("🚀 Docker Setup Verification")
    print("=" * 50)
    
    checks = [
        ("Docker Installation", check_docker_installation),
        ("Container Status", check_containers_status),
        ("Database Connection", check_database),
        ("Redis Connection", check_redis),
        ("Web Service", check_web_service),
        ("Database Migrations", run_migrations),
        ("Test Data Creation", create_test_data),
    ]
    
    results = []
    
    for check_name, check_func in checks:
        try:
            result = check_func()
            results.append((check_name, result))
        except Exception as e:
            print(f"❌ Error in {check_name}: {e}")
            results.append((check_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 VERIFICATION SUMMARY")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for check_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {check_name}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} checks passed")
    
    if passed == total:
        print("🎉 All checks passed! Your Docker setup is working correctly.")
        print("\n📝 Next Steps:")
        print("1. Access the admin interface: http://localhost:8000/admin/")
        print("2. Create a superuser: docker-compose exec web python manage.py createsuperuser")
        print("3. Test the API: http://localhost:8000/api/v1/products/")
    else:
        print("⚠️  Some checks failed. Please review the errors above.")
        print("\n🔧 Troubleshooting:")
        print("1. Check if all containers are running: docker-compose ps")
        print("2. View logs: docker-compose logs web")
        print("3. Restart services: docker-compose restart")

if __name__ == "__main__":
    main() 