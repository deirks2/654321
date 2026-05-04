# 🤖 Discord AI 봇

Claude AI를 연동한 Discord 봇이에요.  
대화 맥락 유지, 채널 제한, 관리자 권한 명령어 지원.

---

## 📁 파일 구조

```
discord-ai-bot/
├── main.py          # 봇 메인 코드
├── requirements.txt # Python 패키지
├── Procfile         # Railway 실행 설정
├── .env.example     # 환경 변수 예시
└── README.md
```

---

## 🔑 준비물

### 1. Discord 봇 토큰
1. https://discord.com/developers/applications 접속
2. **New Application** → 이름 입력
3. 왼쪽 **Bot** 메뉴 → **Add Bot**
4. **Token** 복사 (= `DISCORD_TOKEN`)
5. **Privileged Gateway Intents** 아래 **Message Content Intent** 활성화 ✅
6. 왼쪽 **OAuth2 → URL Generator** →  
   Scopes: `bot` 체크  
   Bot Permissions: `Send Messages`, `Read Message History`, `View Channels` 체크  
   생성된 URL로 서버 초대

### 2. Anthropic API 키
1. https://console.anthropic.com 접속
2. **API Keys** → **Create Key** → 복사 (= `ANTHROPIC_API_KEY`)

---

## 🚀 Railway 배포

### 1. GitHub에 올리기
```bash
git init
git add .
git commit -m "init"
git remote add origin https://github.com/너의아이디/discord-ai-bot.git
git push -u origin main
```

### 2. Railway 프로젝트 생성
1. https://railway.app 로그인 (GitHub 연동)
2. **New Project** → **Deploy from GitHub repo**
3. 방금 올린 레포 선택

### 3. 환경 변수 설정
Railway 프로젝트 → **Variables** 탭 → 아래 값 추가:

| 변수명 | 값 |
|---|---|
| `DISCORD_TOKEN` | 디스코드 봇 토큰 |
| `ANTHROPIC_API_KEY` | Anthropic API 키 |
| `BOT_NAME` | 봇 이름 (예: 지피) |
| `MAX_HISTORY` | 대화 기록 수 (기본 30) |

### 4. Worker 서비스 확인
- Railway가 `Procfile`을 읽어서 자동으로 `worker` 타입으로 실행해요
- **Deploy** 탭에서 로그 확인: `✅ 지피 로그인 완료` 뜨면 성공!

---

## 💬 사용법

### 대화하기
```
지피야 파이썬으로 버블 정렬 짜줘
지피아 어제 배운 내용 요약해줘
@지피 이 코드 리뷰해줘
```

### 명령어
| 명령어 | 설명 | 권한 |
|---|---|---|
| `!도움말` | 사용 가이드 | 모두 |
| `!초기화` | 현재 채널 대화 기록 삭제 | 모두 |
| `!채널등록 [#채널]` | 봇 허용 채널 추가 | 관리자 |
| `!채널해제 [#채널]` | 봇 허용 채널 제거 | 관리자 |
| `!채널목록` | 허용 채널 목록 확인 | 관리자 |
| `!기록확인` | 대화 기록 개수 확인 | 관리자 |

> 채널 등록 없이 사용하면 **모든 채널**에서 동작해요.  
> `!채널등록`으로 특정 채널만 허용하면 그 채널에서만 반응해요.

---

## ⚙️ 커스터마이징

### 봇 이름 변경
Railway Variables에서 `BOT_NAME=원하는이름` 으로 변경

### 봇 성격 설정
`SYSTEM_PROMPT` 변수로 AI 역할/말투 커스터마이징:
```
SYSTEM_PROMPT=너는 코딩 전문 AI 어시스턴트야. 항상 예시 코드를 포함해서 설명해.
```

### 다른 AI API로 교체하고 싶다면
`main.py`의 `ask_ai` 함수에서 `ai.messages.create(...)` 부분을 교체하면 돼요.
