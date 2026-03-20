#!/usr/bin/env python3
"""
遷移實用程序 - Bot Framework 到 M365 Agent Framework

這個腳本提供命令行工具來簡化遷移過程
"""

import asyncio
import sys
from pathlib import Path
from app.core.m365_agent_framework import M365AgentFramework
from app.core.config import DefaultConfig


class MigrationCLI:
    """遷移命令行界面"""
    
    def __init__(self):
        """初始化 CLI"""
        self.config = DefaultConfig()
        self.framework = M365AgentFramework(self.config)
    
    async def run_analysis(self, project_path: str):
        """運行項目分析"""
        print("🔍 開始分析項目...")
        
        try:
            analysis = await self.framework.migration_skill.analyze_bot_framework_project(
                project_path
            )
            
            self._print_analysis_results(analysis)
        except Exception as e:
            print(f"❌ 分析失敗: {str(e)}")
            sys.exit(1)
    
    async def generate_plan(self):
        """生成遷移計劃"""
        print("📋 生成遷移計劃...")
        
        try:
            if not self.framework.migration_skill.analysis_cache:
                print("⚠️ 請先運行分析")
                return
            
            plan = await self.framework.migration_skill.create_migration_plan(
                self.framework.migration_skill.analysis_cache
            )
            
            self._print_migration_plan(plan)
        except Exception as e:
            print(f"❌ 生成計劃失敗: {str(e)}")
            sys.exit(1)
    
    async def generate_skill(self, dialog_name: str, dialog_type: str = "waterfall"):
        """生成 Skill 模板"""
        print(f"🔨 生成 {dialog_name} 的 Skill 模板...")
        
        try:
            template = await self.framework.migration_skill.generate_skill_template(
                dialog_name,
                dialog_type
            )
            
            skill_filename = f"{dialog_name.replace('Dialog', '')}_skill.py"
            with open(skill_filename, 'w', encoding='utf-8') as f:
                f.write(template)
            
            print(f"✅ Skill 模板已生成: {skill_filename}")
        except Exception as e:
            print(f"❌ 生成失敗: {str(e)}")
            sys.exit(1)
    
    def create_mapping(self, source_name: str, source_type: str, 
                      target_skill_name: str, description: str):
        """創建映射"""
        print(f"🗺️ 創建映射: {source_name} -> {target_skill_name}")
        
        try:
            mapping = self.framework.migration_skill.create_mapping(
                source_name,
                source_type,
                target_skill_name,
                description
            )
            
            print(f"✅ 映射已創建")
        except Exception as e:
            print(f"❌ 創建映射失敗: {str(e)}")
            sys.exit(1)
    
    def update_mapping_status(self, source_name: str, status: str):
        """更新映射狀態"""
        print(f"📝 更新 {source_name} 的狀態為 {status}")
        
        try:
            success = self.framework.migration_skill.update_mapping_status(
                source_name,
                status
            )
            
            if success:
                print(f"✅ 狀態已更新")
            else:
                print(f"❌ 未找到映射: {source_name}")
        except Exception as e:
            print(f"❌ 更新失敗: {str(e)}")
            sys.exit(1)
    
    def show_guide(self):
        """顯示遷移指南"""
        guide = self.framework.migration_skill.generate_comparison_guide()
        print(guide)
    
    def show_checklist(self):
        """顯示檢查清單"""
        checklist = self.framework.migration_skill.generate_checklist()
        print("\n📋 遷移檢查清單:\n")
        for i, item in enumerate(checklist, 1):
            print(f"{i}. {item}")
    
    def show_report(self):
        """顯示遷移報告"""
        report = self.framework.migration_skill.generate_migration_report()
        
        print("\n" + "="*60)
        print("遷移報告")
        print("="*60)
        
        analysis = report.get("analysis", {})
        print(f"\n📊 分析結果:")
        print(f"  - 總文件數: {analysis.get('total_files', 0)}")
        print(f"  - Dialog 數: {analysis.get('dialog_count', 0)}")
        print(f"  - Handler 數: {analysis.get('handler_count', 0)}")
        print(f"  - 複雜度評分: {analysis.get('complexity_score', 0):.1f}/100")
        print(f"  - 估算工作量: {analysis.get('estimated_effort_hours', 0):.1f} 小時")
        
        print(f"\n⚠️ 關鍵問題 ({len(report.get('issues', []))} 個):")
        for issue in report.get('issues', []):
            print(f"  - {issue}")
        
        print(f"\n💡 建議 ({len(report.get('recommendations', []))} 個):")
        for rec in report.get('recommendations', []):
            print(f"  - {rec}")
        
        print(f"\n📈 遷移進度:")
        status = report.get('migration_status', {})
        completed = len([s for s in status.values() if s == 'completed'])
        total = len(status)
        percentage = (completed / total * 100) if total > 0 else 0
        print(f"  - 已完成: {completed}/{total} ({percentage:.1f}%)")
        print(f"  - 進行中: {len([s for s in status.values() if s == 'in_progress'])}")
        print(f"  - 待處理: {len([s for s in status.values() if s == 'pending'])}")
    
    def _print_analysis_results(self, analysis):
        """打印分析結果"""
        print("\n" + "="*60)
        print("分析結果")
        print("="*60)
        
        print(f"\n📊 代碼統計:")
        print(f"  - 總文件數: {analysis.total_files}")
        print(f"  - Dialog 數: {analysis.dialog_count}")
        print(f"  - Handler 數: {analysis.handler_count}")
        print(f"  - ActivityHandler 數: {analysis.activity_handler_count}")
        
        print(f"\n📈 複雜度評估:")
        print(f"  - 複雜度評分: {analysis.complexity_score:.1f}/100")
        complexity_level = "簡單" if analysis.complexity_score < 30 \
            else "中等" if analysis.complexity_score < 60 \
            else "複雜" if analysis.complexity_score < 80 \
            else "非常複雜"
        print(f"  - 複雜度等級: {complexity_level}")
        print(f"  - 估算工作量: {analysis.estimated_effort_hours:.1f} 小時")
        
        if analysis.critical_issues:
            print(f"\n⚠️ 關鍵問題 ({len(analysis.critical_issues)} 個):")
            for issue in analysis.critical_issues:
                print(f"  - {issue}")
        
        if analysis.warnings:
            print(f"\n⚠️ 警告 ({len(analysis.warnings)} 個):")
            for warning in analysis.warnings:
                print(f"  - {warning}")
        
        if analysis.recommendations:
            print(f"\n💡 建議 ({len(analysis.recommendations)} 個):")
            for rec in analysis.recommendations:
                print(f"  - {rec}")
    
    def _print_migration_plan(self, plan):
        """打印遷移計劃"""
        print("\n" + "="*60)
        print("遷移計劃")
        print("="*60 + "\n")
        
        total_hours = 0
        for step in plan:
            print(f"步驟 {step['step']}: {step['task']}")
            print(f"  階段: {step['phase']}")
            print(f"  描述: {step['description']}")
            print(f"  工作量: {step['effort_hours']:.1f} 小時")
            print(f"  優先級: {step['priority']}")
            print(f"  可交付物:")
            for deliverable in step['deliverables']:
                print(f"    - {deliverable}")
            print()
            total_hours += step['effort_hours']
        
        print(f"總工作量: {total_hours:.1f} 小時 (~{total_hours/8:.1f} 天)")


