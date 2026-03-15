"""
설정 관리 모듈

외부 시스템 연동에 필요한 설정을 관리합니다.
환경변수, Streamlit secrets, 또는 직접 입력을 통해 설정을 로드합니다.
"""

import os
from dataclasses import dataclass, field
from typing import Optional, Dict


@dataclass
class JiraConfig:
    """Jira Cloud 연동 설정"""
    enabled: bool = False
    base_url: str = ""
    email: str = ""
    api_token: str = ""
    project_key: str = ""
    # 부서별 담당자 배정: 부서명 -> Jira accountId (이슈 생성 시 해당 담당자에게 자동 배정)
    department_assignee_mapping: Dict[str, str] = field(default_factory=dict)
    
    def is_valid(self) -> bool:
        """설정이 유효한지 확인합니다."""
        return all([
            self.enabled,
            self.base_url,
            self.email,
            self.api_token,
            self.project_key
        ])
    
    def get_validation_errors(self) -> list[str]:
        """누락된 설정 필드 목록을 반환합니다."""
        errors = []
        if not self.base_url:
            errors.append("Jira URL이 필요합니다")
        if not self.email:
            errors.append("Jira 이메일이 필요합니다")
        if not self.api_token:
            errors.append("Jira API 토큰이 필요합니다")
        if not self.project_key:
            errors.append("프로젝트 키가 필요합니다")
        return errors


@dataclass
class SlackConfig:
    """Slack 연동 설정 (Webhook 또는 Bot Token 방식)"""
    enabled: bool = False
    use_bot_token: bool = False
    webhook_url: str = ""
    bot_token: str = ""
    channel_id: str = ""
    
    def is_valid(self) -> bool:
        """설정이 유효한지 확인합니다."""
        if not self.enabled:
            return False
        if self.use_bot_token:
            return bool(self.bot_token and self.channel_id)
        else:
            return bool(self.webhook_url)
    
    def get_validation_errors(self) -> list[str]:
        """누락된 설정 필드 목록을 반환합니다."""
        errors = []
        if self.use_bot_token:
            if not self.bot_token:
                errors.append("Bot Token이 필요합니다")
            if not self.channel_id:
                errors.append("채널 ID가 필요합니다")
        else:
            if not self.webhook_url:
                errors.append("Slack Webhook URL이 필요합니다")
        return errors


@dataclass
class EmailConfig:
    """이메일 SMTP 연동 설정"""
    enabled: bool = False
    smtp_server: str = "smtp.gmail.com"
    smtp_port: int = 587
    sender_email: str = ""
    sender_password: str = ""
    recipient_email: str = ""
    
    def is_valid(self) -> bool:
        """설정이 유효한지 확인합니다."""
        return all([
            self.enabled,
            self.smtp_server,
            self.sender_email,
            self.sender_password,
            self.recipient_email
        ])
    
    def get_validation_errors(self) -> list[str]:
        """누락된 설정 필드 목록을 반환합니다."""
        errors = []
        if not self.sender_email:
            errors.append("발신자 이메일이 필요합니다")
        if not self.sender_password:
            errors.append("앱 비밀번호가 필요합니다")
        if not self.recipient_email:
            errors.append("수신자 이메일이 필요합니다")
        return errors


@dataclass
class IntegrationConfig:
    """전체 연동 설정을 관리합니다."""
    jira: JiraConfig = field(default_factory=JiraConfig)
    slack: SlackConfig = field(default_factory=SlackConfig)
    email: EmailConfig = field(default_factory=EmailConfig)
    simulation_mode: bool = True
    demo_assignee_by_department: Dict[str, str] = field(default_factory=dict)
    
    def has_any_integration(self) -> bool:
        return any([
            self.jira.is_valid(),
            self.slack.is_valid(),
            self.email.is_valid(),
        ])

    def get_active_integrations(self) -> list[str]:
        active = []
        if self.jira.is_valid():
            active.append("Jira")
        if self.slack.is_valid():
            active.append("Slack")
        if self.email.is_valid():
            active.append("Email")
        return active


def load_config_from_env() -> IntegrationConfig:
    """환경변수에서 설정을 로드합니다."""
    config = IntegrationConfig()
    
    jira_url = os.getenv("JIRA_BASE_URL", "")
    if jira_url:
        config.jira = JiraConfig(
            enabled=True,
            base_url=jira_url,
            email=os.getenv("JIRA_EMAIL", ""),
            api_token=os.getenv("JIRA_API_TOKEN", ""),
            project_key=os.getenv("JIRA_PROJECT_KEY", "")
        )
    
    slack_bot_token = os.getenv("SLACK_BOT_TOKEN", "")
    slack_channel_id = os.getenv("SLACK_CHANNEL_ID", "")
    if slack_bot_token and slack_channel_id:
        config.slack = SlackConfig(
            enabled=True,
            use_bot_token=True,
            bot_token=slack_bot_token,
            channel_id=slack_channel_id
        )
    else:
        slack_webhook = os.getenv("SLACK_WEBHOOK_URL", "")
        if slack_webhook:
            config.slack = SlackConfig(
                enabled=True,
                use_bot_token=False,
                webhook_url=slack_webhook
            )

    email_sender = os.getenv("EMAIL_SENDER", "")
    if email_sender:
        config.email = EmailConfig(
            enabled=True,
            smtp_server=os.getenv("SMTP_SERVER", "smtp.gmail.com"),
            smtp_port=int(os.getenv("SMTP_PORT", "587")),
            sender_email=email_sender,
            sender_password=os.getenv("EMAIL_PASSWORD", ""),
            recipient_email=os.getenv("EMAIL_RECIPIENT", "")
        )
    
    return config
