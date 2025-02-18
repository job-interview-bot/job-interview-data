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
    driver.scopes = ['calendar_list', 'get', 'company-reports']

    url = 'https://jasoseol.com/recruit'

    driver.get(url)
    driver.implicitly_wait(10)

    # 채용공고 메타데이터 트래픽 캡처
    req = driver.filter_network_log(pat='calendar_list\.json', timeout=TRFIC_PAUSE_TIME)
    recruit_dict = driver.parse_request(req)

    recruits_list = []

    # 채용공고 리스트
    for item in recruit_dict['employment']:
        group_id = [map(lambda x : x['group_id'], x['duty_groups']) for x in item['employments']]
        group_id = set(chain(*group_id)) # IT/인터넷 카테고리 코드가 있는지 확인
        
        if group_id & category_code:
            recruits_list.append({
                "채용사이트명": "자소설",
                "채용사이트_공고id": item['id'],
                "직무_대분류": 0,
                "직무_소분류": "임시",
                "경력사항": "임시", # 코드화되어있어서 일단 못찾음. 확인 필요함

                "회사명": item['name'],
                "근무지역(회사주소)": "임시",
                "회사로고이미지": None,
                
                "공고제목": item['title'],
                "공고본문_타입": "img",
                "공고본문_raw": None,
                "공고출처url": None,

                "모집시작일": item['start_time'],
                "모집마감일": item['end_time'], # "2025-02-17T16:50:16.000+09:00"
                "공고게시일": None
            })

    # 채용공고 별 상세정보
    for item in recruits_list:
        driver.get(f'{url}/{item["채용사이트_공고id"]}')

        req = driver.filter_network_log(pat='get\.json', timeout=TRFIC_PAUSE_TIME, reset=True)
        detail_data = driver.parse_request(req)

        soup = BeautifulSoup(detail_data['content'], 'html.parser')

        # 이미지 태그 가져오기
        img_tag = soup.find("img")

        assert img_tag, "[crawling.jasoseol] 상세정보 에러 2.1 : 이미지 태그를 찾을 수 없습니다."

        # src 속성 가져오기
        img_src = img_tag.get("src")

        assert img_src, "[crawling.jasoseol] 상세정보 에러 2.2 : 이미지 URL을 찾을 수 없습니다."

        item["회사로고이미지"] = detail_data['image_file_name']

        item['공고본문'] = img_src
        item['공고출처url'] = detail_data['employment_page_url']

        item['공고게시일'] = detail_data['created_at']

        # company-reports(get)에 회사 주소 정보 있는데, company_information.json에서 more = true 면 주소정보가 날라오는 듯
        # 테스트 필요함    
        # company-reports는 리스트 형태, 원소['address'] 가 주소값


        time.sleep(PAUSE_TIME)

    # 결과 : recruits_list에 담김.. 형식은 recruits_list 참고
                                  