# collector.py (최종 수정 완료)

import os
import requests
import xml.etree.ElementTree as ET
from urllib.parse import unquote

class DataCollector:
    def __init__(self):
        # .env 파일에서 NTIS API 키를 불러옵니다.
        self.ntis_api_key = os.getenv("NTIS_API_KEY")

    def collect(self, source="ntis", topic="", limit=100):
        """
        주어진 소스에서 데이터를 수집하는 메인 메소드.
        """
        if source == "ntis":
            return self._collect_from_ntis(topic, limit)
        return []

    def _collect_from_ntis(self, topic, limit):
        """NTIS API로부터 특정 주제의 과제 목록을 수집합니다."""
        if not self.ntis_api_key:
            print("오류: NTIS_API_KEY가 .env 파일에 설정되지 않았습니다.")
            return []
        
        if not topic:
            print("오류: 검색할 연구 주제가 비어있습니다.")
            return []

        # API 요청 URL 및 파라미터
        URL = "https://www.ntis.go.kr/rndopen/openApi/public_project"
        params = {
            'apprVkey': unquote(self.ntis_api_key),
            # --------------------------------------------------------------------
            # ▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼ 여기가 핵심 수정 부분 ▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼
            # 불필요한 .encode('UTF-8')를 제거하고, requests가 자동으로 처리하도록 변경
            'query': topic,
            # ▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲
            # --------------------------------------------------------------------
            'startPosition': 1,
            'displayCnt': limit
        }
        
        print(f"NTIS API 요청: 주제='{topic}', 개수={limit}")

        try:
            response = requests.get(URL, params=params, timeout=30)
            response.raise_for_status()

            root = ET.fromstring(response.content)
            
            total_hits = root.find('TOTALHITS')
            if total_hits is None or int(total_hits.text) == 0:
                print("NTIS API 응답: 검색 결과가 없습니다.")
                return []

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
            
            print(f"NTIS API 응답: {len(project_list)}개의 과제를 성공적으로 파싱했습니다.")
            return project_list

        except requests.exceptions.RequestException as e:
            print(f"오류: NTIS API 요청에 실패했습니다. (네트워크/타임아웃 등) - {e}")
            return []
        except ET.ParseError as e:
            print(f"오류: NTIS API의 응답(XML)을 파싱하는 데 실패했습니다. - {e}")
            return []
        except Exception as e:
            print(f"오류: 데이터 수집 중 예기치 않은 오류가 발생했습니다. - {e}")
            return []
