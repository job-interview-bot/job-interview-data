import customized_webdriver as wd
from bs4 import BeautifulSoup
import requests

from selenium.webdriver.common.by import By

from itertools import chain
import time

PAUSE_TIME = 3  # 대기 시간
TRFIC_PAUSE_TIME = 10 # 트래픽 캡처 대기 시간


if __name__ == "__main__":
    category_code = 58 # IT개발/인터넷 코드

    options = wd.ChromeOptions()

    # Chrome 옵션 설정
    # options.add_argument('--headless')
    options.add_argument("--disable-notifications")  # 알림 비활성화
    options.add_experimental_option("prefs", {
        "profile.default_content_setting_values.notifications": 2  # 1: 허용, 2: 차단
    })

    driver = wd.CustomizedDriver(options=options)
    driver.scopes = ['ScreenJobCategory', 'RecruitList', 'gqlScreenActivityDetail']

    url = f'https://linkareer.com/list/recruit?filterBy_activityTypeID=5&filterBy_categoryIDs={category_code}&filterBy_status=OPEN&orderBy_direction=DESC&orderBy_field=RECENT&page=1'
    driver.get(url)
    driver.implicitly_wait(10)

    """
    id : 채용공고 id
    name : 회사명
    start_time : 시작일
    end_time : 종료일
    detail_type : 상세정보 자료형
    detail : 상세정보 데이터 
    """
    recruits_list = []

    # 채용공고 리스트
    btn_idx = 2 # prev가 0번째 idx이므로, 2부터 시작(첫 시작 페이지 제외)
    now_page = ''

    while True:
        req = driver.filter_network_log(pat='RecruitList&variables', timeout=TRFIC_PAUSE_TIME, reset=True)
        
        if req.response.status_code == 408: # 다음 페이지로 넘어가지 못했을 경우
            # 어디까지 수집했는지에 대한 로그처리 필요할듯 (now_page와 마지막으로 수집한 공고 비교 필요..)
            break

        recruits_dict = driver.parse_request(req)

        for item in recruits_dict['data']['activities']['nodes']:

            recruits_list.append({
                'id': item['id'],
                'name': item['organizationName'],
                'start_time': None,
                'end_time': None,
                'detail_type': 'hybrid',
                'detail': None,
                'applyUrl': None
            })

        # 다음 버튼 찾기
        buttons = driver.find_element_all(By.CSS_SELECTOR, '#__next > div.recruit__StyledWrapper-sc-85ef35dd-0.iRyaqA > div > main > div > section > div.Pagination__StyledWrapper-sc-f2d63645-0.iKXhzz > button')
        buttons_len = len(buttons)
        
        # 버튼 요소를 찾지 못했을 경우 처리 필요. 로그로 넘기든.. 일단 임시
        assert buttons, "[crawling.linkcareer] 페이지 넘김 버튼 요소 발견 못함"

        driver.execute_script("arguments[0].click();", buttons[btn_idx])

        # next 버튼일 경우, 페이지 번호(텍스트) 존재 x
        next_page = buttons[btn_idx].find_element(By.CLASS_NAME, 'MuiButton-label').text
        print(next_page, now_page, btn_idx, req.response.status_code)
        
        if not next_page:
            btn_idx = 2
            continue
        
        now_page = next_page
        btn_idx += 1

        time.sleep(PAUSE_TIME)

    
    # 채용공고 별 상세정보
    from datetime import datetime, timezone

    for item in recruits_list:
        driver.get(f'https://linkareer.com/activity/{item["id"]}')

        req = driver.filter_network_log(pat='gqlScreenActivityDetail&variables', timeout=TRFIC_PAUSE_TIME, reset=True)
        detail_data = driver.parse_request(req)

        # 밀리초 날짜 형식으로 변환 (1초 = 1000밀리초)
        start_millisec = detail_data['data']['activity']['recruitStartAt']
        start_time = datetime.fromtimestamp(start_millisec / 1000, timezone.utc).strftime("%Y-%m-%d")
        
        end_millisec = detail_data['data']['activity']['recruitCloseAt']
        end_time = datetime.fromtimestamp(end_millisec / 1000, timezone.utc).strftime("%Y-%m-%d")

        item['start_time'] = start_time
        item['end_time'] = end_time
        item['detail'] = detail_data['data']['activity']['detailText']['text']
        item['applyUrl'] = detail_data['data']['activity']['applyDetail']

        time.sleep(PAUSE_TIME)

# 결과 : recruits_list에 담김.. 형식은 recruits_list 참고