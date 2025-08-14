# collector.py

import os
import requests
import xml.etree.ElementTree as ET
from urllib.parse import unquote, urlencode

class DataCollector:
    """
    NTIS와 같은 외부 소스에서 R&D 과제 데이터를 수집하는 클래스.
    """
    def __init__(self):
        """
        클래스가 생성될 때 .env 파일에서 NTIS API 키를 불러옵니다.
        """
        self.ntis_api_key = os.getenv("NTIS_API_KEY")

    def collect(self, source="ntis", topic="", limit=100):
        """
        주어진 소스에서 데이터를 수집하는 메인 메소드.
        topic을 직접 파라미터로 받습니다.
        """
        if source == "ntis":
            return self._collect_from_ntis(topic, limit)
        return []

    def _collect_from_ntis(self, topic, limit):
        """
        NTIS Open API로부터 특정 주제의 과제 목록을 수집하는 내부 메소드.
        (최종 요청 URL 검수 기능 포함)
        """
        # 1. API 키 및 검색어 유효성 검사
        if not self.ntis_api_key:
            print("오류: NTIS_API_KEY가 .env 파일에 설정되지 않았습니다.")
            return []
        if not topic:
            print("오류: 검색할 연구 주제가 비어있습니다.")
            return []

        # 2. API 요청 파라미터 설정
        URL = "https://www.ntis.go.kr/rndopen/openApi/public_project"
        params = {
            'apprVkey': unquote(self.ntis_api_key),
            'query': topic,
            'startPosition': 1,
            'displayCnt': limit
        }
        
        # 3. 최종 요청 URL 검수 기능
        final_url = f"{URL}?{urlencode(params, encoding='UTF-8')}"
        print("----------------------------------------------------------------------")
        print(f">>> [검수] 프로그램이 실제 접속하는 최종 URL 주소:")
        print(final_url)
        print("----------------------------------------------------------------------")
        
        print(f"NTIS API 요청: 주제='{topic}', 개수={limit}")

        try:
            # 4. API 호출
            response = requests.get(URL, params=params, timeout=30)
            response.raise_for_status()

            # 5. XML 응답 파싱
            root = ET.fromstring(response.content)
            
            # 6. 검색 결과 유무 확인
            total_hits = root.find('TOTALHITS')
            if total_hits is None or int(total_hits.text) == 0:
                print("NTIS API 응답: 검색 결과가 없습니다.")
                return []

            # 7. 결과 데이터 추출
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

        # 8. 예외 처리
        except requests.exceptions.RequestException as e:
            print(f"오류: NTIS API 요청에 실패했습니다. (네트워크/타임아웃 등) - {e}")
            return []
        except ET.ParseError as e:
            print(f"오류: NTIS API의 응답(XML)을 파싱하는 데 실패했습니다. - {e}")
            return []
        except Exception as e:
            print(f"오류: 데이터 수집 중 예기치 않은 오류가 발생했습니다. - {e}")
            return []
