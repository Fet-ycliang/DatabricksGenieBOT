#!/usr/bin/env python3
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import os
from dotenv import load_dotenv

# 載入 .env 檔案（僅用於本地測試）
load_dotenv()

""" Bot Configuration """


class DefaultConfig:
    """Bot Configuration"""

    # Port configuration
    PORT = int(os.getenv("PORT", "3978"))
    
    # Bot Framework credentials - use environment variables with fallbacks for local testing
    APP_ID = os.getenv("APP_ID", "")  # Empty for emulator testing, set for production
    APP_PASSWORD = os.getenv("APP_PASSWORD", "")  # Empty for emulator testing, set for production
    APP_TYPE = os.getenv("APP_TYPE", "SingleTenant")  # "SingleTenant" or "MultiTenant"
    APP_TENANTID = os.getenv("APP_TENANTID", "")
    

    
    # Databricks configuration - use environment variables with fallbacks
    DATABRICKS_SPACE_ID = os.getenv("DATABRICKS_SPACE_ID", "")
    DATABRICKS_HOST = os.getenv("DATABRICKS_HOST", "")
    DATABRICKS_TOKEN = os.getenv("DATABRICKS_TOKEN", "")
    
    # Validate required environment variables (skip validation for emulator testing)
    if not DATABRICKS_TOKEN and APP_ID:  # Only validate if not using emulator (APP_ID is set)
        raise ValueError("DATABRICKS_TOKEN environment variable is required")
    
    # Sample questions configuration - customize these for your Genie space
    # Use semicolon (;) as delimiter for multiple questions
    SAMPLE_QUESTIONS = os.getenv(
        "SAMPLE_QUESTIONS",
        "這個 Genie 空間有哪些可用資料？;"
        "能否解釋一下這些資料集？;"
        "我應該問什麼問題？"
    )
    
    # Admin contact email - shown to users in the info command
    ADMIN_CONTACT_EMAIL = os.getenv("ADMIN_CONTACT_EMAIL", "admin@company.com")
    
    # Timezone configuration for user-facing timestamps
    TIMEZONE = os.getenv("TIMEZONE", "Asia/Taipei")
    
    # Microsoft Graph API OAuth 設定
    # 在 Azure Portal 的 Bot Channels Registration 中設定 OAuth Connection
    OAUTH_CONNECTION_NAME = os.getenv("OAUTH_CONNECTION_NAME", "")
    
    # 是否啟用自動從 Graph API 取得使用者資訊
    # 如果設為 False，則會要求使用者手動輸入 email
    ENABLE_GRAPH_API_AUTO_LOGIN = os.getenv("ENABLE_GRAPH_API_AUTO_LOGIN", "False").lower() == "true"
    
    # Feedback settings
    ENABLE_FEEDBACK_CARDS = os.getenv("ENABLE_FEEDBACK_CARDS", "True").lower() == "true"
    ENABLE_GENIE_FEEDBACK_API = os.getenv("ENABLE_GENIE_FEEDBACK_API", "True").lower() == "true"