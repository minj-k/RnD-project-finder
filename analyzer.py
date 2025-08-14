# analyzer.py

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import pandas as pd

class ContextAnalyzer:
    def get_ranked_context(self, user_topic, projects, top_k=5):
        """사용자 주제와 과제 목록 간의 관련도 순위를 매겨 상위 k개를 반환합니다."""
        if not projects:
            return []
            
        # 프로젝트 데이터를 DataFrame으로 변환
        df = pd.DataFrame(projects)
        # 분석에 사용할 텍스트를 하나로 합침 (제목 + 목표 + 내용 + 키워드)
        df['corpus'] = (
            df['pjtTitle'].fillna('') + ' ' +
            df['pjtGoal'].fillna('') + ' ' +
            df['pjtContent'].fillna('') + ' ' +
            df['pjtKeyword'].fillna('')
        )

        # 사용자 주제와 각 과제의 corpus를 리스트로 합침
        all_texts = [user_topic] + df['corpus'].tolist()

        # TF-IDF 벡터화
        vectorizer = TfidfVectorizer()
        tfidf_matrix = vectorizer.fit_transform(all_texts)
        
        # 코사인 유사도 계산 (첫 번째 벡터(사용자 주제)와 나머지 모든 벡터(과제) 간의 유사도)
        cosine_sim = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:])
        
        # 유사도 점수를 DataFrame에 추가하고 정렬
        df['similarity'] = cosine_sim[0]
        ranked_df = df.sort_values(by='similarity', ascending=False)
        
        # 상위 top_k개의 결과를 딕셔너리 리스트로 변환하여 반환
        top_projects = ranked_df.head(top_k).to_dict(orient='records')
        
        return top_projects
