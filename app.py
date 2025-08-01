# app.py (Final Version)
import streamlit as st
from dotenv import load_dotenv
from collector import DataCollector
from analyzer import ContextAnalyzer
from generator import ProposalGenerator

st.set_page_config(
    page_title="🤖 지능형 연구과제 제안서 생성기",
    page_icon="🤖",
    layout="wide"
)

# --- 모델 및 클래스 로딩 ---
@st.cache_resource
def load_models():
    """필요한 모든 클래스 인스턴스를 초기화하고 로드합니다."""
    load_dotenv()  # .env 파일에서 환경 변수(API 키 등) 로드
    collector = DataCollector()
    analyzer = ContextAnalyzer()
    generator = ProposalGenerator()
    return collector, analyzer, generator

# --- 메인 애플리케이션 로직 ---
try:
    collector, analyzer, generator = load_models()
    
    # --- UI 레이아웃 ---
    st.title("🤖 지능형 연구과제 제안서 생성기")
    st.markdown("아이디어를 입력하면 AI가 최신 정부 R&D 트렌드를 분석하여 과제 제안서 초안을 생성합니다.")
    st.markdown("---")

    with st.form("proposal_form"):
        user_topic = st.text_input(
            "**1. 연구 주제 또는 핵심 아이디어를 입력하세요:**",
            placeholder="예: 생성형 AI를 활용한 개인 맞춤형 교육 콘텐츠 자동 생성 플랫폼"
        )
        
        col1, col2 = st.columns(2)
        with col1:
            source = st.selectbox("**2. 분석할 정보 소스를 선택하세요:**", ("ntis",)) # 현재는 ntis만 지원
        with col2:
            # 분석할 관련 과제 수를 사용자가 선택할 수 있도록 슬라이더 추가
            context_count = st.slider("**3. 참고할 관련 과제 수:**", min_value=3, max_value=15, value=5)

        submitted = st.form_submit_button("🚀 제안서 생성 시작하기")

    # 제출 버튼이 눌리고, 사용자 주제가 입력되었을 경우에만 아래 로직 실행
    if submitted and user_topic:
        st.markdown("---")
        
        # 1단계: 데이터 수집
        with st.spinner("1/3 | 최신 과제 데이터를 수집 중입니다... (NTIS)"):
            # ⚠️ 수정된 부분: keyword 인자 없이 호출합니다.
            projects = collector.collect(source=source, limit=100) # 최근 1개월 데이터 중 최대 100개를 가져옴

        # 수집된 데이터가 있을 경우 계속 진행
        if projects:
            # 2단계: 컨텍스트 분석
            with st.spinner(f"2/3 | '{user_topic}'와 관련성 높은 컨텍스트를 분석 중입니다..."):
                ranked_context = analyzer.get_ranked_context(user_topic, projects, top_k=context_count)
            
            # 분석 결과를 사용자에게 시각적으로 보여줌
            st.subheader("📊 핵심 컨텍스트 분석 결과")
            st.info(f"최근 1개월간 공고된 과제 중, 입력하신 주제와 가장 관련성이 높은 **{len(ranked_context)}개**의 과제입니다.")
            for project in ranked_context:
                st.write(
                    f"[{project.get('title')}]({project.get('url')})  \n"
                    f"_{project.get('department')} | 마감일: {project.get('end_date')}_"
                )

            # 3단계: 제안서 생성
            with st.spinner("3/3 | AI가 제안서를 단계적으로 생성 중입니다... (1~2분 소요)"):
                final_proposal = generator.generate_full_proposal(user_topic, ranked_context)
            
            st.markdown("---")
            st.subheader("📄 AI가 생성한 최종 제안서 초안")
            # st.markdown을 사용해 마크다운 형식의 결과물을 깔끔하게 렌더링
            st.markdown(final_proposal)

        else:
            st.error("관련 과제 데이터를 수집하는 데 실패했습니다. 잠시 후 다시 시도해 주세요.")

except Exception as e:
    # 앱 실행 중 발생할 수 있는 모든 예외를 처리하여 사용자에게 오류 메시지를 보여줌
    st.error(f"앱 실행 중 오류가 발생했습니다: {e}")

