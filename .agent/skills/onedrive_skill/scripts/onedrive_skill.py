"""
Microsoft 365 Agent OneDrive Skill

提供 OneDrive/SharePoint 檔案相關的操作能力
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)


class DriveItem(BaseModel):
    """雲端硬碟項目模型"""
    name: str
    item_id: str
    is_folder: bool
    size: int = 0
    created_datetime: Optional[str] = None
    modified_datetime: Optional[str] = None
    web_url: Optional[str] = None


class OneDriveSkill:
    """OneDrive Skill - 處理檔案和資料夾操作"""
    
    def __init__(self, graph_service):
        """
        初始化 OneDrive Skill
        
        Args:
            graph_service: Microsoft Graph 服務實例
        """
        self.graph_service = graph_service
    
    async def list_drive_items(
        self,
        user_id: str = "me",
        folder_path: str = "root",
        count: int = 10
    ) -> List[DriveItem]:
        """
        列出雲端硬碟中的項目
        
        Args:
            user_id: 使用者 ID
            folder_path: 資料夾路徑（預設為根目錄）
            count: 返回的項目數量
            
        Returns:
            雲端硬碟項目清單
        """
        try:
            result = await self.graph_service.list_user_drive_items(
                user_id,
                count
            )
            
            if "error" in result:
                logger.error(f"列出項目失敗: {result['error']}")
                return []
            
            items = []
            for item in result.get("value", []):
                drive_item = DriveItem(
                    name=item.get("name", ""),
                    item_id=item.get("id", ""),
                    is_folder="folder" in item,
                    size=item.get("size", 0),
                    created_datetime=item.get("createdDateTime"),
                    modified_datetime=item.get("lastModifiedDateTime"),
                    web_url=item.get("webUrl")
                )
                items.append(drive_item)
            
            return items
        except Exception as e:
            logger.error(f"列出項目失敗: {str(e)}")
            return []
    
    async def search_files(
        self,
        user_id: str = "me",
        search_query: str = "",
        count: int = 10
    ) -> List[DriveItem]:
        """
        搜尋檔案
        
        Args:
            user_id: 使用者 ID
            search_query: 搜尋查詢
            count: 返回的結果數量
            
        Returns:
            搜尋結果清單
        """
        try:
            result = await self.graph_service.graph_client.get(
                f"/users/{user_id}/drive/root/search(q='{search_query}')",
                params={"$top": count}
            )
            
            items = []
            for item in result.get("value", []):
                drive_item = DriveItem(
                    name=item.get("name", ""),
                    item_id=item.get("id", ""),
                    is_folder="folder" in item,
                    size=item.get("size", 0),
                    web_url=item.get("webUrl")
                )
                items.append(drive_item)
            
            return items
        except Exception as e:
            logger.error(f"搜尋檔案失敗: {str(e)}")
            return []
    
    async def create_folder(
        self,
        folder_name: str,
        user_id: str = "me",
        parent_folder_id: str = "root"
    ) -> Optional[str]:
        """
        建立資料夾
        
        Args:
            folder_name: 資料夾名稱
            user_id: 使用者 ID
            parent_folder_id: 父資料夾 ID
            
        Returns:
            新建資料夾的 ID，失敗返回 None
        """
        try:
            body = {
                "name": folder_name,
                "folder": {},
                "@microsoft.graph.conflictBehavior": "rename"
            }
            
            result = await self.graph_service.graph_client.post(
                f"/users/{user_id}/drive/items/{parent_folder_id}/children",
                json=body
            )
            
            logger.info(f"已建立資料夾: {folder_name}")
            return result.get("id")
        except Exception as e:
            logger.error(f"建立資料夾失敗: {str(e)}")
            return None
    
    async def get_file_metadata(
        self,
        user_id: str = "me",
        item_id: str = ""
    ) -> Dict[str, Any]:
        """
        取得檔案中繼資料
        
        Args:
            user_id: 使用者 ID
            item_id: 項目 ID
            
        Returns:
            檔案中繼資料
        """
        try:
            result = await self.graph_service.graph_client.get(
                f"/users/{user_id}/drive/items/{item_id}"
            )
            
            return result
        except Exception as e:
            logger.error(f"取得檔案中繼資料失敗: {str(e)}")
            return {"error": str(e)}
    
    async def get_file_sharing_info(
        self,
        user_id: str = "me",
        item_id: str = ""
    ) -> Dict[str, Any]:
        """
        取得檔案共享資訊
        
        Args:
            user_id: 使用者 ID
            item_id: 項目 ID
            
        Returns:
            共享資訊
        """
        try:
            result = await self.graph_service.graph_client.get(
                f"/users/{user_id}/drive/items/{item_id}/permissions"
            )
            
            return result
        except Exception as e:
            logger.error(f"取得共享資訊失敗: {str(e)}")
            return {"error": str(e)}
