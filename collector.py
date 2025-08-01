# collector.py (Web Scraping Version)
import requests
from bs4 import BeautifulSoup
import logging
from typing import List, Dict, Optional

# 로깅 설정: 어떤 일이 일어나고 있는지 터미널에 표시
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class DataCollector:
    """
    API 없이 웹 크롤링(스크래핑)을 통해 연구과제 정보를 수집하는 클래스.
    """
    def __init__(self):
        # 각 사이트별 크롤링 함수를 딕셔너리로 관리하여 확장성을 높임
        self.sources = {
            'ntis': self._scrape_ntis,
            # 'keit': self._scrape_keit, # 다른 사이트 추가 가능
        }

    def collect(self, source: str, keyword: str, limit: int = 10) -> Optional[List[Dict[str, str]]]:
        """지정된 소스에서 키워드 관련 과제 정보를 수집합니다."""
        if source not in self.sources:
            logging.error(f"지원하지 않는 소스입니다: {source}")
            return None
        
        logging.info(f"'{source}'에서 키워드 '{keyword}'로 웹 크롤링을 시작합니다...")
        return self.sources[source](keyword, limit)

    def _scrape_ntis(self, keyword: str, limit: int) -> Optional[List[Dict[str, str]]]:
        """
        NTIS 통합공고 게시판을 스크래핑하여 과제 목록을 가져옵니다.
        """
        # NTIS 통합공고 검색 URL
        base_url = "https://www.ntis.go.kr/ThSearchAnnouncementList.do"
        
        # 웹사이트에 보낼 요청 파라미터 (검색어, 한 페이지에 표시할 개수 등)
        params = {
            'p_menu_id': '080201',
            'searchWord': keyword,
            'pageUnit': limit,
            'pageIndex': 1 # 첫 번째 페이지만 가져옴
        }
        
        # 서버가 실제 브라우저의 요청으로 인식하도록 헤더 설정
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        try:
            # GET 요청으로 웹페이지의 HTML 소스 코드를 가져옴
            response = requests.get(base_url, params=params, headers=headers, timeout=10)
            response.raise_for_status() # HTTP 오류 발생 시 예외 처리

            # BeautifulSoup을 사용하여 HTML 코드를 파싱할 수 있는 객체로 변환
            soup = BeautifulSoup(response.text, 'html.parser')
            
            projects = []
            
            # ⚠️ 가장 중요하고 취약한 부분:
            # 개발자 도구(F12)로 확인한 HTML 구조를 기반으로 데이터를 포함하는 태그를 선택합니다.
            # 예: 공고 목록이 담긴 테이블의 각 행(tr)을 선택
            rows = soup.select("div.board_list_style1 > table > tbody > tr")
            
            if not rows:
                logging.warning("공고 목록을 찾을 수 없습니다. NTIS 웹사이트의 HTML 구조가 변경되었을 수 있습니다.")
                return []

            for row in rows:
                # 각 행(row) 안에서 세부 정보(제목, 기관 등)를 CSS 선택자로 찾음
                # 이 선택자들은 브라우저의 '개발자 도구' -> 'Elements' 탭에서 찾을 수 있습니다.
                title_tag = row.select_one("td.subject a")
                agency_tag = row.select_one("td:nth-of-type(3)") # 3번째 td 태그
                department_tag = row.select_one("td:nth-of-type(4)") # 4번째 td 태그
                date_tag = row.select_one("td:nth-of-type(6)") # 6번째 td 태그

                if title_tag:
                    # 태그 안의 텍스트만 추출하고, 불필요한 공백을 제거
                    title = title_tag.text.strip()
                    # 상세 페이지 링크(href 속성) 추출
                    detail_url = "https://www.ntis.go.kr" + title_tag['href']
                    
                    # 태그가 존재할 경우에만 텍스트 추출 (오류 방지)
                    agency = agency_tag.text.strip() if agency_tag else "N/A"
                    department = department_tag.text.strip() if department_tag else "N/A"
                    date = date_tag.text.strip() if date_tag else "N/A"

                    projects.append({
                        "title": title,
                        "agency": agency,
                        "department": department,
                        "date": date,
                        "url": detail_url,
                        "source": "NTIS Web Scraping"
                    })
            
            logging.info(f"NTIS 웹 크롤링으로 {len(projects)}개의 과제를 찾았습니다.")
            return projects

        except requests.RequestException as e:
            logging.error(f"NTIS 웹사이트 요청 중 오류 발생: {e}")
            return None
        except Exception as e:
            logging.error(f"크롤링 중 알 수 없는 오류 발생: {e}")
            return None
