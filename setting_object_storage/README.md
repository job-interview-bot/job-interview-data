## 윈도우 + Docker 기반 MinIO 구축

### **📌 동작 방식**

**네트워크 흐름 :**

`로컬의 외부 IP` → `로컬의 내부 IP` → `WSL2 어댑터의 Gateway IP`

각 통신들이 모두 NAT 모드로 구성되어있으므로, 각 과정에서 모두 Port forwarding(연결)이 필요

```
[로컬의 공인 IP] → (포트포워딩) → [로컬의 장치 별 내부 IP] → (포트포워딩) → [WSL2 내부 IP]
```

⚡ 주의

`로컬의 외부 IP` → `로컬의 내부 IP` 포트포워딩 시, 윈도우에 방화벽이 있으므로 방화벽 허용 세팅 필요

### 환경 구축 방법

1. **로컬 외부 IP → 로컬 내부 IP 방화벽 허용**
    
    MinIO에서 사용하는 포트에 대해 호스트(로컬 컴퓨터)의 인바운드 방화벽을 열어줍니다. 
    
    1. 제어판 → 시스템 및 보안 → Windows Defender 방화벽 → 고급 설정
    2. 인바운드 규칙 → `새 규칙` 생성
    3. 사용자 지정 → `프로그램` 에서 `모든 프로그램` → `프로토콜 및 포트`에서 “프로토콜 종류” : `TCP`, “로컬 포트” : `특정포트`(MinIO에서 사용할 포트-`9000`, `9001`) 
    4. (선택) 특정 ip 들만 열고 싶을 경우, 다음과 같이 설정:
        - `범위` 에서 “이 규칙이 적용되는 원격 IP 주소”: `다음 IP 주소`
        - 연결하고 싶은 ip들만 추가합니다.
    
    ※ 위의 과정이 번거롭다면 `powershell`에 다음 명령어를 사용해도 됩니다. (대응되는 값을 넣어주세요)
    
    ```powershell
    # powershell
    netsh advfirewall firewall add rule name="MinIO2" dir=in action=allow protocol=TCP localport=9000,9001 remoteip=59.12.196.198,**211.114.197.134,**61.82.47.18
    ```
    
2. **로컬 외부 IP → 로컬 내부 IP 연결**
    
    호스트와 공유기의 포트를 연결해야 합니다. 
    
    공유기 관리 사이트에 접속해서 MinIO에서 사용하는 포트에 대해 포트포워딩을 진행해주세요. 
    
    검색창에 “{공유기 통신사} 포트포워딩”이라고 검색하면 나올거에요
    
3. **로컬 내부 IP → Docker 내부 연결 + docker 실행**
    - `stand-alone` 또는 `distributed` 폴더에 진입
    - **첫 실행 또는 로컬 컴퓨터 재부팅 시**(껐다가 킬 경우), Docker 내부의 ip가 변합니다. 이 경우 `window_run.sh`파일을 실행시켜주세요.
        
        (로컬과 Docker의 연결이 자동으로 되도록 sh파일을 작성했습니다.)
        
        ```bash
        # /stand-alone
        # /distributed
        sh window_run.sh
        ```
        
    - 로컬 컴퓨터를 계속 켜놓은 상태에서 재실행하는 경우, `docker-compose.yaml`파일을 실행시켜주세요
    
    ※ 02.18 현재 distributed 모드는 작성 미완입니다. stand-alone 모드로만 환경구축해주세요. 
    

## 구축 과정(참고용)

구축 과정이 어떻게 되는지를 설명하는 부분입니다.

### 👽 환경 구축한 프로세스

```
[로컬의 공인 IP] → (포트포워딩) → [로컬의 장치 별 내부 IP] → (포트포워딩) → [WSL2 내부 IP]
```

1. 사용할 포트 : `9000`, `9001`
2. 호스트(컴퓨터) 방화벽 오픈
    1. MongoDB 구축 시 적어준 ip에 한해서 인바운드 방화벽 열었습니다.
