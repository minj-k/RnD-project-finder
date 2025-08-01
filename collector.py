# collector.py (Deep Content Analysis Version - Final Robust)
import requests
from bs4 import BeautifulSoup
import logging
from typing import List, Dict, Optional
import io
from pypdf import PdfReader

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class DataCollector:
    """
    상세 페이지 및 첨부 PDF 파일의 내용까지 분석하여
    심층적인 과제 정보를 수집하는 클래스. (최종 안정화 버전)
    """
    def __init__(self):
        self.sources = {'ntis': self._scrape_ntis}
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

    def collect(self, source: str = 'ntis', limit: int = 10) -> Optional[List[Dict[str, str]]]:
        if source not in self.sources:
            logging.error(f"지원하지 않는 소스입니다: {source}")
            return None
        logging.info(f"'{source}'에서 심층 분석을 위한 웹 크롤링을 시작합니다...")
        return self.sources[source](limit)

    def _extract_text_from_pdf(self, pdf_url: str) -> str:
        """PDF URL을 받아 텍스트를 추출합니다."""
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
        """상세 페이지에서 PDF 링크를 찾아 텍스트를 추출합니다."""
        try:
            response = requests.get(detail_url, headers=self.headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')

            # '첨부파일' 텍스트를 포함하는 링크를 직접 찾음 (더 안정적)
            file_link_tag = soup.find('a', title='첨부파일 다운로드', href=lambda href: href and (href.endswith('.pdf') or href.endswith('.hwp')))
            
            if not file_link_tag:
                 # 백업: '제안요청서' 텍스트를 포함하는 링크 찾기
                file_link_tag = soup.find('a', title='첨부파일 다운로드', string=lambda text: text and '제안요청서' in text)
            
            if file_link_tag and file_link_tag['href'].endswith('.pdf'):
                pdf_url = "https://www.ntis.go.kr" + file_link_tag['href']
                return self._extract_text_from_pdf(pdf_url)
            else:
                logging.warning(f"상세 페이지({detail_url})에서 분석 가능한 PDF 첨부파일을 찾지 못했습니다.")
                return ""
        except Exception as e:
            logging.error(f"상세 페이지 스크래핑 중 오류: {e}")
            return ""

    def _scrape_ntis(self, limit: int) -> Optional[List[Dict[str, str]]]:
        # [수정] 동적으로 변하는 페이지 대신, 검색 결과 페이지를 타겟으로 변경
        # '연구'라는 키워드로 검색하여 가장 일반적인 목록을 가져옴
        base_url = f"https://www.ntis.go.kr/ThSearchProjectList.do"
        params = {
            'searchWord': '연구',
            'pageUnit': limit,
            'sort': 'SS04/DESC' # 최신순 정렬
        }
        
        try:
            response = requests.get(base_url, params=params, headers=self.headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # [수정] 훨씬 더 안정적인 선택자로 변경
            # id가 'search_project_list'인 영역을 먼저 찾고, 그 안에서 목록을 탐색
            list_container = soup.find('div', id='search_project_list')
            if not list_container:
                logging.error("과제 목록 컨테이너('search_project_list')를 찾을 수 없습니다. 사이트 구조가 변경되었습니다.")
                return []

            # 컨테이너 안의 각 과제 항목(li)을 선택
            items = list_container.find_all('li')
            if not items:
                logging.error("과제 항목(li)을 찾을 수 없습니다.")
                return []

            projects = []
            for i, item in enumerate(items):
                if i >= limit: break

                title_tag = item.select_one("div.title > a")
                if not title_tag: continue
                
                # 상세 정보 추출
                title = title_tag.text.strip()
                detail_url = "https://www.ntis.go.kr" + title_tag['href']
                
                # 기관, 기간 등의 정보는 dl > dd 구조 안에 있음
                details = item.select("dl > dd")
                agency = details[0].text.strip() if len(details) > 0 else "N/A"
                department = details[1].text.strip() if len(details) > 1 else "N/A"
                period = details[2].text.strip() if len(details) > 2 else "N/A"

                logging.info(f"({i+1}/{limit}) '{title}' 과제의 상세 내용을 분석합니다...")
                summary_text = self._scrape_detail_page(detail_url)
                
                projects.append({
                    "title": title,
                    "agency": agency,
                    "department": department,
                    "end_date": period.split('~')[-1].strip() if '~' in period else period, # 기간에서 마감일만 추출
                    "url": detail_url,
                    "summary": summary_text,
                    "source": "NTIS Search Scraper"
                })
            
            logging.info(f"NTIS 검색 결과 크롤링으로 {len(projects)}개의 과제를 성공적으로 수집했습니다.")
            return projects
        except Exception as e:
            logging.error(f"NTIS 목록 스크래핑 중 오류 발생: {e}")
            return None
