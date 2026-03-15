"""
워크플로우 생성기 서비스

분석된 이메일 의도와 할당된 부서를 기반으로
엔터프라이즈 워크플로우 단계를 생성합니다.
"""

from dataclasses import dataclass


@dataclass
class WorkflowStep:
    """워크플로우의 단일 단계를 나타냅니다."""
    order: int
    action: str
    system: str
    description: str


WORKFLOW_TEMPLATES = {
    "card_lost": {
        "keywords": ["분실", "카드", "도난", "정지", "lost", "card", "stolen"],
        "steps": [
            WorkflowStep(1, "긴급 티켓 생성", "Jira", "긴급 우선순위로 티켓 생성"),
            WorkflowStep(2, "카드 정지 요청", "CoreBanking", "코어뱅킹 시스템에 카드 정지 요청"),
            WorkflowStep(3, "사기팀 알림", "Slack", "#fraud-alert 채널에 긴급 알림"),
            WorkflowStep(4, "부정사용 모니터링", "FDS", "실시간 부정거래 모니터링 강화"),
            WorkflowStep(5, "고객 확인 연락", "Email", "카드 정지 확인 이메일 발송"),
        ]
    },
    "urgent_procurement": {
        "keywords": ["긴급", "발주", "부품", "재고", "부족", "urgent", "procurement", "inventory", "shortage"],
        "steps": [
            WorkflowStep(1, "긴급 구매요청 생성", "SAP", "SAP에 긴급 PR 생성"),
            WorkflowStep(2, "재고 현황 조회", "SAP", "현재 재고 및 리드타임 확인"),
            WorkflowStep(3, "구매팀 긴급 알림", "Slack", "#procurement-urgent 채널 알림"),
            WorkflowStep(4, "승인 요청", "Email", "긴급 결재권자에게 승인 요청"),
            WorkflowStep(5, "공급업체 연락", "Email", "우선순위 공급업체에 납기 확인"),
        ]
    },
    "rfp_consulting": {
        "keywords": ["rfp", "제안", "컨설팅", "프로젝트", "consulting", "proposal", "도입"],
        "steps": [
            WorkflowStep(1, "영업 기회 등록", "Salesforce", "Opportunity 생성"),
            WorkflowStep(2, "제안팀 구성", "Jira", "제안서 작성 태스크 생성"),
            WorkflowStep(3, "파트너 알림", "Slack", "#sales-opportunities 채널 알림"),
            WorkflowStep(4, "킥오프 일정", "Jira", "Jira에 제안 킥오프 미팅 일정 이슈 생성"),
            WorkflowStep(5, "고객 응답", "Email", "RFP 수령 확인 이메일 발송"),
        ]
    },
    "it_incident": {
        "keywords": ["장애", "시스템", "접속", "불가", "incident", "outage", "down", "error", "erp"],
        "steps": [
            WorkflowStep(1, "인시던트 등록", "ServiceNow", "P1/P2 인시던트 생성"),
            WorkflowStep(2, "영향도 분석", "ServiceNow", "영향받는 서비스 및 사용자 파악"),
            WorkflowStep(3, "긴급 대응팀 호출", "Slack", "#incident-war-room 채널 생성"),
            WorkflowStep(4, "경영진 보고", "Email", "CIO/IT임원에게 상황 보고"),
            WorkflowStep(5, "상태 페이지 업데이트", "StatusPage", "내부 상태 페이지 업데이트"),
        ]
    },
    "hr_retirement": {
        "keywords": ["퇴직금", "정산", "퇴직", "retirement", "severance", "pension"],
        "steps": [
            WorkflowStep(1, "HR 케이스 생성", "Workday", "퇴직금 정산 요청 케이스"),
            WorkflowStep(2, "자격 검증", "Workday", "근속연수 및 정산 자격 확인"),
            WorkflowStep(3, "HR팀 할당", "Jira", "담당 HR BP에게 할당"),
            WorkflowStep(4, "재무팀 연계", "Slack", "#hr-finance 채널에 알림"),
            WorkflowStep(5, "신청자 안내", "Email", "필요 서류 및 절차 안내 이메일"),
        ]
    },
    "refund": {
        "keywords": ["refund", "return", "money back", "damaged", "broken", "defective", "환불", "반품", "파손", "손상", "고장"],
        "steps": [
            WorkflowStep(1, "지원 티켓 생성", "Jira", "환불 요청에 대한 새 지원 티켓 생성"),
            WorkflowStep(2, "팀에 할당", "Jira", "고객 지원팀에 티켓 할당"),
            WorkflowStep(3, "알림 전송", "Slack", "#고객지원 채널에 알림"),
            WorkflowStep(4, "CRM 업데이트", "Salesforce", "CRM 시스템에 케이스 기록"),
            WorkflowStep(5, "확인 이메일 발송", "Email", "고객에게 접수 확인 이메일 발송"),
        ]
    },
    "technical": {
        "keywords": ["bug", "error", "crash", "not working", "technical", "problem", "broken app", "버그", "충돌", "작동안함"],
        "steps": [
            WorkflowStep(1, "기술 티켓 생성", "Jira", "기술 지원 티켓 생성"),
            WorkflowStep(2, "엔지니어링팀 할당", "Jira", "엔지니어링팀으로 라우팅"),
            WorkflowStep(3, "로그 요청", "Email", "고객에게 자동 로그 요청 발송"),
            WorkflowStep(4, "DevOps 알림", "Slack", "#devops 채널에 알림"),
            WorkflowStep(5, "상태 페이지 업데이트", "StatusPage", "서비스 상태 확인 및 필요시 업데이트"),
        ]
    },
    "invoice": {
        "keywords": ["invoice", "payment", "billing", "charge", "receipt", "finance", "accounting", "송장", "결제", "청구", "영수증", "재무", "회계", "대금"],
        "steps": [
            WorkflowStep(1, "송장 등록", "SAP", "재무 시스템에 송장 등록"),
            WorkflowStep(2, "재무팀 할당", "Jira", "재무팀 업무 생성"),
            WorkflowStep(3, "회계팀 알림", "Slack", "#회계 채널에 알림"),
            WorkflowStep(4, "검토 일정 예약", "Jira", "Jira에 결제 검토 회의 일정 이슈 생성"),
            WorkflowStep(5, "확인 이메일 발송", "Email", "발신자에게 수령 확인 발송"),
        ]
    },
    "sales": {
        "keywords": ["quote", "pricing", "purchase", "buy", "order", "deal", "contract", "proposal", "견적", "가격", "구매", "주문", "계약"],
        "steps": [
            WorkflowStep(1, "리드 생성", "Salesforce", "영업 리드 생성 또는 업데이트"),
            WorkflowStep(2, "영업 담당자 배정", "Salesforce", "적합한 영업 담당자에게 라우팅"),
            WorkflowStep(3, "영업팀 알림", "Slack", "#영업 채널에 알림"),
            WorkflowStep(4, "후속 일정 예약", "Jira", "Jira에 고객 후속 통화 일정 이슈 생성"),
            WorkflowStep(5, "견적서 생성", "CPQ", "견적 생성 프로세스 시작"),
        ]
    },
    "hr": {
        "keywords": ["employee", "hiring", "job", "application", "leave", "vacation", "benefits", "payroll", "직원", "채용", "지원", "휴가", "복리후생", "급여"],
        "steps": [
            WorkflowStep(1, "HR 티켓 생성", "Workday", "HR 케이스 생성"),
            WorkflowStep(2, "HR팀 할당", "Workday", "HR 전문가에게 라우팅"),
            WorkflowStep(3, "HR팀 알림", "Slack", "#hr 채널에 알림"),
            WorkflowStep(4, "기록 업데이트", "Workday", "필요시 직원 기록 업데이트"),
            WorkflowStep(5, "응답 발송", "Email", "요청자에게 응답 발송"),
        ]
    },
    "general": {
        "keywords": [],
        "steps": [
            WorkflowStep(1, "티켓 생성", "Jira", "일반 문의 티켓 생성"),
            WorkflowStep(2, "요청 분류", "Jira", "요청 분석 및 분류"),
            WorkflowStep(3, "팀 할당", "Jira", "적합한 팀으로 라우팅"),
            WorkflowStep(4, "접수 확인 발송", "Email", "발신자에게 접수 확인 발송"),
            WorkflowStep(5, "후속 설정", "Jira", "Jira에 후속 알림 일정 이슈 생성"),
        ]
    }
}

