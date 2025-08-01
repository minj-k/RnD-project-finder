# analyzer.py (Updated to use detailed context)
import logging
import numpy as np
from sentence_transformers import SentenceTransformer, util
from typing import List, Dict

class ContextAnalyzer:
    """
    수집된 상세 데이터를 분석하여 LLM에 제공할 핵심 컨텍스트를 생성합니다.
    제목과 기관 정보를 함께 사용하여 의미 유사도를 분석합니다.
    """
    def __init__(self, model_name='jhgan/ko-sroberta-multitask'):
        """
        Args:
            model_name (str): 한국어 문장 임베딩에 최적화된 Sentence Transformer 모델 이름.
        """
        try:
            self.model = SentenceTransformer(model_name)
            logging.info(f"문장 임베딩 모델 '{model_name}' 로드 완료.")
        except Exception as e:
            logging.error(f"모델 로딩 중 오류 발생: {e}")
            self.model = None

    def get_ranked_context(self, user_topic: str, projects: List[Dict[str, str]], top_k: int = 5) -> List[Dict[str, str]]:
        """
        사용자 주제와 과제들 간의 의미 유사도를 계산하여 상위 K개의 컨텍스트를 반환합니다.

        Args:
            user_topic (str): 사용자가 입력한 연구 주제.
            projects (List[Dict[str, str]]): DataCollector가 수집한 과제 리스트.
            top_k (int): 반환할 상위 관련 과제 개수.

        Returns:
            List[Dict[str, str]]: 관련도 순으로 정렬된 상위 K개의 과제 리스트.
        """
        if not self.model:
            logging.error("모델이 로드되지 않아 분석을 진행할 수 없습니다.")
            return []
        if not projects:
            logging.warning("분석할 프로젝트 데이터가 없습니다.")
            return []
        
        # 분석을 위해 '제목'과 '공고기관'을 합친 텍스트 생성
        # 예: "인공지능 기반 신약 개발 (한국연구재단)"
        context_texts = [f"{p.get('title', '')} ({p.get('department', '')})" for p in projects]
        
        # 사용자 주제와 과제 텍스트들을 벡터로 변환 (임베딩)
        topic_embedding = self.model.encode(user_topic, convert_to_tensor=True)
        project_embeddings = self.model.encode(context_texts, convert_to_tensor=True)
        
        # 코사인 유사도 계산
        cos_scores = util.cos_sim(topic_embedding, project_embeddings)[0]
        
        # 점수가 높은 순으로 정렬하여 상위 K개의 인덱스 추출
        # argsort는 오름차순이므로, 음수로 만들어 내림차순 효과를 줌
        top_results_indices = np.argsort(-cos_scores.cpu().numpy())[:top_k]
        
        ranked_projects = [projects[i] for i in top_results_indices]
        logging.info(f"'{user_topic}'와 가장 관련성 높은 상위 {len(ranked_projects)}개의 과제를 선별했습니다.")
        
        return ranked_projects
