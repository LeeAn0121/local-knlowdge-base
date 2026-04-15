# Local RAG 설치 가이드 (macOS)

본 가이드는 macOS 환경에서 Local RAG 프로젝트를 설치하고 실행하는 방법을 설명합니다.

## 1. 사전 준비 사항
Homebrew가 설치되어 있어야 합니다.

```zsh
# Python 및 Node.js 설치
brew install python@3.11 node

# Ollama 설치 (애플리케이션 다운로드 또는 brew)
brew install --cask ollama
```

## 2. 프로젝트 설정
```zsh
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
```zsh
cp .env.example .env
```

## 4. 실행 방법
```zsh
python3 -m cli.main serve
```
