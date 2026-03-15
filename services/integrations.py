"""
외부 시스템 연동 클라이언트

Jira, Slack, Email 등 외부 시스템과의 실제 연동을 담당합니다.
플러그인 아키텍처를 사용하여 새로운 시스템을 쉽게 추가할 수 있습니다.
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

import requests

from .base import (
    BaseIntegrationClient,
    IntegrationResult,
    IntegrationRegistry,
    register_integration
)
from .config import JiraConfig, SlackConfig, EmailConfig


@register_integration("Jira", JiraConfig)
class JiraClient(BaseIntegrationClient):
    """Jira Cloud API 클라이언트"""
    
    system_name = "Jira"
    
    def __init__(self, config: JiraConfig):
        self.config = config
        base_url = config.base_url.strip().rstrip('/') if config.base_url else ""
        if base_url and not base_url.startswith('http'):
            base_url = f"https://{base_url}"
        if '/rest/api' in base_url:
            base_url = base_url.split('/rest/api')[0]
        if '/browse' in base_url:
            base_url = base_url.split('/browse')[0]
        if '/jira' in base_url.lower() and 'atlassian.net' in base_url.lower():
            base_url = base_url.split('/jira')[0]
        self.base_url = base_url
        self.auth = (config.email, config.api_token) if config.email and config.api_token else None
    
    @classmethod
    def get_supported_actions(cls) -> list[str]:
        return ["create_ticket", "create_issue", "create_schedule", "test_connection"]

    def execute(self, action: str, context: dict) -> IntegrationResult:
        """Jira 액션을 실행합니다. create_schedule은 기한(duedate)이 있는 일정 이슈를 생성합니다."""
        if action in ["create_ticket", "create_issue"]:
            department = context.get("department", "")
            intent = context.get("intent", "Unknown")
            summary = f"[{department}] {intent}" if department else f"[업무] {intent}"
            assignee_account_id = None
            if getattr(self.config, "department_assignee_mapping", None):
                assignee_account_id = self.config.department_assignee_mapping.get(department)
            return self.create_issue(
                summary=summary,
                description=context.get("description", ""),
                issue_type=context.get("issue_type", "Task"),
                priority=context.get("priority", "Medium"),
                assignee_account_id=assignee_account_id
            )
        elif action == "create_schedule":
            # 일정/미팅 등을 Jira 이슈(기한 포함)로 등록
            title = context.get("title") or context.get("intent", "일정")
            description = context.get("description", "") or context.get("action", "")
            due_date = context.get("due_date") or context.get("duedate")
            department = context.get("department", "")
            summary = f"[일정] {title}" if not title.startswith("[") else title
            return self.create_issue(
                summary=summary,
                description=description,
                issue_type=context.get("issue_type", "Task"),
                priority=context.get("priority", "Medium"),
                assignee_account_id=None,
                due_date=due_date
            )
        elif action == "test_connection":
            return self.test_connection()
        elif action == "execute":
            department = context.get("department", "")
            intent = context.get("intent", "Unknown")
            summary = f"[{department}] {intent}" if department else f"[업무] {intent}"
            return self.create_issue(
                summary=summary,
                description=context.get("description", ""),
                issue_type="Task",
                priority=context.get("priority", "Medium"),
                assignee_account_id=None
            )
        else:
            return IntegrationResult(
                success=False,
                message=f"지원하지 않는 액션: {action}"
            )
    
    def test_connection(self) -> IntegrationResult:
        """Jira 연결을 테스트합니다."""
        if not self.base_url or not self.auth:
            return IntegrationResult(
                success=False,
                message="Jira 설정이 완료되지 않았습니다"
            )
        
        try:
            url = f"{self.base_url}/rest/api/3/myself"
            headers = {
                "Accept": "application/json",
                "Content-Type": "application/json"
            }
            
            response = requests.get(url, auth=self.auth, headers=headers, timeout=10)
            
            if response.status_code == 200:
                try:
                    user_data = response.json()
                    return IntegrationResult(
                        success=True,
                        message=f"연결 성공: {user_data.get('displayName', 'Unknown')}",
                        data=user_data
                    )
                except ValueError:
                    content_preview = response.text[:100] if response.text else "(빈 응답)"
                    if "<html" in response.text.lower():
                        return IntegrationResult(
                            success=False,
                            message="URL 오류: Jira API URL이 아닌 웹 페이지가 반환되었습니다."
                        )
                    return IntegrationResult(
                        success=False,
                        message=f"응답 파싱 오류: {content_preview}"
                    )
            elif response.status_code == 401:
                return IntegrationResult(success=False, message="인증 실패: 이메일 또는 API 토큰을 확인하세요")
            elif response.status_code == 403:
                return IntegrationResult(success=False, message="접근 거부: API 토큰 권한을 확인하세요")
            elif response.status_code == 404:
                return IntegrationResult(success=False, message="URL 오류: Jira URL을 확인하세요")
            else:
                return IntegrationResult(success=False, message=f"연결 실패 (HTTP {response.status_code})")
                
        except requests.exceptions.Timeout:
            return IntegrationResult(success=False, message="연결 시간 초과")
        except requests.exceptions.ConnectionError:
            return IntegrationResult(success=False, message="연결 실패: URL을 확인하세요")
        except requests.exceptions.RequestException as e:
            return IntegrationResult(success=False, message=f"연결 오류: {str(e)}")
    
    def get_assignable_users(self, query: str = "") -> IntegrationResult:
        """프로젝트에 이슈를 배정할 수 있는 사용자 목록을 조회합니다."""
        if not self.base_url or not self.auth or not self.config.project_key:
            return IntegrationResult(success=False, message="Jira 설정이 완료되지 않았습니다")
        try:
            url = f"{self.base_url}/rest/api/3/user/assignable/search"
            params = {"project": self.config.project_key}
            if query:
                params["query"] = query
            headers = {"Accept": "application/json"}
            response = requests.get(url, params=params, auth=self.auth, headers=headers, timeout=10)
            if response.status_code != 200:
                return IntegrationResult(success=False, message=f"사용자 조회 실패 (HTTP {response.status_code})")
            users = response.json()
            result_list = [
                {"accountId": u.get("accountId"), "displayName": u.get("displayName", ""), "emailAddress": u.get("emailAddress", "")}
                for u in users
            ]
            return IntegrationResult(success=True, message=f"배정 가능 사용자 {len(result_list)}명", data={"users": result_list})
        except requests.exceptions.RequestException as e:
            return IntegrationResult(success=False, message=f"Jira 오류: {str(e)}")

    def create_issue(
        self,
        summary: str,
        description: str,
        issue_type: str = "Task",
        priority: str = "Medium",
        assignee_account_id: Optional[str] = None,
        due_date: Optional[str] = None
    ) -> IntegrationResult:
        """Jira 이슈를 생성합니다. due_date가 있으면 기한(일정) 이슈로 등록합니다 (형식: YYYY-MM-DD)."""
        if not self.base_url or not self.auth:
            return IntegrationResult(success=False, message="Jira 설정이 완료되지 않았습니다")
        
        try:
            url = f"{self.base_url}/rest/api/3/issue"
            
            priority_mapping = {
                "Low": "Low", "Medium": "Medium", "High": "High", "Critical": "Highest",
                "낮음": "Low", "보통": "Medium", "높음": "High", "긴급": "Highest"
            }
            jira_priority = priority_mapping.get(priority, "Medium")
            
            fields = {
                "project": {"key": self.config.project_key},
                "summary": summary,
                "description": {
                    "type": "doc", "version": 1,
                    "content": [{"type": "paragraph", "content": [{"type": "text", "text": description or ""}]}]
                },
                "issuetype": {"name": issue_type},
                "priority": {"name": jira_priority}
            }
            if assignee_account_id:
                fields["assignee"] = {"accountId": assignee_account_id}
            if due_date:
                # Jira duedate 형식: YYYY-MM-DD
                fields["duedate"] = str(due_date).strip()[:10]
            
            payload = {"fields": fields}
            
            headers = {"Content-Type": "application/json", "Accept": "application/json"}
            response = requests.post(url, json=payload, auth=self.auth, headers=headers, timeout=30)
            
            if response.status_code in [200, 201]:
                try:
                    issue_data = response.json()
                    issue_key = issue_data.get("key", "Unknown")
                    issue_url = f"{self.base_url}/browse/{issue_key}"
                    data = {"key": issue_key, "url": issue_url, "summary": summary}
                    assignee_display_name = None
                    if assignee_account_id:
                        get_result = self._get_issue_assignee_display_name(issue_key)
                        if get_result:
                            data["assignee_display_name"] = get_result
                            assignee_display_name = get_result
                    if assignee_display_name:
                        message = f"이슈 '{summary}'가 **{assignee_display_name}**에게 배정되었습니다 ({issue_key})"
                    else:
                        message = f"이슈 '{summary}' 생성 완료 ({issue_key})"
                    return IntegrationResult(success=True, message=message, data=data)
                except ValueError:
                    return IntegrationResult(success=False, message="이슈 생성됨 (응답 파싱 오류)")
            else:
                return IntegrationResult(success=False, message=f"이슈 생성 실패 (HTTP {response.status_code})")
                
        except requests.exceptions.RequestException as e:
            return IntegrationResult(success=False, message=f"Jira 오류: {str(e)}")

    def _get_issue_assignee_display_name(self, issue_key: str) -> Optional[str]:
        """이슈의 담당자 표시 이름을 조회합니다."""
        try:
            url = f"{self.base_url}/rest/api/3/issue/{issue_key}"
            params = {"fields": "assignee"}
            headers = {"Accept": "application/json"}
            response = requests.get(url, params=params, auth=self.auth, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                assignee = (data.get("fields") or {}).get("assignee")
                if assignee:
                    return assignee.get("displayName") or assignee.get("emailAddress") or "담당자"
            return None
        except Exception:
            return None


@register_integration("Slack", SlackConfig)
class SlackClient(BaseIntegrationClient):
    """Slack 클라이언트 (Webhook 또는 Bot Token 방식)"""
    
    system_name = "Slack"
    
    def __init__(self, config: SlackConfig):
        self.config = config
        self.use_bot_token = config.use_bot_token
        self.webhook_url = config.webhook_url
        self.bot_token = config.bot_token
        self.channel_id = config.channel_id
    
    @classmethod
    def get_supported_actions(cls) -> list[str]:
        return ["send_message", "send_notification", "test_connection"]
    
    def execute(self, action: str, context: dict) -> IntegrationResult:
        """Slack 액션을 실행합니다."""
        if action in ["send_message", "send_notification"]:
            return self.send_workflow_notification(
                title=context.get("title", "새 워크플로우"),
                intent=context.get("intent", ""),
                department=context.get("department", ""),
                priority=context.get("priority", "Medium"),
                ticket_id=context.get("ticket_id")
            )
        elif action == "test_connection":
            return self.test_connection()
        elif action == "execute":
            return self.send_workflow_notification(
                title=context.get("title", "새 워크플로우"),
                intent=context.get("intent", ""),
                department=context.get("department", ""),
                priority=context.get("priority", "Medium"),
                ticket_id=context.get("ticket_id")
            )
        else:
            return IntegrationResult(success=False, message=f"지원하지 않는 액션: {action}")
    
    def test_connection(self) -> IntegrationResult:
        """Slack 연결을 테스트합니다."""
        if self.use_bot_token:
            return self._test_bot_token()
        else:
            return self.send_message("🔔 AI 워크플로우 오케스트레이터 연결 테스트")
    
    def _test_bot_token(self) -> IntegrationResult:
        try:
            url = "https://slack.com/api/auth.test"
            headers = {"Authorization": f"Bearer {self.bot_token}", "Content-Type": "application/json"}
            response = requests.post(url, headers=headers, timeout=10)
            data = response.json()
            
            if data.get("ok"):
                return IntegrationResult(
                    success=True,
                    message=f"연결 성공: {data.get('team', 'Unknown')} 워크스페이스",
                    data=data
                )
            else:
                error = data.get("error", "알 수 없는 오류")
                return IntegrationResult(success=False, message=f"Slack 오류: {error}")
        except requests.exceptions.RequestException as e:
            return IntegrationResult(success=False, message=f"연결 오류: {str(e)}")
    
    def send_message(self, text: str, blocks: Optional[list] = None) -> IntegrationResult:
        if self.use_bot_token:
            return self._send_via_bot_token(text, blocks)
        else:
            return self._send_via_webhook(text, blocks)
    
    def _send_via_webhook(self, text: str, blocks: Optional[list] = None) -> IntegrationResult:
        try:
            payload = {"text": text}
            if blocks:
                payload["blocks"] = blocks
            
            response = requests.post(self.webhook_url, json=payload, timeout=10)
            
            if response.status_code == 200 and response.text == "ok":
                return IntegrationResult(success=True, message="Slack 메시지 전송 완료")
            else:
                if "<!DOCTYPE html>" in response.text:
                    return IntegrationResult(success=False, message="Webhook URL이 올바르지 않습니다.")
                return IntegrationResult(success=False, message=f"Slack 전송 실패: {response.text[:100]}")
        except requests.exceptions.RequestException as e:
            return IntegrationResult(success=False, message=f"Slack 오류: {str(e)}")
    
    def _send_via_bot_token(self, text: str, blocks: Optional[list] = None) -> IntegrationResult:
        try:
            url = "https://slack.com/api/chat.postMessage"
            headers = {"Authorization": f"Bearer {self.bot_token}", "Content-Type": "application/json"}
            payload = {"channel": self.channel_id, "text": text}
            if blocks:
                payload["blocks"] = blocks
            
            response = requests.post(url, headers=headers, json=payload, timeout=10)
            data = response.json()
            
            if data.get("ok"):
                return IntegrationResult(success=True, message="Slack 메시지 전송 완료", data={"ts": data.get("ts")})
            else:
                return IntegrationResult(success=False, message=f"Slack 오류: {data.get('error')}")
        except requests.exceptions.RequestException as e:
            return IntegrationResult(success=False, message=f"Slack 오류: {str(e)}")
    
    def send_workflow_notification(
        self, title: str, intent: str, department: str, priority: str, ticket_id: Optional[str] = None
    ) -> IntegrationResult:
        priority_emoji = {"Low": "🟢", "Medium": "🟡", "High": "🟠", "Critical": "🔴",
                         "낮음": "🟢", "보통": "🟡", "높음": "🟠", "긴급": "🔴"}
        emoji = priority_emoji.get(priority, "⚪")
        
        blocks = [
            {"type": "header", "text": {"type": "plain_text", "text": f"📋 {title}", "emoji": True}},
            {"type": "section", "fields": [
                {"type": "mrkdwn", "text": f"*의도:*\n{intent}"},
                {"type": "mrkdwn", "text": f"*담당 부서:*\n{department}"},
                {"type": "mrkdwn", "text": f"*우선순위:*\n{emoji} {priority}"},
            ]}
        ]
        if ticket_id:
            blocks[1]["fields"].append({"type": "mrkdwn", "text": f"*티켓 ID:*\n{ticket_id}"})
        blocks.append({"type": "context", "elements": [{"type": "mrkdwn", "text": "📤 AI 워크플로우 오케스트레이터"}]})
        
        return self.send_message(f"새 워크플로우: {title} - {intent}", blocks)


@register_integration("Email", EmailConfig)
class EmailClient(BaseIntegrationClient):
    """이메일 SMTP 클라이언트"""
    
    system_name = "Email"
    
    def __init__(self, config: EmailConfig):
        self.config = config
    
    @classmethod
    def get_supported_actions(cls) -> list[str]:
        return ["send_email", "send_notification", "test_connection"]
    
    def execute(self, action: str, context: dict) -> IntegrationResult:
        """Email 액션을 실행합니다."""
        if action in ["send_email", "send_notification"]:
            return self.send_workflow_notification(
                title=context.get("title", "새 워크플로우"),
                intent=context.get("intent", ""),
                department=context.get("department", ""),
                priority=context.get("priority", "Medium"),
                workflow_steps=context.get("workflow_steps", []),
                ticket_id=context.get("ticket_id")
            )
        elif action == "test_connection":
            return self.test_connection()
        elif action == "execute":
            return self.send_workflow_notification(
                title=context.get("title", "새 워크플로우"),
                intent=context.get("intent", ""),
                department=context.get("department", ""),
                priority=context.get("priority", "Medium"),
                workflow_steps=context.get("workflow_steps", []),
                ticket_id=context.get("ticket_id")
            )
        else:
            return IntegrationResult(success=False, message=f"지원하지 않는 액션: {action}")
    
    def test_connection(self) -> IntegrationResult:
        try:
            server = smtplib.SMTP(self.config.smtp_server, self.config.smtp_port)
            server.starttls()
            server.login(self.config.sender_email, self.config.sender_password)
            server.quit()
            return IntegrationResult(success=True, message="이메일 서버 연결 성공")
        except smtplib.SMTPAuthenticationError:
            return IntegrationResult(success=False, message="이메일 인증 실패: 앱 비밀번호를 확인하세요")
        except Exception as e:
            return IntegrationResult(success=False, message=f"연결 오류: {str(e)}")
    
    def send_email(self, subject: str, body: str, to_email: Optional[str] = None, html_body: Optional[str] = None) -> IntegrationResult:
        try:
            recipient = to_email or self.config.recipient_email
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = self.config.sender_email
            msg["To"] = recipient
            msg.attach(MIMEText(body, "plain", "utf-8"))
            if html_body:
                msg.attach(MIMEText(html_body, "html", "utf-8"))
            
            server = smtplib.SMTP(self.config.smtp_server, self.config.smtp_port)
            server.starttls()
            server.login(self.config.sender_email, self.config.sender_password)
            server.sendmail(self.config.sender_email, recipient, msg.as_string())
            server.quit()
            
            return IntegrationResult(success=True, message=f"이메일 발송 완료: {recipient}")
        except Exception as e:
            return IntegrationResult(success=False, message=f"이메일 발송 실패: {str(e)}")
    
    def send_workflow_notification(
        self, title: str, intent: str, department: str, priority: str,
        workflow_steps: list[str] = None, ticket_id: Optional[str] = None
    ) -> IntegrationResult:
        workflow_steps = workflow_steps or ["워크플로우 실행됨"]
        subject = f"[AI 워크플로우] {title}"
        steps_text = "\n".join([f"  {i+1}. {step}" for i, step in enumerate(workflow_steps)])
        
        body = f"""AI 워크플로우 오케스트레이터 알림

의도: {intent}
담당 부서: {department}
우선순위: {priority}
{"티켓 ID: " + ticket_id if ticket_id else ""}

워크플로우 단계:
{steps_text}
"""
        return self.send_email(subject, body)


def get_registered_systems() -> list[str]:
    """등록된 모든 시스템 목록을 반환합니다."""
    return IntegrationRegistry.get_registered_systems()


def get_client(system_name: str, config) -> Optional[BaseIntegrationClient]:
    """시스템 클라이언트를 가져옵니다."""
    return IntegrationRegistry.get_client(system_name, config)