async def main():
    """主函數"""
    cli = MigrationCLI()
    
    if len(sys.argv) < 2:
        print("遷移工具使用方法:")
        print()
        print("  python migration_utils.py analyze <project_path>")
        print("  python migration_utils.py plan")
        print("  python migration_utils.py generate <dialog_name> [dialog_type]")
        print("  python migration_utils.py map <source> <type> <target> <description>")
        print("  python migration_utils.py update <source> <status>")
        print("  python migration_utils.py guide")
        print("  python migration_utils.py checklist")
        print("  python migration_utils.py report")
        print()
        sys.exit(0)
    
    command = sys.argv[1]
    
    try:
        if command == "analyze":
            project_path = sys.argv[2] if len(sys.argv) > 2 else "."
            await cli.run_analysis(project_path)
        
        elif command == "plan":
            await cli.generate_plan()
        
        elif command == "generate":
            dialog_name = sys.argv[2] if len(sys.argv) > 2 else "MyDialog"
            dialog_type = sys.argv[3] if len(sys.argv) > 3 else "waterfall"
            await cli.generate_skill(dialog_name, dialog_type)
        
        elif command == "map":
            if len(sys.argv) < 6:
                print("用法: migration_utils.py map <source> <type> <target> <description>")
                sys.exit(1)
            cli.create_mapping(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5])
        
        elif command == "update":
            if len(sys.argv) < 4:
                print("用法: migration_utils.py update <source> <status>")
                sys.exit(1)
            cli.update_mapping_status(sys.argv[2], sys.argv[3])
        
        elif command == "guide":
            cli.show_guide()
        
        elif command == "checklist":
            cli.show_checklist()
        
        elif command == "report":
            cli.show_report()
        
        else:
            print(f"❌ 未知命令: {command}")
            sys.exit(1)
    
    except Exception as e:
        print(f"❌ 執行失敗: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
