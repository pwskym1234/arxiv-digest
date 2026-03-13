"""arxiv에서 최신 논문을 가져오는 모듈

arxiv API를 사용해 각 관심 분야의 최신 논문을 크롤링합니다.
무료이며 인증이 필요 없습니다.
"""

import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from dataclasses import dataclass

from config import RESEARCH_FIELDS


@dataclass
class ArxivPaper:
    arxiv_id: str
    title: str
    authors: list[str]
    abstract: str
    categories: list[str]
    published: str
    pdf_url: str
    html_url: str       # ar5iv HTML 버전 URL
    field: str           # 우리가 분류한 관심 분야명


ARXIV_API_URL = "http://export.arxiv.org/api/query"
ARXIV_NS = {"atom": "http://www.w3.org/2005/Atom"}


def _parse_entry(entry: ET.Element, field: str) -> ArxivPaper:
    """arxiv API 응답의 entry 하나를 ArxivPaper로 변환"""
    arxiv_id_full = entry.find("atom:id", ARXIV_NS).text
    arxiv_id = arxiv_id_full.split("/abs/")[-1]

    title = entry.find("atom:title", ARXIV_NS).text.strip().replace("\n", " ")

    authors = []
    for author in entry.findall("atom:author", ARXIV_NS):
        name = author.find("atom:name", ARXIV_NS).text
        authors.append(name)

    abstract = entry.find("atom:summary", ARXIV_NS).text.strip().replace("\n", " ")

    categories = []
    for cat in entry.findall("atom:category", ARXIV_NS):
        categories.append(cat.get("term"))

    published = entry.find("atom:published", ARXIV_NS).text[:10]

    pdf_url = f"https://arxiv.org/pdf/{arxiv_id}"
    html_url = f"https://ar5iv.labs.arxiv.org/html/{arxiv_id}"

    return ArxivPaper(
        arxiv_id=arxiv_id,
        title=title,
        authors=authors,
        abstract=abstract,
        categories=categories,
        published=published,
        pdf_url=pdf_url,
        html_url=html_url,
        field=field,
    )


def _search_arxiv(categories: list[str], keywords: list[str], max_results: int = 20) -> list[ET.Element]:
    """arxiv API로 검색 쿼리 실행"""
    # 카테고리 OR 조건
    cat_query = " OR ".join(f"cat:{cat}" for cat in categories)

    # 키워드 OR 조건 (제목+초록에서 검색)
    if keywords:
        kw_query = " OR ".join(f'all:"{kw}"' for kw in keywords[:5])  # 상위 5개만
        query = f"({cat_query}) AND ({kw_query})"
    else:
        query = cat_query

    params = {
        "search_query": query,
        "start": 0,
        "max_results": max_results,
        "sortBy": "submittedDate",
        "sortOrder": "descending",
    }

    url = f"{ARXIV_API_URL}?{urllib.parse.urlencode(params)}"

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "arxiv-digest/1.0"})
        with urllib.request.urlopen(req, timeout=30) as response:
            data = response.read()
    except Exception as e:
        print(f"  ⚠️  arxiv API 요청 실패: {e}")
        return []

    root = ET.fromstring(data)
    entries = root.findall("atom:entry", ARXIV_NS)
    return entries


def _is_recent(published_date: str, days: int = 7) -> bool:
    """논문이 최근 N일 이내인지 확인"""
    try:
        pub = datetime.strptime(published_date, "%Y-%m-%d")
        cutoff = datetime.now() - timedelta(days=days)
        return pub >= cutoff
    except ValueError:
        return True  # 파싱 실패 시 포함


def crawl_papers() -> dict[str, list[ArxivPaper]]:
    """
    모든 관심 분야에서 최신 논문을 크롤링한다.

    Returns:
        {분야명: [ArxivPaper, ...]} 딕셔너리
    """
    results: dict[str, list[ArxivPaper]] = {}

    for field_name, field_config in RESEARCH_FIELDS.items():
        print(f"🔍 [{field_name}] 논문 검색 중...")

        entries = _search_arxiv(
            categories=field_config["categories"],
            keywords=field_config["keywords"],
            max_results=20,  # 넉넉하게 가져와서 나중에 AI가 선별
        )

        papers = []
        seen_ids = set()

        for entry in entries:
            paper = _parse_entry(entry, field_name)

            # 중복 제거
            if paper.arxiv_id in seen_ids:
                continue
            seen_ids.add(paper.arxiv_id)

            # 최근 7일 이내만
            if not _is_recent(paper.published):
                continue

            papers.append(paper)

        results[field_name] = papers
        print(f"  📄 {len(papers)}편 발견")

    total = sum(len(v) for v in results.values())
    print(f"\n📚 총 {total}편 크롤링 완료.\n")
    return results
