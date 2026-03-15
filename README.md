# AI 워크플로우 오케스트레이터

> **엔터프라이즈 AI 트랜스포메이션 PoC (Proof of Concept)**

대기업 환경에서 AI를 활용한 업무 프로세스 자동화를 시연하는 컨설팅 프로토타입입니다.

---

## 📋 Executive Summary

### 비즈니스 문제

대기업 고객센터/지원팀의 현실:

| 현황 | 문제점 |
|------|--------|
| 하루 수백 건의 고객 문의 유입 | 담당자 수동 분류에 **2시간 이상** 소요 |
| 복잡한 부서 간 업무 이관 | 담당자 파악에 평균 **30분** 지연 |
| 여러 시스템 분산 운영 | Jira, Slack, CRM 각각 수동 입력 |
| 우선순위 판단 주관적 | 긴급 건 누락 → 고객 이탈 리스크 |

### 솔루션

**AI 기반 워크플로우 오케스트레이터**

```
고객 이메일 → AI 의도 분석 → 자동 분류 → 워크플로우 생성 → 시스템 연동
```

- **LLM**이 이메일 내용을 분석하여 의도, 담당 부서, 우선순위 자동 분류
- **워크플로우 엔진**이 비즈니스 규칙에 따라 처리 단계 자동 생성
- **시스템 연동**으로 Jira 티켓 생성, Slack 알림, 이메일 회신 자동화

### 기대 효과

| 지표 | Before | After | 개선율 |
|------|--------|-------|--------|
| 분류 소요 시간 | 2시간 | 5분 | **96% 단축** |
| 담당자 배정 | 30분 | 즉시 | **100% 단축** |
| 시스템 입력 | 수동 3회 | 자동 1회 | **67% 절감** |
| 긴급 건 누락률 | 5% | 0.1% | **98% 감소** |

---

## 🏗️ 시스템 아키텍처

### 플러그인 아키텍처

본 시스템은 **확장 가능한 플러그인 아키텍처**로 설계되어 새로운 엔터프라이즈 시스템을 코드 수정 없이 추가할 수 있습니다.

```
┌─────────────────────────────────────────────────────────────────┐
│                        Streamlit Web UI                         │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                      AI Analysis Engine                          │
│              (OpenAI GPT → 의도/부서/우선순위 분석)                │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Workflow Generator                            │
│               (비즈니스 규칙 기반 워크플로우 생성)                  │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Automation Engine                             │
│            ┌──────────────────────────────────┐                 │
│            │     IntegrationRegistry          │ ◄── 플러그인    │
│            │  (클라이언트 자동 등록/관리)       │     레지스트리  │
│            └──────────────────────────────────┘                 │
│                           │                                     │
│      ┌────────────────────┼────────────────────┐               │
│      ▼                    ▼                    ▼               │
│  ┌────────┐          ┌────────┐          ┌────────┐           │
│  │  Jira  │          │ Slack  │          │ Email  │  ← 기본   │
│  │ Client │          │ Client │          │ Client │           │
│  └────────┘          └────────┘          └────────┘           │
│      └────────────────────┼────────────────────┘               │
│                            ▼                                    │
│               ┌────────────┴────────────┐                       │
│               ▼                         ▼                       │
│          ┌────────┐               ┌────────────┐                │
│          │  SAP   │               │ ServiceNow │  ← 플러그인 예시 │
│          │ Client │               │  Client    │                 │
│          └────────┘               └────────────┘                 │
└─────────────────────────────────────────────────────────────────┘
                                │
            ┌───────────────────┼───────────────────┐
            ▼                   ▼                   ▼
      ┌──────────┐        ┌──────────┐        ┌──────────┐
      │  Jira    │        │  Slack   │        │  Gmail   │
      │  Cloud   │        │  API     │        │  SMTP    │
      └──────────┘        └──────────┘        └──────────┘
```

### 핵심 설계 원칙

| 원칙 | 구현 |
|------|------|
| **개방-폐쇄 원칙** | 새 시스템 추가 시 기존 코드 수정 불필요 |
| **의존성 역전** | 추상 베이스 클래스로 결합도 최소화 |
| **단일 책임** | 각 클라이언트가 하나의 시스템만 담당 |

---

## 💡 주요 기능

### 1. AI 이메일 분석
- GPT-4o 기반 자연어 처리
- 의도(Intent), 담당 부서, 우선순위, 신뢰도 자동 추출
- JSON 구조화 출력으로 시스템 연동 용이

### 2. 동적 워크플로우 생성
- 의도별 맞춤 워크플로우 템플릿
- 비즈니스 규칙 기반 단계 생성
- 확장 가능한 템플릿 구조

