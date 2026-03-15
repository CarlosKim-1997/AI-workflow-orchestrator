"""
자동화 엔진 서비스

플러그인 아키텍처를 사용하여 엔터프라이즈 시스템을 통합합니다.
IntegrationRegistry를 통해 등록된 모든 시스템을 자동으로 지원합니다.
"""

import time
import random
from datetime import date, timedelta
from dataclasses import dataclass
from enum import Enum
from typing import Callable, Optional, Any

from .workflow_generator import WorkflowStep
from .config import IntegrationConfig
from .base import IntegrationRegistry, IntegrationResult


class ExecutionStatus(Enum):
    PENDING = "대기중"
    RUNNING = "실행중"
    SUCCESS = "성공"
    FAILED = "실패"


@dataclass
class ExecutionResult:
    """단일 워크플로우 단계 실행 결과입니다."""
    step: WorkflowStep
    status: ExecutionStatus
    message: str
    duration_ms: int
    data: Optional[dict] = None


@dataclass
class WorkflowContext:
    """워크플로우 실행 컨텍스트 (분석 결과 등 공유 데이터)"""
    intent: str = ""
    department: str = ""
    priority: str = ""
    email_content: str = ""
    jira_ticket_id: Optional[str] = None
    
    def to_dict(self) -> dict:
        """컨텍스트를 딕셔너리로 변환합니다."""
        return {
            "intent": self.intent,
            "department": self.department,
            "priority": self.priority,
            "email_content": self.email_content,
            "ticket_id": self.jira_ticket_id,
            "title": f"[AI 워크플로우] {self.intent}",
            "summary": f"[AI 워크플로우] {self.intent}",
            "description": f"""AI 워크플로우 오케스트레이터에서 자동 생성

의도: {self.intent}
담당 부서: {self.department}
우선순위: {self.priority}

원본 이메일 내용:
{self.email_content[:500] if self.email_content else '(없음)'}
""",
            "workflow_steps": ["워크플로우가 자동으로 실행되었습니다"],
        }


