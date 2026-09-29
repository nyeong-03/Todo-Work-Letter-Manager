# 기회 챙김 (Gihoe Chaeggim)_ 가제

대학생이 뉴스레터·공지사항을 주제별로 정리하고, 목표·일정과 연결해서 관리하는
**개인용(1인 사용)** 웹앱입니다. 샘플 데이터만으로도 전체 기능을 바로 체험할 수 있고,
원하면 Gmail 계정 1개를 연결해 실제 뉴스레터를 자동으로 가져올 수 있습니다.

## 기능

- **뉴스레터 정리**: 자격증 / 공모전·대외활동 / 학업·학교생활 / 취업·진로 / 기타로 자동 분류,
  검색·카테고리 필터, 요약·분류 결과 직접 수정 가능
- **Gmail 연동 (선택)**: OAuth 2.0 읽기 전용 권한으로 최근 N일 메일 중 뉴스레터로 보이는 것만
  가져와 분류·요약. **메일 원문은 저장하지 않고 요약/분류 결과만 저장**
- **목표 관리**: 목표 추가/수정/삭제, 뉴스레터·일정과 연결
- **일정 관리**: 추가/수정/완료 토글/삭제, 뉴스레터의 마감일을 일정으로 옮기기(항상 사용자 확인 후 저장)
- **대시보드**: 오늘 확인할 항목, 다가오는 마감, 최근 뉴스레터, 목표별 진행 상황

## 기술 스택

- Python 3.10+, Flask, SQLite(표준 라이브러리 `sqlite3`)
- Gmail 연동: `google-auth`, `google-auth-oauthlib`, `google-api-python-client`
- 프런트엔드: Jinja2 템플릿 + 일반 CSS (별도 프레임워크 없음)

## 실행 방법

```bash
cd gihoe-chaeggim
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env             # 값은 아래 "Gmail 연동 설정" 참고 (연동 안 하면 그대로 둬도 됨)

python app.py
```

브라우저에서 `http://localhost:5000` 접속하면 샘플 데이터가 채워진 상태로 바로 시작됩니다.
Gmail을 연결하지 않아도 뉴스레터 직접 추가, 목표, 일정 기능은 전부 사용할 수 있습니다.

### 테스트 실행 (선택)

```bash
pip install pytest
pytest
```

## Gmail 연동 설정 (선택 기능)

Gmail 연동을 쓰지 않으실 거면 이 섹션은 건너뛰어도 돼요. 앱의 나머지 기능은 그대로 동작합니다.

### 1. Google Cloud Console에서 준비하기 (직접 하셔야 하는 부분)

1. https://console.cloud.google.com 에서 새 프로젝트를 만들거나 기존 프로젝트를 선택합니다.
2. **APIs & Services → Library**에서 **Gmail API**를 검색해 활성화(Enable)합니다.
3. **APIs & Services → OAuth consent screen**을 설정합니다.
   - User Type은 **External**을 선택합니다(개인 Google 계정 기준).
   - 앱 이름, 이메일 등 필수 항목을 채웁니다.
   - Scopes 단계에서 `https://www.googleapis.com/auth/gmail.readonly`를 추가합니다.
   - **Test users**에 본인의 Gmail 주소를 추가합니다. (앱이 "게시" 상태가 아니면 테스트 사용자만 로그인할 수 있어요.)
4. **APIs & Services → Credentials → Create Credentials → OAuth client ID**를 선택합니다.
   - Application type: **Web application**
   - **Authorized redirect URIs**에 정확히 아래 주소를 추가합니다.
     ```
     http://localhost:5000/gmail/callback
     ```
   - 생성 후 나오는 **Client ID**와 **Client secret**을 복사해 둡니다.

### 2. `.env` 파일 채우기 (코드에서 구현한 부분과 연결됨)

`.env.example`을 복사한 `.env` 파일에 아래 값을 채웁니다.

```
FLASK_SECRET_KEY=아무 무작위 문자열
GOOGLE_CLIENT_ID=위에서 복사한 Client ID
GOOGLE_CLIENT_SECRET=위에서 복사한 Client secret
GOOGLE_REDIRECT_URI=http://localhost:5000/gmail/callback
```

`.env`는 `.gitignore`에 이미 포함되어 있어 Git에 올라가지 않습니다.

### 3. 연결하고 사용하기

1. `python app.py`로 앱을 실행하고 **뉴스레터** 화면으로 이동합니다.
2. **Gmail 연결하기** 버튼을 누르면 Google 로그인/권한 승인 화면으로 이동합니다.
   (여기서부터는 코드가 아니라 Google 화면이며, 본인이 직접 승인해야 합니다.)
3. 승인하면 다시 앱으로 돌아오고, 연결된 이메일 주소가 표시됩니다.
4. 기간(3/7/30/90일)을 고르고 **지금 가져오기**를 누르면 그 기간 동안 온 메일 중
   `List-Unsubscribe` 헤더가 있는(=뉴스레터/알림 시스템이 보낸 것으로 보이는) 메일만
   골라 분류·요약해 저장합니다.
