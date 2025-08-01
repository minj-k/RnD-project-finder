# collector.py (Web Scraping - Detailed Version)
import requests
from bs4 import BeautifulSoup
import logging
from typing import List, Dict, Optional

# 로깅 설정: 스크립트 실행 과정을 터미널에 출력하여 디버깅에 용이하게 함
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class DataCollector:
    """
    API 없이 NTIS 웹사이트를 직접 크롤링하여 연구과제 정보를 수집하는 클래스.
    제공된 URL 구조에 맞춰 상세 정보를 추출합니다.
    """
    def __init__(self):
        # 다른 정보 소스를 추가할 경우를 대비한 딕셔너리 구조
        self.sources = {
            'ntis': self._scrape_ntis,
        }

    def collect(self, source: str = 'ntis', limit: int = 20) -> Optional[List[Dict[str, str]]]:
        """
        지정된 소스에서 과제 정보를 수집합니다.
        
        Args:
            source (str): 정보 소스 (기본값: 'ntis').
            limit (int): 수집할 최대 과제 수.
        
        Returns:
            Optional[List[Dict[str, str]]]: 수집된 과제 정보 리스트. 실패 시 None.
        """
        if source not in self.sources:
            logging.error(f"지원하지 않는 소스입니다: {source}")
            return None
        
        logging.info(f"'{source}'에서 웹 크롤링을 시작합니다...")
        return self.sources[source](limit)

    def _scrape_ntis(self, limit: int) -> Optional[List[Dict[str, str]]]:
        """
        NTIS 국가R&D통합공고 페이지를 스크래핑하여 상세 과제 정보를 추출합니다.
        """
        # 사용자가 제공한 '최근 1개월' 공고 링크
        # pageUnit 파라미터를 추가하여 한 페이지에 가져올 공고 수를 조절
        base_url = f"https://www.ntis.go.kr/rndgate/eg/un/ra/mng.do?searchCondition=1m&pageUnit={limit}"
        
        # 실제 브라우저처럼 보이게 하기 위한 User-Agent 헤더
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        try:
            # 웹페이지 HTML 요청 및 수신
            response = requests.get(base_url, headers=headers, timeout=10)
            response.raise_for_status()  # HTTP 요청 실패 시 예외 발생

            # BeautifulSoup으로 HTML 파싱
            soup = BeautifulSoup(response.text, 'html.parser')
            
            projects = []
            
            # ⚠️ 가장 중요한 CSS 선택자 부분
            # 공고 목록이 담긴 테이블의 각 행(tr)을 선택합니다.
            # 클래스 이름에 공백이 포함된 경우, 점(.)으로 연결하여 선택합니다. (예: .board_list.type_list)
            rows = soup.select("div.board_list_style1 > table.type_list > tbody > tr")
            
            if not rows:
                logging.warning("공고 목록을 찾을 수 없습니다. NTIS 웹사이트의 HTML 구조가 변경되었을 수 있습니다.")
                return []

            for row in rows:
                # 각 행(row) 내부의 셀(td)들을 리스트로 가져옴
                cells = row.find_all('td')
                
                # 셀 개수가 충분한지 확인하여 오류 방지
                if len(cells) < 7:
                    continue

                # 각 셀에서 정보 추출
                project_id = cells[0].text.strip()
                title_tag = cells[1].find('a')
                title = title_tag.text.strip() if title_tag else "N/A"
                detail_url = "https://www.ntis.go.kr" + title_tag['href'] if title_tag else "N/A"
                agency = cells[2].text.strip()
                department = cells[3].text.strip()
                status = cells[4].text.strip()
                start_date = cells[5].text.strip()
                end_date = cells[6].text.strip()

                projects.append({
                    "id": project_id,
                    "title": title,
                    "agency": agency,          # 소관부처
                    "department": department,  # 공고기관
                    "status": status,          # 사업상태
                    "start_date": start_date,  # 입력일
                    "end_date": end_date,      # 마감일
                    "url": detail_url,
                    "source": "NTIS Web Scraping"
                })
            
            logging.info(f"NTIS 웹 크롤링으로 {len(projects)}개의 과제를 성공적으로 수집했습니다.")
            return projects

        except requests.RequestException as e:
            logging.error(f"NTIS 웹사이트 요청 중 오류 발생: {e}")
            return None
        except Exception as e:
            logging.error(f"크롤링 중 알 수 없는 오류 발생: {e}")
            return None

# 이 파일이 직접 실행될 때 테스트용으로 코드를 실행
if __name__ == '__main__':
    collector = DataCollector()
    # 최근 1개월 공고 중 최대 15개를 가져오는 테스트
    ntis_projects = collector.collect(source='ntis', limit=15)
    
    if ntis_projects:
        print("\n--- NTIS 과제 공고 수집 결과 ---")
        # 수집된 첫 번째 과제 정보 상세 출력
        import json
        print(json.dumps(ntis_projects[0], indent=2, ensure_ascii=False))
        print(f"\n총 {len(ntis_projects)}개의 과제를 수집했습니다.")