### 3. 엔터프라이즈 시스템 연동
- **Jira Cloud**: 티켓/이슈 자동 생성 (`[담당부서] 의도` 형식), 일정(기한) 이슈 생성
- **Slack**: Bot Token으로 지정 채널에 실시간 팀 알림
- **Email**: 자동 회신 발송
- 시뮬레이션/실제 연동 모드 전환

---

## 🚀 빠른 시작

### 사전 요구사항
- Python 3.10+
- OpenAI API 키

### 설치

```bash
# 저장소 클론
git clone https://github.com/your-repo/ai-workflow-orchestrator.git
cd ai-workflow-orchestrator

# 가상환경 생성
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# 환경변수 설정
cp .env.example .env
# .env 파일에 API 키 입력
```

### 실행

```bash
streamlit run app.py
```

브라우저에서 `http://localhost:8501` 접속

---

## 📁 프로젝트 구조

```
ai-workflow-orchestrator/
├── app.py                      # Streamlit 메인 애플리케이션
├── requirements.txt            # Python 의존성
├── .env.example               # 환경변수 템플릿
│
├── services/                   # 비즈니스 로직 레이어
│   ├── __init__.py            # 모듈 익스포트
│   ├── base.py                # 🔌 플러그인 베이스 클래스 & 레지스트리
│   ├── ai_analyzer.py         # LLM 기반 이메일 분석
│   ├── workflow_generator.py  # 워크플로우 생성 엔진
│   ├── automation_engine.py   # 시스템 연동 오케스트레이터
│   ├── integrations.py        # 기본 클라이언트 (Jira, Slack, Email)
│   ├── integrations_enterprise.py  # 🏢 엔터프라이즈 플러그인 예시
│   └── config.py              # 설정 관리
│
├── prompts/                    # LLM 프롬프트 템플릿
│   └── email_analysis_prompt.txt
│
└── docs/                       # 문서
    ├── ARCHITECTURE.md        # 아키텍처 상세
    ├── EXTENSIBILITY.md       # 확장 가이드
    ├── BUSINESS_SCENARIOS.md  # 비즈니스 시나리오 & ROI
    └── PRESENTATION_PROMPT.md # 발표 자료 제작용 AI 프롬프트
```

### 핵심 파일 설명

| 파일 | 역할 |
|------|------|
| `base.py` | `BaseIntegrationClient`, `IntegrationRegistry` - 플러그인 아키텍처 핵심 |
| `integrations.py` | 실제 동작하는 Jira, Slack, Email 클라이언트 |
| `integrations_enterprise.py` | SAP, ServiceNow 예시 (확장 참고용) |
| `automation_engine.py` | 레지스트리 기반으로 클라이언트 자동 탐색 및 실행 |

---

## 🔌 플러그인 아키텍처

### 새 시스템 추가 방법

**3단계만으로 새 엔터프라이즈 시스템을 통합할 수 있습니다:**

```python
# 1. BaseIntegrationClient 상속
from services.base import BaseIntegrationClient, register_integration

# 2. @register_integration 데코레이터로 등록
@register_integration("SAP", SAPConfig)
class SAPClient(BaseIntegrationClient):
    system_name = "SAP"
    
    def test_connection(self) -> IntegrationResult:
        # SAP 연결 테스트 구현
        ...
    
    def execute(self, action: str, context: dict) -> IntegrationResult:
        # SAP 액션 실행 구현
        ...

# 3. 자동으로 AutomationEngine에서 사용 가능!
```

### 현재 구현된 클라이언트

| 시스템 | 상태 | 용도 | 파일 |
|--------|------|------|------|
| Jira Cloud | ✅ 실제 연동 | 티켓/이슈 관리 | `integrations.py` |
| Slack | ✅ 실제 연동 | 팀 알림 | `integrations.py` |
| Gmail SMTP | ✅ 실제 연동 | 이메일 발송 | `integrations.py` |
| SAP | 📦 플러그인 예시 | ERP 연동 | `integrations_enterprise.py` |
| ServiceNow | 📦 플러그인 예시 | ITSM 연동 | `integrations_enterprise.py` |

### 아키텍처 장점

| 장점 | 설명 |
|------|------|
| **Zero-Code 확장** | 기존 엔진 코드 수정 없이 새 시스템 추가 |
| **런타임 등록** | 데코레이터로 자동 레지스트리 등록 |
| **일관된 인터페이스** | 모든 클라이언트가 동일한 API 제공 |
| **시뮬레이션 지원** | 실제 연동 전 테스트 가능 |

상세 내용: [EXTENSIBILITY.md](docs/EXTENSIBILITY.md)

---

## 📊 비즈니스 시나리오

