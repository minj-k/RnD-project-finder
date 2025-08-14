# collector.py

import os
import requests
import xml.etree.ElementTree as ET

class DataCollector:
    def __init__(self):
        self.ntis_api_key = os.getenv("NTIS_API_KEY")

    def collect(self, source="ntis", limit=100):
        if source == "ntis":
            return self._collect_from_ntis(limit)
        return []

    def _collect_from_ntis(self, limit):
        """NTIS API로부터 최신 과제 목록을 수집합니다."""
        if not self.ntis_api_key:
            print("NTIS_API_KEY가 .env 파일에 설정되지 않았습니다.")
            return []

        # 최신 과제를 가져오기 위해 검색어를 비워두고, 날짜 내림차순으로 정렬
        URL = "https://www.ntis.go.kr/rndopen/openApi/public_project"
        params = {
            'apprVkey': self.ntis_api_key,
            'query': ' ', # 공백으로 전체 검색
            'sortby': 'DATE/DESC', # 최신순 정렬
            'startPosition': 1,
            'displayCnt': limit
        }
        
        try:
            response = requests.get(URL, params=params, timeout=20)
            response.raise_for_status()
            root = ET.fromstring(response.content)

            project_list = []
            for hit in root.findall('.//HIT'):
                project_data = {
                    'pjtId': hit.findtext('ProjectNumber'),
                    'pjtTitle': hit.findtext('./ProjectTitle/Korean'),
                    'pjtGoal': hit.findtext('./Goal/Full'),
                    'pjtContent': hit.findtext('./Abstract/Full'),
                    'pjtKeyword': hit.findtext('./Keyword/Korean')
                }
                project_list.append(project_data)
            return project_list
        except requests.exceptions.RequestException as e:
            print(f"NTIS API 요청 오류: {e}")
            return []
        except ET.ParseError as e:
            print(f"NTIS XML 파싱 오류: {e}")
            return []
