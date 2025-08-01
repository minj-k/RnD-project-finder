# app.py
# 필요 라이브러리 설치: pip install streamlit
import streamlit as st
from dotenv import load_dotenv
from collector import DataCollector
from analyzer import ContextAnalyzer
from generator import ProposalGenerator

# 페이지 설정
st.set_page_config(page_title="🤖 지능형 연구과제 제안서 생성기", layout="wide")

# 모델/클래스 인스턴스 초기화 (캐싱을 통해 반복 로딩 방지)
@st.cache_resource
def load_models():
    load_dotenv()
    collector = DataCollector()
    analyzer = ContextAnalyzer()
    generator = ProposalGenerator()
    return collector, analyzer, generator

collector, analyzer, generator = load_models()

# --- UI 레이아웃 ---
st.title("🤖 지능형 연구과제 제안서 생성기")
st.markdown("아이디어를 입력하면 AI가 최신 트렌드를 분석하여 과제 제안서 초안을 생성해 드립니다.")

with st.form("proposal_form"):
    user_topic = st.text_input(
        "**1. 연구 주제 또는 아이디어를 입력하세요:**", 
        placeholder="예: 생성형 AI를 활용한 개인 맞춤형 교육 콘텐츠 자동 생성 플랫폼"
    )
    
    col1, col2 = st.columns(2)
    with col1:
        source = st.selectbox("**2. 정보 소스를 선택하세요:**", ("ntis", "keit"))
    with col2:
        context_count = st.slider("**3. 분석할 관련 과제 수:**", min_value=3, max_value=20, value=5)

    submitted = st.form_submit_button("🚀 제안서 생성 시작하기")

if submitted and user_topic:
    with st.spinner("1. 최신 과제 데이터를 수집 중입니다..."):
        projects = collector.collect(source=source, keyword=user_topic, limit=50)

    if projects:
        with st.spinner("2. 주제와 관련성 높은 컨텍스트를 분석 및 랭킹 중입니다..."):
            ranked_context = analyzer.get_ranked_context(user_topic, projects, top_k=context_count)
        
        st.subheader("📊 핵심 컨텍스트 분석 결과")
        st.markdown(f"**'{user_topic}'** 와 가장 관련성이 높은 최신 과제들입니다.")
        for project in ranked_context:
            st.info(f"**{project['title']}** (기관: {project['agency']})")

        with st.spinner("3. LLM이 제안서를 단계적으로 생성 중입니다... (1~2분 소요)"):
            final_proposal = generator.generate_full_proposal(user_topic, ranked_context)
        
        st.subheader("📄 AI가 생성한 최종 제안서 초안")
        st.markdown(final_proposal)

    else:
        st.error("관련 과제 데이터를 수집하는 데 실패했습니다. 키워드를 변경하여 다시 시도해 보세요.")
