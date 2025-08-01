# collector.py (Final Version - Selenium with Step-by-Step Debugging)
import requests
from bs4 import BeautifulSoup
import logging
from typing import List, Dict, Optional
import io
# from pypdf import PdfReader # PDF 분석을 잠시 비활성화하므로 주석 처리

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import traceback

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class DataCollector:
    """
    Selenium을 사용하여 동적 웹사이트의 정보를 수집하는 최종 안정화 버전.
    문제의 원인을 찾기 위해 PDF 분석 기능을 잠시 비활성화한 디버깅 버전입니다.
    """
    def __init__(self):
        self.sources = {'ntis': self._scrape_ntis}
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.driver = None
        try:
            options = webdriver.ChromeOptions()
            options.add_argument("window-size=1920,1080")
            options.add_argument("--log-level=3")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-gpu")
            options.add_argument("--disable-dev-shm-usage")
            options.add_experimental_option('excludeSwitches', ['enable-logging', 'enable-automation'])
            options.add_experimental_option('useAutomationExtension', False)
            
            self.driver = webdriver.Chrome(service=Service(), options=options)
            self.driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
                "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
            })
            
            logging.info("Selenium WebDriver가 성공적으로 초기화되었습니다.")
        except Exception as e:
            logging.error(f"Selenium WebDriver 초기화 중 오류 발생: {e}")
            self.driver = None

    def __del__(self):
        if self.driver:
            self.driver.quit()

    def collect(self, source: str = 'ntis', limit: int = 10) -> Optional[List[Dict[str, str]]]:
        if not self.driver:
            return None
        return self.sources[source](limit)

    def _scrape_ntis(self, limit: int) -> Optional[List[Dict[str, str]]]:
        base_url = f"https://www.ntis.go.kr/ThSearchProjectList.do?searchWord=연구&sort=SS04/DESC"
        
        try:
            self.driver.get(base_url)
            
            # [핵심] Selenium의 네이티브 기능을 사용하여 요소를 직접 찾습니다.
            wait = WebDriverWait(self.driver, 20)
            list_container = wait.until(EC.presence_of_element_located((By.ID, "search_project_list")))
            
            # JavaScript가 모든 'li' 태그를 렌더링할 시간을 줍니다.
            time.sleep(2) 

            items = list_container.find_elements(By.TAG_NAME, 'li')
            if not items:
                raise Exception("과제 항목(li)을 찾을 수 없습니다.")

            projects = []
            for i, item in enumerate(items):
                if i >= limit: break

                # BeautifulSoup 대신 Selenium의 find_element를 사용합니다.
                title_tag = item.find_element(By.CSS_SELECTOR, "div.title > a")
                title = title_tag.text.strip()
                detail_url = "https://www.ntis.go.kr" + title_tag.get_attribute('href')
                
                details = item.find_elements(By.CSS_SELECTOR, "dl > dd")
                agency = details[0].text.strip() if len(details) > 0 else "N/A"
                department = details[1].text.strip() if len(details) > 1 else "N/A"
                period = details[2].text.strip() if len(details) > 2 else "N/A"

                logging.info(f"({i+1}/{limit}) '{title}' 과제 목록 정보 수집 완료.")
                
                # [수정] 상세 페이지 및 PDF 분석 기능을 잠시 비활성화합니다.
                summary_text = "[디버깅 모드] 상세 내용 분석 비활성화됨"
                
                projects.append({
                    "title": title, "agency": agency, "department": department,
                    "end_date": period.split('~')[-1].strip() if '~' in period else period,
                    "url": detail_url, "summary": summary_text, "source": "NTIS Selenium Scraper (Debug)"
                })
            
            logging.info(f"NTIS 목록 크롤링으로 {len(projects)}개의 과제를 성공적으로 수집했습니다.")
            return projects
        except Exception as e:
            logging.error(f"NTIS 목록 스크래핑 중 오류 발생: {e}")
            try:
                with open("error_page.html", "w", encoding="utf-8") as f:
                    f.write(self.driver.page_source)
                logging.info("오류 발생 시점의 화면을 'error_page.html' 파일로 저장했습니다.")
            except Exception as e_save:
                logging.error(f"오류 페이지 저장 실패: {e_save}")
            
            with open("error.log", "a", encoding="utf-8") as f:
                f.write(f"\n--- Collector Error (Debug Mode) ---\n")
                f.write(traceback.format_exc())

            return None
