# collector.py
import requests
from bs4 import BeautifulSoup
import logging
from typing import List, Dict, Optional

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class DataCollector:
    """
    다양한 연구과제 정보 사이트에서 데이터를 수집하고 정형화하는 클래스.
    """
    def __init__(self):
        self.sources = {
            'ntis': self._scrape_ntis,
            'keit': self._scrape_keit, # KEIT 크롤링 함수 (예시)
        }

    def collect(self, source: str, keyword: str, limit: int = 10) -> Optional[List[Dict[str, str]]]:
        """지정된 소스에서 키워 관련 과제 정보를 수집합니다."""
        if source not in self.sources:
            logging.error(f"지원하지 않는 소스입니다: {source}")
            return None
        
        logging.info(f"'{source}'에서 키워드 '{keyword}'로 데이터 수집을 시작합니다...")
        return self.sources[source](keyword, limit)

    def _scrape_ntis(self, keyword: str, limit: int) -> Optional[List[Dict[str, str]]]:
        """NTIS 통합공고 게시판을 스크래핑합니다."""
        base_url = "https://www.ntis.go.kr/ThSearchAnnouncementList.do"
        params = {'p_menu_id': '080201', 'searchWord': keyword, 'pageUnit': limit}
        
        try:
            response = requests.get(base_url, params=params, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            projects = []
            # NTIS의 실제 HTML 구조에 따라 CSS 선택자를 정교하게 수정해야 합니다.
            # 이 코드는 개념적인 예시입니다.
            rows = soup.select("table.type_list > tbody > tr")
            
            for row in rows:
                title_tag = row.select_one(".subject a")
                agency_tag = row.select_one("td:nth-of-type(3)") # 3번째 td 가정
                
                if title_tag and agency_tag:
                    projects.append({
                        "title": title_tag.text.strip(),
                        "agency": agency_tag.text.strip(),
                        "url": "https://www.ntis.go.kr" + title_tag['href'],
                        "summary": "", # 요약은 상세 페이지에 들어가서 추가 수집 필요
                        "source": "NTIS"
                    })
            
            logging.info(f"NTIS에서 {len(projects)}개의 과제를 찾았습니다.")
            return projects
        except requests.RequestException as e:
            logging.error(f"NTIS 데이터 수집 중 오류: {e}")
            return None

    def _scrape_keit(self, keyword: str, limit: int) -> Optional[List[Dict[str, str]]]:
        """KEIT 사이트 크롤링 로직 (구현 필요)"""
        logging.info("KEIT 크롤링 기능은 현재 구현되지 않았습니다.")
        return []

# 사용 예시
# if __name__ == '__main__':
#     collector = DataCollector()
#     ntis_projects = collector.collect(source='ntis', keyword='인공지능')
#     if ntis_projects:
#         print(ntis_projects)
