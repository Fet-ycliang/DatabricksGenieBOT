"""
Bot Framework to M365 Agent Framework 遷移 Skill

提供遷移工具和助手，幫助從 Bot Framework 遷移到 M365 Agent Framework
"""

from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
from dataclasses import dataclass
import logging
import json

logger = logging.getLogger(__name__)


class MigrationPhase(Enum):
    """遷移階段"""
    ASSESSMENT = "assessment"          # 評估現有代碼
    PLANNING = "planning"              # 規劃遷移步驟
    REFACTORING = "refactoring"        # 重構代碼
    TESTING = "testing"                # 測試
    DEPLOYMENT = "deployment"          # 部署


@dataclass
class MigrationAnalysis:
    """遷移分析結果"""
    total_files: int
    dialog_count: int
    handler_count: int
    activity_handler_count: int
    complexity_score: float  # 0-100，越高越複雜
    estimated_effort_hours: float
    critical_issues: List[str]
    warnings: List[str]
    recommendations: List[str]


@dataclass
class SkillMapping:
    """Dialog/Handler 到 Skill 的映射"""
    source_name: str
    source_type: str  # "dialog", "handler", "activity_handler"
    target_skill_name: str
    description: str
    migration_status: str  # "pending", "in_progress", "completed"
    complexity: str  # "low", "medium", "high"


