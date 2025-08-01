# collector.py (Deep Content Analysis Version - More Robust)
import requests
from bs4 import BeautifulSoup
import logging
from typing import List, Dict, Optional
import io
from pypdf import PdfReader # pypdf 라이브러리 임포트

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class DataCollector:
    """
    상세 페이지 및 첨부 PDF 파일의 내용까지 분석하여
    심층적인 과제 정보를 수집하는 클래스. (선택자 안정성 강화 버전)
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
            
            text = ""
            for page in reader.pages:
                text += page.extract_text() or ""
            
            logging.info(f"PDF에서 {len(text)} 자의 텍스트를 추출했습니다.")
            return text[:2000] # 너무 긴 텍스트는 일부만 반환
        except Exception as e:
            logging.error(f"PDF 처리 중 오류 발생: {e} (URL: {pdf_url})")
            return ""

    def _scrape_detail_page(self, detail_url: str) -> str:
        """상세 페이지에서 PDF 링크를 찾아 텍스트를 추출합니다."""
        try:
            response = requests.get(detail_url, headers=self.headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')

            # 1차 시도: 기존의 구체적인 선택자로 PDF 링크 찾기
            file_link_tag = soup.select_one("a.file-down[href$='.pdf']")
            
            # 2차 시도: 1차 시도가 실패하면, '첨부파일' 텍스트를 기준으로 다시 찾기
            if not file_link_tag:
                logging.warning("기본 선택자로 PDF 링크를 찾지 못했습니다. 텍스트 기반으로 다시 시도합니다.")
                # '첨부파일'이라는 텍스트를 포함하는 헤더 태그(th, strong 등)를 찾음
                attach_header = soup.find(lambda tag: tag.name in ['th', 'strong', 'h3', 'h4'] and '첨부파일' in tag.text)
                if attach_header:
                    # 헤더의 부모 요소(tr) 또는 가장 가까운 컨테이너(div) 안에서 PDF 링크를 탐색
                    parent_container = attach_header.find_parent('tr') or attach_header.find_parent('div', class_='file_list')
                    if parent_container:
                        file_link_tag = parent_container.select_one("a[href$='.pdf']")

            if file_link_tag:
                pdf_url = "https://www.ntis.go.kr" + file_link_tag['href']
                return self._extract_text_from_pdf(pdf_url)
            else:
                logging.warning(f"상세 페이지({detail_url})에서 PDF 첨부파일을 최종적으로 찾지 못했습니다.")
                return ""
        except Exception as e:
            logging.error(f"상세 페이지 스크래핑 중 오류: {e}")
            return ""

    def _scrape_ntis(self, limit: int) -> Optional[List[Dict[str, str]]]:
        base_url = f"https://www.ntis.go.kr/rndgate/eg/un/ra/mng.do?searchCondition=1m&pageUnit={limit}"
        
        try:
            response = requests.get(base_url, headers=self.headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 1차 시도: 기존의 구체적인 선택자
            primary_selector = "div.board_list_style1 > table.type_list > tbody > tr"
            rows = soup.select(primary_selector)
            
            # 2차 시도: 1차 시도가 실패하면, 더 일반적인 백업 선택자 사용
            if not rows:
                backup_selector = "table.type_list tbody tr"
                logging.warning(f"기본 선택자 '{primary_selector}'로 목록을 찾지 못했습니다. 백업 선택자 '{backup_selector}'로 다시 시도합니다.")
                rows = soup.select(backup_selector)

            if not rows:
                logging.error("백업 선택자로도 공고 목록을 찾을 수 없습니다. NTIS 웹사이트의 HTML 구조가 크게 변경된 것 같습니다.")
                return []

            projects = []
            for i, row in enumerate(rows):
                if i >= limit: break
                
                cells = row.find_all('td')
                if len(cells) < 7: continue

                title_tag = cells[1].find('a')
                if not title_tag: continue
                
                detail_url = "https://www.ntis.go.kr" + title_tag['href']
                
                logging.info(f"({i+1}/{limit}) '{title_tag.text.strip()}' 과제의 상세 내용을 분석합니다...")
                summary_text = self._scrape_detail_page(detail_url)
                
                projects.append({
                    "title": title_tag.text.strip(),
                    "agency": cells[2].text.strip(),
                    "department": cells[3].text.strip(),
                    "end_date": cells[6].text.strip(),
                    "url": detail_url,
                    "summary": summary_text,
                    "source": "NTIS Deep Scraper"
                })
            
            logging.info(f"NTIS 심층 크롤링으로 {len(projects)}개의 과제를 성공적으로 수집했습니다.")
            return projects
        except Exception as e:
            logging.error(f"NTIS 목록 스크래핑 중 오류 발생: {e}")
            return None
