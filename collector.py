# collector.py (Final Version - Direct API Call)
import requests
import logging
from typing import List, Dict, Optional
import io
from pypdf import PdfReader

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class DataCollector:
    """
    NTIS의 내부 API를 직접 호출하여 안정적으로 과제 정보를 수집하는 클래스.
    Selenium을 사용하지 않아 훨씬 빠르고 안정적입니다.
    """
    def __init__(self):
        self.sources = {'ntis': self._call_ntis_api}
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Referer': 'https://www.ntis.go.kr/ThSearchProjectList.do' # 요청 출처를 명시하여 차단을 피함
        }

    def collect(self, source: str = 'ntis', limit: int = 10) -> Optional[List[Dict[str, str]]]:
        if source not in self.sources:
            logging.error(f"지원하지 않는 소스입니다: {source}")
            return None
        logging.info(f"'{source}' 내부 API를 직접 호출하여 데이터 수집을 시작합니다...")
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

    def _call_ntis_api(self, limit: int) -> Optional[List[Dict[str, str]]]:
        # NTIS 과제 목록을 가져오는 내부 API의 실제 주소
        api_url = "https://www.ntis.go.kr/ThProjectListAjax.do"
        
        # API에 POST 방식으로 보낼 데이터
        payload = {
            'searchWord': '연구',
            'sort': 'SS04/DESC',
            'pageUnit': limit,
            'pageIndex': 1
        }
        
        try:
            # POST 요청으로 API 호출
            response = requests.post(api_url, data=payload, headers=self.headers, timeout=15)
            response.raise_for_status()
            
            # 응답은 JSON 형식이므로, .json()으로 파싱
            data = response.json()
            
            projects = []
            # 'projectList' 키에 실제 과제 목록이 들어있음
            for item in data.get('projectList', []):
                # 상세 페이지 URL 조합
                detail_url = f"https://www.ntis.go.kr/ThMain.do?menuNo=2021&p_prj_no={item.get('prjNo')}"
                
                logging.info(f"'{item.get('koPrjNm')}' 과제의 상세 내용을 분석합니다...")
                summary_text = self._scrape_detail_page(detail_url)
                
                projects.append({
                    "title": item.get('koPrjNm', 'N/A'),
                    "agency": item.get('leadRsrhOrgNm', 'N/A'),
                    "department": item.get('mngRsrhOrgNm', 'N/A'),
                    "end_date": item.get('prjTerm', 'N/A').split('~')[-1].strip(),
                    "url": detail_url,
                    "summary": summary_text,
                    "source": "NTIS Internal API"
                })
            
            logging.info(f"NTIS 내부 API 호출로 {len(projects)}개의 과제를 성공적으로 수집했습니다.")
            return projects
        except requests.RequestException as e:
            logging.error(f"NTIS API 요청 중 오류 발생: {e}")
            return None
        except Exception as e:
            logging.error(f"데이터 처리 중 오류 발생: {e}")
            return None

