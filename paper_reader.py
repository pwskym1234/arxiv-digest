"""논문 전문을 읽는 모듈

ar5iv.labs.arxiv.org의 HTML 버전을 사용해 논문 전문을 추출합니다.
PDF 파싱보다 훨씬 깔끔하고 안정적입니다.
"""

import urllib.request
import re
from html.parser import HTMLParser

from config import MAX_PAPER_TEXT_LENGTH
from arxiv_crawler import ArxivPaper


class _TextExtractor(HTMLParser):
    """간단한 HTML → 텍스트 변환기"""

    SKIP_TAGS = {"script", "style", "nav", "footer", "header", "button", "noscript"}

    def __init__(self):
        super().__init__()
        self._text_parts: list[str] = []
        self._skip_depth = 0
        self._current_tag = ""

    def handle_starttag(self, tag, attrs):
        self._current_tag = tag
        attrs_dict = dict(attrs)

        # 불필요한 태그 건너뛰기
        if tag in self.SKIP_TAGS:
            self._skip_depth += 1
            return

        # class로 불필요한 섹션 필터링 (참고문헌, 네비게이션 등)
        cls = attrs_dict.get("class", "")
        if any(skip in cls for skip in ["ltx_bibliography", "ltx_page_footer", "ltx_page_header", "ltx_navigation"]):
            self._skip_depth += 1
            return

        # 섹션/헤딩 구분을 위한 줄바꿈
        if tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            self._text_parts.append("\n\n## ")
        elif tag in ("p", "div", "section", "article"):
            self._text_parts.append("\n")

    def handle_endtag(self, tag):
        if tag in self.SKIP_TAGS or self._skip_depth > 0:
            if tag in self.SKIP_TAGS:
                self._skip_depth = max(0, self._skip_depth - 1)
            return

        if tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            self._text_parts.append("\n")

    def handle_data(self, data):
        if self._skip_depth > 0:
            return
        text = data.strip()
        if text:
            self._text_parts.append(text + " ")

    def get_text(self) -> str:
        raw = "".join(self._text_parts)
        # 연속 공백/줄바꿈 정리
        raw = re.sub(r"\n{3,}", "\n\n", raw)
        raw = re.sub(r" {2,}", " ", raw)
        return raw.strip()


def fetch_paper_text(paper: ArxivPaper) -> str:
    """
    논문의 전문 텍스트를 가져온다.

    1차: ar5iv HTML 버전 시도
    2차: 실패 시 초록(abstract)만 반환

    Returns:
        논문 텍스트 (최대 MAX_PAPER_TEXT_LENGTH 글자)
    """
    print(f"  📖 논문 읽는 중: {paper.title[:60]}...")

    # ar5iv HTML 버전 시도
    try:
        req = urllib.request.Request(
            paper.html_url,
            headers={"User-Agent": "arxiv-digest/1.0 (academic research summarizer)"},
        )
        with urllib.request.urlopen(req, timeout=30) as response:
            html_content = response.read().decode("utf-8", errors="replace")

        extractor = _TextExtractor()
        extractor.feed(html_content)
        text = extractor.get_text()

        if len(text) > 500:  # 충분한 텍스트가 추출됨
            # 너무 길면 잘라내기
            if len(text) > MAX_PAPER_TEXT_LENGTH:
                text = text[:MAX_PAPER_TEXT_LENGTH] + "\n\n[... 논문이 길어 이후 내용 생략 ...]"
            print(f"    ✅ 전문 추출 완료 ({len(text):,}자)")
            return text

    except Exception as e:
        print(f"    ⚠️  HTML 추출 실패: {e}")

    # 폴백: 초록만 사용
    print(f"    📋 초록만 사용합니다.")
    return f"""제목: {paper.title}

저자: {', '.join(paper.authors[:5])}

초록(Abstract):
{paper.abstract}

[전문을 가져오지 못해 초록만 사용합니다. 자세한 내용은 {paper.pdf_url} 에서 확인하세요.]"""