DEPARTMENT_MAPPING = {
    "Customer Support": ["refund", "card_lost", "general"],
    "고객 지원": ["refund", "card_lost", "general"],
    "고객센터": ["refund", "card_lost", "general"],
    "Engineering": ["technical", "it_incident"],
    "엔지니어링": ["technical", "it_incident"],
    "IT": ["technical", "it_incident"],
    "IT운영": ["it_incident"],
    "Finance": ["invoice"],
    "재무": ["invoice"],
    "회계": ["invoice"],
    "Procurement": ["urgent_procurement"],
    "구매": ["urgent_procurement"],
    "구매팀": ["urgent_procurement"],
    "Sales": ["sales", "rfp_consulting"],
    "영업": ["sales", "rfp_consulting"],
    "컨설팅": ["rfp_consulting"],
    "HR": ["hr", "hr_retirement"],
    "인사": ["hr", "hr_retirement"],
    "인사팀": ["hr", "hr_retirement"],
}


def _detect_workflow_type(intent: str, department: str) -> str:
    """의도와 부서를 기반으로 워크플로우 유형을 결정합니다."""
    intent_lower = intent.lower()
    
    for workflow_type, config in WORKFLOW_TEMPLATES.items():
        if workflow_type == "general":
            continue
        for keyword in config["keywords"]:
            if keyword in intent_lower:
                return workflow_type
    
    for dept, workflow_types in DEPARTMENT_MAPPING.items():
        if dept.lower() in department.lower():
            return workflow_types[0]
    
    return "general"


def generate_workflow(intent: str, department: str) -> list[WorkflowStep]:
    """
    감지된 의도와 부서를 기반으로 워크플로우를 생성합니다.
    
    Args:
        intent: AI 분석에서 분류된 의도
        department: AI 분석에서 할당된 부서
    
    Returns:
        생성된 워크플로우를 나타내는 WorkflowStep 객체 리스트
    """
    workflow_type = _detect_workflow_type(intent, department)
    template = WORKFLOW_TEMPLATES.get(workflow_type, WORKFLOW_TEMPLATES["general"])
    
    return template["steps"].copy()


def get_workflow_summary(steps: list[WorkflowStep]) -> str:
    """워크플로우의 사람이 읽을 수 있는 요약을 생성합니다."""
    lines = [f"{step.order}. {step.action} ({step.system})" for step in steps]
    return "\n".join(lines)
