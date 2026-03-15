"""
AI 워크플로우 오케스트레이터 - 개념 증명(PoC)

AI가 고객 이메일 분석을 통해 엔터프라이즈 워크플로우를
자동으로 생성하고 실행하는 방법을 시연하는 애플리케이션입니다.
"""

import streamlit as st
from dotenv import load_dotenv
import os

from services.ai_analyzer import analyze_email
from services.workflow_generator import generate_workflow, WorkflowStep
from services.automation_engine import AutomationEngine, ExecutionStatus
from services.config import (
    IntegrationConfig,
    JiraConfig,
    SlackConfig,
    EmailConfig,
)
from services.integrations import JiraClient, SlackClient, EmailClient
import services.integrations_enterprise  # noqa: F401 - SAP, ServiceNow 등록
from services.base import IntegrationRegistry

load_dotenv()

DEMO_EMAILS = {
    "🏦 금융 - 카드 분실 신고": """제목: [긴급] 법인카드 분실 신고

고객센터 담당자님께,

당사 임원 법인카드가 분실되어 긴급히 신고드립니다.

카드번호: 9411-2XXX-XXXX-3847
분실 일시: 2024년 3월 15일 오후 3시경
분실 장소: 서울 강남역 인근

즉시 카드 정지 처리 부탁드리며, 부정 사용 내역이 있다면 
확인 후 연락 부탁드립니다.

한국투자증권 재무팀
김재무 과장
02-1234-5678""",
    
    "🏭 제조 - 긴급 부품 발주": """제목: [긴급] 반도체 부품 긴급 발주 요청

구매팀 담당자님께,

생산라인 3번에서 사용 중인 반도체 부품 재고가 부족하여
긴급 발주가 필요합니다.

부품번호: IC-7890-KR
필요수량: 5,000개
희망납기: 1주일 이내

현재 재고로는 3일치 생산분만 가능하며, 
납기 지연 시 고객사 납품에 차질이 예상됩니다.

생산관리팀에서 긴급도 '상' 으로 분류하였습니다.

현대모비스 생산관리팀
이생산 차장""",
    
    "💼 컨설팅 - 프로젝트 제안 요청": """제목: AI 트랜스포메이션 컨설팅 RFP

컨설팅 담당자님께,

당사는 전사적 AI 도입을 검토 중인 금융지주사입니다.

다음 영역에 대한 컨설팅 제안을 요청드립니다:
1. 고객센터 AI 자동화 (콜센터 + 이메일)
2. 심사/승인 프로세스 AI 도입
3. 리스크 관리 AI 모델 구축

예상 프로젝트 규모: 12개월
예산 범위: 15-20억원

제안서 제출 기한: 2024년 4월 30일
문의: 디지털혁신팀 홍길동 상무
연락처: 02-9876-5432

BNK금융그룹 디지털혁신팀""",
    
    "🔧 IT - 시스템 장애 신고": """제목: [장애] ERP 시스템 접속 불가 - 전사 영향

IT 헬프데스크 담당자님께,

오늘 오전 9시부터 SAP ERP 시스템 접속이 불가능합니다.
전사 약 500명의 사용자가 업무에 영향을 받고 있습니다.

증상:
- 로그인 시도 시 "서버 연결 실패" 오류
- VPN 연결은 정상
- 다른 시스템(이메일, 그룹웨어)은 정상

영향 범위:
- 재무팀: 월말 결산 마감 지연 예상
- 구매팀: 발주 처리 불가
- 생산팀: 자재 출고 지연

긴급 복구 요청드립니다.

포스코 경영지원팀
박시스템 대리
내선: 2345""",
    
    "📋 HR - 퇴직금 정산 문의": """제목: 퇴직금 중간 정산 신청 문의

인사팀 담당자님께,

주택 구입을 위해 퇴직금 중간정산을 신청하고자 합니다.

근속연수: 8년 4개월
신청 사유: 무주택자 주택 구입 (관련 서류 첨부 예정)
예상 정산 금액: 약 5,000만원

다음 사항을 확인 부탁드립니다:
1. 중간정산 가능 여부
2. 필요 서류 목록
3. 처리 소요 기간

감사합니다.
한화에어로스페이스 기술연구소
최연구 책임""",
    
    "💰 재무 - 공급업체 송장": """제목: 송장 #INV-2024-0892 - 결제 요청

회계 담당자님께,

2024년 1분기 IT 인프라 유지보수 서비스에 대한 
송장을 첨부합니다.

송장번호: INV-2024-0892
공급가액: 85,000,000원
부가세: 8,500,000원
합계: 93,500,000원
결제 기한: 2024년 4월 15일

대금 지급 계좌:
우리은행 1005-XXX-XXXXXX
예금주: (주)클라우드테크

한국전력 재무팀 앞
클라우드테크 영업팀
accounts@cloudtech.co.kr""",
}

