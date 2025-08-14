# collector.py

import requests
import pandas as pd
import xml.etree.ElementTree as ET

def collect_ntis_projects(api_key, keyword, display_count=100):
    """
    NTIS API로 과제를 검색하여 pandas DataFrame으로 반환하는 수집기 함수.
    """
    [cite_start]URL = "https://www.ntis.go.kr/rndopen/openApi/public_project" # [cite: 43]
    params = {
        'apprVkey': api_key,
        'query': keyword.encode('UTF-8'),
        'startPosition': 1,
        'displayCnt': display_count
    [cite_start]} # [cite: 43]

    try:
        response = requests.get(URL, params=params, timeout=20)
        response.raise_for_status()
        root = ET.fromstring(response.content)

        project_list = []
        for hit in root.findall('.//HIT'):
            # [cite_start]매뉴얼을 기반으로 필요한 데이터 필드를 체계적으로 추출 [cite: 51, 52, 53, 54]
            project_data = {
                '과제고유번호': hit.findtext('ProjectNumber'),
                '국문과제명': hit.findtext('./ProjectTitle/Korean'),
                '연구책임자': hit.findtext('./Manager/Name'),
                '과제수행기관': hit.findtext('./Resear chAgency/Name'),
                '사업부처명': hit.findtext('./Ministry/Name'),
                '총연구기간시작': hit.findtext('./ProjectPeriod/TotalStart'),
                '총연구기간종료': hit.findtext('./ProjectPeriod/TotalEnd'),
                '정부투자연구비': int(hit.findtext('GovernmentFunds', '0')), # 숫자로 변환
                '연구목표': hit.findtext('./Goal/Full'),
                '연구내용': hit.findtext('./Abstract/Full'),
                '기대효과': hit.findtext('./Effect/Full'),
                '한글키워드': hit.findtext('./Keyword/Korean')
            }
            project_list.append(project_data)
        
        if not project_list:
            return pd.DataFrame() # 결과가 없으면 빈 DataFrame 반환

        return pd.DataFrame(project_list)

    except requests.exceptions.RequestException as e:
        print(f"API 요청 오류: {e}")
        return pd.DataFrame()
    except ET.ParseError as e:
        print(f"XML 파싱 오류: {e}")
        return pd.DataFrame()
