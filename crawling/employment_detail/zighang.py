import customized_webdriver as wd
from bs4 import BeautifulSoup
import requests

from selenium.webdriver.common.by import By

from itertools import chain
import time
import pandas as pd
from datetime import datetime, timedelta, timezone
import sys, os

PAUSE_TIME = 3  # 대기 시간
TRFIC_PAUSE_TIME = 10 # 트래픽 캡처 대기 시간
KST = timezone(timedelta(hours=9))

if __name__ == "__main__":

    data_size = 500 # 수집할 채용공고 개수
    category_codes = [ # IT개발/인터넷 코드
        'AI_%EB%8D%B0%EC%9D%B4%ED%84%B0', # AI_데이터 
        'IT%EA%B0%9C%EB%B0%9C_%EB%8D%B0%EC%9D%B4%ED%84%B0', # IT개발_데이터
    ]
    headers = {
        "User-Agent" : "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"
    }


    recruits_list = []

    # 현재 크롤링 시작 시간
    now = datetime.now(KST)
    today_str = now.strftime("%Y%m%d")
    print(f'## {now.strftime("%Y%m%d")} - 직행 사이트 크롤링 시작 ##')

    params = {
        'page': 0,
        'size':	11,
        'isOpen': 'true',
        'sortCondition': 'UPLOAD',
        'orderBy': 'DESC',
        'companyTypes':	'',
        'industries': '',
        'recruitmentTypeNames':	'',
        'recruitmentDeadlineType': '',
        'educations': '',
        'carrers': 'ZERO,ONE,TWO,THREE,FOUR,FIVE,SIX,SEVEN,EIGHT,NINE,TEN,IRRELEVANCE', # 경력
        'recruitmentAddress': '',
        'recJobMajorCategory': '임시', # category_codes 반복문으로 돌려서 집어넣기
        'recJobSubCategory': '',
        'companyName': '',
        'keywords':	'',
        # 날짜값이 2025-02-18 05:24 일 경우, 시간에 %20을 넣어서 조회 가능
        # 이 때, size 쿼리 파라미터는 없어도 됨.
        # e.g) 'uploadStartDate': '2025-02-18%2005:24
        'uploadStartDate': '', 
        'uploadEndDate': '',
        'workStartDate': '',
        'workEndDate': ''
    }


    # 채용공고 리스트
    for code in category_codes:
        params['recJobMajorCategory'] = code
        url = "".join([
            "https://api.zighang.com/api/recruitment/filter/v4?",
            f"page={params['page']}&",
            f"size={params['size']}&",
            f"isOpen={params['isOpen']}&",
            f"sortCondition={params['sortCondition']}&",
            f"orderBy={params['orderBy']}&",
            f"companyTypes={params['companyTypes']}&",
            f"industries={params['industries']}&",
            f"recruitmentTypeNames={params['recruitmentTypeNames']}&",
            f"recruitmentDeadlineType={params['recruitmentDeadlineType']}&",
            f"educations={params['educations']}&",
            f"carrers={params['carrers']}&",
            f"recruitmentAddress={params['recruitmentAddress']}&",
            f"recJobMajorCategory={params['recJobMajorCategory']}&",
            f"recJobSubCategory={params['recJobSubCategory']}&",
            f"companyName={params['companyName']}&",
            f"keywords={params['keywords']}&",
            f"uploadStartDate={params['uploadStartDate']}&",
            f"uploadEndDate={params['uploadEndDate']}&",
            f"workStartDate={params['workStartDate']}&",
            f"workEndDate={params['workEndDate']}"
        ])
        res = requests.get(url, headers=headers)

        for item in res.json()['recruitments']['recruitmentSimpleList']:
            post_date = datetime.strptime(item['uploadDate'], "%Y-%m-%d %H:%M").replace(tzinfo=KST)

            # 공고게시일 기준 24h 이내
            if now - post_date <= timedelta(hours=24):
                recruits_list.append({
                    "채용사이트명": "직행",
                    "채용사이트_공고id": item['recruitmentUid'],
                    "직무_대분류": 0,
                    "직무_소분류": "임시",
                    "경력사항": " [SEP] ".join(x for x in item['careers']), # 리스트형태. ['ONE', 'NINE']

                    "회사명": item['companyName'],
                    "근무지역(회사주소)": item['companyAddress'],
                    "회사로고이미지": item['mainImageUrl'],
                    
                    "공고제목": item['title'],
                    "공고본문_타입": None,
                    "공고본문_raw": None,
                    "공고출처url": item['recruitmentAnnouncementLink'],

                    "모집시작일": item['recruitmentStartDate'],
                    "모집마감일": item['recruitmentDeadline'],
                    "공고게시일": item['uploadDate'] # 2025-02-18 05:24
                })

    options = wd.ChromeOptions()

    # Chrome 옵션 설정
    # options.add_argument('--headless')
    options.add_argument("--disable-notifications")  # 알림 비활성화
    options.add_experimental_option("prefs", {
        "profile.default_content_setting_values.notifications": 2  # 1: 허용, 2: 차단
    })

    driver = wd.CustomizedDriver(options=options)

    # 채용공고 별 상세정보
    for idx, item in enumerate(recruits_list):
        
        url = f"https://zighang.com/recruitment/{item['채용사이트_공고id']}"
        driver.get(url)

        # elem = driver.find_element_one(value="#root > main > div.relative:nth-child(3)")
        detail_source = driver.find_element_all(value="#root > main > div.relative")[2].get_attribute('outerHTML')

        detail_html = BeautifulSoup(detail_source, 'html.parser')

        if detail_html.select_one('div.flex'): # 그룹바이 어쩌구는 div가 하나 더 생겨버림. 별도 처리..
            detail_source = driver.find_element_all(value="#root > main > div.relative")[3].get_attribute('outerHTML')
            detail_html = BeautifulSoup(detail_source, 'html.parser')
        
        # iframe 태그로 존재한다면 img
        if detail_html.find('iframe'):
            item['공고본문_타입'] = 'img'
            item['공고본문_raw'] = BeautifulSoup(detail_html.get('srcdoc'), 'html.parser').find('img').get('src')
        elif detail_html.find('img'): # 이미지와 텍스트가 동시에 있는 버전
            item['공고본문_타입'] = 'hybrid'
            elem = detail_html.find('img')
            item['공고본문_raw'] = {
                'img': elem.get('src'),
                'text': elem.get('alt')
            }
        elif detail_html.select_one('div.break-keep > div'): #
            item['공고본문_타입'] = 'text'
            item['공고본문_raw'] = detail_html.select_one('div.break-keep > div').text
        else: 
            item['공고본문_타입'] = 'unknown'
            item['공고본문_raw'] = detail_html.text

        # res = requests.get(url)
        # soup = BeautifulSoup(res.text, 'html.parser')
        
        # detail_res = soup.select_one('#root > main > div.relative:nth-child(3) > iframe')
        # detail_html = BeautifulSoup(detail_res.get('srcdoc'), 'html.parser')
        
        # item['공고본문_타입'] = 'img'
        # item['공고본문_raw'] = detail_html.find('img').get('src')

        time.sleep(PAUSE_TIME)

    # 결과 : recruits_list에 담김.. 형식은 recruits_list 참고
    recruits_result = pd.DataFrame(recruits_list)


    # 저장할 폴더 경로
    folder_path = f'results/{today_str}'
    os.makedirs(folder_path, exist_ok=True)

    # CSV 파일 저장 (UTF-8 인코딩, 인덱스 없이)
    recruits_result.to_csv(f'{folder_path}/zighang_{today_str}.csv', index=False, encoding='utf-8')
    print(f"## {folder_path}/zighang_{today_str}.csv 저장 완료")