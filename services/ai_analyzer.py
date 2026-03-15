"""
AI 이메일 분석기 서비스

OpenAI의 LLM API를 사용하여 이메일 분석 기능을 제공합니다.
고객 이메일에서 의도, 부서, 우선순위, 신뢰도를 추출합니다.
"""

import json
import os
from pathlib import Path
from typing import TypedDict

from openai import OpenAI


class AnalysisResult(TypedDict):
    intent: str
    department: str
    priority: str
    confidence: float


def _load_prompt_template() -> str:
    """파일에서 이메일 분석 프롬프트 템플릿을 로드합니다."""
    prompt_path = Path(__file__).parent.parent / "prompts" / "email_analysis_prompt.txt"
    with open(prompt_path, "r", encoding="utf-8") as f:
        return f.read()


def analyze_email(email_text: str, api_key: str | None = None) -> AnalysisResult:
    """
    LLM을 사용하여 고객 이메일을 분석하고 구조화된 데이터를 추출합니다.
    
    Args:
        email_text: 분석할 원본 이메일 텍스트
        api_key: OpenAI API 키 (선택사항, 환경 변수로 대체 가능)
    
    Returns:
        의도, 부서, 우선순위, 신뢰도를 포함하는 AnalysisResult
    
    Raises:
        ValueError: LLM 응답을 유효한 JSON으로 파싱할 수 없는 경우
        openai.APIError: OpenAI API 호출에 문제가 있는 경우
    """
    client = OpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))
    
    prompt_template = _load_prompt_template()
    prompt = prompt_template.replace("{email_text}", email_text)
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": "You are an enterprise workflow assistant. Always respond with valid JSON only."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.3,
        response_format={"type": "json_object"}
    )
    
    result_text = response.choices[0].message.content
    
    try:
        result = json.loads(result_text)
    except json.JSONDecodeError as e:
        raise ValueError(f"LLM 응답을 JSON으로 파싱하는데 실패했습니다: {e}")
    
    required_fields = ["intent", "department", "priority", "confidence"]
    for field in required_fields:
        if field not in result:
            raise ValueError(f"LLM 응답에 필수 필드가 누락되었습니다: {field}")
    
    if not isinstance(result["confidence"], (int, float)):
        try:
            result["confidence"] = float(result["confidence"])
        except (ValueError, TypeError):
            result["confidence"] = 0.5
    
    result["confidence"] = max(0.0, min(1.0, result["confidence"]))
    
    return AnalysisResult(
        intent=str(result["intent"]),
        department=str(result["department"]),
        priority=str(result["priority"]),
        confidence=float(result["confidence"])
    )
