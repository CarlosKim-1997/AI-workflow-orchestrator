"""
통합 클라이언트 베이스 모듈

모든 외부 시스템 연동 클라이언트의 추상 베이스 클래스와
플러그인 레지스트리를 정의합니다.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, Type, Dict, Any


@dataclass
class IntegrationResult:
    """연동 작업 결과"""
    success: bool
    message: str
    data: Optional[dict] = None


@dataclass
class BaseConfig(ABC):
    """연동 설정 베이스 클래스"""
    enabled: bool = False
    
    @abstractmethod
    def is_valid(self) -> bool:
        """설정이 유효한지 확인합니다."""
        pass
    
    @abstractmethod
    def get_validation_errors(self) -> list[str]:
        """누락된 설정 필드 목록을 반환합니다."""
        pass


class BaseIntegrationClient(ABC):
    """
    모든 외부 시스템 연동 클라이언트의 추상 베이스 클래스
    
    새로운 시스템을 추가하려면:
    1. 이 클래스를 상속
    2. 필수 메서드 구현
    3. IntegrationRegistry에 등록
    """
    
    system_name: str = "Unknown"
    
    @abstractmethod
    def __init__(self, config: Any):
        """클라이언트를 초기화합니다."""
        pass
    
    @abstractmethod
    def test_connection(self) -> IntegrationResult:
        """연결을 테스트합니다."""
        pass
    
    @abstractmethod
    def execute(self, action: str, context: dict) -> IntegrationResult:
        """
        주어진 액션을 실행합니다.
        
        Args:
            action: 실행할 액션 (예: "create_ticket", "send_message")
            context: 워크플로우 컨텍스트 데이터
        
        Returns:
            IntegrationResult: 실행 결과
        """
        pass
    
    @classmethod
    def get_supported_actions(cls) -> list[str]:
        """지원하는 액션 목록을 반환합니다."""
        return []


class IntegrationRegistry:
    """
    통합 클라이언트 레지스트리 (싱글톤)
    
    새로운 시스템 추가 방법:
    
    ```python
    from services.base import IntegrationRegistry, BaseIntegrationClient
    
    class MySAPClient(BaseIntegrationClient):
        system_name = "SAP"
        # ... 구현 ...
    
    # 등록
    IntegrationRegistry.register("SAP", MySAPClient, SAPConfig)
    ```
    """
    
    _clients: Dict[str, Type[BaseIntegrationClient]] = {}
    _configs: Dict[str, Type[BaseConfig]] = {}
    _instances: Dict[str, BaseIntegrationClient] = {}
    
    @classmethod
    def register(
        cls,
        system_name: str,
        client_class: Type[BaseIntegrationClient],
        config_class: Type[BaseConfig] = None
    ):
        """
        새로운 통합 클라이언트를 등록합니다.
        
        Args:
            system_name: 시스템 이름 (예: "SAP", "ServiceNow")
            client_class: 클라이언트 클래스
            config_class: 설정 클래스 (선택사항)
        """
        cls._clients[system_name] = client_class
        if config_class:
            cls._configs[system_name] = config_class
        print(f"[Registry] '{system_name}' 클라이언트 등록됨")
    
    @classmethod
    def unregister(cls, system_name: str):
        """클라이언트 등록을 해제합니다."""
        if system_name in cls._clients:
            del cls._clients[system_name]
        if system_name in cls._configs:
            del cls._configs[system_name]
        if system_name in cls._instances:
            del cls._instances[system_name]
    
    @classmethod
    def get_client(cls, system_name: str, config: Any = None) -> Optional[BaseIntegrationClient]:
        """
        등록된 클라이언트 인스턴스를 반환합니다.
        
        Args:
            system_name: 시스템 이름
            config: 설정 객체
        
        Returns:
            클라이언트 인스턴스 또는 None
        """
        if system_name not in cls._clients:
            return None
        
        cache_key = f"{system_name}_{id(config)}"
        
        if cache_key not in cls._instances:
            client_class = cls._clients[system_name]
            cls._instances[cache_key] = client_class(config)
        
        return cls._instances[cache_key]
    
    @classmethod
    def is_registered(cls, system_name: str) -> bool:
        """시스템이 등록되어 있는지 확인합니다."""
        return system_name in cls._clients
    
    @classmethod
    def get_registered_systems(cls) -> list[str]:
        """등록된 모든 시스템 이름을 반환합니다."""
        return list(cls._clients.keys())
    
    @classmethod
    def get_config_class(cls, system_name: str) -> Optional[Type[BaseConfig]]:
        """시스템의 설정 클래스를 반환합니다."""
        return cls._configs.get(system_name)
    
    @classmethod
    def clear(cls):
        """모든 등록을 초기화합니다 (테스트용)."""
        cls._clients.clear()
        cls._configs.clear()
        cls._instances.clear()


def register_integration(system_name: str, config_class: Type[BaseConfig] = None):
    """
    클라이언트 클래스를 레지스트리에 등록하는 데코레이터
    
    사용법:
    ```python
    @register_integration("SAP", SAPConfig)
    class SAPClient(BaseIntegrationClient):
        ...
    ```
    """
    def decorator(cls: Type[BaseIntegrationClient]):
        cls.system_name = system_name
        IntegrationRegistry.register(system_name, cls, config_class)
        return cls
    return decorator
