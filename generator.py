# generator.py
import os
import google.generativeai as genai
from typing import List, Dict

class ProposalGenerator:
    """LLM을 이용해 단계적으로 연구 제안서를 생성합니다."""
    def __init__(self, model_name='gemini-1.5-pro-latest'):
        genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))
        self.model = genai.GenerativeModel(model_name)
        logging.info(f"LLM 생성 모델 '{model_name}' 준비 완료.")

    def _generate(self, prompt: str) -> str:
        """LLM API 호출을 위한 내부 함수"""
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            logging.error(f"LLM 생성 중 오류: {e}")
            return f"오류: {e}"

    def generate_full_proposal(self, user_topic: str, ranked_context: List[Dict[str, str]]) -> str:
        """다단계 프롬프트를 통해 완전한 제안서를 생성합니다."""
        
        # 1단계: 제목 생성
        context_str = "\n".join([f"- {p['title']} ({p['agency']})" for p in ranked_context])
        prompt1_title = f"""
        **역할:** 당신은 대한민국 정부 R&D 과제 공고를 위한 전문 카피라이터입니다.
        
        **임무:** 아래 '핵심 연구 주제'와 '최신 관련 과제 동향'을 참고하여, 심사위원의 시선을 사로잡을 혁신적이고 구체적인 연구과제 국문 제목 5개를 제안하시오. 제목은 핵심 기술과 최종 목표가 명확히 드러나야 합니다.

        **핵심 연구 주제:** {user_topic}
        
        **최신 관련 과제 동향:**
        {context_str}
        
        **결과물 (제목 5개만):**
        """
        titles_text = self._generate(prompt1_title)
        
        # 2단계: 생성된 제목과 컨텍스트를 기반으로 본문 생성
        prompt2_body = f"""
        **역할:** 당신은 20년 경력의 수석 연구기획자(PI)입니다. 현재 정부 과제 제안서를 작성 중입니다.
        
        **임무:** 아래 '선정된 연구 제목'과 '관련 기술 동향'을 바탕으로, 아래 목차에 맞춰 상세한 연구 제안서 초안을 작성하시오. 문체는 전문적이고 논리적이며, 설득력 있어야 합니다. 각 항목은 2~3문단으로 상세히 서술하시오.

        **선정된 연구 제목:**
        {titles_text.splitlines()[0]}

        **관련 기술 동향(컨텍스트):**
        {context_str}
        
        **작성할 목차:**
        1.  **연구의 필요성:** 이 연구가 왜 지금 중요한지 기술적, 사회적, 경제적 관점에서 설명. 기존 연구의 한계점 지적.
        2.  **연구의 최종 목표 및 내용:** 과제를 통해 달성하고자 하는 정량적/정성적 최종 목표와 이를 위한 세부 연구 내용(예: 1차년도-OO개발, 2차년도-XX고도화)을 구체적으로 서술.
        3.  **연구 방법 및 추진 전략:** 각 세부 연구 내용을 어떤 기술과 방법론(예: Transformer 기반 언어모델, 전이학습 등)으로 수행할 것인지 구체적인 실행 계획을 제시.
        4.  **기대효과 및 활용방안:** 연구 성공 시 예상되는 기술적 파급효과와 산업/공공 분야에서의 구체적인 활용 계획을 제시.

        **결과물 (목차에 따른 상세 서술):**
        """
        body_text = self._generate(prompt2_body)
        
        final_proposal = f"# 제안서: {titles_text.splitlines()[0]}\n\n"
        final_proposal += "## 생성된 추천 제목 리스트\n" + titles_text + "\n\n"
        final_proposal += "## 상세 제안 내용\n" + body_text
        
        return final_proposal