PRIORITY_TRANSLATIONS = {
    "Low": "낮음",
    "Medium": "보통",
    "High": "높음",
    "Critical": "긴급"
}


def init_session_state():
    """Streamlit 세션 상태 변수를 초기화합니다."""
    if "analysis_result" not in st.session_state:
        st.session_state.analysis_result = None
    if "workflow_steps" not in st.session_state:
        st.session_state.workflow_steps = None
    if "automation_results" not in st.session_state:
        st.session_state.automation_results = None
    if "email_text" not in st.session_state:
        st.session_state.email_text = ""
    if "integration_config" not in st.session_state:
        st.session_state.integration_config = IntegrationConfig()


def get_integration_config() -> IntegrationConfig:
    """세션에서 연동 설정을 가져옵니다."""
    return st.session_state.integration_config


def render_sidebar():
    """사이드바에 연동 설정 UI를 렌더링합니다."""
    with st.sidebar:
        st.header("⚙️ 연동 설정")
        
        config = get_integration_config()
        
        simulation_mode = st.toggle(
            "시뮬레이션 모드",
            value=config.simulation_mode,
            help="활성화하면 실제 시스템에 연결하지 않고 시뮬레이션합니다."
        )
        config.simulation_mode = simulation_mode
        
        if simulation_mode:
            st.info("🔄 시뮬레이션 모드가 활성화되어 있습니다.")
        else:
            st.warning("⚡ 실제 연동 모드입니다. 아래 설정을 확인하세요.")
        
        st.divider()
        
        with st.expander("🎫 Jira 설정", expanded=not simulation_mode):
            jira_enabled = st.checkbox(
                "Jira 연동 활성화",
                value=config.jira.enabled,
                key="jira_enabled"
            )
            
            jira_url = st.text_input(
                "Jira URL",
                value=config.jira.base_url or os.getenv("JIRA_BASE_URL", ""),
                placeholder="https://your-domain.atlassian.net",
                help="Jira Cloud URL (예: https://company.atlassian.net)"
            )
            
            jira_email = st.text_input(
                "Jira 이메일",
                value=config.jira.email or os.getenv("JIRA_EMAIL", ""),
                placeholder="your-email@company.com"
            )
            
            jira_token = st.text_input(
                "API 토큰",
                value=config.jira.api_token or os.getenv("JIRA_API_TOKEN", ""),
                type="password",
                help="Atlassian 계정 설정에서 생성한 API 토큰"
            )
            
            jira_project = st.text_input(
                "프로젝트 키",
                value=config.jira.project_key or os.getenv("JIRA_PROJECT_KEY", ""),
                placeholder="TEST",
                help="이슈를 생성할 Jira 프로젝트 키"
            )
            
            config.jira = JiraConfig(
                enabled=jira_enabled,
                base_url=jira_url,
                email=jira_email,
                api_token=jira_token,
                project_key=jira_project,
                department_assignee_mapping=getattr(config.jira, "department_assignee_mapping", None) or {}
            )
            
            if jira_enabled and jira_url and jira_email and jira_token:
                if st.button("🔗 Jira 연결 테스트", key="test_jira"):
                    with st.spinner("연결 테스트 중..."):
                        client = JiraClient(config.jira)
                        result = client.test_connection()
                        if result.success:
                            st.success(f"✅ {result.message}")
                        else:
                            st.error(f"❌ {result.message}")
        
        with st.expander("💬 Slack 설정", expanded=not simulation_mode):
            slack_enabled = st.checkbox(
                "Slack 연동 활성화",
                value=config.slack.enabled,
                key="slack_enabled"
            )
            
            slack_bot_token = st.text_input(
                "Bot Token",
                value=config.slack.bot_token or os.getenv("SLACK_BOT_TOKEN", ""),
                type="password",
                placeholder="xoxb-...",
                help="Bot User OAuth Token (xoxb-로 시작)"
            )
            
            slack_channel = st.text_input(
                "채널 ID",
                value=config.slack.channel_id or os.getenv("SLACK_CHANNEL_ID", ""),
                placeholder="C01234ABCDE",
                help="채널 우클릭 → 링크 복사 → 마지막 부분이 채널 ID"
            )
            
            config.slack = SlackConfig(
                enabled=slack_enabled,
                use_bot_token=True,
                bot_token=slack_bot_token,
                channel_id=slack_channel
            )
            
            can_test = slack_enabled and slack_bot_token and slack_channel
            if can_test:
                if st.button("🔗 Slack 연결 테스트", key="test_slack"):
                    with st.spinner("연결 테스트 중..."):
                        client = SlackClient(config.slack)
                        result = client.test_connection()
                        if result.success:
                            st.success(f"✅ {result.message}")
                        else:
                            st.error(f"❌ {result.message}")
        
        with st.expander("📧 이메일 설정", expanded=not simulation_mode):
            email_enabled = st.checkbox(
                "이메일 연동 활성화",
                value=config.email.enabled,
                key="email_enabled"
            )
            
            email_sender = st.text_input(
                "발신자 이메일",
                value=config.email.sender_email or os.getenv("EMAIL_SENDER", ""),
                placeholder="your-email@gmail.com"
            )
            
            email_password = st.text_input(
                "앱 비밀번호",
                value=config.email.sender_password or os.getenv("EMAIL_PASSWORD", ""),
                type="password",
                help="Gmail 앱 비밀번호 (2단계 인증 필요)"
            )
            
            email_recipient = st.text_input(
                "수신자 이메일",
                value=config.email.recipient_email or os.getenv("EMAIL_RECIPIENT", ""),
                placeholder="recipient@company.com",
                help="알림을 받을 이메일 주소"
            )
            
            config.email = EmailConfig(
                enabled=email_enabled,
                smtp_server="smtp.gmail.com",
                smtp_port=587,
                sender_email=email_sender,
                sender_password=email_password,
                recipient_email=email_recipient
            )
            
            if email_enabled and email_sender and email_password:
                if st.button("🔗 이메일 연결 테스트", key="test_email"):
                    with st.spinner("연결 테스트 중..."):
                        client = EmailClient(config.email)
                        result = client.test_connection()
                        if result.success:
                            st.success(f"✅ {result.message}")
                        else:
                            st.error(f"❌ {result.message}")
        
        st.divider()
        
        st.markdown("**연동 상태:**")
        active = config.get_active_integrations()
        if active and not simulation_mode:
            for integration in active:
                st.success(f"✅ {integration}")
        elif simulation_mode:
            st.info("🔄 시뮬레이션 모드")
        else:
            st.warning("⚠️ 활성화된 연동 없음")
        
        st.session_state.integration_config = config


