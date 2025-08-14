# generator.py

import os
import google.generativeai as genai

class ProposalGenerator:
    def __init__(self):
        # 클래스 생성 시 API 키 설정 시도
        self.api_key_configured = self._setup_api_key()

    def _setup_api_key(self):
        """환경 변수에서 API 키를 설정합니다."""
        api_key = os.getenv("GOOGLE_API_KEY")
        if api_key:
            genai.configure(api_key=api_key)
            return True
        return False

    def generate_full_proposal(self, user_topic, ranked_context):
        """관련 과제 목록을 바탕으로 완전한 제안서를 생성합니다."""
        if not self.api_key_configured:
            return "오류: GOOGLE_API_KEY가 .env 파일에 설정되지 않았습니다."
        if not ranked_context:
            return "오류: 분석된 참고 과제가 없습니다."

        # 여러 참고 과제 정보를 프롬프트에 포함시키기 위해 문자열로 변환
        context_str = ""
        for i, proj in enumerate(ranked_context, 1):
            context_str += f"\n--- 참고자료 {i} ---\n"
            context_str += f"과제명: {proj.get('pjtTitle', 'N/A')}\n"
            context_str += f"연구목표: {proj.get('pjtGoal', 'N/A')}\n"
            context_str += "----------------\n"

        prompt = f"""
        # 페르소나:
        당신은 대한민국 정부 R&D 과제 기획 전문가입니다.

        # 미션:
        '새로운 연구 주제'에 대한 혁신적인 R&D 과제 계획서 초안을 작성하세요.
        아래 '참고 자료'들을 종합적으로 분석하여, 각 자료의 강점을 흡수하고 독창적인 아이디어를 더해 설득력 있는 계획서를 만들어야 합니다.

        # 새로운 연구 주제:
        {user_topic}

        # 참고 자료 (관련도 높은 순):
        {context_str}

        # 결과물 형식 (반드시 이 목차를 준수하고, 각 항목을 상세히 서술하세요):
        ## 1. 제안배경 및 필요성
        ## 2. 연구개발의 최종 목표 및 내용
        ## 3. 연구 추진전략 및 체계
        ## 4. 기대효과 및 성과 활용 방안
        ## 5. 주요 핵심 키워드 (5개)
        """

        try:
            model = genai.GenerativeModel('gemini-1.5-pro-latest')
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"LLM API 호출 중 오류가 발생했습니다: {e}"
