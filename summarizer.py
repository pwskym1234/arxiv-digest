"""Claude API로 논문을 선별하고 한국어로 요약하는 모듈

2단계 프로세스:
  1단계: 초록만 보고 분야당 1~2편 선별 (비용 절약)
  2단계: 선별된 논문의 전문을 읽고 상세 한국어 요약
"""

import anthropic
from dataclasses import dataclass

from config import ANTHROPIC_API_KEY, CLAUDE_MODEL, MAX_SUMMARY_TOKENS, RESEARCH_FIELDS
from arxiv_crawler import ArxivPaper
from paper_reader import fetch_paper_text


@dataclass
class PaperSummary:
    paper: ArxivPaper
    summary: str          # 한국어 요약
    one_line: str         # 한 줄 요약 (블로그 목차용)


# ── 1단계: 논문 선별 프롬프트 ──
SELECTION_PROMPT = """너는 최신 학술 논문을 선별하는 전문 큐레이터야.

아래는 "{field}" 분야에서 최근 발표된 논문들의 제목과 초록이야.
이 중에서 가장 흥미롭고 임팩트가 큰 논문 {n}편을 골라줘.

선별 기준:
- 새로운 방법론이나 큰 성능 향상을 보인 논문
- 실용적 응용 가능성이 높은 논문
- 해당 분야의 중요한 문제를 다루는 논문
- 단순 서베이/리뷰보다는 새로운 기여가 있는 논문 우선

반드시 아래 형식으로만 답해줘 (다른 텍스트 없이):
SELECTED: arxiv_id_1
SELECTED: arxiv_id_2"""


# ── 2단계: 상세 요약 프롬프트 ──
SUMMARY_PROMPT = """너는 최신 학술 논문을 고등학생도 이해할 수 있게 설명하는 전문 과학 커뮤니케이터야.

아래 논문을 읽고 한국어로 요약해줘. 다음 규칙을 반드시 따라:

1. **구조**: 아래 형식으로 작성해:
   - 📌 한 줄 요약 (이 논문이 뭘 했는지 한 문장으로)
   - 🔍 연구 배경 (왜 이 연구가 필요한지, 기존에 어떤 문제가 있었는지)
   - 💡 핵심 방법 (어떤 방법/기술을 사용했는지)
   - 📊 주요 결과 (수치, 벤치마크 등 구체적 성과)
   - 🌍 의미와 전망 (이 연구가 왜 중요하고 앞으로 어떤 영향을 줄 수 있는지)

2. **난이도 조절**:
   - 전문 용어가 나오면 괄호 안에 쉬운 설명을 추가해. 예: "Transformer(문장의 각 단어가 다른 단어들과 얼마나 관련 있는지 계산하는 AI 구조)"
   - 추상적인 개념은 일상적인 비유로 설명해. 예: "gradient descent는 산에서 가장 낮은 골짜기를 찾아 내려가는 것과 비슷합니다"
   - 수학 공식이 핵심이면, 공식의 의미를 말로 풀어서 설명해

3. **분량**: 각 섹션당 3~6문장. 전체 800~1500자 정도.

4. **고유명사**: 모델명, 데이터셋명, 수치 등은 원문 그대로 유지해.

아래가 논문 전문이야:

제목: {title}
저자: {authors}
분야: {field}

{paper_text}"""


def _create_client() -> anthropic.Anthropic:
    return anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


