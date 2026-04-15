# Local RAG 설치 가이드 (Linux)

본 가이드는 Linux(Ubuntu/Debian 등) 환경에서 Local RAG 프로젝트를 설치하고 실행하는 방법을 설명합니다.

## 1. 사전 준비 사항
```bash
# 시스템 패키지 업데이트
sudo apt update

# Python 및 가상 환경 도구 설치
sudo apt install python3.11 python3.11-venv python3-pip

# Node.js 설치 (nvm 권장 또는 공식 저장소 사용)
curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
sudo apt install -y nodejs

# Ollama 설치
curl -fsSL https://ollama.com/install.sh | sh
```

## 2. 프로젝트 설정
```bash
git clone <your-repository-url>
cd local-rag

# 가상 환경 설정
python3 -m venv .venv
source .venv/bin/activate

# 패키지 설치
pip install -e .

# Web UI 의존성 설치
cd web
npm install
cd ..
```

## 3. 환경 설정
```bash
cp .env.example .env
```

## 4. 실행 방법
```bash
python3 -m cli.main serve
```
