#!/usr/bin/env python
"""
環境診斷和自動修復腳本
檢查並修復常見的依賴問題（Chrome, 權限等）
"""

import subprocess
import sys
import os
import platform
from pathlib import Path

class Diagnostics:
    """環境診斷工具"""
    
    def __init__(self):
        self.system = platform.system()
        self.issues = []
        self.fixes = []
    
    def check_python_version(self):
        """檢查 Python 版本"""
        print("\n📌 檢查 Python 版本...")
        version = sys.version_info
        print(f"   當前版本: {version.major}.{version.minor}.{version.micro}")
        
        if version.major < 3 or (version.major == 3 and version.minor < 11):
            self.issues.append("Python 版本過低（需要 3.11+）")
            return False
        
        print("   ✅ Python 版本正確")
        return True
    
    def check_venv(self):
        """檢查虛擬環境"""
        print("\n📌 檢查虛擬環境...")
        
        in_venv = hasattr(sys, 'real_prefix') or (
            hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix
        )
        
        if not in_venv:
            print("   ⚠️  未在虛擬環境中")
            self.issues.append("未激活虛擬環境")
            self.fixes.append({
                'issue': '未激活虛擬環境',
                'fix': 'source .venv/bin/activate  # Linux/Mac\n或\n.\\.venv\\Scripts\\Activate.ps1  # Windows'
            })
            return False
        
        print("   ✅ 虛擬環境已激活")
        return True
    
    def check_requirements(self):
        """檢查必要的包"""
        print("\n📌 檢查必要的包...")
        
        required_packages = {
            'aiohttp': '>=3.8',
            'botbuilder-core': '>=4.17',
            'matplotlib': '>=3.7.0',
            'seaborn': '>=0.12.0',
        }
        
        missing = []
        
        for package, version in required_packages.items():
            try:
                __import__(package.replace('-', '_'))
                print(f"   ✅ {package} 已安裝")
            except ImportError:
                print(f"   ❌ {package} 未安裝")
                missing.append(f"{package}{version}")
        
        if missing:
            self.issues.append(f"缺少包: {', '.join(missing)}")
            self.fixes.append({
                'issue': '缺少必要的包',
                'fix': f"uv sync"
            })
            return False
        
        return True
    
    def check_chrome(self):
        """檢查 Chrome/Chromium"""
        print("\n📌 檢查 Chrome/Chromium...")
        
        chrome_paths = {
            'chromium-browser': 'Linux (Chromium)',
            'chromium': 'Linux (Chromium)',
            'google-chrome': 'Linux (Google Chrome)',
            '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome': 'macOS',
            'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe': 'Windows',
        }
        
        found = False
        for path, system in chrome_paths.items():
            try:
                result = subprocess.run(
                    [path, '--version'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    print(f"   ✅ Chrome 已找到: {system}")
                    print(f"      {result.stdout.strip()}")
                    found = True
                    break
            except (FileNotFoundError, OSError, subprocess.TimeoutExpired):
                continue
        
        if not found:
            print("   ❌ Chrome/Chromium 未找到")
            self.issues.append("缺少 Chrome/Chromium")
            
            if self.system == 'Windows':
                fix_cmd = 'choco install googlechrome'
            elif self.system == 'Darwin':  # macOS
                fix_cmd = 'brew install --cask google-chrome'
            else:  # Linux
                fix_cmd = 'apt-get update && apt-get install -y chromium-browser'
            
            self.fixes.append({
                'issue': '缺少 Chrome',
                'fix': f'{fix_cmd}'
            })
            return False
        
        print("   ✅ Chrome 檢查通過")
        return True
    
    def check_kaleido(self):
        """檢查 Kaleido 功能"""
        print("\n📌 檢查 Kaleido 功能...")
        
        try:
            import kaleido
            print(f"   ✅ Kaleido {kaleido.__version__} 已安裝")
            
            # 測試圖表生成
            try:
                import plotly.graph_objects as go
                fig = go.Figure(data=go.Bar(x=['test'], y=[1]))
                
                # 嘗試導出 (不保存)
                from io import BytesIO
                img_data = fig.to_image(format='png')
                
                print("   ✅ Kaleido 可正常生成圖表")
                return True
            except Exception as e:
                print(f"   ❌ Kaleido 無法生成圖表: {e}")
                self.issues.append(f"Kaleido 圖表生成失敗: {e}")
                self.fixes.append({
                    'issue': 'Kaleido 圖表生成失敗',
                    'fix': '請確保 Chrome 已正確安裝'
                })
                return False
        
        except ImportError:
            print("   ❌ Kaleido 未安裝")
            self.issues.append("Kaleido 未安裝")
            self.fixes.append({
                'issue': 'Kaleido 未安裝',
                'fix': 'pip install kaleido'
            })
            return False
    
    def check_environment_variables(self):
        """檢查環境變數"""
        print("\n📌 檢查環境變數...")
        
        required_vars = {
            'DATABRICKS_TOKEN': '必需 (Databricks API)',
            'APP_ID': '生產必需 (Azure Bot)',
            'APP_PASSWORD': '生產必需 (Azure Bot)',
        }
        
        missing = []
        
        for var, desc in required_vars.items():
            if os.getenv(var):
                print(f"   ✅ {var} 已設定")
            else:
                if 'APP_' in var:
                    print(f"   ⚠️  {var} 未設定 ({desc})")
                else:
                    print(f"   ❌ {var} 未設定 ({desc})")
                    missing.append(var)
        
        if missing:
            self.issues.append(f"缺少環境變數: {', '.join(missing)}")
            return False
        
        return True
    
    def run_all_checks(self):
        """運行所有檢查"""
        print("="*60)
        print("🔍 Databricks Genie Bot 環境診斷")
        print("="*60)
        
        checks = [
            self.check_python_version,
            self.check_venv,
            self.check_environment_variables,
            self.check_environment_variables,
            self.check_requirements,
        ]
        
        results = []
        for check in checks:
            try:
                results.append(check())
            except Exception as e:
                print(f"   ❌ 檢查失敗: {e}")
                results.append(False)
        
        # 打印摘要
        print("\n" + "="*60)
        print("📊 診斷摘要")
        print("="*60)
        
        passed = sum(results)
        total = len(results)
        
        print(f"\n✅ 通過: {passed}/{total}")
        
        if self.issues:
            print(f"\n❌ 發現 {len(self.issues)} 個問題:\n")
            for i, issue in enumerate(self.issues, 1):
                print(f"   {i}. {issue}")
        
        if self.fixes:
            print("\n🔧 建議修復:\n")
            for i, fix_info in enumerate(self.fixes, 1):
                print(f"   {i}. {fix_info['issue']}")
                print(f"      修復方案: {fix_info['fix']}")
                print()
        
        print("="*60)
        
        return passed == total
    
    def auto_fix(self):
        """嘗試自動修復"""
        print("\n🤖 嘗試自動修復...\n")
        
        try:
            # 升級 pip
            print("📦 升級 pip...")
            subprocess.run([sys.executable, '-m', 'pip', 'install', '--upgrade', 'pip'],
                         check=True, capture_output=True)
            print("   ✅ pip 已升級")
            
            print("\n✅ 自動修復完成！請重新運行診斷。")
            return True
        
        except Exception as e:
            print(f"\n❌ 自動修復失敗: {e}")
            return False

def main():
    """主函數"""
    diag = Diagnostics()
    
    # 運行所有檢查
    success = diag.run_all_checks()
    
    if not success:
        # 詢問是否自動修復
        print("\n是否嘗試自動修復? (y/n) ", end="")
        response = input().strip().lower()
        
        if response == 'y':
            diag.auto_fix()
            
            # 重新運行檢查
            print("\n" + "="*60)
            print("🔄 重新運行診斷...")
            print("="*60)
            diag = Diagnostics()
            success = diag.run_all_checks()
        
        if not success:
            print("\n📖 更多幫助，請參考:")
            print("   - docs/troubleshooting.md (通用故障排查)")
    
    # 返回狀態碼
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
