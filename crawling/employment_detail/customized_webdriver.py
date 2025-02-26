import json
import os
import re
from seleniumwire.utils import decode

from seleniumwire import webdriver as wd_wire

# 웹 드라이버 설치 관련
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager

import requests
from bs4 import BeautifulSoup

from selenium.webdriver import ActionChains  # noqa
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

from selenium.common.exceptions import TimeoutException
from selenium.webdriver import ChromeOptions

from typing import Optional, Union, List, Dict, Callable
from selenium.webdriver.remote.webelement import WebElement
from seleniumwire.request import Request, Response



class DotDict(dict):
    """dot(.)으로 속성처럼 접근 가능한 dict"""
    def __getattr__(self, key):
        return self[key]

    def __setattr__(self, key, value):
        self[key] = value


class CustomizedDriver(wd_wire.Chrome):
    def __init__(self, *args, **kwargs):
        """WebDriver 설정 및 인스턴스 생성
        """
        # Selenium webdriver 설정
        driver_path = ChromeDriverManager().install()
        
        # 윈도우에서 실행 시 
        # correct_driver_path = os.path.join(os.path.dirname(driver_path), "chromedriver.exe") # 오류 출처 : https://private.tistory.com/178
        # super().__init__(*args, service=ChromeService(executable_path=correct_driver_path), **kwargs)

        # 맥에서 실행 시
        super().__init__(*args, service=ChromeService(executable_path=driver_path), **kwargs)

        # 네트워크 트래픽 캡처 범위 설정
        self.scopes = ['.*'] # 일단 모든 네트워크 트래픽을 캡처하도록 설정
        

    def find_element_one(self, locator = By.CSS_SELECTOR, value: Optional[str] = None, timeout: int = 10) -> Optional[Callable[..., WebElement]]:
        """html 요소 찾기 (단일)

        Args:
            locator (str): 사용할 locator 전략 설정
            timeout (int, optional): Defaults to 10.

        Returns:
            Optional[WebElement]: 
        """
        try:
            elem = WebDriverWait(self, timeout).until(
                EC.presence_of_element_located((locator, value))
            )
        except TimeoutException:
            return None
        
        return elem
        
    def find_element_all(self, locator = By.CSS_SELECTOR, value: Optional[str]=None, timeout: int = 10) -> List[WebElement]:
        """html 요소 찾기 (복수)

        Returns:
            List[WebElement]:
        """
        try:
            elem = WebDriverWait(self, timeout).until(
                EC.presence_of_all_elements_located((locator, value))
            )
        except TimeoutException:
            return []
        
        return elem
        
    
    def filter_network_log(self, **kwargs) -> Union[Request, DotDict]:
        """네트워크 트래픽 필터링 (단일)

        Args:
            pat: 찾으려는 request의 패턴. regex를 사용할 수 있음.
            timeout (int, optional): capture 대기 시간. Defaults to 60.
            reset (bool, optional): request 데이터 삭제 여부. Defaults to False.

        Returns:
            캡처한 request의 반환 데이터
        """

        # pat이 없을 경우 에러 발생
        if not kwargs.get('pat', False):
            raise TypeError("CustomizedDriver.capture_response() missing 1 required positional argument: 'pat'") 

        reset = kwargs.get('reset', False)
        timeout = kwargs.get('timeout', 10)

        try:
            req = self.wait_for_request(pat=kwargs['pat'], timeout=timeout)
        except TimeoutException:
            # 패턴 미발견 시 시간 초과
            req = DotDict({
                'response':DotDict({
                    'status_code': 408,
                    'data': None
                })
            })

        if reset:
            del self.requests

        return req

    def filter_network_log_all(self, **kwargs) -> Dict[str, Union[int, List[Request]]]:
        """네트워크 트래픽 필터링 (복수)

        Args:
            pat: 찾으려는 request의 패턴. regex를 사용할 수 있음.
            timeout (int, optional): capture 대기 시간. Defaults to 60.
            reset (bool, optional): request 데이터 삭제 여부. Defaults to False.

        Returns:
            캡처한 request의 반환 데이터
        """

        # pat이 없을 경우 에러 발생
        if not kwargs.get('pat', False):
            raise TypeError("CustomizedDriver.capture_response() missing 1 required positional argument: 'pat'") 

        reset = kwargs.get('reset', False)
        timeout = kwargs.get('timeout', 10)

        reqs = DotDict({
            'response':DotDict({
                'status_code': 200, 
                'data': []
                })
            })

        # reqs = DotDict({
        #     'status_code': 200,
        #     'data': []
        # })


        try:
            found_req = self.wait_for_request(pat=kwargs['pat'], timeout=timeout)
        except TimeoutException:
            # 패턴 시간 초과
            found_req = False

            reqs = DotDict({
                'response':DotDict({
                    'status_code': 408,
                    'data': None
                })
            })

        if found_req:
            for req in self.requests:
                # req.response is not None : response를 받은 경우에만(요청 성공 시에만) 고려
                if req.response and re.search(kwargs['pat'], req.url):
                    reqs.response.data.append(req)
                
        if reset:
            del self.requests

        return reqs
    

    def check_status_code(self, req):
        """네트워크 트래픽의 status code 확인
        """
        assert req.response.status_code == 200, 'No response captured. Please capture response first.'

        # if not self.request.status_code == 408:
            
        #     # 패턴 시간 초과
        #     response_dict = None
        #     # 에러 대신 로그 출력하도록 변경할 예정
        #     # print('No response captured. Please capture response first.')
        #     # driver.get_log('performance')
        return True

    def parse_request(self, req):
        """네트워크 트래픽 json 형태로 변환
        """
        assert req.response.status_code == 200, 'No response captured. Please capture response first.'

        # 408 에러 시 headers 값이 안나오므로,,, json 형태 변환 에러 처리 필요
            
        # json 형태로 변환  
        response_dict = json.loads(decode(req.response.body, req.response.headers.get('Content-Encoding', 'identity')).decode('utf-8')) 
            
            
        return response_dict


        
