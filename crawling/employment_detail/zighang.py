import customized_webdriver as wd
from bs4 import BeautifulSoup
import requests

from selenium.webdriver.common.by import By

from itertools import chain
import time

PAUSE_TIME = 3  # 대기 시간
TRFIC_PAUSE_TIME = 10 # 트래픽 캡처 대기 시간


if __name__ == "__main__":

    data_size = 500 # 수집할 채용공고 개수
    category_codes = [ # IT개발/인터넷 코드
        'AI_%EB%8D%B0%EC%9D%B4%ED%84%B0', # AI_데이터 
        'IT%EA%B0%9C%EB%B0%9C_%EB%8D%B0%EC%9D%B4%ED%84%B0', # IT개발_데이터
    ]
    headers = {
        "User-Agent" : "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"
    }


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
            recruits_list.append({
                'id': item['recruitmentUid'],
                'name': item['companyName'],
                'start_time': item['recruitmentStartDate'],
                'end_time': item['recruitmentDeadline'],
                'detail_type': 'img',
                'detail': None,
                'applyUrl': item['recruitmentAnnouncementLink']
            })


    # 채용공고 별 상세정보
    for item in recruits_list:
        url = f"https://zighang.com/recruitment/{item['id']}"
        res = requests.get(url)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        detail_res = soup.select_one('#root > main > div:nth-child(11) > iframe')
        detail_html = BeautifulSoup(detail_res.get('srcdoc'), 'html.parser')
        

        item['detail'] = detail_html.find('img').get('src')

        time.sleep(PAUSE_TIME)