"""
Health Check 端點測試腳本

此腳本用於測試 DatabricksGenieBOT 的 health check 和 ready check 端點。

使用方法：
    python test_health_check.py
    python test_health_check.py --url https://your-app.azurewebsites.net
    python test_health_check.py --timeout 10
"""

import asyncio
import httpx
import json
import argparse
from typing import Dict, Optional
from datetime import datetime
from urllib.parse import urljoin


class HealthCheckTester:
    """Health Check 測試工具"""
    
    def __init__(self, base_url: str = "http://localhost:3978", timeout: int = 10):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.results = []
    
    async def test_health_endpoint(self) -> Dict:
        """測試 /health 端點"""
        print("\n" + "="*60)
        print("📋 Testing /health endpoint")
        print("="*60)
        
        url = urljoin(self.base_url, "/health")
        try:
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(timeout=float(self.timeout))
            ) as client:
                response = await client.get(url)
                status = response.status_code
                data = response.json()
                
                result = {
                    "endpoint": "/health",
                    "status_code": status,
                    "success": status in [200, 503],
                    "response": data,
                    "timestamp": datetime.now().isoformat()
                }
                    
                    self._print_response(status, data)
                    self.results.append(result)
                    return result
                    
        except asyncio.TimeoutError:
            error_msg = f"⏱️  Request timeout (>{self.timeout}s)"
            print(f"❌ {error_msg}")
            result = {
                "endpoint": "/health",
                "success": False,
                "error": error_msg,
                "timestamp": datetime.now().isoformat()
            }
            self.results.append(result)
            return result
        except Exception as e:
            error_msg = str(e)
            print(f"❌ Error: {error_msg}")
            result = {
                "endpoint": "/health",
                "success": False,
                "error": error_msg,
                "timestamp": datetime.now().isoformat()
            }
            self.results.append(result)
            return result
    
    async def test_ready_endpoint(self) -> Dict:
        """測試 /ready 端點"""
        print("\n" + "="*60)
        print("📋 Testing /ready endpoint")
        print("="*60)
        
        url = urljoin(self.base_url, "/ready")
        try:
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(timeout=float(self.timeout))
            ) as client:
                response = await client.get(url)
                status = response.status_code
                data = response.json()
                
                result = {
                    "endpoint": "/ready",
                    "status_code": status,
                    "success": status in [200, 503],
                    "response": data,
                    "timestamp": datetime.now().isoformat()
                }
                    
                    self._print_response(status, data)
                    self.results.append(result)
                    return result
                    
        except asyncio.TimeoutError:
            error_msg = f"⏱️  Request timeout (>{self.timeout}s)"
            print(f"❌ {error_msg}")
            result = {
                "endpoint": "/ready",
                "success": False,
                "error": error_msg,
                "timestamp": datetime.now().isoformat()
            }
            self.results.append(result)
            return result
        except Exception as e:
            error_msg = str(e)
            print(f"❌ Error: {error_msg}")
            result = {
                "endpoint": "/ready",
                "success": False,
                "error": error_msg,
                "timestamp": datetime.now().isoformat()
            }
            self.results.append(result)
            return result
    
    async def test_heartbeat(self) -> Dict:
        """測試根路徑 / 端點 (心跳檢查)"""
        print("\n" + "="*60)
        print("📋 Testing / endpoint (heartbeat)")
        print("="*60)
        
        url = self.base_url
        try:
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(timeout=float(self.timeout))
            ) as client:
                response = await client.get(url)
                status = response.status_code
                data = response.json()
                
                result = {
                    "endpoint": "/",
                    "status_code": status,
                    "success": status == 200,
                    "response": data,
                    "timestamp": datetime.now().isoformat()
                }
                    
                    self._print_response(status, data)
                    self.results.append(result)
                    return result
                    
        except asyncio.TimeoutError:
            error_msg = f"⏱️  Request timeout (>{self.timeout}s)"
            print(f"❌ {error_msg}")
            result = {
                "endpoint": "/",
                "success": False,
                "error": error_msg,
                "timestamp": datetime.now().isoformat()
            }
            self.results.append(result)
            return result
        except Exception as e:
            error_msg = str(e)
            print(f"❌ Error: {error_msg}")
            result = {
                "endpoint": "/",
                "success": False,
                "error": error_msg,
                "timestamp": datetime.now().isoformat()
            }
            self.results.append(result)
            return result
    
    def _print_response(self, status_code: int, data: Dict):
        """美化列印回應資料"""
        status_emoji = "✅" if status_code == 200 else "⚠️ " if status_code == 503 else "❌"
        print(f"\n{status_emoji} Status Code: {status_code}")
        print("\n📦 Response:")
        print(json.dumps(data, indent=2, ensure_ascii=False))
    
    def print_summary(self):
        """列印測試摘要"""
        print("\n" + "="*60)
        print("📊 Test Summary")
        print("="*60)
        
        total_tests = len(self.results)
        successful_tests = sum(1 for r in self.results if r.get("success"))
        failed_tests = total_tests - successful_tests
        
        print(f"\nTotal Tests: {total_tests}")
        print(f"✅ Passed: {successful_tests}")
        print(f"❌ Failed: {failed_tests}")
        
        print("\nDetailed Results:")
        for result in self.results:
            status = "✅ PASS" if result.get("success") else "❌ FAIL"
            endpoint = result.get("endpoint")
            error = result.get("error", "")
            status_code = result.get("status_code", "N/A")
            
            if error:
                print(f"\n{status} | {endpoint}")
                print(f"   Error: {error}")
            else:
                print(f"\n{status} | {endpoint}")
                print(f"   Status Code: {status_code}")
    
    async def run_all_tests(self):
        """執行所有測試"""
        print(f"\n🚀 Starting Health Check Tests")
        print(f"📍 Base URL: {self.base_url}")
        print(f"⏱️  Timeout: {self.timeout}s")
        
        await self.test_heartbeat()
        await self.test_health_endpoint()
        await self.test_ready_endpoint()
        
        self.print_summary()
        
        # 返回總體結果
        all_successful = all(r.get("success") for r in self.results)
        return 0 if all_successful else 1


async def main():
    parser = argparse.ArgumentParser(
        description="Test DatabricksGenieBOT health check endpoints"
    )
    parser.add_argument(
        "--url",
        default="http://localhost:3978",
        help="Base URL of the application (default: http://localhost:3978)"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=10,
        help="Request timeout in seconds (default: 10)"
    )
    
    args = parser.parse_args()
    
    tester = HealthCheckTester(base_url=args.url, timeout=args.timeout)
    exit_code = await tester.run_all_tests()
    
    return exit_code


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
