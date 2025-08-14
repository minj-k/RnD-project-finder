# analyzer.py

import pandas as pd
from sklearn.preprocessing import MinMaxScaler

def analyze_and_select_project(projects_df, keyword):
    """
    수집된 과제들에 대해 점수를 매겨 가장 적합한 과제를 선택하는 분석기.
    - 점수 기준: 정부투자연구비(60%) + 연구내용 내 키워드 빈도(40%)
    """
    if projects_df.empty:
        return None  # 분석할 과제가 없으면 None 반환

    # 복사본을 만들어 원본 데이터프레임의 변경을 방지
    df = projects_df.copy()

    # --- 1. 정부투자연구비 점수 계산 (정규화) ---
    # MinMaxScaler를 사용하여 연구비 값을 0과 1 사이의 점수로 변환
    scaler = MinMaxScaler()
    # '정부투자연구비'가 0 또는 양수인 값만 필터링하여 음수 값으로 인한 오류 방지
    valid_budget = df[df['정부투자연구비'] >= 0][['정부투자연구비']]
    if not valid_budget.empty:
        df.loc[valid_budget.index, 'budget_score'] = scaler.fit_transform(valid_budget)
    df['budget_score'] = df['budget_score'].fillna(0) # 유효하지 않은 값은 0으로 처리

    # --- 2. 키워드 빈도 점수 계산 (정규화) ---
    # '연구내용' 컬럼이 문자열이 아닌 경우를 대비해 str로 변환하고, 결측값(NA)은 빈 문자열로 대체
    df['keyword_freq'] = df['연구내용'].astype(str).str.count(keyword)
    
    # MinMaxScaler를 사용하여 키워드 빈도 값을 0과 1 사이의 점수로 변환
    valid_freq = df[df['keyword_freq'] >= 0][['keyword_freq']]
    if not valid_freq.empty:
        df.loc[valid_freq.index, 'freq_score'] = scaler.fit_transform(valid_freq)
    df['freq_score'] = df['freq_score'].fillna(0) # 유효하지 않은 값은 0으로 처리

    # --- 3. 최종 점수 계산 (가중치 적용) ---
    # 설정한 가중치 6:4를 적용하여 최종 점수 계산
    df['total_score'] = (0.6 * df['budget_score']) + (0.4 * df['freq_score'])

    # --- 4. 최고 점수 과제 선택 ---
    # 최종 점수가 가장 높은 과제의 인덱스를 찾아 해당 행을 반환
    best_project_index = df['total_score'].idxmax()
    best_project = df.loc[best_project_index]

    return best_project
