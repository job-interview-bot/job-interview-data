
# step 1: WSL2의 현재 IP를 가져오고, 포트포워딩을 설정 

# WSL2의 현재 IP 가져오기
WSL_IP=$(wsl hostname -I | awk '{print $1}')

echo "WSL2 IP: $WSL_IP"

# 기존 포트 포워딩 삭제 (오류 무시)
# winpty 명령어 : TTY(터미널)과 윈도우 환경이 호환되지 않는 프로그램을 실행할 수 있도록 도와주는 래퍼(wrapper)
powershell.exe -Command "netsh interface portproxy delete v4tov4 listenport=9000" 2>/dev/null
powershell.exe -Command "netsh interface portproxy delete v4tov4 listenport=9001" 2>/dev/null

# 새로운 포트 포워딩 추가
# winpty powershell.exe -Command "netsh interface portproxy add v4tov4 listenaddress=0.0.0.0 listenport=9000 connectaddress=$WSL_IP connectport=9000"
# winpty powershell.exe -Command "netsh interface portproxy add v4tov4 listenaddress=0.0.0.0 listenport=9001 connectaddress=$WSL_IP connectport=9001"
powershell.exe -Command "Start-Process powershell -ArgumentList 'netsh interface portproxy add v4tov4 listenaddress=0.0.0.0 listenport=9000 connectaddress=$WSL_IP connectport=9000' -Verb RunAs"
powershell.exe -Command "Start-Process powershell -ArgumentList 'netsh interface portproxy add v4tov4 listenaddress=0.0.0.0 listenport=9001 connectaddress=$WSL_IP connectport=9001' -Verb RunAs"


echo "Port forwarding updated for WSL2 IP: $WSL_IP"

# Docker Compose 실행
exec docker compose up -d


