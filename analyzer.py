# analyzer.py
# 필요 라이브러리 설치: pip install sentence-transformers scikit-learn
from sentence_transformers import SentenceTransformer, util
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from typing import List, Dict

class ContextAnalyzer:
    """
    수집된 데이터를 분석하여 LLM에 제공할 핵심 컨텍스트를 생성합니다.
    """
    def __init__(self, model_name='jhgan/ko-sroberta-multitask'):
        # 한국어 문장 임베딩에 특화된 모델 로드
        self.model = SentenceTransformer(model_name)
        logging.info(f"문장 임베딩 모델 '{model_name}' 로드 완료.")

    def get_ranked_context(self, user_topic: str, projects: List[Dict[str, str]], top_k: int = 5) -> List[Dict[str, str]]:
        """
        사용자 주제와 과제들 간의 의미 유사도를 계산하여 상위 K개의 컨텍스트를 반환합니다.
        """
        if not projects:
            return []
        
        # 과제 제목 리스트 생성
        project_titles = [p['title'] for p in projects]
        
        # 사용자 주제와 과제 제목들을 벡터로 변환 (임베딩)
        topic_embedding = self.model.encode(user_topic, convert_to_tensor=True)
        project_embeddings = self.model.encode(project_titles, convert_to_tensor=True)
        
        # 코사인 유사도 계산
        cos_scores = util.cos_sim(topic_embedding, project_embeddings)[0]
        
        # 점수가 높은 순으로 정렬하여 상위 K개의 인덱스 추출
        top_results_indices = np.argsort(-cos_scores)[:top_k]
        
        ranked_projects = [projects[i] for i in top_results_indices]
        logging.info(f"'{user_topic}'와 가장 관련성 높은 상위 {len(ranked_projects)}개의 과제를 선별했습니다.")
        
        return ranked_projects

# 사용 예시
# if __name__ == '__main__':
#     # 가상의 데이터
#     sample_projects = [{'title': '인공지능 기반 신약 개발 플랫폼 구축'}, {'title': '자율주행차를 위한 딥러닝 영상 인식 기술'}, {'title': '해양 생태계 모니터링 시스템'}]
#     analyzer = ContextAnalyzer()
#     ranked_context = analyzer.get_ranked_context("AI를 이용한 약물 후보물질 탐색", sample_projects)
#     print(ranked_context)