3. 호스트(컴퓨터)와 공유기 포트포워딩
4. 호스트(컴퓨터)와 WSL2(Docker의 기반 가상환경) 포트포워딩
    1. WSL2의 사설 ip가 DHCP 프로토콜로 진행됨(자동할당). 따라서 호스트 종료 시 ip가 변경됨. 
        
        → 스크립트 작성으로 자동화 
        
5. MinIO 실행용 docker-compose.yaml 파일 작성
6. docker 실행

### 환경 구축 시 사용해야하는 기본 명령어 정리

1. 호스트 방화벽 오픈
    
    ```powershell
    # powershell
    netsh advfirewall firewall add rule name="MinIO2" dir=in action=allow protocol=TCP localport=9000,9001 remoteip=59.12.196.198,**211.114.197.134,**61.82.47.18
    ```
    
    - 📢 설명
        - `dir=in` → 인바운드 트래픽 설정
        - `action=allow` 인바운드 요청 허용 (action=block → 인바운드 요청 차단)
        - `remoteip=192.168.1.100` → 특정 원격 ip만 허용
            - 미지정 시 모든 네트워크 접근 허용
        - `protocol=TCP` → TCP 프로토콜 이용
        - `localport=9000` → 9000 포트로만 접근 가능
            - 미지정 시 모든 포트로의 접근이 허용됨
        - `remoteport=5000` : 여기엔 없지만 이 옵션까지 추가할 경우,
            - 클라이언트가 보낸 source Port가 `5000`일 경우에만 허용
2. 호스트, 공유기 포트포워딩
    
    → 이건 인터넷 검색하시면 나와요.. 각자 공유기 설정 페이지 들어가서 세팅해야됨
    
3. 호스트와 WSL2(Gateway ip) 포트포워딩
    - `9001`, `9000` 포트 모두 작업 필요
    
    ```powershell
    # powershell
    netsh interface portproxy add v4tov4 listenaddress=0.0.0.0 listenport=9001 connectaddress=172.24.190.147 connectport=9001
    ```
    
    - 📢 설명
        - `netsh interface portproxy add`
            - `netsh` : Windows에서 네트워크 설정을 변경하는 명령어
            - `interface portproxy add` : 포트 프록시(Port Proxy)를 추가하는 기능
                
                → Windows가 특정 포트로 들어오는 요청을 다른 IP와 포트로 전달하도록 설정.
                
        - `v4tov4`
            - IPv4 → IPv4로 포트포워딩
        - `listenaddress=0.0.0.0`
            - Windows 호스트에서 모든 네트워크 인터페이스(모든 IP주소)에서 요청을 수신하겠다.
            - 즉, Windows의 어떤 IP로 접근해도 포트 `9001`이 열린 상태가 됨
        - `listenport=9001`
            - Windows 호스트로 접근한 IP에서 특정 포트
        - `connectaddress=172.24.190.147`
            - Windows가 받은 요청을 WSL2 내부의 특정 IP로 포워딩하도록 지정
            - 172.24.190.147은 WSL2에서 사용하는 가상 네트워크 어댑터의 Gateway IP 주소(vEthernet (WSL)  Gateway IP 주소)
        - `connectport=9001`
            - WSL2 내부에서 요청을 전달할 포트 지정
        
        결론 : Windows에서 받은 `9001` 번 포트 요청을 WSL2 내부의 172.24.190.147:9001으로 전달
        
    - WSL2 Gateway 알아내는 법
        
        일단 윈도우 위에 Docker가 깔려있다면 WSL2도 같이 깔았을 거임
        
        - powershell에  `wsl hostname -I` 명령어 입력했을 때 나오는 ip가 WSL2 Gateway ip임
        
        ```powershell
        # powershell
        wsl hostname -I
        
        # 결과
        172.24.190.147
        ```