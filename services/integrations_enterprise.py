"""
엔터프라이즈 시스템 연동 플러그인 (SAP, ServiceNow 시연용 스텁)
"""

from dataclasses import dataclass
from typing import Optional

from .base import (
    BaseIntegrationClient,
    BaseConfig,
    IntegrationResult,
    register_integration
)


# =============================================================================
# SAP 연동
# =============================================================================

@dataclass
class SAPConfig(BaseConfig):
    """SAP 연동 설정"""
    enabled: bool = False
    server_url: str = ""
    client_id: str = ""
    client_secret: str = ""
    company_code: str = ""
    
    def is_valid(self) -> bool:
        return bool(
            self.enabled and
            self.server_url and
            self.client_id and
            self.client_secret
        )
    
    def get_validation_errors(self) -> list[str]:
        errors = []
        if not self.server_url:
            errors.append("SAP 서버 URL이 필요합니다")
        if not self.client_id:
            errors.append("SAP 클라이언트 ID가 필요합니다")
        if not self.client_secret:
            errors.append("SAP 클라이언트 시크릿이 필요합니다")
        return errors


@register_integration("SAP", SAPConfig)
class SAPClient(BaseIntegrationClient):
    """
    SAP ERP 연동 클라이언트
    
    지원 기능:
    - 구매 요청(PR) 생성
    - 구매 주문(PO) 생성
    - 재고 확인
    - 문서 상태 조회
    
    실제 구현 시 참고:
    - SAP RFC/BAPI 호출
    - SAP OData API
    - SAP Business API Hub
    """
    
    system_name = "SAP"
    
    def __init__(self, config: SAPConfig):
        self.config = config
        self.server_url = config.server_url if config else ""
        self.company_code = config.company_code if config else "1000"
    
    @classmethod
    def get_supported_actions(cls) -> list[str]:
        return [
            "create_purchase_request",
            "create_purchase_order",
            "check_inventory",
            "get_document_status",
            "create_material_document",
            "test_connection"
        ]
    
    def test_connection(self) -> IntegrationResult:
        """SAP 연결을 테스트합니다."""
        if not self.config or not self.config.is_valid():
            return IntegrationResult(
                success=False,
                message="SAP 설정이 완료되지 않았습니다"
            )
        
        return IntegrationResult(
            success=True,
            message=f"SAP 연결 성공: {self.server_url}",
            data={"company_code": self.company_code}
        )
    
    def execute(self, action: str, context: dict) -> IntegrationResult:
        """SAP 액션을 실행합니다."""
        if action == "create_purchase_request":
            return self._create_purchase_request(context)
        elif action == "create_purchase_order":
            return self._create_purchase_order(context)
        elif action == "check_inventory":
            return self._check_inventory(context)
        elif action == "create_material_document":
            return self._create_material_document(context)
        elif action == "test_connection":
            return self.test_connection()
        else:
            return self._execute_generic(action, context)
    
    def _create_purchase_request(self, context: dict) -> IntegrationResult:
        """구매 요청을 생성합니다."""
        pr_number = f"PR-{self.company_code}-{hash(context.get('intent', ''))%10000:04d}"
        return IntegrationResult(
            success=True,
            message=f"SAP 구매 요청 생성 완료: {pr_number}",
            data={
                "pr_number": pr_number,
                "company_code": self.company_code,
                "status": "Created"
            }
        )
    
    def _create_purchase_order(self, context: dict) -> IntegrationResult:
        """구매 주문을 생성합니다."""
        po_number = f"PO-{self.company_code}-{hash(context.get('intent', ''))%10000:04d}"
        return IntegrationResult(
            success=True,
            message=f"SAP 구매 주문 생성 완료: {po_number}",
            data={
                "po_number": po_number,
                "company_code": self.company_code,
                "status": "Created"
            }
        )
    
    def _check_inventory(self, context: dict) -> IntegrationResult:
        """재고를 확인합니다."""
        return IntegrationResult(
            success=True,
            message="SAP 재고 확인 완료",
            data={
                "available_qty": 100,
                "reserved_qty": 20,
                "plant": self.company_code
            }
        )
    
    def _create_material_document(self, context: dict) -> IntegrationResult:
        """자재 문서를 생성합니다."""
        doc_number = f"MAT-{hash(context.get('intent', ''))%100000:05d}"
        return IntegrationResult(
            success=True,
            message=f"SAP 자재 문서 생성 완료: {doc_number}",
            data={"document_number": doc_number}
        )
    
    def _execute_generic(self, action: str, context: dict) -> IntegrationResult:
        """일반 SAP 액션을 실행합니다."""
        return IntegrationResult(
            success=True,
            message=f"SAP {action} 실행 완료",
            data={"action": action}
        )


