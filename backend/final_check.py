"""
Final verification before submission
"""
import json
import os
import sys
from pathlib import Path

def check_required_files():
    """Check all required files are present"""
    print("\n" + "="*60)
    print("CHECKING REQUIRED FILES")
    print("="*60)
    
    required_files = [
        "run.sh",
        "requirements.txt",
        "README.md",
        "design_notes.md",
        "capabilities.json"
    ]
    
    missing = []
    for file in required_files:
        if os.path.exists(file):
            print(f"✅ {file}")
        else:
            print(f"❌ {file} - MISSING")
            missing.append(file)
    
    return len(missing) == 0

def check_capabilities_json():
    """Verify capabilities.json is properly filled"""
    print("\n" + "="*60)
    print("CHECKING CAPABILITIES.JSON")
    print("="*60)
    
    try:
        with open('capabilities.json', 'r') as f:
            capabilities = json.load(f)
        
        print(f"Found {len(capabilities)} capabilities")
        
        # Check key capabilities
        key_capabilities = [
            "static_scraping",
            "js_rendering",
            "click_tabs",
            "load_more_clicks",
            "pagination_links",
            "noise_filtering"
        ]
        
        for cap in key_capabilities:
            if cap in capabilities and capabilities[cap]:
                print(f"✅ {cap}: True")
            else:
                print(f"❌ {cap}: Missing or False")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to read capabilities.json: {e}")
        return False

def check_structure():
    """Check project structure"""
    print("\n" + "="*60)
    print("CHECKING PROJECT STRUCTURE")
    print("="*60)
    
    required_dirs = [
        "backend",
        "backend/app",
        "backend/app/models",
        "backend/app/scraper",
        "backend/app/utils",
        "frontend",
        "frontend/src",
        "frontend/src/components"
    ]
    
    all_good = True
    for dir_path in required_dirs:
        if os.path.isdir(dir_path):
            print(f"✅ {dir_path}/")
        else:
            print(f"❌ {dir_path}/ - MISSING")
            all_good = False
    
    return all_good

def check_run_script():
    """Check run.sh is executable and correct"""
    print("\n" + "="*60)
    print("CHECKING RUN.SH")
    print("="*60)
    
    if not os.path.exists("run.sh"):
        print("❌ run.sh not found")
        return False
    
    try:
        with open("run.sh", "r") as f:
            content = f.read()
        
        # Check for key components
        checks = [
            ("virtual environment", "venv" in content or "virtualenv" in content),
            ("install dependencies", "pip install" in content or "requirements.txt" in content),
            ("start server", "uvicorn" in content or "gunicorn" in content or "flask" in content),
            ("port 8000", ":8000" in content or "8000" in content)
        ]
        
        all_good = True
        for check_name, check_result in checks:
            if check_result:
                print(f"✅ {check_name}")
            else:
                print(f"⚠️  {check_name} - Not found")
                all_good = False
        
        return all_good
        
    except Exception as e:
        print(f"❌ Failed to read run.sh: {e}")
        return False

def main():
    """Run all checks"""
    print("\n" + "="*60)
    print("LYFTR AI ASSIGNMENT - FINAL SUBMISSION CHECK")
    print("="*60)
    
    checks = [
        ("Required Files", check_required_files),
        ("Capabilities JSON", check_capabilities_json),
        ("Project Structure", check_structure),
        ("Run Script", check_run_script)
    ]
    
    results = []
    for check_name, check_func in checks:
        print(f"\n{check_name}:")
        result = check_func()
        results.append(result)
    
    print("\n" + "="*60)
    print("FINAL VERIFICATION SUMMARY")
    print("="*60)
    
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print("✅ ALL CHECKS PASSED!")
        print("\n🎉 YOUR PROJECT IS READY FOR SUBMISSION!")
        print("\nNext steps:")
        print("1. Commit all changes to git")
        print("2. Push to your GitHub repository")
        print("3. Email careers@lyftrai with subject: Full-Stack Assignment - [Your Name]")
        print("4. Include your repository link and the three primary test URLs")
    else:
        print(f"⚠️  {passed}/{total} checks passed")
        print("\nPlease fix the issues above before submission.")
    
    return passed == total

if __name__ == "__main__":
    # Change to project root directory
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    
    success = main()
    sys.exit(0 if success else 1)