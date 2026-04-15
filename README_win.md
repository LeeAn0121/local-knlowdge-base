# Local RAG 설치 가이드 (Windows)

본 가이드는 Windows 환경에서 Local RAG 프로젝트를 설치하고 실행하는 방법을 설명합니다.

## 1. 사전 준비 사항
아래 도구들이 설치되어 있어야 합니다.
* **Python 3.11 이상**: [python.org](https://www.python.org/)에서 설치 (설치 시 "Add Python to PATH" 체크 권장)
* **Node.js (LTS)**: Web UI 실행을 위해 필요 [nodejs.org](https://nodejs.org/)
* **Git**: 저장소 클론을 위해 필요
* **Ollama**: 로컬 LLM 실행을 위해 필요 [ollama.com](https://ollama.com/)

## 2. 프로젝트 설정
먼저 저장소를 클론하고 해당 폴더로 이동합니다.

```powershell
git clone <your-repository-url>
cd local-rag
```

### 가상 환경 및 Python 패키지 설치
```powershell
# 가상 환경 생성
python -m venv .venv

# 가상 환경 활성화
.\.venv\Scripts\activate

# 패키지 설치 (Editable 모드)
pip install -e .
```

### Web UI 의존성 설치
```powershell
cd web
npm install
cd ..
```

## 3. 환경 설정
`.env.example` 파일을 복사하여 `.env` 파일을 만들고 필요한 설정을 수정합니다.
```powershell
copy .env.example .env
```

## 4. 실행 방법
Ollama가 실행 중인지 확인한 후, 아래 명령어를 통해 API 서버와 Web UI를 동시에 실행합니다.

```powershell
python -m cli.main serve
```

* **API 서버**: http://localhost:8000
* **Web UI**: http://localhost:3000
* **Swagger 문서**: http://localhost:8000/docs
