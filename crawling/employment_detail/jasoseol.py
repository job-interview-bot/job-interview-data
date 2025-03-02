## detail

import customized_webdriver as wd
from bs4 import BeautifulSoup

from itertools import chain
import time
from datetime import datetime, timedelta, timezone
import pandas as pd
import sys, os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

PAUSE_TIME = 2  # 대기 시간
TRFIC_PAUSE_TIME = 20  # 트래픽 캡처 대기 시간
KST = timezone(timedelta(hours=9))

if __name__ == "__main__":
    # 채용공고 IT/인터넷 카테고리 코드
    category_code = set(
        {
            160,
            164,
            165,
            166,
            167,
            168,
            169,
            170,
            171,
            172,
            173,
            174,
            175,
            176,
            177,
            178,
            179,
            180,
            181,
            182,
        }
    )

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
    driver.scopes = ["calendar_list", "get", "company-reports"]

    url = "https://jasoseol.com/recruit"

    driver.get(url)
    driver.implicitly_wait(10)

    # 채용공고 메타데이터 트래픽 캡처
    req = driver.filter_network_log(
        pat=r"calendar_list\.json", timeout=TRFIC_PAUSE_TIME
    )
    recruit_dict = driver.parse_request(req)

    recruits_list = []
    # 현재 크롤링 시작 시간
    now = datetime.now(KST)
    today_str = now.strftime("%Y%m%d")
    print(f'## {now.strftime("%Y%m%d")} - 자소설 사이트 크롤링 시작 ##')
    time_24h_ago = now - timedelta(hours=24)
    # 채용공고 리스트 - 2024.11.29 부터 시작
    # 오늘의 채용공고만 가져오는 방식으로 변경
    # 초기 시작에는 이전 1달 크롤링
    for item in recruit_dict["employment"]:
        group_id = [
            map(lambda x: x["group_id"], x["duty_groups"]) for x in item["employments"]
        ]
        group_id = set(chain(*group_id))  # IT/인터넷 카테고리 코드가 있는지 확인

        if group_id & category_code:
            recruits_list.append(
                {
                    "채용사이트명": "자소설",
                    "채용사이트_공고id": item["id"],
                    "직무_대분류": "IT/인터넷",  # [합의 필요] 서연's 코드 : 0
                    "직무_소분류": "임시",
                    "경력사항": "임시",  # 코드화되어있어서 일단 못찾음. 확인 필요함
                    "회사명": item["name"],
                    "근무지역(회사주소)": "임시",
                    "회사로고이미지": None,
                    "공고제목": item["title"],
                    "공고본문_타입": "img",  # [합의 필요] 예원's -> 채용 형태로 추정함 : item['recruit_type']
                    "공고본문_raw": None,
                    "공고출처url": None,
                    "모집시작일": item["start_time"],
                    "모집마감일": item["end_time"],  # "2025-02-17T16:50:16.000+09:00"
                    "공고게시일": None,
                }
            )

    # 자소설은 공고게시일/모집시작일 기준으로 오래된 순으로 정렬되는 것 같음. 최신순 수집을 위해 reverse 해주기
    recruits_list.reverse()

    # # 더미데이터 뽑기용
    # recruits_list = recruits_list[:100] if len(recruits_list) > 100 else recruits_list
    # print(len(recruits_list))

    # 채용공고 별 상세정보

    remove_idx = []
    for idx, item in enumerate(recruits_list):
        try:
            driver.get(f'{url}/{item["채용사이트_공고id"]}')
            time.sleep(PAUSE_TIME)
            WebDriverWait(driver, TRFIC_PAUSE_TIME).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )

            req = driver.filter_network_log(
                pat=r"get\.json", timeout=TRFIC_PAUSE_TIME, reset=True
            )
            assert req is not None, "No network request matched the pattern."
            assert (
                req.response.status_code == 200
            ), f"Unexpected status code: {req.response.status_code}"

            detail_data = driver.parse_request(req)

            soup = BeautifulSoup(detail_data["content"], "html.parser")

            item["공고게시일"] = detail_data["created_at"]
            post_date = datetime.strptime(item["공고게시일"], "%Y-%m-%dT%H:%M:%S.%f%z")

            # 24시간 제한
            if now - post_date <= timedelta(hours=24):
                # 이미지 태그 가져오기
                img_tag = soup.find("img")

                assert (
                    img_tag
                ), "[crawling.jasoseol] 상세정보 에러 2.1 : 이미지 태그를 찾을 수 없습니다."

                # src 속성 가져오기
                img_src = img_tag.get("src")

                assert (
                    img_src
                ), "[crawling.jasoseol] 상세정보 에러 2.2 : 이미지 URL을 찾을 수 없습니다."

                item["회사로고이미지"] = detail_data["image_file_name"]

                item["공고본문"] = img_src
                item["공고출처url"] = detail_data["employment_page_url"]
                item["공고게시일"] = detail_data["created_at"]
                # company-reports(get)에 회사 주소 정보 있는데, company_information.json에서 more = true 면 주소정보가 날라오는 듯
                # 테스트 필요함
                # company-reports는 리스트 형태, 원소['address'] 가 주소값

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
    folder_path = f"results/{today_str}"
    os.makedirs(folder_path, exist_ok=True)

    # CSV 파일 저장 (UTF-8 인코딩, 인덱스 없이)
    recruits_result.to_csv(
        f"{folder_path}/jasoseol_{today_str}.csv", index=False, encoding="utf-8"
    )
    print(f"## {folder_path}/jasoseol_{today_str}.csv 저장 완료")

    driver.close()
