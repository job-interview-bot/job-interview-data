wget https://mirror.cs.uchicago.edu/google-chrome/pool/main/g/google-chrome-stable/google-chrome-stable_114.0.5735.90-1_amd64.deb
sudo apt-get update
sudo apt-get install -y fonts-liberation libasound2t64 libnspr4 libnss3 libu2f-udev xdg-utils
sudo apt --fix-broken install
sudo dpkg --install google-chrome-stable_114.0.5735.90-1_amd64.deb