import customized_webdriver as wd
from bs4 import BeautifulSoup

from itertools import chain
import time

PAUSE_TIME = 3  # 대기 시간
TRFIC_PAUSE_TIME = 10 # 트래픽 캡처 대기 시간


if __name__ == "__main__":
    # 채용공고 IT/인터넷 카테고리 코드
    category_code = set({160,164,165,166,167,168,169,170,171,172,173,174,175,176,177,178,179,180,181,182})

    options = wd.ChromeOptions()

    # Chrome 옵션 설정
    # options.add_argument('--headless')
    options.add_argument("--disable-notifications")  # 알림 비활성화
    options.add_experimental_option("prefs", {
        "profile.default_content_setting_values.notifications": 2  # 1: 허용, 2: 차단
    })

    driver = wd.CustomizedDriver(options=options)
    driver.scopes = ['calendar_list', 'get']

    url = 'https://jasoseol.com/recruit'

    driver.get(url)
    driver.implicitly_wait(10)

    # 채용공고 메타데이터 트래픽 캡처
    req = driver.filter_network_log(pat='calendar_list\.json', timeout=TRFIC_PAUSE_TIME)
    recruit_dict = driver.parse_request(req)

    """
    id : 채용공고 id
    name : 회사명
    start_time : 시작일
    end_time : 종료일
    detail_type: 상세정보 데이터타입
    detail: 상세정보 데이터
    applyUrl: 채용 url
    1. 어느 사이트에서 수집했는지
    2. 회사 로고 이미지
    3. 회사 위치
    4. 경력사항
    
    """
    recruits_list = []

    # 채용공고 리스트
    for item in recruit_dict['employment']:
        group_id = [map(lambda x : x['group_id'], x['duty_groups']) for x in item['employments']]
        group_id = set(chain(*group_id)) # IT/인터넷 카테고리 코드가 있는지 확인
        
        if group_id & category_code:
            recruits_list.append({
                'id': item['id'],
                'name': item['name'],
                'start_time': item['start_time'],
                'end_time': item['end_time'],
                'detail_type': None,
                'detail': None,
                'applyUrl': None
            })

    # 채용공고 별 상세정보
    for item in recruits_list:
        driver.get(f'{url}/{item["id"]}')

        req = driver.filter_network_log(pat='get\.json', timeout=TRFIC_PAUSE_TIME, reset=True)
        detail_data = driver.parse_request(req)

        soup = BeautifulSoup(detail_data['content'], 'html.parser')

        # 이미지 태그 가져오기
        img_tag = soup.find("img")

        assert img_tag, "[crawling.jasoseol] 상세정보 에러 2.1 : 이미지 태그를 찾을 수 없습니다."

        # src 속성 가져오기
        img_src = img_tag.get("src")

        assert img_src, "[crawling.jasoseol] 상세정보 에러 2.2 : 이미지 URL을 찾을 수 없습니다."

        item['detail_type'] = 'img'
        item['detail'] = img_src
        item['applyUrl'] = detail_data['employment_page_url']
        print(item)

        time.sleep(PAUSE_TIME)

    # 결과 : recruits_list에 담김.. 형식은 recruits_list 참고
                                  