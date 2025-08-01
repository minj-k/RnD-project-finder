# collector.py (Final Version - Session-Based API Call)
import requests
import logging
from typing import List, Dict, Optional
import io
from pypdf import PdfReader
import traceback

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class DataCollector:
    """
    requests.Session 객체를 사용하여 쿠키를 유지함으로써, 서버 차단을 우회하고
    안정적으로 내부 API를 호출하는 최종 버전의 클래스.
    """
    def __init__(self):
        self.sources = {'ntis': self._call_ntis_api_with_session}
        self.session = requests.Session() # [핵심] 세션 객체 생성
        # [핵심] 세션 전체에 적용될 헤더 설정
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        })

    def collect(self, source: str = 'ntis', limit: int = 10) -> Optional[List[Dict[str, str]]]:
        if source not in self.sources:
            logging.error(f"지원하지 않는 소스입니다: {source}")
            return None
        logging.info(f"'{source}' 세션 기반 API 호출로 데이터 수집을 시작합니다...")
        return self.sources[source](limit)

    def _extract_text_from_pdf(self, pdf_url: str) -> str:
        try:
            # PDF 다운로드 시에도 동일한 세션 사용
            response = self.session.get(pdf_url, timeout=20)
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
            # 상세 페이지 접속 시에도 동일한 세션 사용
            response = self.session.get(detail_url, timeout=10)
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

    def _call_ntis_api_with_session(self, limit: int) -> Optional[List[Dict[str, str]]]:
        main_page_url = "https://www.ntis.go.kr/ThSearchProjectList.do"
        api_url = "https://www.ntis.go.kr/ThProjectListAjax.do"
        
        payload = {
            'searchWord': '연구',
            'sort': 'SS04/DESC',
            'pageUnit': limit,
            'pageIndex': 1
        }
        
        try:
            # 1단계: 메인 페이지에 먼저 접속하여 세션 쿠키를 받음
            logging.info("서버로부터 세션 쿠키를 얻기 위해 메인 페이지에 접속합니다...")
            self.session.get(main_page_url, timeout=15)
            
            # 2단계: 발급받은 쿠키가 포함된 세션으로 API에 POST 요청
            logging.info("세션 쿠키를 사용하여 내부 API를 호출합니다...")
            # 헤더에 Referer와 X-Requested-With를 추가하여 AJAX 요청처럼 위장
            api_headers = {
                'Referer': main_page_url,
                'X-Requested-With': 'XMLHttpRequest',
            }
            response = self.session.post(api_url, data=payload, headers=api_headers, timeout=15)
            response.raise_for_status()
            
            data = response.json()

            projects = []
            for item in data.get('projectList', []):
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
                    "source": "NTIS Internal API (Session)"
                })
            
            logging.info(f"NTIS 내부 API 호출로 {len(projects)}개의 과제를 성공적으로 수집했습니다.")
            return projects
        except requests.exceptions.JSONDecodeError:
            logging.error("서버가 JSON이 아닌 응답을 반환했습니다. 서버 정책이 변경되었을 수 있습니다.")
            logging.error(f"서버 응답 내용:\n{response.text[:500]}")
            return None
        except requests.RequestException as e:
            logging.error(f"NTIS API 요청 중 네트워크 오류 발생: {e}")
            return None
        except Exception as e:
            logging.error(f"데이터 처리 중 알 수 없는 오류 발생: {e}")
            with open("error.log", "a", encoding="utf-8") as f:
                f.write(traceback.format_exc())
            return None
