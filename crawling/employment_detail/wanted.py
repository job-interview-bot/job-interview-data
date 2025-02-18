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
    driver.scopes = ['results', 'details']

    url = f'https://www.wanted.co.kr/wdlist/{category_code}?country=kr&job_sort=job.latest_order&years=0&locations=all'

    driver.get(url)
    driver.implicitly_wait(10)

    recruits_list = []

    # 무한 스크롤 대응
    prev_page_len = 0
    reqs = None

    while True:
        time.sleep(PAUSE_TIME)

        reqs = driver.filter_network_log_all(pat='results', timeout=TRFIC_PAUSE_TIME)
        driver.check_status_code(reqs)
        now_page_len = len(reqs.response.data)

        if prev_page_len == now_page_len:
            break

        if prev_page_len > 5:
            break

        prev_page_len = now_page_len

        # 스크롤을 아래로 내리기
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

    
    # 채용공고 리스트
    for req in reqs.response.data:
        recruits_dict = driver.parse_request(req)
        for item in recruits_dict['data']:
            recruits_list.append({
                "채용사이트명": "원티드",
                "채용사이트_공고id": item['id'],
                "직무_대분류": 0,
                "직무_소분류": "임시",
                "경력사항": "임시",

                "회사명": item['company']['name'],
                "근무지역(회사주소)": None,
                "회사로고이미지": None, # url임
                
                "공고제목": None,
                "공고본문_타입": "categorical",
                "공고본문_raw": None,
                "공고출처url": None,

                "모집시작일": None, # 모집시작날짜가 따로 없는 것 같음.
                "모집마감일": None,
                "공고게시일": "임시" # 공고게시날짜가 따로 없는 것 같음.
            })

    # 리스트 체크용
    # print(len(recruits_list))
    # tmp = set([x['id'] for x in recruits_list])
    # print(len(tmp))

    # 채용공고 별 상세정보
    url = 'https://www.wanted.co.kr/wd'

    for item in recruits_list:
        driver.get(f'{url}/{item["채용사이트_공고id"]}')

        req = driver.filter_network_log(pat='details', timeout=TRFIC_PAUSE_TIME, reset=True)
        detail_data = driver.parse_request(req)['data']['job']

        # -> 2-5년이면 2, 5로 찍힘 어떻게 처리할 지 생각해볼 것
        # item["경력사항"] = detail_data['annual_from'], detail_data['annual_to'] 

        item['근무지역(회사주소)'] = detail_data['address']['full_location']
        item['회사로고이미지'] = detail_data['company']['logo_img']['origin']
        
        item['공고제목'] = detail_data['detail']['position']
        item['공고본문_raw'] = detail_data['detail']
        # 공고 url 외부링크가 있을 경우, 다음 변수에 담김
        out_link = detail_data['detail']['out_link']
        item['공고출처url'] = f'{url}/{item["채용사이트_공고id"]}' if not out_link else out_link

        item['모집마감일'] = detail_data['due_time']
        
        
        time.sleep(PAUSE_TIME)       

# 결과 : recruits_list에 담김.. 형식은 recruits_list 참고                           