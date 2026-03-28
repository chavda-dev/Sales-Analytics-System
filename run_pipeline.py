"""
run_pipeline.py — One-click full pipeline runner
Executes all stages in sequence: Ingestion → Cleaning →
Transformation → DB Load → Analytics → Visualization
"""

import sys
import time
import traceback

def run_stage(name: str, module_path: str):
    import importlib.util
    print(f"\n{'='*60}")
    print(f"  STAGE: {name}")
    print(f"{'='*60}")
    start = time.time()
    try:
        spec = importlib.util.spec_from_file_location("module", module_path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        mod.main()
        elapsed = time.time() - start
        print(f"\n  ✅ {name} completed in {elapsed:.1f}s")
        return True
    except Exception as e:
        print(f"\n  ❌ {name} FAILED: {e}")
        traceback.print_exc()
        return False


def main():
    import os
    base = os.path.dirname(os.path.abspath(__file__))
    scripts = os.path.join(base, "scripts")

    stages = [
        ("1. Data Ingestion",       os.path.join(scripts, "ingestion.py")),
        ("2. Data Cleaning",        os.path.join(scripts, "cleaning.py")),
        ("3. Transformation",       os.path.join(scripts, "transformation.py")),
        ("4. Database Loading",     os.path.join(scripts, "db_loader.py")),
        ("5. Analytics Engine",     os.path.join(scripts, "analytics.py")),
        ("6. Visualization Charts", os.path.join(scripts, "visualization.py")),
    ]

    print("\n" + "="*60)
    print("  SALES ANALYTICS SYSTEM — FULL PIPELINE")
    print("="*60)
    total_start = time.time()

    results = []
    for name, path in stages:
        success = run_stage(name, path)
        results.append((name, success))
        if not success:
            print(f"\n⚠️  Pipeline stopped at: {name}")
            sys.exit(1)

    total_elapsed = time.time() - total_start
    print("\n" + "="*60)
    print("  PIPELINE SUMMARY")
    print("="*60)
    for name, success in results:
        status = "✅" if success else "❌"
        print(f"  {status} {name}")
    print(f"\n  Total time: {total_elapsed:.1f}s")
    print("\n  🚀 All stages complete! Launch the dashboard:")
    print("     streamlit run app/dashboard.py")
    print("     python app/api.py  (bonus API)")
    print("="*60)


if __name__ == "__main__":
    main()