def render_header():
    """애플리케이션 헤더를 렌더링합니다."""
    st.title("🔄 AI 워크플로우 오케스트레이터")
    st.markdown("### 엔터프라이즈 프로세스 자동화 개념 증명")
    st.markdown("""
    이 애플리케이션은 AI가 고객 이메일을 분석하고 엔터프라이즈 워크플로우를 
    자동으로 생성하고 실행하는 방법을 시연합니다.
    """)
    st.divider()


def render_email_input() -> str:
    """이메일 입력 섹션을 렌더링합니다."""
    st.subheader("📧 고객 이메일 입력")
    
    col1, col2 = st.columns([3, 1])
    
    with col2:
        st.markdown("**데모 이메일 선택:**")
        selected_demo = st.selectbox(
            "예제 선택",
            options=["직접 입력"] + list(DEMO_EMAILS.keys()),
            label_visibility="collapsed"
        )
        
        if selected_demo != "직접 입력":
            st.session_state.email_text = DEMO_EMAILS[selected_demo]
    
    with col1:
        email_text = st.text_area(
            "이메일 내용을 입력하세요:",
            value=st.session_state.email_text,
            height=200,
            placeholder="고객 이메일을 여기에 붙여넣으세요..."
        )
        st.session_state.email_text = email_text
    
    return email_text