class MigrationSkill:
    """
    遷移 Skill - 協助從 Bot Framework 遷移到 M365 Agent Framework
    """
    
    def __init__(self):
        """初始化遷移 Skill"""
        self.migration_mappings: Dict[str, SkillMapping] = {}
        self.analysis_cache: Optional[MigrationAnalysis] = None
        self.migration_plan: List[Dict[str, Any]] = []
    
    # ========================================================================
    # 第一階段：評估 (Assessment)
    # ========================================================================
    
    async def analyze_bot_framework_project(
        self,
        project_path: str
    ) -> MigrationAnalysis:
        """
        分析 Bot Framework 項目
        
        Args:
            project_path: 項目根路徑
            
        Returns:
            遷移分析結果
        """
        try:
            analysis = MigrationAnalysis(
                total_files=0,
                dialog_count=0,
                handler_count=0,
                activity_handler_count=0,
                complexity_score=0.0,
                estimated_effort_hours=0.0,
                critical_issues=[],
                warnings=[],
                recommendations=[]
            )
            
            logger.info(f"開始分析項目: {project_path}")
            
            # 實際應用中會掃描目錄
            # 這裡是示範邏輯
            
            # 分析 dialog 文件
            analysis.dialog_count = self._count_dialogs(project_path)
            
            # 分析 handler 文件
            analysis.handler_count = self._count_handlers(project_path)
            
            # 分析 ActivityHandler
            analysis.activity_handler_count = self._count_activity_handlers(project_path)
            
            # 計算總文件數
            analysis.total_files = analysis.dialog_count + analysis.handler_count
            
            # 評估複雜度
            analysis.complexity_score = self._calculate_complexity(
                analysis.dialog_count,
                analysis.handler_count,
                analysis.activity_handler_count
            )
            
            # 估算工作量
            analysis.estimated_effort_hours = self._estimate_effort(analysis.complexity_score)
            
            # 識別關鍵問題
            analysis.critical_issues = self._identify_critical_issues(project_path)
            
            # 收集警告
            analysis.warnings = self._collect_warnings(project_path)
            
            # 提供建議
            analysis.recommendations = self._generate_recommendations(analysis)
            
            self.analysis_cache = analysis
            logger.info(f"分析完成。複雜度評分: {analysis.complexity_score}/100")
            
            return analysis
        except Exception as e:
            logger.error(f"分析項目失敗: {str(e)}")
            raise
    
    def _count_dialogs(self, project_path: str) -> int:
        """計算 Dialog 文件數量"""
        # 實際應用中會掃描 bot/dialogs/ 目錄
        return 1  # 示例值
    
    def _count_handlers(self, project_path: str) -> int:
        """計算 Handler 文件數量"""
        # 實際應用中會掃描 bot/handlers/ 目錄
        return 3  # 示例值
    
    def _count_activity_handlers(self, project_path: str) -> int:
        """計算 ActivityHandler 文件數量"""
        return 1  # 示例值
    
    def _calculate_complexity(
        self,
        dialog_count: int,
        handler_count: int,
        activity_handler_count: int
    ) -> float:
        """計算項目複雜度"""
        base_score = 20.0
        dialog_score = dialog_count * 15
        handler_score = handler_count * 10
        activity_score = activity_handler_count * 25
        
        total = base_score + dialog_score + handler_score + activity_score
        return min(total, 100.0)
    
    def _estimate_effort(self, complexity_score: float) -> float:
        """估算遷移工作量（小時）"""
        if complexity_score < 30:
            return 8.0  # 1 天
        elif complexity_score < 60:
            return 24.0  # 3 天
        elif complexity_score < 80:
            return 40.0  # 1 周
        else:
            return 60.0  # 1.5 周
    
    def _identify_critical_issues(self, project_path: str) -> List[str]:
        """識別關鍵問題"""
        issues = []
        
        # 檢查常見問題
        issues.append("Dialog 中的複雜狀態管理")
        issues.append("多步驟 Waterfall Dialog")
        issues.append("OAuth 和 SSO 集成")
        
        return issues
    
    def _collect_warnings(self, project_path: str) -> List[str]:
        """收集警告信息"""
        warnings = []
        
        warnings.append("需要重新評估異步操作流程")
        warnings.append("舊版依賴項可能需要更新")
        warnings.append("部分 Bot Framework API 無直接對應")
        
        return warnings
    
    def _generate_recommendations(self, analysis: MigrationAnalysis) -> List[str]:
        """生成建議"""
        recommendations = []
        
        recommendations.append("將 Dialog 轉換為 M365 Skill")
        recommendations.append("重構事件處理流程")
        recommendations.append("整合 Microsoft Graph API")
        recommendations.append("實施完整的單元測試")
        recommendations.append("評估 OAuth/SSO 遷移策略")
        
        return recommendations
    
    # ========================================================================
    # 第二階段：規劃 (Planning)
    # ========================================================================
    
    async def create_migration_plan(
        self,
        analysis: MigrationAnalysis
    ) -> List[Dict[str, Any]]:
        """
        基於分析結果創建遷移計劃
        
        Args:
            analysis: 遷移分析結果
            
        Returns:
            遷移計劃步驟列表
        """
        try:
            plan = []
            
            # 第 1 步：依賴項更新
            plan.append({
                "step": 1,
                "phase": "準備",
                "task": "更新依賴項",
                "description": "更新 pyproject.toml，添加 M365 Agent Framework 依賴項",
                "effort_hours": 2,
                "priority": "high",
                "deliverables": ["更新的 pyproject.toml", "安裝測試報告"]
            })
            
            # 第 2 步：創建 Skills
            plan.append({
                "step": 2,
                "phase": "開發",
                "task": "創建初始 Skill 結構",
                "description": "為每個 Dialog/Handler 創建對應的 Skill",
                "effort_hours": analysis.estimated_effort_hours * 0.3,
                "priority": "high",
                "deliverables": ["BaseSkill 模板", "Skills 目錄結構"]
            })
            
            # 第 3 步：遷移身份驗證
            plan.append({
                "step": 3,
                "phase": "開發",
                "task": "遷移身份驗證邏輯",
                "description": "從 OAuth 遷移到 Microsoft Graph 認證",
                "effort_hours": analysis.estimated_effort_hours * 0.2,
                "priority": "high",
                "deliverables": ["認證 Skill", "測試案例"]
            })
            
            # 第 4 步：重構事件處理
            plan.append({
                "step": 4,
                "phase": "開發",
                "task": "重構事件處理流程",
                "description": "轉換 Dialog 邏輯到 Skill 方法",
                "effort_hours": analysis.estimated_effort_hours * 0.3,
                "priority": "high",
                "deliverables": ["功能 Skills", "單元測試"]
            })
            
            # 第 5 步：集成測試
            plan.append({
                "step": 5,
                "phase": "測試",
                "task": "執行集成測試",
                "description": "測試所有 Skills 的集成",
                "effort_hours": analysis.estimated_effort_hours * 0.15,
                "priority": "high",
                "deliverables": ["測試報告", "缺陷清單"]
            })
            
            # 第 6 步：部署
            plan.append({
                "step": 6,
                "phase": "部署",
                "task": "部署到生產環境",
                "description": "逐步部署到生產，監控性能",
                "effort_hours": analysis.estimated_effort_hours * 0.05,
                "priority": "high",
                "deliverables": ["部署檢查清單", "上線報告"]
            })
            
            self.migration_plan = plan
            logger.info(f"遷移計劃已創建，包含 {len(plan)} 個步驟")
            
            return plan
        except Exception as e:
            logger.error(f"創建遷移計劃失敗: {str(e)}")
            raise
    
    # ========================================================================
    # 第三階段：代碼轉換 (Code Transformation)
    # ========================================================================
    
    async def generate_skill_template(
        self,
        dialog_name: str,
        dialog_type: str = "waterfall"
    ) -> str:
        """
        生成 Skill 模板代碼
        
        Args:
            dialog_name: Dialog 名稱
            dialog_type: Dialog 類型（waterfall, component 等）
            
        Returns:
            生成的 Skill 代碼
        """
        try:
            skill_name = self._convert_dialog_name_to_skill_name(dialog_name)
            
            template = f'''"""
{skill_name} - 從 {dialog_name} 遷移而來

原始 Bot Framework Dialog: {dialog_name}
遷移日期: {{date}}
狀態: 準備迁移
"""

from typing import Optional, Dict, Any, List
import logging

logger = logging.getLogger(__name__)


class {skill_name}:
    """
    {skill_name} Skill
    
    從 {dialog_name} 遷移而來
    """
    
    def __init__(self, graph_service):
        """
        初始化 {{skill_name}}
        
        Args:
            graph_service: Microsoft Graph 服務實例
        """
        self.graph_service = graph_service
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """
        執行主邏輯
        
        遷移提示：
        1. 將 Dialog 步驟轉換為異步方法
        2. 使用 Microsoft Graph API 而非 Bot Framework API
        3. 實施適當的錯誤處理
        4. 添加日誌記錄
        """
        try:
            # TODO: 實現遷移的邏輯
            result = await self._process(**kwargs)
            return result
        except Exception as e:
            logger.error(f"執行失敗: {{str(e)}}")
            return {{"error": str(e)}}
    
    async def _process(self, **kwargs) -> Dict[str, Any]:
        """
        內部處理邏輯
        
        遷移檢查清單：
        - [ ] 轉換狀態管理
        - [ ] 轉換異步調用
        - [ ] 轉換驗證邏輯
        - [ ] 添加單元測試
        """
        pass
'''
            
            logger.info(f"生成 {{skill_name}} 的 Skill 模板")
            return template
        except Exception as e:
            logger.error(f"生成模板失敗: {{str(e)}}")
            raise
    
    def _convert_dialog_name_to_skill_name(self, dialog_name: str) -> str:
        """將 Dialog 名稱轉換為 Skill 類名"""
        # SSODialog -> SSOSkill
        if dialog_name.endswith("Dialog"):
            return dialog_name.replace("Dialog", "Skill")
        return dialog_name + "Skill"
    
    # ========================================================================
    # 第四階段：對應關係管理
    # ========================================================================
    
    def create_mapping(
        self,
        source_name: str,
        source_type: str,
        target_skill_name: str,
        description: str,
        complexity: str = "medium"
    ) -> SkillMapping:
        """
        創建 Dialog/Handler 到 Skill 的映射
        
        Args:
            source_name: 原始 Dialog/Handler 名稱
            source_type: 原始元素類型
            target_skill_name: 目標 Skill 名稱
            description: 描述
            complexity: 複雜度
            
        Returns:
            映射對象
        """
        mapping = SkillMapping(
            source_name=source_name,
            source_type=source_type,
            target_skill_name=target_skill_name,
            description=description,
            migration_status="pending",
            complexity=complexity
        )
        
        self.migration_mappings[source_name] = mapping
        logger.info(f"創建映射: {source_name} -> {target_skill_name}")
        
        return mapping
    
    def update_mapping_status(
        self,
        source_name: str,
        status: str
    ) -> bool:
        """
        更新映射狀態
        
        Args:
            source_name: 原始名稱
            status: 新狀態
            
        Returns:
            是否成功
        """
        if source_name not in self.migration_mappings:
            return False
        
        self.migration_mappings[source_name].migration_status = status
        logger.info(f"更新映射狀態: {source_name} -> {status}")
        
        return True
    
    def get_mapping_status(self) -> Dict[str, str]:
        """
        獲取所有映射的遷移狀態
        
        Returns:
            映射狀態字典
        """
        return {
            name: mapping.migration_status
            for name, mapping in self.migration_mappings.items()
        }
    
    # ========================================================================
    # 遷移幫助工具
    # ========================================================================
    
    def generate_comparison_guide(self) -> str:
        """
        生成 Bot Framework 與 M365 Agent Framework 的對比指南
        
        Returns:
            對比指南文本
        """
        guide = """
# Bot Framework 到 M365 Agent Framework 遷移指南

## 概念對應

| Bot Framework | M365 Agent Framework | 說明 |
|---|---|---|
| Dialog | Skill | 代表一個功能單元 |
| ActivityHandler | AgentFramework | 主要事件處理器 |
| DialogSet | SkillRegistry | 技能管理器 |
| OAuthPrompt | Microsoft Graph Auth | 身份驗證 |
| Waterfall Dialog | Async Methods | 流程控制 |
| ConversationState | User Context | 狀態管理 |

## 代碼轉換示例

### Dialog 轉換為 Skill

#### 原始 Bot Framework 代碼：
```python
class MyDialog(ComponentDialog):
    def __init__(self):
        super().__init__("MyDialog")
        
        self.add_dialog(
            WaterfallDialog("MyWaterfall", [
                self.step_one,
                self.step_two,
            ])
        )
    
    async def step_one(self, step_context):
        # 實現邏輯
        pass
```

#### 轉換為 M365 Skill：
```python
class MySkill:
    def __init__(self, graph_service):
        self.graph_service = graph_service
    
    async def execute(self, **kwargs):
        result_one = await self.step_one(**kwargs)
        result_two = await self.step_two(result_one)
        return result_two
    
    async def step_one(self, **kwargs):
        # 實現邏輯
        pass
```

## 常見遷移模式

### 1. 狀態管理

**Bot Framework:**
```python
conversation_state.create_property("key")
user_state.create_property("key")
```

**M365 Agent Framework:**
```python
# 使用 M365AgentFramework 的用戶上下文
context = await framework.get_user_context(user_id)
```

### 2. API 調用

**Bot Framework:**
```python
# 使用自定義服務調用 API
result = await self.genie_service.query()
```

**M365 Agent Framework:**
```python
# 使用 Microsoft Graph Skill
result = await self.mail_skill.get_recent_emails()
```

### 3. 身份驗證

**Bot Framework:**
```python
OAuthPrompt(
    "oauth",
    OAuthPromptSettings(connection_name="...")
)
```

**M365 Agent Framework:**
```python
# 使用 Azure AD 認證
from azure.identity import DefaultAzureCredential
credential = DefaultAzureCredential()
```

## 遷移檢查清單

- [ ] 更新依賴項
- [ ] 創建 Skill 結構
- [ ] 遷移身份驗證
- [ ] 轉換 Dialog 為 Skill
- [ ] 轉換事件處理
- [ ] 更新狀態管理
- [ ] 編寫單元測試
- [ ] 執行集成測試
- [ ] 文檔更新
- [ ] 用戶驗收測試

## 性能考慮

1. **異步操作**: M365 API 調用充分利用異步
2. **緩存**: 實施適當的緩存策略
3. **錯誤恢復**: 實施重試邏輯
4. **監控**: 添加詳細的日誌和監控

"""
        return guide
    
    def generate_checklist(self) -> List[str]:
        """
        生成遷移檢查清單
        
        Returns:
            檢查項列表
        """
        checklist = [
            "✓ 分析現有 Bot Framework 代碼",
            "✓ 識別所有 Dialog 和 Handler",
            "✓ 評估遷移複雜度",
            "✓ 創建遷移計劃",
            "✓ 更新依賴項",
            "✓ 創建基礎 Skill 結構",
            "✓ 遷移身份驗證邏輯",
            "✓ 轉換每個 Dialog 為 Skill",
            "✓ 轉換事件處理流程",
            "✓ 實施完整的單元測試",
            "✓ 執行集成測試",
            "✓ 性能測試和優化",
            "✓ 文檔更新",
            "✓ 用戶驗收測試",
            "✓ 部署到測試環境",
            "✓ 部署到生產環境",
            "✓ 監控和維護"
        ]
        return checklist
    
    # ========================================================================
    # 報告生成
    # ========================================================================
    
    def generate_migration_report(self) -> Dict[str, Any]:
        """
        生成遷移報告
        
        Returns:
            遷移報告
        """
        if not self.analysis_cache:
            return {"error": "未進行分析，請先運行 analyze_bot_framework_project"}
        
        report = {
            "analysis": {
                "total_files": self.analysis_cache.total_files,
                "dialog_count": self.analysis_cache.dialog_count,
                "handler_count": self.analysis_cache.handler_count,
                "activity_handler_count": self.analysis_cache.activity_handler_count,
                "complexity_score": self.analysis_cache.complexity_score,
                "estimated_effort_hours": self.analysis_cache.estimated_effort_hours,
            },
            "issues": self.analysis_cache.critical_issues,
            "warnings": self.analysis_cache.warnings,
            "recommendations": self.analysis_cache.recommendations,
            "plan_steps": len(self.migration_plan),
            "mapping_count": len(self.migration_mappings),
            "migration_status": self.get_mapping_status()
        }
        
        return report
