"""
서비스 모듈

AI 워크플로우 오케스트레이터의 핵심 서비스를 제공합니다.

플러그인 아키텍처:
    - BaseIntegrationClient: 모든 연동 클라이언트의 추상 베이스 클래스
    - IntegrationRegistry: 클라이언트 레지스트리 (싱글톤)
    - @register_integration: 클라이언트 등록 데코레이터

새 시스템 추가 방법:
    ```python
    from services.base import BaseIntegrationClient, register_integration
    
    @register_integration("MySystem", MySystemConfig)
    class MySystemClient(BaseIntegrationClient):
        system_name = "MySystem"
        
        def test_connection(self) -> IntegrationResult:
            ...
        
        def execute(self, action: str, context: dict) -> IntegrationResult:
            ...
    ```
"""

from .ai_analyzer import analyze_email
from .workflow_generator import generate_workflow
from .automation_engine import AutomationEngine, ExecutionStatus, WorkflowContext
from .config import IntegrationConfig, JiraConfig, SlackConfig, EmailConfig

from .base import (
    BaseIntegrationClient,
    BaseConfig,
    IntegrationResult,
    IntegrationRegistry,
    register_integration
)

from .integrations import JiraClient, SlackClient, EmailClient

__all__ = [
    "analyze_email",
    "generate_workflow",
    "AutomationEngine",
    "ExecutionStatus",
    "WorkflowContext",
    "IntegrationConfig",
    "JiraConfig",
    "SlackConfig",
    "EmailConfig",
    "BaseIntegrationClient",
    "BaseConfig",
    "IntegrationResult",
    "IntegrationRegistry",
    "register_integration",
    "JiraClient",
    "SlackClient",
    "EmailClient",
]
