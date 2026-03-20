#!/usr/bin/env python3
"""
獨立遷移分析工具 - 無需完整應用程式導入

這個工具可以獨立運行，分析 Bot Framework 代碼並生成遷移報告
"""

import os
import sys
from pathlib import Path
from dataclasses import dataclass
from enum import Enum
from typing import List, Dict, Optional
import json
from datetime import datetime


class MigrationPhase(Enum):
    """遷移階段"""
    ASSESSMENT = "評估"
    PLANNING = "規劃"
    REFACTORING = "重構"
    TESTING = "測試"
    DEPLOYMENT = "部署"


@dataclass
class DialogInfo:
    """Dialog 信息"""
    name: str
    file_path: str
    methods: List[str]
    dependencies: List[str]


@dataclass
class HandlerInfo:
    """Handler 信息"""
    name: str
    file_path: str
    methods: List[str]
    handles: List[str]


@dataclass
class MigrationAnalysis:
    """遷移分析結果"""
    project_name: str
    total_dialogs: int
    total_handlers: int
    total_activities: int
    complexity_score: int
    estimated_effort: str
    dialogs: List[DialogInfo]
    handlers: List[HandlerInfo]
    analysis_date: str


class BotFrameworkAnalyzer:
    """Bot Framework 項目分析器"""
    
    def __init__(self, project_path: str):
        """初始化分析器"""
        self.project_path = Path(project_path).resolve()
        self.dialogs: List[DialogInfo] = []
        self.handlers: List[HandlerInfo] = []
        self.activity_count = 0
        
    def analyze(self) -> MigrationAnalysis:
        """執行項目分析"""
        print("🔍 開始掃描 Bot Framework 項目...")
        
        # 分析 dialogs
        self._analyze_dialogs()
        
        # 分析 handlers
        self._analyze_handlers()
        
        # 分析 activities
        self._analyze_activities()
        
        # 計算複雜度
        complexity = self._calculate_complexity()
        effort = self._estimate_effort(complexity)
        
        analysis = MigrationAnalysis(
            project_name=self.project_path.name,
            total_dialogs=len(self.dialogs),
            total_handlers=len(self.handlers),
            total_activities=self.activity_count,
            complexity_score=complexity,
            estimated_effort=effort,
            dialogs=self.dialogs,
            handlers=self.handlers,
            analysis_date=datetime.now().isoformat()
        )
        
        return analysis
    
    def _analyze_dialogs(self):
        """分析 Dialog 文件"""
        dialogs_dir = self.project_path / "bot" / "dialogs"
        
        if not dialogs_dir.exists():
            print(f"⚠️ 未找到 dialogs 目錄: {dialogs_dir}")
            return
        
        print(f"📁 掃描 dialogs 目錄: {dialogs_dir}")
        
        for py_file in dialogs_dir.glob("*.py"):
            if py_file.name == "__init__.py":
                continue
            
            try:
                content = py_file.read_text(encoding='utf-8', errors='ignore')
            except:
                content = py_file.read_text(encoding='latin-1', errors='ignore')
            
            methods = self._extract_methods(content)
            dependencies = self._extract_imports(content)
            
            dialog_info = DialogInfo(
                name=py_file.stem,
                file_path=str(py_file.relative_to(self.project_path)),
                methods=methods,
                dependencies=dependencies
            )
            
            self.dialogs.append(dialog_info)
            print(f"  ✅ Dialog: {py_file.stem} ({len(methods)} 個方法)")
    
    def _analyze_handlers(self):
        """分析 Handler 文件"""
        handlers_dir = self.project_path / "bot" / "handlers"
        
        if not handlers_dir.exists():
            print(f"⚠️ 未找到 handlers 目錄: {handlers_dir}")
            return
        
        print(f"📁 掃描 handlers 目錄: {handlers_dir}")
        
        for py_file in handlers_dir.glob("*.py"):
            if py_file.name == "__init__.py":
                continue
            
            try:
                content = py_file.read_text(encoding='utf-8', errors='ignore')
            except:
                content = py_file.read_text(encoding='latin-1', errors='ignore')
            
            methods = self._extract_methods(content)
            handles = self._extract_activity_handlers(content)
            dependencies = self._extract_imports(content)
            
            handler_info = HandlerInfo(
                name=py_file.stem,
                file_path=str(py_file.relative_to(self.project_path)),
                methods=methods,
                handles=handles
            )
            
            self.handlers.append(handler_info)
            print(f"  ✅ Handler: {py_file.stem} ({len(methods)} 個方法)")
    
    def _analyze_activities(self):
        """分析 Activity 類型"""
        handlers_dir = self.project_path / "bot" / "handlers"
        
        if not handlers_dir.exists():
            return
        
        activity_types = set()
        
        for py_file in handlers_dir.glob("*.py"):
            try:
                content = py_file.read_text(encoding='utf-8', errors='ignore')
            except:
                content = py_file.read_text(encoding='latin-1', errors='ignore')
            
            # 查找 ActivityHandler 相關的方法
            if "on_members_added_activity" in content:
                activity_types.add("members_added")
            if "on_message_activity" in content:
                activity_types.add("message")
            if "on_token_response_activity" in content:
                activity_types.add("token_response")
            if "on_message_reaction_activity" in content:
                activity_types.add("message_reaction")
        
        self.activity_count = len(activity_types)
        print(f"📊 找到 {self.activity_count} 種 Activity 類型")
    
    def _extract_methods(self, content: str) -> List[str]:
        """提取方法名稱"""
        methods = []
        for line in content.split('\n'):
            line = line.strip()
            if line.startswith('def ') and not line.startswith('def _'):
                method_name = line.split('(')[0].replace('def ', '')
                methods.append(method_name)
        return methods
    
    def _extract_imports(self, content: str) -> List[str]:
        """提取導入模塊"""
        imports = []
        for line in content.split('\n'):
            line = line.strip()
            if line.startswith('from ') or line.startswith('import '):
                imports.append(line)
        return imports[:5]  # 只返回前 5 個
    
    def _extract_activity_handlers(self, content: str) -> List[str]:
        """提取 Activity 處理方法"""
        handlers = []
        activity_methods = [
            'on_message_activity',
            'on_members_added_activity',
            'on_members_removed_activity',
            'on_token_response_activity',
            'on_message_reaction_activity',
        ]
        
        for method in activity_methods:
            if f'def {method}' in content:
                handlers.append(method)
        
        return handlers
    
    def _calculate_complexity(self) -> int:
        """計算複雜度分數"""
        # 基礎分數
        base = 20
        
        # Dialog 複雜度: 15 分/個
        dialog_score = len(self.dialogs) * 15
        
        # Handler 複雜度: 10 分/個
        handler_score = len(self.handlers) * 10
        
        # Activity 複雜度: 25 分/種
        activity_score = self.activity_count * 25
        
        total = base + dialog_score + handler_score + activity_score
        
        # 限制在 100 以內
        return min(total, 100)
    
    def _estimate_effort(self, complexity: int) -> str:
        """估計遷移工作量"""
        if complexity < 30:
            return "低 (~8 小時)"
        elif complexity < 60:
            return "中等 (~24 小時)"
        elif complexity < 80:
            return "中高 (~40 小時)"
        else:
            return "高 (~60+ 小時)"


