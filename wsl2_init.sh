#!/bin/bash

# Git 설정
git config --global commit.template ".commit_template"
git config --global core.editor "code --wait"

echo -e "\e[34m[✔] Git config 완료\e[0m"

# pre-commit 설정
pip3 install --user pre-commit  # WSL2에서는 pip 대신 pip3 사용이 권장됨
export PATH="$HOME/.local/bin:$PATH"  # pre-commit이 ~/.local/bin에 설치되므로 PATH 추가
pre-commit autoupdate
pre-commit install

echo -e "\e[34m[✔] pre-commit 설정 완료\e[0m"