def render_analysis_section(email_text: str):
    """AI 분석 섹션을 렌더링합니다."""
    st.subheader("🤖 AI 이메일 분석")
    
    api_key = st.text_input(
        "OpenAI API 키",
        type="password",
        value=os.getenv("OPENAI_API_KEY", ""),
        help="API 키는 분석 시에만 사용되며 저장되지 않습니다."
    )
    
    col1, col2 = st.columns([1, 4])
    with col1:
        analyze_button = st.button("📊 이메일 분석", type="primary", use_container_width=True)
    
    if analyze_button:
        if not email_text.strip():
            st.error("이메일 내용을 입력해주세요.")
            return
        
        if not api_key:
            st.error("OpenAI API 키를 입력해주세요.")
            return
        
        with st.spinner("AI가 이메일을 분석하고 있습니다..."):
            try:
                result = analyze_email(email_text, api_key)
                st.session_state.analysis_result = result
                
                workflow_steps = generate_workflow(result["intent"], result["department"])
                st.session_state.workflow_steps = workflow_steps
                st.session_state.automation_results = None
                
            except Exception as e:
                st.error(f"분석 중 오류가 발생했습니다: {str(e)}")
                return
    
    if st.session_state.analysis_result:
        result = st.session_state.analysis_result
        
        st.success("분석 완료!")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("의도", result["intent"])
        
        with col2:
            st.metric("담당 부서", result["department"])
        
        with col3:
            priority_colors = {
                "Low": "🟢",
                "Medium": "🟡", 
                "High": "🟠",
                "Critical": "🔴"
            }
            priority_icon = priority_colors.get(result["priority"], "⚪")
            priority_kr = PRIORITY_TRANSLATIONS.get(result["priority"], result["priority"])
            st.metric("우선순위", f"{priority_icon} {priority_kr}")
        
        with col4:
            confidence_pct = f"{result['confidence'] * 100:.1f}%"
            st.metric("신뢰도", confidence_pct)


def render_workflow_section():
    """생성된 워크플로우 섹션을 렌더링합니다."""
    if not st.session_state.workflow_steps:
        return
    
    st.divider()
    st.subheader("📋 생성된 워크플로우")
    
    config = get_integration_config()
    active_integrations = config.get_active_integrations() if not config.simulation_mode else []
    
    steps: list[WorkflowStep] = st.session_state.workflow_steps
    
    for step in steps:
        with st.container():
            col1, col2, col3 = st.columns([0.5, 2, 1.5])
            
            with col1:
                st.markdown(f"### {step.order}")
            
            with col2:
                st.markdown(f"**{step.action}**")
                st.caption(step.description)
            
            with col3:
                if step.system in active_integrations:
                    st.success(f"🔗 {step.system} (실제 연동)")
                else:
                    st.info(f"🔗 {step.system}")


