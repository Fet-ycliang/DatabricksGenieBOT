"""
環境一致性測試腳本
測試 venv 和 uv 環境是否一致
"""
import sys
import importlib.metadata
import json

def test_critical_imports():
    """測試關鍵套件能否正常導入"""
    critical_packages = [
        'fastapi',
        'uvicorn',
        'pandas',
        'requests',
        'botbuilder.core',
        'azure.identity',
        'databricks.sdk',
        'matplotlib',
        'seaborn',
    ]
    
    results = {}
    for package in critical_packages:
        try:
            __import__(package.replace('.', '/').split('/')[0])
            results[package] = "✓ OK"
        except ImportError as e:
            results[package] = f"✗ FAILED: {e}"
    
    return results

def test_package_versions():
    """檢查關鍵套件版本"""
    critical_packages = [
        'fastapi',
        'uvicorn',
        'pandas',
        'botbuilder-core',
    ]
    
    versions = {}
    for package in critical_packages:
        try:
            versions[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            versions[package] = "NOT INSTALLED"
    
    return versions

def test_app_startup():
    """測試應用程式能否正常導入"""
    try:
        from app.main import app
        from app.core.config import DefaultConfig
        return "✓ 應用程式模組載入成功"
    except Exception as e:
        return f"✗ 應用程式模組載入失敗: {e}"

if __name__ == "__main__":
    print("=" * 60)
    print(f"Python 版本: {sys.version}")
    print(f"Python 路徑: {sys.executable}")
    print("=" * 60)
    
    print("\n[1] 測試關鍵套件導入:")
    import_results = test_critical_imports()
    for package, result in import_results.items():
        print(f"  {package:30s} {result}")
    
    print("\n[2] 測試套件版本:")
    versions = test_package_versions()
    for package, version in versions.items():
        print(f"  {package:30s} {version}")
    
    print("\n[3] 測試應用程式啟動:")
    app_result = test_app_startup()
    print(f"  {app_result}")
    
    # 檢查是否所有測試通過
    all_passed = all("✓" in str(v) for v in import_results.values())
    all_passed = all_passed and ("✓" in app_result)
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✓ 所有測試通過！環境設置正確")
        sys.exit(0)
    else:
        print("✗ 部分測試失敗，請檢查環境配置")
        sys.exit(1)
