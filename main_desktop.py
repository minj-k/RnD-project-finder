# main_desktop.py 파일의 Worker 클래스 부분만 수정

class Worker(QObject):
    finished = Signal(str)
    progress = Signal(str)

    def __init__(self, user_topic, source, context_count):
        super().__init__()
        self.user_topic = user_topic
        self.source = source
        self.context_count = context_count
        
        load_dotenv()
        self.collector = DataCollector()
        self.analyzer = ContextAnalyzer()
        self.generator = ProposalGenerator()

    def run(self):
        """오류 추적 기능이 강화된 작업 실행 메소드"""
        try:
            # --- 1. 데이터 수집 단계 ---
            self.progress.emit("1/3 | 데이터 수집 시작...")
            print("[체크포인트] 1. Collector 호출 시작")
            projects = self.collector.collect(
                source=self.source, topic=self.user_topic, limit=100
            )
            print("[체크포인트] 1. Collector 호출 완료")

            if not projects:
                error_message = f"'{self.user_topic}'에 대한 데이터를 수집하지 못했거나 검색 결과가 없습니다."
                self.finished.emit(f"오류: {error_message}")
                return

            # --- 2. 컨텍스트 분석 단계 ---
            self.progress.emit("2/3 | 컨텍스트 분석 시작...")
            print("[체크포인트] 2. Analyzer 호출 시작")
            ranked_context = self.analyzer.get_ranked_context(
                self.user_topic, projects, top_k=self.context_count
            )
            print("[체크포인트] 2. Analyzer 호출 완료")

            # --- 3. 제안서 생성 단계 ---
            self.progress.emit("3/3 | AI 제안서 생성 시작...")
            print("[체크포인트] 3. Generator 호출 시작")
            final_proposal = self.generator.generate_full_proposal(
                self.user_topic, ranked_context
            )
            print("[체크포인트] 3. Generator 호출 완료")
            
            self.finished.emit(final_proposal)

        except Exception as e:
            # ▼▼▼ 어떤 종류의 오류든 여기서 잡아서 상세하게 보여줍니다 ▼▼▼
            import traceback
            error_details = traceback.format_exc()
            print(f"!!!!!!!!!!!!!! 오류 발생 !!!!!!!!!!!!!!")
            print(f"오류 타입: {type(e).__name__}")
            print(f"오류 메시지: {e}")
            print("--- 상세 스택 트레이스 ---")
            print(error_details)
            print(f"!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
            self.finished.emit(f"작업 중 오류가 발생했습니다: {e}\n\n터미널 창의 상세 오류 정보를 확인해주세요.")
