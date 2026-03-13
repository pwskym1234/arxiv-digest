# 📚 arxiv Digest

매일 arxiv에서 최신 논문을 자동 크롤링 → AI 선별 → 한국어 요약 → GitHub Pages 블로그에 발행하는 자동화 시스템입니다.

## 🏗️ 동작 방식

```
매일 오전 10시 (KST)
  ↓
GitHub Actions 실행
  ↓
arxiv API → 5개 분야 최신 논문 수집
  ↓
Claude AI → 분야당 1~2편 선별 (초록 기반)
  ↓
ar5iv → 선별된 논문 전문 추출
  ↓
Claude AI → 고등학생도 이해할 수 있는 한국어 요약
  ↓
_posts/에 마크다운 파일 생성
  ↓
자동 git commit & push
  ↓
GitHub Pages 블로그 업데이트!
```

## 🚀 5분 안에 셋업하기

### Step 1: 이 레포지토리를 GitHub에 올리기

```bash
cd arxiv-digest
git init
git add .
git commit -m "🚀 initial commit"
git remote add origin https://github.com/YOUR_USERNAME/arxiv-digest.git
git branch -M main
git push -u origin main
```

### Step 2: GitHub Pages 활성화

1. GitHub 레포지토리 → **Settings** → **Pages**
2. Source: **Deploy from a branch**
3. Branch: **main** / **(root)**
4. **Save** 클릭

몇 분 후 `https://YOUR_USERNAME.github.io/arxiv-digest/` 에서 블로그 확인 가능!

### Step 3: Anthropic API 키 등록

1. [Anthropic Console](https://console.anthropic.com/) 에서 API 키 발급
2. GitHub 레포지토리 → **Settings** → **Secrets and variables** → **Actions**
3. **New repository secret** 클릭
4. Name: `ANTHROPIC_API_KEY`, Value: 발급받은 키 입력

### Step 4: 첫 실행 테스트

1. GitHub 레포지토리 → **Actions** 탭
2. 왼쪽에서 **Daily arxiv Digest** 클릭
3. **Run workflow** 버튼 클릭

이후로는 매일 한국시간 오전 10시에 자동 실행됩니다.

---

## ⚙️ 커스터마이징

### 관심 분야 수정

`scripts/config.py`의 `RESEARCH_FIELDS`를 수정하세요.

arxiv 카테고리 전체 목록: https://arxiv.org/category_taxonomy

```python
RESEARCH_FIELDS = {
    "나의 관심 분야": {
        "categories": ["cs.AI", "cs.LG"],  # arxiv 카테고리
        "keywords": ["keyword1", "keyword2"],  # 검색 키워드
        "papers_per_day": 2,  # 하루 선별 수
        "emoji": "🔬",
    },
}
```

### 실행 시간 변경

`.github/workflows/daily.yml`의 cron 표현식 수정:

```yaml
schedule:
  - cron: '0 1 * * *'  # UTC 01:00 = KST 10:00
```

UTC 기준이므로 원하는 한국시간에서 9시간을 빼세요.

### 요약 스타일 변경

`scripts/summarizer.py`의 `SUMMARY_PROMPT`를 수정하세요.

### AI 모델 변경

`scripts/config.py`의 `CLAUDE_MODEL`을 변경하세요:
- `claude-haiku-4-5-20251001`: 저렴하지만 품질 ↓
- `claude-sonnet-4-20250514`: 균형 (추천)
- `claude-opus-4-20250115`: 최고 품질, 비용 ↑

---

## 💰 예상 비용

| 항목 | 비용 |
|------|------|
| GitHub Pages 호스팅 | **무료** |
| GitHub Actions (월 2000분) | **무료** |
| arxiv API | **무료** |
| Claude Sonnet API (~7편/일) | **~$0.5/일 ($15/월)** |

---

## 📁 프로젝트 구조

```
arxiv-digest/
├── .github/workflows/
│   └── daily.yml           # GitHub Actions 자동화
├── scripts/
│   ├── config.py            # 설정 (분야, 모델, 키워드)
│   ├── arxiv_crawler.py     # arxiv 논문 크롤링
│   ├── paper_reader.py      # 논문 전문 추출
│   ├── summarizer.py        # AI 선별 + 한국어 요약
│   ├── blog_publisher.py    # 마크다운 포스트 생성
│   └── main.py              # 오케스트레이터
├── _posts/                  # 블로그 포스트 (자동 생성)
├── _config.yml              # Jekyll 블로그 설정
├── index.md                 # 블로그 홈페이지
└── requirements.txt
```

## 🔧 로컬에서 테스트

```bash
# 의존성 설치
pip install -r requirements.txt

# API 키 설정
export ANTHROPIC_API_KEY="sk-ant-xxxxx"

# 실행
python3 scripts/main.py

# 블로그 로컬 미리보기 (Ruby/Jekyll 필요)
bundle exec jekyll serve
```