def print_analysis_report(analysis: MigrationAnalysis):
    """打印分析報告"""
    
    print("\n" + "=" * 80)
    print("📊 遷移分析報告")
    print("=" * 80)
    print(f"\n📁 項目: {analysis.project_name}")
    print(f"📅 分析時間: {analysis.analysis_date}")
    
    print("\n【概覽】")
    print(f"  • Dialog 數量: {analysis.total_dialogs}")
    print(f"  • Handler 數量: {analysis.total_handlers}")
    print(f"  • Activity 類型: {analysis.total_activities}")
    print(f"  • 複雜度分數: {analysis.complexity_score}/100")
    print(f"  • 估計工作量: {analysis.estimated_effort}")
    
    if analysis.dialogs:
        print("\n【Dialog 清單】")
        for dialog in analysis.dialogs:
            print(f"\n  📄 {dialog.name}")
            print(f"     位置: {dialog.file_path}")
            print(f"     方法: {', '.join(dialog.methods[:3])}")
            if len(dialog.methods) > 3:
                print(f"           + {len(dialog.methods) - 3} 個其他方法")
    
    if analysis.handlers:
        print("\n【Handler 清單】")
        for handler in analysis.handlers:
            print(f"\n  📄 {handler.name}")
            print(f"     位置: {handler.file_path}")
            print(f"     方法: {', '.join(handler.methods[:3])}")
            if handler.handles:
                print(f"     處理: {', '.join(handler.handles)}")
    
    # 遷移計劃
    print("\n【推薦遷移計劃】")
    
    phases = [
        ("1️⃣ 評估", "✅ 已完成 - 詳見上方分析"),
        ("2️⃣ 規劃", "📋 生成遷移藍圖和依賴映射"),
        ("3️⃣ 重構", f"🔧 轉換 {analysis.total_dialogs} 個 Dialog + {analysis.total_handlers} 個 Handler 到 Skill"),
        ("4️⃣ 測試", "🧪 單元測試和集成測試"),
        ("5️⃣ 部署", "🚀 逐步遷移到生產環境")
    ]
    
    for phase_name, phase_desc in phases:
        print(f"\n  {phase_name}")
        print(f"  {phase_desc}")
    
    # 後續步驟
    print("\n【後續步驟】")
    print("""
  1. 生成遷移計劃:
     python run_migration_analysis.py plan
  
  2. 根據複雜度，優先遷移核心 Dialog:
     - 首先遷移 SSO Dialog (sso_dialog.py)
     - 其次遷移主 Handler (handlers/bot.py)
     - 最後遷移命令 Handler (handlers/commands.py)
  
  3. 為每個 Dialog/Handler 生成 Skill 模板:
     python run_migration_analysis.py generate sso_dialog sso
  
  4. 測試和驗證
  
  5. 逐步部署到生產環境
    """)
    
    print("\n" + "=" * 80)


