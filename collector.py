# collector.py 파일의 _collect_from_ntis 함수만 교체

def _collect_from_ntis(self, topic, limit):
    """
    NTIS Open API로부터 특정 주제의 과제 목록을 수집하는 내부 메소드.
    (최종 요청 URL 검수 기능 추가)
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
    


    from urllib.parse import urlencode
    
    # 파라미터를 포함한 전체 URL 생성
    # (주의: params의 query는 한글이므로, urlencode 시 인코딩된 형태로 바뀜)
    final_url = f"{URL}?{urlencode(params, encoding='UTF-8')}"
    print("----------------------------------------------------------------------")
    print(f">>> [검수] 프로그램이 실제 접속하는 최종 URL 주소:")
    print(final_url)
    print("----------------------------------------------------------------------")

    
    print(f"NTIS API 요청: 주제='{topic}', 개수={limit}")

    try:
        # requests 라이브러리는 params 딕셔너리를 받아 자동으로 위 URL을 만듭니다.
        response = requests.get(URL, params=params, timeout=30)
        response.raise_for_status()

        # ... (이하 코드는 동일) ...