# =============================================================================
# ServiceNow 연동
# =============================================================================

@dataclass
class ServiceNowConfig(BaseConfig):
    """ServiceNow 연동 설정"""
    enabled: bool = False
    instance_url: str = ""
    username: str = ""
    password: str = ""
    
    def is_valid(self) -> bool:
        return bool(
            self.enabled and
            self.instance_url and
            self.username and
            self.password
        )
    
    def get_validation_errors(self) -> list[str]:
        errors = []
        if not self.instance_url:
            errors.append("ServiceNow 인스턴스 URL이 필요합니다")
        if not self.username:
            errors.append("ServiceNow 사용자명이 필요합니다")
        if not self.password:
            errors.append("ServiceNow 비밀번호가 필요합니다")
        return errors


@register_integration("ServiceNow", ServiceNowConfig)
class ServiceNowClient(BaseIntegrationClient):
    """
    ServiceNow ITSM 연동 클라이언트
    
    지원 기능:
    - Incident 생성/업데이트
    - Change Request 생성
    - Problem 생성
    - CMDB 조회
    
    실제 구현 시 참고:
    - ServiceNow REST API
    - Table API
    - Scripted REST API
    """
    
    system_name = "ServiceNow"
    
    def __init__(self, config: ServiceNowConfig):
        self.config = config
        self.instance_url = config.instance_url if config else ""
    
    @classmethod
    def get_supported_actions(cls) -> list[str]:
        return [
            "create_incident",
            "create_change_request",
            "create_problem",
            "update_incident",
            "get_cmdb_ci",
            "test_connection"
        ]
    
    def test_connection(self) -> IntegrationResult:
        if not self.config or not self.config.is_valid():
            return IntegrationResult(
                success=False,
                message="ServiceNow 설정이 완료되지 않았습니다"
            )
        
        return IntegrationResult(
            success=True,
            message=f"ServiceNow 연결 성공: {self.instance_url}"
        )
    
    def execute(self, action: str, context: dict) -> IntegrationResult:
        if action == "create_incident":
            return self._create_incident(context)
        elif action == "create_change_request":
            return self._create_change_request(context)
        elif action == "test_connection":
            return self.test_connection()
        elif action == "execute":
            return self._create_incident(context)
        else:
            return IntegrationResult(
                success=True,
                message=f"ServiceNow {action} 실행 완료"
            )
    
    def _create_incident(self, context: dict) -> IntegrationResult:
        incident_number = f"INC{hash(context.get('intent', ''))%10000000:07d}"
        priority_map = {"긴급": "1", "높음": "2", "보통": "3", "낮음": "4"}
        priority = priority_map.get(context.get("priority", "보통"), "3")
        
        return IntegrationResult(
            success=True,
            message=f"ServiceNow Incident 생성 완료: {incident_number}",
            data={
                "number": incident_number,
                "priority": priority,
                "state": "New",
                "short_description": context.get("title", "")
            }
        )
    
    def _create_change_request(self, context: dict) -> IntegrationResult:
        change_number = f"CHG{hash(context.get('intent', ''))%10000000:07d}"
        return IntegrationResult(
            success=True,
            message=f"ServiceNow Change Request 생성 완료: {change_number}",
            data={
                "number": change_number,
                "state": "Draft",
                "type": "Standard"
            }
        )


# =============================================================================
# 시스템 등록 확인
# =============================================================================

def get_enterprise_systems() -> list[str]:
    """등록된 엔터프라이즈 시스템 목록을 반환합니다."""
    from .base import IntegrationRegistry
    return IntegrationRegistry.get_registered_systems()
