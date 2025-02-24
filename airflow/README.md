# Airflow 환경 구축 관련

## pre-required
- .env에 username, pwd 등 세팅 필요합니다 (노션 자료 공유란 참고)
- .env 위치는 **`/job-interview-data/.env`** 를 기본으로 하며, 바꾸실 경우 그에 따른 경로 수정이 필요합니다.
- airflow는 ubuntu를 기반으로 하여, windows 기반으로는 동작하지 않습니다. 따라서 **wsl2 (v22.04) 설치가 필요**합니다.
- **`Docker desktop > Settings > Resources > WSL Integration`** 확인 후 Enable integration with my default WSL distro가 체크 되었는지, Enable integration with additional distros: (Ubuntu) 가 활성화되었는지 확인합니다.
    - 모두 활성화 이후 Refetch distros, Apply & Restart 하시면 됩니다.


- **포트 포워딩**이 선행되어야 합니다. (노션 페이지 참고)
- 사용되는 포트는 다음과 같습니다. (02.21 커밋 기준)
    - airflow : 8080
    - nginx : 80
    - mysql : 3306

- nginx.conf 파일 생성이 필요합니다. (특정 IP 리스트만 허용하기 위함)
```bash
events {
    worker_connections 1024;
}

http {
    server {
        listen 80;
        server_name _;

        location / {
            proxy_pass http://airflow-webserver:8080;
            allow [ip주소];  # 허용할 IP 입력 (본인 ip)
            deny all;  # 나머지 IP 차단
        }
    }
}

```



## Settings
- 초기 설치 및 테스트 실행
```bash
pip install apache-airflow
export AIRFLOW_HOME=`pwd`
airflow db init # db 초기화 (혹은 airflow db migrate)
airflow webserver --port 8080 # http://localhost:8080 으로 접속 가능

## 스케줄러 실행
export AIRFLOW_HOME=`pwd`
airflow scheduler
```

- docker-compose 띄우기
```bash
# cd airflow/
sh run.sh
```


## TroubleShooting
- MySQL Client가 설치되지 않을 경우 : WSL 업데이트 필요
```bash
sudo apt update
sudo apt install python3-dev default-libmysqlclient-dev build-essential pkg-config
pip install mysqlclient
```
