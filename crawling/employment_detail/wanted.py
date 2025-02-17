import customized_webdriver as wd
from bs4 import BeautifulSoup
import requests

from selenium.webdriver.common.by import By

from itertools import chain
import time

PAUSE_TIME = 3  # 대기 시간
TRFIC_PAUSE_TIME = 10 # 트래픽 캡처 대기 시간


if __name__ == "__main__":
    category_code = 518 # IT개발/인터넷 코드

    options = wd.ChromeOptions()

    # Chrome 옵션 설정
    # options.add_argument('--headless')
    options.add_argument("--disable-notifications")  # 알림 비활성화
    options.add_experimental_option("prefs", {
        "profile.default_content_setting_values.notifications": 2  # 1: 허용, 2: 차단
    })

    driver = wd.CustomizedDriver(options=options)
    driver.scopes = ['results\?', 'details\?']

    url = f'https://www.wanted.co.kr/wdlist/{category_code}?country=kr&job_sort=job.latest_order&years=0&locations=all'

    driver.get(url)
    driver.implicitly_wait(10)

    """
    id : 채용공고 id
    name : 회사명
    start_time : 시작일
    end_time : 종료일
    detail_type: 상세정보 데이터타입
    detail: 상세정보 데이터
    applyUrl: 채용 url
    """
    recruits_list = []

    # 무한 스크롤 대응
    prev_page_len = 0
    reqs = None

    while True:
        time.sleep(PAUSE_TIME)

        reqs = driver.filter_network_log_all(pat='results\?', timeout=TRFIC_PAUSE_TIME)
        driver.check_status_code(reqs)
        now_page_len = len(reqs.response.data)

        if prev_page_len == now_page_len:
            break

        prev_page_len = now_page_len

        # 스크롤을 아래로 내리기
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

    
    # 채용공고 리스트
    for req in reqs.response.data:
        recruits_dict = driver.parse_request(req)
        for item in recruits_dict['data']:
            recruits_list.append({
                'id': item['id'],
                'name': item['company']['name'],
                'start_time': None,
                'end_time': None,
                'detail_type': 'text',
                'detail': None,
                'applyUrl': None
            })

    # 리스트 체크용
    # print(len(recruits_list))
    # tmp = set([x['id'] for x in recruits_list])
    # print(len(tmp))

    # 채용공고 별 상세정보
    url = 'https://www.wanted.co.kr/wd'

    for item in recruits_list:
        driver.get(f'{url}/{item["id"]}')

        req = driver.filter_network_log(pat='details\?', timeout=TRFIC_PAUSE_TIME, reset=True)
        detail_data = driver.parse_request(req)

        item['end_time'] = detail_data['job']['due_time']
        item['detail_type'] = 'categorical'
        item['detail'] = detail_data['job']['detail']
        item['applyUrl'] = f'{url}/{item["id"]}'
        
        time.sleep(PAUSE_TIME)       

# 결과 : recruits_list에 담김.. 형식은 recruits_list 참고                           