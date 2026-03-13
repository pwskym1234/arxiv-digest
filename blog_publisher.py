"""블로그 포스트를 생성하는 모듈

Jekyll 형식의 마크다운 파일을 _posts/ 디렉토리에 생성합니다.
GitHub Actions에서 실행 시 자동으로 커밋 & 푸시됩니다.
"""

from datetime import datetime
from pathlib import Path

from config import RESEARCH_FIELDS
from summarizer import PaperSummary


# 프로젝트 루트 (_posts가 있는 곳)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
POSTS_DIR = PROJECT_ROOT / "_posts"


def _generate_post_content(
    summaries: list[PaperSummary],
    target_date: datetime,
) -> str:
    """하루치 요약을 하나의 Jekyll 마크다운 포스트로 생성"""

    date_str = target_date.strftime("%Y-%m-%d")
    day_kr = ["월", "화", "수", "목", "금", "토", "일"][target_date.weekday()]

    # 분야별로 그룹핑
    by_field: dict[str, list[PaperSummary]] = {}
    for s in summaries:
        field = s.paper.field
        by_field.setdefault(field, []).append(s)

    # Jekyll Front Matter
    lines = [
        "---",
        f'layout: post',
        f'title: "📚 {date_str} ({day_kr}) 논문 다이제스트"',
        f"date: {date_str}",
        f"categories: [digest]",
        f"tags: [{', '.join(by_field.keys())}]",
        "---",
        "",
        f"# 📚 {date_str} ({day_kr}) 논문 다이제스트",
        "",
        f"> 오늘의 AI 선별 논문 **{len(summaries)}편**을 한국어로 요약했습니다.",
        "",
    ]

    # 목차
    lines.append("## 📑 목차")
    lines.append("")
    for field_name, field_summaries in by_field.items():
        emoji = RESEARCH_FIELDS.get(field_name, {}).get("emoji", "📄")
        lines.append(f"**{emoji} {field_name}**")
        for s in field_summaries:
            # 앵커 링크 생성
            anchor = s.paper.arxiv_id.replace(".", "").replace("/", "")
            lines.append(f"- [{s.one_line}](#{anchor})")
        lines.append("")

    lines.append("---")
    lines.append("")

    # 각 논문 요약
    for field_name, field_summaries in by_field.items():
        emoji = RESEARCH_FIELDS.get(field_name, {}).get("emoji", "📄")
        lines.append(f"## {emoji} {field_name}")
        lines.append("")

        for s in field_summaries:
            anchor = s.paper.arxiv_id.replace(".", "").replace("/", "")
            lines.append(f'<a name="{anchor}"></a>')
            lines.append(f"### {s.paper.title}")
            lines.append("")
            lines.append(f"**저자**: {', '.join(s.paper.authors[:5])}")
            if len(s.paper.authors) > 5:
                lines.append(f" 외 {len(s.paper.authors) - 5}명")
            lines.append("")
            lines.append(f"**arxiv**: [{s.paper.arxiv_id}]({s.paper.pdf_url}) | "
                        f"[HTML]({s.paper.html_url})")
            lines.append("")
            lines.append(s.summary)
            lines.append("")
            lines.append("---")
            lines.append("")

    # 푸터
    lines.append(f"*이 포스트는 arxiv에서 자동으로 크롤링한 논문을 AI가 선별하고 요약한 것입니다.*")
    lines.append(f"*요약에 오류가 있을 수 있으니, 정확한 내용은 원문을 참고해주세요.*")

    return "\n".join(lines)


def publish_post(
    summaries: list[PaperSummary],
    target_date: datetime | None = None,
) -> Path | None:
    """
    Jekyll 마크다운 포스트 파일을 생성한다.

    Returns:
        생성된 파일 경로 또는 None
    """
    if not summaries:
        print("⚠️  발행할 논문 요약이 없습니다.")
        return None

    if target_date is None:
        target_date = datetime.now()

    date_str = target_date.strftime("%Y-%m-%d")

    # 포스트 디렉토리 확인
    POSTS_DIR.mkdir(parents=True, exist_ok=True)

    # 파일명 (Jekyll 형식: YYYY-MM-DD-title.md)
    filename = f"{date_str}-arxiv-digest.md"
    filepath = POSTS_DIR / filename

    # 포스트 내용 생성
    content = _generate_post_content(summaries, target_date)

    # 파일 쓰기
    filepath.write_text(content, encoding="utf-8")

    print(f"✅ 블로그 포스트 생성: {filepath}")
    print(f"   ({len(content):,}자, 논문 {len(summaries)}편)")

    return filepath
