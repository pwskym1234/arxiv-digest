"""
arxiv-digest — 메인 실행 스크립트

매일 arxiv에서 논문을 크롤링하고, AI로 선별/요약 후, 블로그 포스트를 생성합니다.

사용법:
    python3 scripts/main.py              # 오늘 날짜
    python3 scripts/main.py --date 2025-03-12   # 특정 날짜
"""

import argparse
import sys
from datetime import datetime
from pathlib import Path

# scripts/ 디렉토리를 경로에 추가
sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import ANTHROPIC_API_KEY, RESEARCH_FIELDS
from arxiv_crawler import crawl_papers
from summarizer import process_papers
from blog_publisher import publish_post


def main():
    parser = argparse.ArgumentParser(description="arxiv 논문 자동 요약 블로그")
    parser.add_argument("--date", type=str, default=None, help="대상 날짜 (YYYY-MM-DD)")
    args = parser.parse_args()

    if args.date:
        try:
            target_date = datetime.strptime(args.date, "%Y-%m-%d")
        except ValueError:
            print(f"❌ 날짜 형식 오류: {args.date}")
            sys.exit(1)
    else:
        target_date = datetime.now()

    # API 키 확인
    if not ANTHROPIC_API_KEY:
        print("❌ ANTHROPIC_API_KEY가 설정되지 않았습니다.")
        print("   GitHub Secrets 또는 환경변수에 설정해주세요.")
        sys.exit(1)

    date_str = target_date.strftime("%Y-%m-%d")
    print("=" * 60)
    print(f"📚 arxiv-digest — {date_str}")
    print(f"   분야: {', '.join(RESEARCH_FIELDS.keys())}")
    print("=" * 60)

    # Step 1: arxiv 크롤링
    print("\n📥 Step 1: arxiv에서 최신 논문 크롤링")
    print("-" * 40)
    papers_by_field = crawl_papers()

    total_found = sum(len(v) for v in papers_by_field.values())
    if total_found == 0:
        print("📭 오늘은 관련 논문이 없습니다. 종료합니다.")
        return

    # Step 2: AI 선별 + 전문 읽기 + 요약
    print("🤖 Step 2: AI 선별 & 요약")
    print("-" * 40)
    summaries = process_papers(papers_by_field)

    if not summaries:
        print("⚠️  요약 결과가 없습니다. 종료합니다.")
        return

    # Step 3: 블로그 포스트 생성
    print("\n📝 Step 3: 블로그 포스트 생성")
    print("-" * 40)
    filepath = publish_post(summaries, target_date)

    # 완료
    print("\n" + "=" * 60)
    if filepath:
        print(f"🎉 완료! 포스트가 생성되었습니다:")
        print(f"   {filepath}")
        print(f"   GitHub Actions가 자동으로 커밋 & 배포합니다.")
    print("=" * 60)


if __name__ == "__main__":
    main()
