import customized_webdriver as wd
from bs4 import BeautifulSoup
import requests

from selenium.webdriver.common.by import By

from itertools import chain
import time
from datetime import datetime, timedelta, timezone
import pandas as pd
import sys, os
import logging

PAUSE_TIME = 3  # 대기 시간
TRFIC_PAUSE_TIME = 10 # 트래픽 캡처 대기 시간
KST = timezone(timedelta(hours=9))

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
log_dir = os.path.join(BASE_DIR, "logs/")
if not os.path.exists(log_dir):
    os.makedirs(log_dir, exist_ok=True)

log_file = os.path.join(log_dir, 'dag.log')
# 기존 핸들러에 추가하거나 기본 설정 재구성
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)



if __name__ == "__main__":
    category_code = 58  # IT개발/인터넷 코드

    options = wd.ChromeOptions()

    # Chrome 옵션 설정
    options.add_argument('--headless')  # GUI 없이 실행
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    options.add_argument("--disable-notifications")  # 알림 비활성화
    options.add_experimental_option("prefs", {
        "profile.default_content_setting_values.notifications": 2  # 1: 허용, 2: 차단
    })
    driver = wd.CustomizedDriver(options=options)
    driver.scopes = ["ScreenJobCategory", "RecruitList", "gqlScreenActivityDetail"]

    url = f"https://linkareer.com/list/recruit?filterBy_activityTypeID=5&filterBy_categoryIDs={category_code}&filterBy_status=OPEN&orderBy_direction=DESC&orderBy_field=RECENT&page=1"
    driver.get(url)
    driver.implicitly_wait(10)

    recruits_list = []

    # 현재 크롤링 시작 시간
    now = datetime.now(KST)
    today_str = now.strftime("%Y%m%d")
    print(f"## {today_str} - 링커리어 사이트 크롤링 시작 ##")
    time_24h_ago = now - timedelta(hours=24)

    # 채용공고 리스트
    btn_idx = 2  # prev가 0번째 idx이므로, 2부터 시작(첫 시작 페이지 제외)
    now_page = "0"

    while True:
        req = driver.filter_network_log(
            pat="RecruitList&variables", timeout=TRFIC_PAUSE_TIME, reset=True
        )

        # 페이지 넘버링 변수 수정
        if (
            int(now_page.strip()) == 7 or req.response.status_code == 408
        ):  # 5페이지 이상 혹은 다음 페이지로 넘어가지 못했을 경우
            # 어디까지 수집했는지에 대한 로그처리 필요할듯 (now_page와 마지막으로 수집한 공고 비교 필요..)
            break

        recruits_dict = driver.parse_request(req)

        for item in recruits_dict["data"]["activities"]["nodes"]:

            recruits_list.append(
                {
                    "채용사이트명": "링커리어",
                    "채용사이트_공고id": item["id"],
                    "직무_대분류": 0,  # [합의 필요] 서연's 코드 : 0
                    "직무_소분류": " [SEP] ".join(
                        [i["name"] for i in item["categories"]]
                    ),
                    "경력사항": " [SEP] ".join(
                        [i for i in item["jobTypes"]]
                    ),  # 근무경험이 여러개인 경우, [SEP]으로 분리. e.g. "NEW [SEP] EXPERIENCED"
                    "회사명": item["organizationName"],
                    "근무지역(회사주소)": " [SEP] ".join(
                        [i["address"] for i in item["addresses"]]
                    ),  # 주소 여러개일 경우, [SEP]으로 분리
                    "회사로고이미지": item["logoImage"]["url"],
                    "회사복지": {
                        "is_remote_work": item["addresses"][0][
                            "isPossibleWorkingFromHome"
                        ]  # [논의 필요] .md 파일에는 회사 복지 사항을 공고 상세에 넣는 걸로 표기했는데, 이렇게 따로 빼는 것도 좋을듯
                    },
                    "공고제목": item["title"],
                    "공고본문_타입": "hybrid",
                    "공고본문_raw": None,
                    "공고출처url": None,
                    "모집시작일": None,
                    "모집마감일": None,
                    "공고게시일": None,
                }
            )

        # 다음 버튼 찾기
        buttons = driver.find_element_all(
            By.CSS_SELECTOR,
            "#__next > div.recruit__StyledWrapper-sc-85ef35dd-0.iRyaqA > div > main > div > section > div.Pagination__StyledWrapper-sc-f2d63645-0.iKXhzz > button",
        )
        buttons_len = len(buttons)

        # 버튼 요소를 찾지 못했을 경우 처리 필요. 로그로 넘기든.. 일단 임시
        assert buttons, "[crawling.linkcareer] 페이지 넘김 버튼 요소 발견 못함"

        driver.execute_script("arguments[0].click();", buttons[btn_idx])

        # next 버튼일 경우, 페이지 번호(텍스트) 존재 x
        next_page = buttons[btn_idx].find_element(By.CLASS_NAME, "MuiButton-label").text
        print(next_page, now_page, btn_idx, req.response.status_code)

        if not next_page:
            btn_idx = 2
            continue

        now_page = next_page
        btn_idx += 1

        time.sleep(PAUSE_TIME)

    # 채용공고 별 상세정보
    from datetime import datetime, timezone

    remove_idx = []
    for idx, item in enumerate(recruits_list):
        try:
            driver.get(f'https://linkareer.com/activity/{item["채용사이트_공고id"]}')

            time.sleep(PAUSE_TIME)

            req = driver.filter_network_log(
                pat=r"gqlScreenActivityDetail&variables",
                timeout=TRFIC_PAUSE_TIME,
                reset=True,
            )
            detail_data = driver.parse_request(req)

            # 밀리초 날짜 형식으로 변환 (1초 = 1000밀리초)
            start_millisec = detail_data["data"]["activity"]["recruitStartAt"]
            # 밀리초(ms) → 초(s) 변환 후 datetime 변환
            start_datetime = datetime.fromtimestamp(start_millisec / 1000, timezone.utc).astimezone(KST)

            # 현재 시간으로부터 24시간 이내인지 확인
            time_diff = now - start_datetime
            is_within_24h = timedelta(0) <= time_diff <= timedelta(hours=24)

            # print(time_diff)
            # print(is_within_24h)

            if is_within_24h:
                start_time = datetime.fromtimestamp(
                    start_millisec / 1000, timezone.utc
                ).strftime("%Y%m%d")

                end_millisec = detail_data["data"]["activity"]["recruitCloseAt"]
                end_time = datetime.fromtimestamp(
                    end_millisec / 1000, timezone.utc
                ).strftime("%Y%m%d")

                created_millisec = detail_data["data"]["activity"]["createdAt"]
                created_time = datetime.fromtimestamp(
                    created_millisec / 1000, timezone.utc
                ).strftime("%Y%m%d")

                item["모집시작일"] = start_time
                item["모집마감일"] = end_time
                item["공고게시일"] = created_time

                # 여기서 HTML 파싱 후 텍스트만 추출
                raw_html = detail_data["data"]["activity"]["detailText"]["text"]
                soup = BeautifulSoup(raw_html, "html.parser")
                clean_text = soup.get_text(
                    separator="\n", strip=True
                )  # 태그 제거 후 순수 텍스트만 가져오기
                item["공고본문_raw"] = clean_text
                item["공고출처url"] = detail_data["data"]["activity"]["applyDetail"]

            else:
                remove_idx.append(idx)
                continue

        except Exception as e:
            print(f"[{type(e).__name__}] item_id({item['채용사이트_공고id']}): {e}")
            # print(e.with_traceback())
            continue  # 다음 아이템으로 넘어감

    # 결과 : recruits_list에 담김.. 형식은 recruits_list 참고
    recruits_result = pd.DataFrame(recruits_list)

    recruits_result.drop(remove_idx, inplace=True)

    # 저장할 폴더 경로
    folder_path = os.path.join(BASE_DIR, f'results/{today_str}')
    os.makedirs(folder_path, exist_ok=True)

    # CSV 파일 저장 (UTF-8 인코딩, 인덱스 없이)
    recruits_result.to_csv(os.path.join(folder_path, f'linkareer_{today_str}.csv'), index=False, encoding='utf-8')
    logging.info(f"## {os.path.join(folder_path, f'linkareer_{today_str}.csv')} 저장 완료")