class AutomationEngine:
    """
    워크플로우 단계를 실행하여 엔터프라이즈 자동화를 수행합니다.
    
    플러그인 아키텍처:
    - IntegrationRegistry에 등록된 모든 시스템을 자동으로 지원
    - 새로운 시스템 추가 시 엔진 코드 수정 불필요
    - 시뮬레이션 모드와 실제 연동 모드 지원
    
    새 시스템 추가 방법:
    1. BaseIntegrationClient를 상속하여 클라이언트 구현
    2. @register_integration 데코레이터로 등록
    3. 자동으로 AutomationEngine에서 사용 가능
    """
    
    def __init__(
        self,
        failure_rate: float = 0.0,
        config: Optional[IntegrationConfig] = None
    ):
        self.failure_rate = failure_rate
        self.config = config or IntegrationConfig()
        self.context = WorkflowContext()
        
        self._clients: dict[str, Any] = {}
        self._initialize_clients()
        
        self._simulation_handlers: dict[str, Callable] = {
            "Jira": self._simulate_jira,
            "Slack": self._simulate_slack,
            "Email": self._simulate_email,
            "SAP": self._simulate_sap,
            "StatusPage": self._simulate_statuspage,
            "Workday": self._simulate_workday,
            "CPQ": self._simulate_cpq,
            "ServiceNow": self._simulate_servicenow,
            "CoreBanking": self._simulate_corebanking,
            "FDS": self._simulate_fds,
        }
    
    def _initialize_clients(self):
        """등록된 시스템의 클라이언트를 초기화합니다."""
        system_config_map = {
            "Jira": self.config.jira,
            "Slack": self.config.slack,
            "Email": self.config.email,
        }
        
        for system_name, system_config in system_config_map.items():
            if system_config is None:
                continue
            if system_config and system_config.is_valid():
                client = IntegrationRegistry.get_client(system_name, system_config)
                if client:
                    self._clients[system_name] = client
                    print(f"[AutomationEngine] '{system_name}' 클라이언트 초기화됨")
    
    def register_client(self, system_name: str, config: Any):
        """
        런타임에 새 클라이언트를 등록합니다.
        
        Args:
            system_name: 시스템 이름
            config: 시스템 설정 객체
        """
        if IntegrationRegistry.is_registered(system_name):
            client = IntegrationRegistry.get_client(system_name, config)
            if client:
                self._clients[system_name] = client
                print(f"[AutomationEngine] '{system_name}' 클라이언트 동적 등록됨")
    
    def get_available_systems(self) -> dict[str, bool]:
        """
        사용 가능한 시스템과 활성화 상태를 반환합니다.
        
        Returns:
            {시스템명: 활성화여부} 딕셔너리
        """
        registered = IntegrationRegistry.get_registered_systems()
        return {
            system: system in self._clients
            for system in registered
        }
    
    def set_context(
        self,
        intent: str,
        department: str,
        priority: str,
        email_content: str = ""
    ):
        """워크플로우 컨텍스트를 설정합니다."""
        self.context = WorkflowContext(
            intent=intent,
            department=department,
            priority=priority,
            email_content=email_content
        )
    
    def is_simulation_mode(self) -> bool:
        """시뮬레이션 모드인지 확인합니다."""
        return self.config.simulation_mode or not self.config.has_any_integration()
    
    def execute_step(self, step: WorkflowStep) -> ExecutionResult:
        """
        단일 워크플로우 단계를 실행합니다.
        
        플러그인 시스템을 통해:
        1. 등록된 클라이언트가 있으면 실제 연동
        2. 없으면 시뮬레이션 모드로 실행
        """
        start_time = time.time()
        
        client = self._clients.get(step.system) if not self.config.simulation_mode else None
        
        if client:
            try:
                context_dict = self.context.to_dict()
                context_dict["action"] = step.action
                action_type = self._get_action_type(step)
                if action_type == "create_schedule":
                    context_dict.setdefault("title", step.action or step.description)
                    context_dict.setdefault("due_date", (date.today() + timedelta(days=7)).strftime("%Y-%m-%d"))
                    context_dict.setdefault("description", step.description)
                
                result = client.execute(action_type, context_dict)
                duration_ms = int((time.time() - start_time) * 1000)
                
                if result.data and result.data.get("key"):
                    self.context.jira_ticket_id = result.data["key"]
                
                return ExecutionResult(
                    step=step,
                    status=ExecutionStatus.SUCCESS if result.success else ExecutionStatus.FAILED,
                    message=result.message,
                    duration_ms=duration_ms,
                    data=result.data
                )
            except Exception as e:
                duration_ms = int((time.time() - start_time) * 1000)
                return ExecutionResult(
                    step=step,
                    status=ExecutionStatus.FAILED,
                    message=f"실행 오류: {str(e)}",
                    duration_ms=duration_ms
                )
        else:
            if random.random() < self.failure_rate:
                duration_ms = int((time.time() - start_time) * 1000) + random.randint(100, 300)
                return ExecutionResult(
                    step=step,
                    status=ExecutionStatus.FAILED,
                    message=f"{step.system} 연결 시간 초과 (시뮬레이션)",
                    duration_ms=duration_ms
                )
            
            handler = self._simulation_handlers.get(step.system, self._simulate_generic)
            
            try:
                result = handler(step)
                duration_ms = int((time.time() - start_time) * 1000)
                return ExecutionResult(
                    step=step,
                    status=ExecutionStatus.SUCCESS,
                    message=result,
                    duration_ms=duration_ms
                )
            except Exception as e:
                duration_ms = int((time.time() - start_time) * 1000)
                return ExecutionResult(
                    step=step,
                    status=ExecutionStatus.FAILED,
                    message=f"시뮬레이션 오류: {str(e)}",
                    duration_ms=duration_ms
                )
    
    def _get_action_type(self, step: WorkflowStep) -> str:
        """워크플로우 단계에서 액션 타입을 추출합니다. 시스템별로 지원 액션을 매핑합니다."""
        action_lower = step.action.lower()
        system = step.system.lower()
        
        # Jira: 티켓/이슈 생성, 일정(기한) 이슈 생성
        if "jira" in system:
            if any(k in action_lower for k in ["일정", "예약", "미팅", "킥오프", "후속 설정", "event", "schedule", "meeting"]):
                return "create_schedule"
            if any(k in action_lower for k in ["티켓", "이슈", "생성", "구성", "할당", "등록", "ticket", "issue", "create", "task"]):
                return "create_ticket"
            return "create_ticket"  # Jira 기본 동작
        # Slack: 알림, 메시지, 전송, 호출, 연계
        if "slack" in system:
            if any(k in action_lower for k in ["알림", "메시지", "전송", "호출", "연계", "notify", "message", "send", "channel"]):
                return "send_notification"
            return "send_notification"  # Slack 기본 동작
        # Email: 이메일 발송, 응답, 안내, 연락, 확인, 보고
        if "email" in system:
            if any(k in action_lower for k in ["이메일", "발송", "응답", "안내", "연락", "확인", "보고", "email", "send"]):
                return "send_notification"
            return "send_notification"  # Email 기본 동작
        # ServiceNow: 인시던트, 변경요청, 등록, 분석
        if "servicenow" in system:
            if any(k in action_lower for k in ["변경", "change"]):
                return "create_change_request"
            if any(k in action_lower for k in ["인시던트", "incident", "등록", "영향도"]):
                return "create_incident"
            return "create_incident"
        # SAP: 구매, 재고, 문서
        if "sap" in system:
            if any(k in action_lower for k in ["구매요청", "구매 주문", "pr", "po"]):
                return "create_purchase_request"
            if any(k in action_lower for k in ["재고", "inventory"]):
                return "check_inventory"
            return "create_purchase_request"
        # 공통 키워드 (시스템 무관)
        if any(k in action_lower for k in ["티켓", "이슈", "생성", "ticket", "create"]):
            return "create_ticket"
        if any(k in action_lower for k in ["알림", "메시지", "전송", "notify", "message"]):
            return "send_notification"
        if any(k in action_lower for k in ["이메일", "발송", "email", "send"]):
            return "send_email"
        return "execute"
    
    def execute_workflow(
        self,
        steps: list[WorkflowStep],
        progress_callback: Callable | None = None
    ) -> list[ExecutionResult]:
        """워크플로우의 모든 단계를 순차적으로 실행합니다."""
        results = []
        
        for step in steps:
            result = self.execute_step(step)
            results.append(result)
            
            if progress_callback:
                progress_callback(result)
            
            if result.status == ExecutionStatus.FAILED:
                for remaining_step in steps[step.order:]:
                    results.append(ExecutionResult(
                        step=remaining_step,
                        status=ExecutionStatus.PENDING,
                        message="이전 단계 실패로 건너뜀",
                        duration_ms=0
                    ))
                break
        
        return results
    
    def _simulate_jira(self, step: WorkflowStep) -> str:
        time.sleep(random.uniform(0.3, 0.7))
        ticket_id = f"TICKET-{random.randint(1000, 9999)}"
        return f"Jira: {step.action} 완료. 티켓 ID: {ticket_id} (시뮬레이션)"
    
    def _simulate_slack(self, step: WorkflowStep) -> str:
        time.sleep(random.uniform(0.2, 0.4))
        return f"Slack: 채널에 메시지 전송 완료 (시뮬레이션)"
    
    def _simulate_email(self, step: WorkflowStep) -> str:
        time.sleep(random.uniform(0.2, 0.5))
        return f"Email: 메시지 발송 대기열에 추가됨 (시뮬레이션)"
    
    def _simulate_sap(self, step: WorkflowStep) -> str:
        time.sleep(random.uniform(0.5, 1.0))
        doc_id = f"SAP-DOC-{random.randint(10000, 99999)}"
        return f"SAP: 문서 등록 완료. 문서 ID: {doc_id} (시뮬레이션)"
    
    def _simulate_statuspage(self, step: WorkflowStep) -> str:
        time.sleep(random.uniform(0.3, 0.5))
        return f"StatusPage: 상태 확인 완료 - 모든 시스템 정상 (시뮬레이션)"
    
    def _simulate_workday(self, step: WorkflowStep) -> str:
        time.sleep(random.uniform(0.4, 0.7))
        case_id = f"HR-{random.randint(1000, 9999)}"
        return f"Workday: HR 케이스 생성 완료. 케이스 ID: {case_id} (시뮬레이션)"
    
    def _simulate_cpq(self, step: WorkflowStep) -> str:
        time.sleep(random.uniform(0.5, 0.8))
        quote_id = f"Q-{random.randint(10000, 99999)}"
        return f"CPQ: 견적 생성 시작됨. 견적 ID: {quote_id} (시뮬레이션)"
    
    def _simulate_servicenow(self, step: WorkflowStep) -> str:
        time.sleep(random.uniform(0.4, 0.7))
        incident_id = f"INC{random.randint(100000, 999999)}"
        return f"ServiceNow: 인시던트 생성 완료. ID: {incident_id} (시뮬레이션)"
    
    def _simulate_corebanking(self, step: WorkflowStep) -> str:
        time.sleep(random.uniform(0.3, 0.6))
        return f"CoreBanking: 트랜잭션 처리 완료 (시뮬레이션)"
    
    def _simulate_fds(self, step: WorkflowStep) -> str:
        time.sleep(random.uniform(0.2, 0.4))
        return f"FDS: 이상거래 모니터링 등록 완료 (시뮬레이션)"
    
    def _simulate_generic(self, step: WorkflowStep) -> str:
        time.sleep(random.uniform(0.3, 0.6))
        return f"{step.system}: {step.action} 성공적으로 완료 (시뮬레이션)"