def render_automation_section():
    """자동화 실행 섹션을 렌더링합니다."""
    if not st.session_state.workflow_steps:
        return
    
    st.divider()
    st.subheader("⚡ 자동화 실행")
    
    config = get_integration_config()
    
    if config.simulation_mode:
        st.info("🔄 시뮬레이션 모드: 실제 시스템에 연결하지 않고 테스트합니다.")
    else:
        active = config.get_active_integrations()
        if active:
            st.success(f"⚡ 실제 연동 모드: {', '.join(active)}")
        else:
            st.warning("⚠️ 활성화된 연동이 없습니다. 사이드바에서 연동을 설정하세요.")
    
    col1, col2 = st.columns([1, 4])
    with col1:
        run_button = st.button("🚀 자동화 실행", type="primary", use_container_width=True)
    
    if run_button:
        st.session_state.automation_results = []
        
        engine = AutomationEngine(failure_rate=0.0, config=config)
        
        if st.session_state.analysis_result:
            result = st.session_state.analysis_result
            engine.set_context(
                intent=result["intent"],
                department=result["department"],
                priority=result["priority"],
                email_content=st.session_state.email_text
            )
        
        progress_bar = st.progress(0)
        status_container = st.container()
        
        steps = st.session_state.workflow_steps
        total_steps = len(steps)
        
        for i, step in enumerate(steps):
            result = engine.execute_step(step)
            st.session_state.automation_results.append(result)
            
            progress_bar.progress((i + 1) / total_steps)
            
            with status_container:
                if result.status == ExecutionStatus.SUCCESS:
                    if result.data and result.data.get("key"):
                        summary = result.data.get("summary", "")
                        issue_key = result.data.get("key", "")
                        issue_url = result.data.get("url", "")
                        if issue_url and issue_url != "#":
                            st.success(f"✅ 단계 {step.order}: 이슈 **'{summary or issue_key}'** 생성 완료. [Jira에서 보기]({issue_url}) ({issue_key})")
                        else:
                            st.success(f"✅ 단계 {step.order}: 이슈 **'{summary or issue_key}'** 생성 완료 ({issue_key})")
                    else:
                        st.success(f"✅ 단계 {step.order}: {result.message}")
                else:
                    st.error(f"❌ 단계 {step.order}: {result.message}")
        
        st.balloons()
        st.success("🎉 모든 자동화 단계가 완료되었습니다!")
        
        if not config.simulation_mode and config.has_any_integration():
            st.info("💡 실제 시스템에서 결과를 확인하세요!")
    
    elif st.session_state.automation_results:
        st.markdown("**실행 결과:**")
        for result in st.session_state.automation_results:
            if result.status == ExecutionStatus.SUCCESS:
                if result.data and result.data.get("key"):
                    summary = result.data.get("summary", "")
                    link = result.data.get("url", "")
                    key = result.data.get("key", "")
                    if link and link != "#":
                        st.success(f"✅ 단계 {result.step.order}: 이슈 **'{summary or key}'** 생성 완료 | [Jira에서 보기]({link}) ({key}) ({result.duration_ms}ms)")
                    else:
                        st.success(f"✅ 단계 {result.step.order}: 이슈 **'{summary or key}'** 생성 완료 ({key}) ({result.duration_ms}ms)")
                else:
                    st.success(f"✅ 단계 {result.step.order}: {result.message} ({result.duration_ms}ms)")
            else:
                st.error(f"❌ 단계 {result.step.order}: {result.message}")


def render_footer():
    """애플리케이션 푸터를 렌더링합니다."""
    st.divider()
    
    config = get_integration_config()
    mode_text = "시뮬레이션" if config.simulation_mode else "실제 연동"
    
    st.markdown(f"""
    <div style='text-align: center; color: gray; padding: 20px;'>
        <p>AI 워크플로우 오케스트레이터 PoC | 엔터프라이즈 프로세스 자동화 데모</p>
        <p style='font-size: 0.8em;'>현재 모드: {mode_text}</p>
    </div>
    """, unsafe_allow_html=True)


def main():
    """메인 애플리케이션 진입점입니다."""
    st.set_page_config(
        page_title="AI 워크플로우 오케스트레이터",
        page_icon="🔄",
        layout="wide"
    )
    
    init_session_state()
    render_sidebar()
    render_header()
    
    email_text = render_email_input()
    
    st.divider()
    
    render_analysis_section(email_text)
    render_workflow_section()
    render_automation_section()
    render_footer()


if __name__ == "__main__":
    main()
