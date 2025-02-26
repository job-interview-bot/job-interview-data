import customized_webdriver as wd
from bs4 import BeautifulSoup
import requests

from selenium.webdriver.common.by import By

from itertools import chain
import time
import pandas as pd
import re
from datetime import datetime, timedelta, timezone
import sys, os

PAUSE_TIME = 1.5  # 대기 시간
TRFIC_PAUSE_TIME = 30  # 트래픽 캡처 대기 시간
KST = timezone(timedelta(hours=9))


if __name__ == "__main__":
    category_code = 518  # IT개발/인터넷 코드

    options = wd.ChromeOptions()

    # Chrome 옵션 설정
    # options.add_argument('--headless')
    options.add_argument("--disable-notifications")  # 알림 비활성화
    options.add_experimental_option(
        "prefs",
        {"profile.default_content_setting_values.notifications": 2},  # 1: 허용, 2: 차단
    )
    options.page_load_strategy = "none"  # 로딩 무시 옵션 추가

    driver = wd.CustomizedDriver(options=options)
    driver.scopes = ["results", "details"]

    url = f"https://www.wanted.co.kr/wdlist/{category_code}?country=kr&job_sort=job.latest_order&years=-1&locations=all"

    driver.get(url)
    driver.implicitly_wait(10)

    recruits_list = []

    # 현재 크롤링 시작 시간
    now = datetime.now(KST)
    today_str = now.strftime("%Y%m%d")
    print(f'## {now.strftime("%Y%m%d")} - 원티드 사이트 크롤링 시작 ##')

    # 무한 스크롤 대응
    prev_page_len = 0
    reqs = None

    while True:
        try:
            time.sleep(PAUSE_TIME)

            reqs = driver.filter_network_log_all(
                pat=r"results", timeout=TRFIC_PAUSE_TIME
            )
            driver.check_status_code(reqs)
            now_page_len = len(reqs.response.data)

            if prev_page_len == now_page_len:
                break

            # 부분 수집용
            # if prev_page_len > 5:
            #     break

            prev_page_len = now_page_len

            # 스크롤을 아래로 내리기
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

        except AssertionError as e:
            print(f"[AssertionError]: {e}")
            continue  # 다음 아이템으로 넘어감

    # 채용공고 리스트
    for req in reqs.response.data:
        recruits_dict = driver.parse_request(req)

        # # 더미데이터 뽑기용
        # if len(recruits_list) >= 100:
        #     print(len(recruits_list))
        #     break

        for item in recruits_dict["data"]:
            recruits_list.append(
                {
                    "채용사이트명": "원티드",
                    "채용사이트_공고id": item["id"],
                    "직무_대분류": 0,
                    "직무_소분류": "임시",
                    "경력사항": "임시",
                    "회사명": item["company"]["name"],
                    "근무지역(회사주소)": None,
                    "회사로고이미지": None,  # url임
                    "공고제목": None,
                    "공고본문_타입": "categorical",
                    "공고본문_raw": None,
                    "공고출처url": None,
                    "모집시작일": None,  # 모집시작날짜가 따로 없는 것 같음.
                    "모집마감일": None,
                    "공고게시일": None,  # 공고게시날짜가 따로 없는 것 같음.
                }
            )

    # 리스트 체크용
    print(len(recruits_list))
    # tmp = set([x['id'] for x in recruits_list])
    # print(len(tmp))

    # 채용공고 별 상세정보
    url = "https://www.wanted.co.kr/wd"

    for item in recruits_list:
        try:
            driver.get(f'{url}/{item["채용사이트_공고id"]}')

            time.sleep(PAUSE_TIME)

            response = requests.get(f'{url}/{item["채용사이트_공고id"]}')
            html = response.text

            item["공고게시일"] = re.search(
                r'"datePosted"\s*:\s*"(\d{4}-\d{2}-\d{2})"', html
            ).group(1)
            post_date = datetime.strptime(item["공고게시일"], "%Y-%m-%d").replace(
                tzinfo=KST
            )

            req = driver.filter_network_log(
                pat=r"details", timeout=TRFIC_PAUSE_TIME, reset=True
            )
            detail_data = driver.parse_request(req)["data"]["job"]

            # 경력사항 범위 [TO] 구분자로 연결 -> 2-5년이면 2 [TO] 5로 찍힘.
            item["경력사항"] = " [TO] ".join(
                [str(detail_data["annual_from"]), str(detail_data["annual_to"])]
            )

            item["근무지역(회사주소)"] = detail_data["address"]["full_location"]
            item["회사로고이미지"] = detail_data["company"]["logo_img"]["origin"]

            item["공고제목"] = detail_data["detail"]["position"]
            item["공고본문_raw"] = detail_data["detail"]
            # 공고 url 외부링크가 있을 경우, 다음 변수에 담김
            out_link = detail_data["detail"].get("out_link", None)
            item["공고출처url"] = (
                f'{url}/{item["채용사이트_공고id"]}' if not out_link else out_link
            )

            item["모집시작일"] = re.search(
                r'"datePosted"\s*:\s*"(\d{4}-\d{2}-\d{2})"', html
            ).group(1)
            item["모집마감일"] = detail_data["due_time"]

        except Exception as e:
            print(f"[{type(e).__name__}] item_id({item['채용사이트_공고id']}): {e}")
            # print(e.with_traceback())
            continue  # 다음 아이템으로 넘어감

    # 결과 : recruits_list에 담김.. 형식은 recruits_list 참고
    recruits_result = pd.DataFrame(recruits_list)

    # 저장할 폴더 경로
    folder_path = f"results/{today_str}"
    os.makedirs(folder_path, exist_ok=True)

    # CSV 파일 저장 (UTF-8 인코딩, 인덱스 없이)
    recruits_result.to_csv(
        f"{folder_path}/wanted{today_str}_all.csv", index=False, encoding="utf-8"
    )
    print(f"## {folder_path}/wanted{today_str}_all.csv 저장 완료")

    driver.close()