def select_papers(
    papers_by_field: dict[str, list[ArxivPaper]],
) -> list[ArxivPaper]:
    """
    1단계: 각 분야에서 초록 기반으로 상위 논문을 선별한다.

    Returns:
        선별된 ArxivPaper 리스트
    """
    client = _create_client()
    selected: list[ArxivPaper] = []

    for field_name, papers in papers_by_field.items():
        if not papers:
            print(f"  ⏭️  [{field_name}] 논문 없음, 건너뜀")
            continue

        n = RESEARCH_FIELDS[field_name]["papers_per_day"]
        print(f"🎯 [{field_name}] {len(papers)}편 중 {n}편 선별 중...")

        # 초록 목록 구성
        abstracts_text = ""
        for i, p in enumerate(papers[:15], 1):  # 최대 15편만 선별 대상
            abstracts_text += f"\n---\nID: {p.arxiv_id}\n제목: {p.title}\n초록: {p.abstract[:500]}\n"

        prompt = SELECTION_PROMPT.format(field=field_name, n=n)

        try:
            response = client.messages.create(
                model=CLAUDE_MODEL,
                max_tokens=500,
                messages=[{"role": "user", "content": f"{prompt}\n\n{abstracts_text}"}],
            )
            result = response.content[0].text

            # 선택된 ID 파싱
            selected_ids = []
            for line in result.strip().split("\n"):
                if line.startswith("SELECTED:"):
                    sid = line.replace("SELECTED:", "").strip()
                    selected_ids.append(sid)

            # ID로 논문 매칭
            id_to_paper = {p.arxiv_id: p for p in papers}
            for sid in selected_ids[:n]:
                if sid in id_to_paper:
                    selected.append(id_to_paper[sid])
                    print(f"  ✅ 선정: {id_to_paper[sid].title[:60]}")

            # 선별 결과가 없으면 최신 논문으로 폴백
            if not any(p.field == field_name for p in selected) and papers:
                fallback = papers[0]
                selected.append(fallback)
                print(f"  ⚠️  선별 실패, 최신 논문으로 대체: {fallback.title[:60]}")

        except anthropic.APIError as e:
            print(f"  ❌ 선별 API 오류: {e}")
            if papers:
                selected.append(papers[0])

    print(f"\n📋 총 {len(selected)}편 선별 완료.\n")
    return selected


def summarize_paper(paper: ArxivPaper, paper_text: str) -> PaperSummary:
    """
    2단계: 논문 전문을 읽고 상세 한국어 요약을 생성한다.
    """
    client = _create_client()

    prompt = SUMMARY_PROMPT.format(
        title=paper.title,
        authors=", ".join(paper.authors[:5]),
        field=paper.field,
        paper_text=paper_text,
    )

    print(f"🤖 요약 중: {paper.title[:60]}...")

    try:
        response = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=MAX_SUMMARY_TOKENS,
            messages=[{"role": "user", "content": prompt}],
        )
        summary_text = response.content[0].text

        # 한 줄 요약 추출 (📌 뒤의 첫 줄)
        one_line = ""
        for line in summary_text.split("\n"):
            if "📌" in line or "한 줄 요약" in line:
                one_line = line.replace("📌", "").replace("**한 줄 요약**", "").replace("한 줄 요약", "").strip()
                # 마크다운 볼드 등 제거
                one_line = one_line.strip("*: -")
                break

        if not one_line:
            one_line = paper.title  # 폴백

        print(f"  ✅ 완료 ({len(summary_text)}자)")

        return PaperSummary(
            paper=paper,
            summary=summary_text,
            one_line=one_line,
        )

    except anthropic.APIError as e:
        print(f"  ❌ 요약 API 오류: {e}")
        return PaperSummary(
            paper=paper,
            summary=f"⚠️ 요약 생성 실패: {e}",
            one_line=paper.title,
        )


def process_papers(papers_by_field: dict[str, list[ArxivPaper]]) -> list[PaperSummary]:
    """
    전체 파이프라인: 선별 → 전문 읽기 → 요약

    Returns:
        PaperSummary 리스트
    """
    # 1단계: 선별
    selected = select_papers(papers_by_field)

    if not selected:
        print("⚠️  선별된 논문이 없습니다.")
        return []

    # 2단계: 전문 읽기 + 요약
    summaries: list[PaperSummary] = []
    for i, paper in enumerate(selected, 1):
        print(f"\n📄 [{i}/{len(selected)}] 처리 중...")

        # 논문 전문 가져오기
        paper_text = fetch_paper_text(paper)

        # 요약 생성
        summary = summarize_paper(paper, paper_text)
        summaries.append(summary)

    print(f"\n📝 총 {len(summaries)}편 요약 완료.\n")
    return summaries
