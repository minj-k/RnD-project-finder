# collector.py (Deep Content Analysis Version - Selenium Final Debugging)
import requests
from bs4 import BeautifulSoup
import logging
from typing import List, Dict, Optional
import io
from pypdf import PdfReader

# Selenium 관련 라이브러리 임포트
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class DataCollector:
    """
    Selenium을 사용하여 JavaScript로 동적 로딩되는 웹사이트의
    상세 내용 및 PDF까지 분석하여 정보를 수집하는 클래스. (최종 안정화 및 디버깅 버전)
    """
    def __init__(self):
        self.sources = {'ntis': self._scrape_ntis}
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        # Selenium WebDriver 설정
        try:
            options = webdriver.ChromeOptions()
            # [수정] 디버깅을 위해 헤드리스 모드를 비활성화합니다. 실행 시 크롬 창이 뜹니다.
            # options.add_argument('--headless') 
            options.add_argument('--log-level=3')
            options.add_argument("window-size=1920x1080")
            options.add_argument("--disable-gpu")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_experimental_option('excludeSwitches', ['enable-logging'])
            
            self.driver = webdriver.Chrome(service=Service(), options=options)
            logging.info("Selenium WebDriver가 성공적으로 초기화되었습니다.")
        except Exception as e:
            logging.error(f"Selenium WebDriver 초기화 중 오류 발생: {e}")
            logging.error("Chrome 브라우저가 설치되어 있는지, 최신 버전인지 확인해주세요.")
            self.driver = None

    def __del__(self):
        """클래스 소멸 시 브라우저 종료"""
        if self.driver:
            self.driver.quit()

    def collect(self, source: str = 'ntis', limit: int = 10) -> Optional[List[Dict[str, str]]]:
        if not self.driver:
            logging.error("WebDriver가 초기화되지 않아 수집을 진행할 수 없습니다.")
            return None
        if source not in self.sources:
            logging.error(f"지원하지 않는 소스입니다: {source}")
            return None
        logging.info(f"'{source}'에서 Selenium을 이용한 심층 분석을 시작합니다...")
        return self.sources[source](limit)

    def _extract_text_from_pdf(self, pdf_url: str) -> str:
        try:
            response = requests.get(pdf_url, headers=self.headers, timeout=20)
            response.raise_for_status()
            pdf_file = io.BytesIO(response.content)
            reader = PdfReader(pdf_file)
            text = "".join(page.extract_text() or "" for page in reader.pages)
            logging.info(f"PDF에서 {len(text)} 자의 텍스트를 추출했습니다.")
            return text[:2000]
        except Exception as e:
            logging.error(f"PDF 처리 중 오류 발생: {e} (URL: {pdf_url})")
            return ""

    def _scrape_detail_page(self, detail_url: str) -> str:
        try:
            response = requests.get(detail_url, headers=self.headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            file_link_tag = soup.find('a', title='첨부파일 다운로드', href=lambda href: href and href.endswith('.pdf'))
            if file_link_tag:
                pdf_url = "https://www.ntis.go.kr" + file_link_tag['href']
                return self._extract_text_from_pdf(pdf_url)
            return ""
        except Exception as e:
            logging.warning(f"상세 페이지({detail_url}) 분석 중 오류: {e}")
            return ""

    def _scrape_ntis(self, limit: int) -> Optional[List[Dict[str, str]]]:
        base_url = f"https://www.ntis.go.kr/ThSearchProjectList.do?searchWord=연구&sort=SS04/DESC"
        
        try:
            self.driver.get(base_url)
            
            # [추가] 페이지가 완전히 로드될 시간을 조금 더 줍니다.
            time.sleep(2)
            
            wait = WebDriverWait(self.driver, 20)
            wait.until(EC.presence_of_element_located((By.ID, "search_project_list")))
            
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            list_container = soup.find('div', id='search_project_list')
            if not list_container:
                logging.error("과제 목록 컨테이너('search_project_list')를 찾을 수 없습니다.")
                return []

            items = list_container.find_all('li')
            if not items:
                logging.error("과제 항목(li)을 찾을 수 없습니다.")
                return []

            projects = []
            for i, item in enumerate(items):
                if i >= limit: break

                title_tag = item.select_one("div.title > a")
                if not title_tag: continue
                
                title = title_tag.text.strip()
                detail_url = "https://www.ntis.go.kr" + title_tag.get_attribute('href')
                
                details = item.select("dl > dd")
                agency = details[0].text.strip() if len(details) > 0 else "N/A"
                department = details[1].text.strip() if len(details) > 1 else "N/A"
                period = details[2].text.strip() if len(details) > 2 else "N/A"

                logging.info(f"({i+1}/{limit}) '{title}' 과제의 상세 내용을 분석합니다...")
                summary_text = self._scrape_detail_page(detail_url)
                
                projects.append({
                    "title": title, "agency": agency, "department": department,
                    "end_date": period.split('~')[-1].strip() if '~' in period else period,
                    "url": detail_url, "summary": summary_text, "source": "NTIS Selenium Scraper"
                })
            
            logging.info(f"NTIS Selenium 크롤링으로 {len(projects)}개의 과제를 성공적으로 수집했습니다.")
            return projects
        except Exception as e:
            logging.error(f"NTIS 목록 스크래핑 중 오류 발생: {e}")
            return None
