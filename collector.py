# collector.py
import requests
import os
import logging
from typing import List, Dict, Optional
from urllib.parse import unquote # API 응답이 URL 인코딩 되어 있을 경우를 대비

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class DataCollector:
    """
    NTIS API를 포함한 다양한 소스에서 연구과제 정보를 수집하는 클래스.
    """
    def __init__(self):
        # 환경 변수에서 NTIS API 키를 불러옵니다.
        self.ntis_api_key = os.getenv('NTIS_API_KEY')
        if not self.ntis_api_key:
            # .env 파일에 키가 없으면 로깅하고 예외를 발생시키는 대신 None을 반환하도록 처리
            logging.error("NTIS_API_KEY가 .env 파일에 설정되지 않았습니다.")
            # raise ValueError("NTIS_API_KEY가 .env 파일에 설정되지 않았습니다.")
        
        self.sources = {
            'ntis': self._call_ntis_api,
            # 'keit': self._scrape_keit, # 다른 소스 추가 가능
        }

    def collect(self, source: str, keyword: str, limit: int = 10) -> Optional[List[Dict[str, str]]]:
        """지정된 소스에서 키워드 관련 과제 정보를 수집합니다."""
        if source not in self.sources:
            logging.error(f"지원하지 않는 소스입니다: {source}")
            return None
        
        logging.info(f"'{source}'에서 키워드 '{keyword}'로 데이터 수집을 시작합니다...")
        return self.sources[source](keyword, limit)

    def _call_ntis_api(self, keyword: str, limit: int) -> Optional[List[Dict[str, str]]]:
        """NTIS 국가R&D 통합공고문 검색 API를 호출합니다."""
        if not self.ntis_api_key:
            logging.error("NTIS API 키가 없어 API를 호출할 수 없습니다.")
            return None
            
        # NTIS API 엔드포인트
        base_url = "http://www.ntis.go.kr/ThOpenApiMajorView.do"
        
        # API 요청 파라미터 설정
        params = {
            'strServiceId': '0802', # 통합공고문 검색 서비스 ID
            'strUserId': unquote(self.ntis_api_key), # URL 디코딩된 인증키
            'strSearchWord': keyword, # 검색어
            'strStartNo': '1', # 시작번호
            'strEndNo': str(limit) # 가져올 개수
        }

        try:
            response = requests.get(base_url, params=params, timeout=10)
            response.raise_for_status() # 오류 발생 시 예외 처리
            
            # 응답 데이터가 XML 형식이므로 파싱이 필요합니다.
            # Python의 내장 라이브러리인 ElementTree를 사용합니다.
            import xml.etree.ElementTree as ET
            
            root = ET.fromstring(response.content)
            
            projects = []
            # 'anList' 아래의 'list' 태그가 각 과제 정보를 담고 있습니다.
            for item in root.findall('.//list'):
                # 각 태그의 텍스트를 안전하게 추출하는 함수
                def get_text(element_name):
                    found = item.find(element_name)
                    return found.text.strip() if found is not None and found.text else ""

                projects.append({
                    "title": get_text('anKoTitle'), # 공고한글명
                    "agency": get_text('organName'), # 소관부처명
                    "department": get_text('reqOrganName'), # 공고기관명
                    "summary": get_text('anBssSt'), # 사업상태 (예: 공고)
                    "url": get_text('anDetailLink'), # 상세 URL
                    "source": "NTIS API"
                })
            
            logging.info(f"NTIS API에서 {len(projects)}개의 과제를 성공적으로 가져왔습니다.")
            return projects

        except requests.RequestException as e:
            logging.error(f"NTIS API 요청 중 오류 발생: {e}")
            return None
        except ET.ParseError as e:
            logging.error(f"NTIS API 응답 (XML) 파싱 중 오류 발생: {e}")
            logging.error(f"오류가 발생한 응답 내용: {response.text}")
            return None