### 시나리오 1: 금융사 고객센터
> 하루 500건 이메일 → AI 자동 분류 → 담당 부서 즉시 배정

### 시나리오 2: 제조업 공급망
> 공급업체 송장 이메일 → SAP 자동 등록 → 회계팀 알림

### 시나리오 3: IT서비스 헬프데스크
> 기술 문의 → 긴급도 판단 → ServiceNow 티켓 생성 → 엔지니어 배정

---

## 🛠️ 기술 스택

| 구분 | 기술 | 설명 |
|------|------|------|
| **Backend** | Python 3.10+ | 타입 힌트, dataclass 활용 |
| **Frontend** | Streamlit | 빠른 프로토타이핑 |
| **AI/LLM** | OpenAI GPT-4o-mini | 자연어 분석 |
| **API 연동** | REST API, Webhook | 실시간 시스템 연동 |
| **아키텍처** | 플러그인 패턴 | Registry + Abstract Base Class |
| **설계 원칙** | SOLID | 개방-폐쇄, 의존성 역전 |

---

## 📝 향후 발전 방향

1. **멀티 채널 확장**: 카카오톡, 웹챗, 전화 음성 연동
2. **고급 분석**: 감정 분석, 긴급도 예측 ML 모델
3. **대시보드**: 처리 현황 실시간 모니터링
4. **규정 준수**: 금융권 컴플라이언스 체크 자동화

---

## 🔜 추후 변경 가능 사항

아래 기능은 **현재 버전에는 UI/기능으로 포함하지 않았으며**, 추후 확장 시 바로 붙일 수 있도록 **구조만** 남겨 두었습니다.

| 항목 | 설명 | 코드 상 준비된 구조 |
|------|------|----------------------|
| **Jira 담당자 자동 배정** | 이메일 분석 결과(담당 부서)에 따라 해당 부서 담당자에게 이슈 자동 배정 | `JiraConfig.department_assignee_mapping`, `JiraClient.get_assignable_users()`, `create_issue(assignee_account_id=...)`, 이슈 조회로 담당자 표시 이름 반환 |

담당자 배정을 쓰려면: 설정에 부서별 Jira 사용자(accountId) 매핑 UI를 추가하고, 해당 매핑을 `JiraConfig.department_assignee_mapping`에 넣어 전달하면 됩니다.

---

## 💬 Slack 연동: Bot Token / Channel ID 알아보는 방법

앱에서 **Slack 연동**에 필요한 값입니다. (Bot Token + 채널 ID 방식)

### 1. Bot Token (Bot User OAuth Token) 얻기

1. **Slack API 앱 페이지** 접속: [https://api.slack.com/apps](https://api.slack.com/apps)
2. **Create New App** → **From scratch** 선택 후 앱 이름과 워크스페이스 지정
3. 왼쪽 메뉴에서 **OAuth & Permissions** 클릭
4. **Scopes** → **Bot Token Scopes**에서 **Add an OAuth Scope** 클릭 후 다음 스코프 추가:
   - `chat:write` — 봇이 채널에 메시지 보내기
   - (선택) `channels:read`, `groups:read` — 채널 목록 조회
5. 페이지 상단 **Install to Workspace** 클릭 → 허용
6. **OAuth & Permissions** 페이지에 표시되는 **Bot User OAuth Token** (`xoxb-` 로 시작) 복사  
   → 이 값이 **Bot Token**입니다. `.env`의 `SLACK_BOT_TOKEN` 또는 앱 사이드바에 입력합니다.

### 2. Channel ID 알아내기

**방법 A: 채널에서 링크 복사**

1. Slack에서 메시지를 보낼 **채널**로 이동
2. 채널 이름을 **우클릭** → **채널 세부정보 보기** (또는 **View channel details**)
3. 아래로 내려 **연결** 영역의 **채널 링크 복사** 클릭  
   - 복사된 URL 예: `https://your-workspace.slack.com/archives/C01234ABCDE`  
   - **`C01234ABCDE`** 부분이 해당 채널의 **Channel ID**입니다.

**방법 B: 웹에서 URL 확인**

1. 브라우저로 Slack 워크스페이스 접속 후 해당 채널 열기
2. 주소창 URL에서 `/archives/` 뒤의 **C로 시작하는 영문·숫자 조합**이 Channel ID  
   - 예: `.../archives/C09ABC12XYZ` → Channel ID는 `C09ABC12XYZ`

**주의:** 봇이 메시지를 보내려면 해당 채널에 **앱(봇)을 초대**해야 합니다. 채널에서 `/invite @봇이름` 입력 후 초대하세요.

---

## 📄 라이선스

MIT License

---

## 👤 Contact

프로젝트 관련 문의: [이메일 주소]