5. **연결 해제** 버튼으로 언제든 연결을 끊을 수 있고, 체크박스를 켜면 가져온 뉴스레터도 함께 삭제합니다.

### OAuth 토큰/데이터는 어디에, 어떻게 저장되나요

- Gmail의 refresh token은 로컬 SQLite 파일 `data/app.db`의 `gmail_account` 테이블에 저장됩니다.
- 이 앱은 **1인 로컬 사용**을 전제로 설계되어 있어서, 토큰이 암호화되어 있지 않습니다.
  `data/` 폴더는 `.gitignore`에 포함되어 있어 Git에는 올라가지 않지만,
  **이 폴더(특히 `data/app.db`)를 다른 사람과 공유하거나 공개 저장소에 커밋하지 마세요.**
  다른 사람과 공유되는 서버에 배포할 계획이라면 토큰 암호화 등 추가 보안 조치가 필요합니다.
- 메일 **원문(본문)은 어디에도 저장되지 않습니다.** 가져오는 즉시 분류·요약만 만들고 원문은 버립니다.
  원문을 다시 보고 싶으면 뉴스레터 카드의 "Gmail에서 원문 보기" 링크로 Gmail을 직접 엽니다.
- 연결 상태, 가져오기 성공/실패, 연결 해제는 모두 뉴스레터 화면 상단에 초록/빨강 알림 메시지로 표시됩니다.

## 실제 AI로 교체하기

지금은 `src/classifier.py`의 규칙 기반(키워드 매칭) 로직이 분류·요약·마감일 추출을 담당합니다.
API 키 없이도 앱 전체를 체험할 수 있도록 하기 위한 기본값입니다.

실제 LLM으로 바꾸려면 `classify_and_summarize(subject, body, received_on)` 함수 내부만
API 호출로 교체하면 됩니다. 이 함수를 호출하는 나머지 코드(수동 추가, Gmail 가져오기)는
그대로 두면 됩니다. API 키는 `.env`에 `ANTHROPIC_API_KEY` 같은 이름으로 추가하고
`config.py`에서 읽어오는 식으로 연결하면 됩니다. 프런트엔드(템플릿/JS)에는 API 키를
절대 노출하지 마세요 — 항상 서버(Flask 라우트)에서만 호출해야 합니다.

## 프로젝트 구조

```
gihoe-chaeggim/
├── app.py                 # Flask 앱 생성, 블루프린트 등록, DB 초기화
├── config.py               # .env 값 로딩
├── requirements.txt
├── .env.example
├── src/
│   ├── db.py                # SQLite 스키마 및 연결
│   ├── sample_data.py       # 샘플 목표/뉴스레터/일정 시드 데이터
│   ├── classifier.py        # 규칙 기반 분류·요약·마감일 추출 (AI로 교체 가능)
│   ├── gmail_auth.py        # OAuth 흐름, 토큰 저장/삭제
│   ├── gmail_fetch.py       # 뉴스레터로 보이는 메일 조회 (읽기 전용)
│   └── routes/
│       ├── dashboard.py
│       ├── newsletters.py
│       ├── goals.py
│       ├── schedule.py
│       └── gmail.py
├── templates/                # Jinja2 화면
├── static/style.css
└── tests/test_app.py
```

## 아직 연결되지 않은 것 / 알아두실 점

- **Gmail 연동은 실제 Google 계정으로 아직 테스트되지 않았습니다.** 이 코드를 만든 환경은
  네트워크가 차단되어 있어 `google-auth`/`google-api-python-client` 설치와 실제 OAuth 승인,
  실제 Gmail API 호출을 직접 실행해 보지 못했습니다. 대신 아래는 확인했습니다.
  - 문법 오류 없음 (`py_compile`로 모든 파일 확인)
  - 패키지가 설치되어 있지 않거나 `.env`가 비어 있을 때 앱이 죽지 않고
    친절한 안내 메시지를 보여주는지 (`/gmail/connect`, `/gmail/sync`)
  - 나머지 화면(대시보드/뉴스레터/목표/일정)의 추가·수정·삭제·필터·완료 토글 버튼이
    실제로 동작하는지 (자동 테스트 5개로 확인, `tests/test_app.py`)
  - 처음 연결하고 "지금 가져오기"를 눌렀을 때 오류가 나면, 오류 메시지를 그대로 알려주시면
    같이 원인을 찾아 고칠게요.
- 뉴스레터 판별은 `List-Unsubscribe` 헤더 유무로 판단합니다. 이 헤더가 없는 일반 공지 메일(예: 학교
  메일 시스템에 따라)은 자동으로는 걸러지지 않을 수 있습니다 — 이런 경우 뉴스레터 화면에서 "직접 추가"로
  붙여넣으면 동일하게 분류·요약됩니다.
- AI 요약은 지금 규칙 기반이라 완벽한 문장 요약이 아니라 "본문 앞부분을 다듬은 것"에 가깝습니다.
  더 자연스러운 요약이 필요하면 위 "실제 AI로 교체하기" 섹션을 참고해 주세요.
- 실제 메일 계정 외의 Google Calendar 연동, 외부 공고 사이트 자동 수집은 이번 버전에 포함되지 않았습니다(요청하신 범위 밖).
