"""
Run evaluation test from correct location
"""
import subprocess
import sys
import os

def run_evaluation():
    print("="*60)
    print("RUNNING FULL EVALUATION TEST")
    print("="*60)
    
    # Check where evaluation_test.py is located
    possible_paths = [
        "evaluation_test.py",
        "backend/evaluation_test.py",
        "./backend/evaluation_test.py"
    ]
    
    found_path = None
    for path in possible_paths:
        if os.path.exists(path):
            found_path = path
            print(f"Found evaluation test at: {found_path}")
            break
    
    if not found_path:
        print("❌ evaluation_test.py not found in common locations!")
        print("\nSearching for file...")
        result = subprocess.run(
            ["find", ".", "-name", "evaluation_test.py", "-type", "f"],
            capture_output=True,
            text=True
        )
        if result.stdout:
            print(f"Found at: {result.stdout}")
            found_path = result.stdout.strip()
        else:
            print("Could not find evaluation_test.py. Please check the file location.")
            return
    
    # Run the evaluation
    print(f"\nRunning evaluation test: python {found_path}")
    print("-"*60)
    
    try:
        result = subprocess.run(
            [sys.executable, found_path],
            capture_output=False,
            text=True
        )
        
        if result.returncode == 0:
            print("\n✅ Evaluation completed successfully!")
        else:
            print(f"\n❌ Evaluation failed with return code: {result.returncode}")
            
    except Exception as e:
        print(f"❌ Error running evaluation: {e}")
        print("\nTrying alternative method...")
        
        # Try to run it directly
        import asyncio
        try:
            # Import and run if it's a module
            sys.path.insert(0, os.path.dirname(os.path.abspath(found_path)))
            import evaluation_test as eval_module
            asyncio.run(eval_module.main())
        except Exception as import_error:
            print(f"Could not import module: {import_error}")
            print("\nPlease run manually:")
            print(f"  cd {os.path.dirname(found_path) or '.'}")
            print(f"  python {os.path.basename(found_path)}")

if __name__ == "__main__":
    print("\nChecking services...")
    print("Backend should be running at: http://localhost:8000")
    print("Frontend should be running at: http://localhost:5173")
    print("\nMake sure both are running before continuing!")
    
    input("\nPress Enter to continue (or Ctrl+C to cancel)...")
    
    run_evaluation()