def save_analysis_json(analysis: MigrationAnalysis, output_file: str = "migration_analysis.json"):
    """保存分析結果到 JSON"""
    
    data = {
        "project": analysis.project_name,
        "analysis_date": analysis.analysis_date,
        "summary": {
            "total_dialogs": analysis.total_dialogs,
            "total_handlers": analysis.total_handlers,
            "total_activities": analysis.total_activities,
            "complexity_score": analysis.complexity_score,
            "estimated_effort": analysis.estimated_effort
        },
        "dialogs": [
            {
                "name": d.name,
                "file_path": d.file_path,
                "methods": d.methods,
                "dependencies": d.dependencies
            }
            for d in analysis.dialogs
        ],
        "handlers": [
            {
                "name": h.name,
                "file_path": h.file_path,
                "methods": h.methods,
                "handles": h.handles
            }
            for h in analysis.handlers
        ]
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ 分析結果已保存到: {output_file}")


def main():
    """主函數"""
    
    if len(sys.argv) < 2:
        print("使用方法:")
        print("  python run_migration_analysis.py analyze [project_path]")
        print("  python run_migration_analysis.py plan")
        print("\n示例:")
        print("  python run_migration_analysis.py analyze .")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "analyze":
        project_path = sys.argv[2] if len(sys.argv) > 2 else "."
        
        # 執行分析
        analyzer = BotFrameworkAnalyzer(project_path)
        analysis = analyzer.analyze()
        
        # 打印報告
        print_analysis_report(analysis)
        
        # 保存 JSON
        save_analysis_json(analysis)
        
    elif command == "plan":
        print("📋 遷移計劃生成")
        print("""
根據分析結果，推薦的遷移路徑如下：

【階段 1: 準備 (1-2 天)】
  □ 審查現有的 Dialog 和 Handler 實現
  □ 規劃 M365 Skill 結構
  □ 設置開發環境

【階段 2: 核心遷移 (3-5 天)】
  □ 將 SSO Dialog 轉換為 SSOSkill
  □ 將命令 Handler 轉換為 CommandSkill
  □ 將 Bot Handler 轉換為核心 BotSkill

【階段 3: 功能遷移 (2-3 天)】
  □ 遷移郵件相關功能
  □ 遷移日曆相關功能
  □ 遷移 Teams 相關功能

【階段 4: 測試 (2-3 天)】
  □ 單元測試
  □ 集成測試
  □ 端到端測試

【階段 5: 部署 (1 天)】
  □ 容器化
  □ 部署到 Azure
  □ 監控和日誌記錄

總時間估計: 10-15 天
        """)
    else:
        print(f"❌ 未知命令: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
