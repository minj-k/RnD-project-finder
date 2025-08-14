# main_desktop.py

import sys
import traceback
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTextEdit, QSlider, QComboBox,
    QFormLayout, QGroupBox
)
from PySide6.QtCore import Qt, QThread, Signal, QObject

# 기존에 만들었던 로직 모듈들을 임포트합니다.
from collector import DataCollector
from analyzer import ContextAnalyzer
from generator import ProposalGenerator
from dotenv import load_dotenv

# --- 백그라운드 작업을 위한 Worker 클래스 ---
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

            self.progress.emit("2/3 | 컨텍스트 분석 시작...")
            print("[체크포인트] 2. Analyzer 호출 시작")
            ranked_context = self.analyzer.get_ranked_context(
                self.user_topic, projects, top_k=self.context_count
            )
            print("[체크포인트] 2. Analyzer 호출 완료")

            self.progress.emit("3/3 | AI 제안서 생성 시작...")
            print("[체크포인트] 3. Generator 호출 시작")
            final_proposal = self.generator.generate_full_proposal(
                self.user_topic, ranked_context
            )
            print("[체크포인트] 3. Generator 호출 완료")
            
            self.finished.emit(final_proposal)

        except Exception as e:
            error_details = traceback.format_exc()
            print(f"!!!!!!!!!!!!!! 오류 발생 !!!!!!!!!!!!!!")
            print(f"오류 타입: {type(e).__name__}")
            print(f"오류 메시지: {e}")
            print("--- 상세 스택 트레이스 ---")
            print(error_details)
            print(f"!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
            self.finished.emit(f"작업 중 오류가 발생했습니다: {e}\n\n터미널 창의 상세 오류 정보를 확인해주세요.")


# --- 메인 윈도우 클래스 ---
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🤖 지능형 연구과제 제안서 생성기")
        self.setGeometry(100, 100, 900, 700)

        self.topic_label = QLabel("연구 주제 또는 핵심 아이디어:")
        self.topic_input = QLineEdit()
        self.topic_input.setPlaceholderText("예: 생성형 AI를 활용한 교육 플랫폼")

        self.source_label = QLabel("정보 소스:")
        self.source_combo = QComboBox()
        self.source_combo.addItems(["ntis"])

        self.count_label = QLabel(f"참고할 관련 과제 수: 5")
        self.count_slider = QSlider(Qt.Horizontal)
        self.count_slider.setRange(3, 10)
        self.count_slider.setValue(5)
        self.count_slider.valueChanged.connect(self.update_count_label)

        self.generate_button = QPushButton("🚀 제안서 생성 시작하기")
        self.generate_button.clicked.connect(self.start_generation_process)

        self.status_label = QLabel("준비 완료. 생성 버튼을 눌러주세요.")
        self.status_label.setStyleSheet("color: gray;")

        self.result_display = QTextEdit()
        self.result_display.setReadOnly(True)
        self.result_display.setPlaceholderText("이곳에 AI가 생성한 제안서가 표시됩니다...")

        input_group = QGroupBox("입력 설정")
        form_layout = QFormLayout()
        form_layout.addRow(self.topic_label, self.topic_input)
        form_layout.addRow(self.source_label, self.source_combo)
        
        count_layout = QHBoxLayout()
        count_layout.addWidget(self.count_slider)
        count_layout.addWidget(self.count_label)
        form_layout.addRow("관련 과제 수:", count_layout)
        
        input_group.setLayout(form_layout)

        main_layout = QVBoxLayout()
        main_layout.addWidget(input_group)
        main_layout.addWidget(self.generate_button)
        main_layout.addWidget(self.status_label)
        main_layout.addWidget(QLabel("--- 결과 ---"))
        main_layout.addWidget(self.result_display)
        
        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

    def update_count_label(self, value):
        self.count_label.setText(f"참고할 관련 과제 수: {value}")

    def start_generation_process(self):
        user_topic = self.topic_input.text()
        if not user_topic:
            self.status_label.setText("오류: 연구 주제를 입력해주세요.")
            self.status_label.setStyleSheet("color: red;")
            return

        self.generate_button.setEnabled(False)
        self.status_label.setText("생성을 시작합니다...")
        self.status_label.setStyleSheet("color: blue;")
        self.result_display.clear()

        self.thread = QThread()
        self.worker = Worker(
            user_topic=user_topic,
            source=self.source_combo.currentText(),
            context_count=self.count_slider.value()
        )
        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.on_generation_finished)
        self.worker.progress.connect(self.update_status_label)
        
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        self.thread.start()

    def update_status_label(self, message):
        self.status_label.setText(message)

    def on_generation_finished(self, proposal):
        self.result_display.setMarkdown(proposal)
        self.status_label.setText("생성 완료!")
        self.status_label.setStyleSheet("color: green;")
        self.generate_button.setEnabled(True)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
