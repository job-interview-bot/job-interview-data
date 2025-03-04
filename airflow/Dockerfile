FROM apache/airflow:2.10.5-python3.9

USER root

# 필수 패키지 및 종속성 설치
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    gnupg \
    ca-certificates \
    libappindicator3-1 \
    libasound2 >= 1.0.17 \
    libatk-bridge2.0-0 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libx11-xcb1 \
    libxss1 \
    libxtst6 \
    xdg-utils \
    libgbm1 \
    fonts-liberation \
    libu2f-udev \
    libvulkan1

# Google Chrome 114.0.5735.90
RUN wget https://mirror.cs.uchicago.edu/google-chrome/pool/main/g/google-chrome-stable/google-chrome-stable_114.0.5735.90-1_amd64.deb
RUN sudo apt-get install unzip
RUN sudo dpkg --install google-chrome-stable_114.0.5735.90-1_amd64.deb

# ChromeDriver 114.0.5735.90 설치 (다운로드 후 /usr/bin에 압축해제)
RUN wget https://chromedriver.storage.googleapis.com/114.0.5735.90/chromedriver_linux64.zip && \
    unzip chromedriver_linux64.zip -d /usr/bin/ && \
    chmod +x /usr/bin/chromedriver && \
    rm chromedriver_linux64.zip

# Chrome 실행 옵션 추가
CMD ["google-chrome-stable", "--no-sandbox", "--headless"]

# Airflow 설정
COPY requirements.txt /tmp/requirements.txt
USER airflow
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# 권한 및 환경 설정
USER root
RUN chmod 777 /usr/bin/chromedriver && \
    rm -rf /var/lib/apt/lists/*

USER airflow