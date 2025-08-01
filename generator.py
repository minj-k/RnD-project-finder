# generator.py (Updated to use detailed context)
import os
import logging
import google.generativeai as genai
from typing import List, Dict

class ProposalGenerator:
    """LLM을 이용해 상세 컨텍스트를 기반으로 연구 제안서를 단계적으로 생성합니다."""
    def __init__(self, model_name='gemini-1.5-pro-latest'):
        """
        Args:
            model_name (str): 사용할 Google Gemini 모델 이름.
        """
        try:
            api_key = os.getenv('GOOGLE_API_KEY')
            if not api_key:
                raise ValueError("GOOGLE_API_KEY 환경 변수가 설정되지 않았습니다.")
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel(model_name)
            logging.info(f"LLM 생성 모델 '{model_name}' 준비 완료.")
        except Exception as e:
            logging.error(f"LLM 모델 초기화 중 오류: {e}")
            self.model = None

    def _generate(self, prompt: str) -> str:
        """LLM API 호출을 위한 내부 헬퍼 함수"""
        if not self.model:
            return "오류: LLM 모델이 초기화되지 않았습니다."
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            logging.error(f"LLM 생성 중 오류: {e}")
            return f"오류: LLM API 호출에 실패했습니다. ({e})"

    def _format_context(self, ranked_context: List[Dict[str, str]]) -> str:
        """LLM에게 제공할 컨텍스트 문자열을 포맷팅합니다."""
        context_lines = []
        for p in ranked_context:
            line = (
                f"- 제목: {p.get('title', 'N/A')}\n"
                f"  (소관부처: {p.get('agency', 'N/A')}, "
                f"공고기관: {p.get('department', 'N/A')}, "
                f"마감일: {p.get('end_date', 'N/A')})"
            )
            context_lines.append(line)
        return "\n".join(context_lines)

    def generate_full_proposal(self, user_topic: str, ranked_context: List[Dict[str, str]]) -> str:
        """다단계 프롬프트를 통해 완전한 제안서를 생성합니다."""
        if not ranked_context:
            logging.warning("컨텍스트 정보 없이 제안서 생성을 시도합니다.")
        
        formatted_context = self._format_context(ranked_context)
        
        # 1단계: 제목 생성 프롬프트
        prompt1_title = f"""
**역할:** 당신은 대한민국 정부 R&D 과제 기획 전문가입니다.

**임무:** 아래 '핵심 연구 주제'와 '최신 관련 과제 동향'을 깊이 있게 분석하여, 정부 과제 심사위원의 주목을 받을 만한 혁신적이고 구체적인 국문 연구과제 제목 5개를 제안하시오. 제목에는 핵심 기술과 최종 목표가 명확히 드러나야 합니다.

**핵심 연구 주제:**
{user_topic}

**최신 관련 과제 동향 (컨텍스트):**
{formatted_context}

**결과물 (제목 5개만, 번호 목록으로):**
"""
        titles_text = self._generate(prompt1_title)
        
        # 생성된 제목 중 첫 번째 제목을 대표로 선택
        try:
            best_title = titles_text.splitlines()[0].split('. ')[1]
        except IndexError:
            best_title = user_topic # 제목 생성 실패 시 사용자 주제를 제목으로 사용
            titles_text = "1. " + user_topic

        # 2단계: 본문 생성 프롬프트
        prompt2_body = f"""
**역할:** 당신은 20년 경력의 수석 연구기획자(PI)로서, 정부 과제 제안서 최종본을 작성하고 있습니다.

**임무:** 아래 '선정된 연구 제목'과 '상세 기술 동향'을 바탕으로, 아래 목차에 맞춰 매우 상세하고 논리적인 연구 제안서 초안을 작성하시오. 문체는 전문적이고 설득력 있어야 하며, 각 항목은 2~3개의 문단으로 구체적인 근거를 들어 서술해야 합니다. 특히, 컨텍스트의 '소관부처'나 '공고기관'의 특성을 고려하여 제안서의 방향성을 맞추면 좋습니다.

**선정된 연구 제목:**
{best_title}

**상세 기술 동향 (컨텍스트):**
{formatted_context}

**작성할 목차:**
1.  **연구개발의 필요성:** 이 연구가 왜 지금 시급하고 중요한지 기술적, 사회적, 정책적 관점에서 구체적으로 설명. (예: '최근 OOO부에서 공고한 과제 동향을 볼 때...')
2.  **연구개발의 최종 목표 및 내용:** 과제를 통해 달성하고자 하는 정량적/정성적 최종 목표와, 이를 달성하기 위한 연차별 세부 연구 내용을 구체적으로 서술.
3.  **연구개발 방법 및 추진 전략:** 각 세부 연구 내용을 어떤 최신 기술과 검증된 방법론으로 수행할 것인지 구체적인 실행 계획을 제시.
4.  **기대효과 및 활용방안:** 연구 성공 시 예상되는 기술적 파급효과와, 결과물이 산업 및 공공 분야에서 어떻게 활용될 수 있는지 구체적인 계획을 제시.

**결과물 (Markdown 형식의 상세 서술):**
"""
        body_text = self._generate(prompt2_body)
        
        # 최종 결과물 조합
        final_proposal = f"# 제안서: {best_title}\n\n"
        final_proposal += "## AI 추천 과제 제목 리스트\n" + titles_text + "\n\n"
        final_proposal += "--- \n\n"
        final_proposal += "## 상세 제안 내용\n" + body_text
        
        return final_proposal
