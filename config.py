"""프로젝트 설정"""

import os

# ── Anthropic ──
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
CLAUDE_MODEL = "claude-sonnet-4-20250514"

# ── 관심 분야 & arxiv 카테고리 매핑 ──
# arxiv 카테고리 목록: https://arxiv.org/category_taxonomy
RESEARCH_FIELDS = {
    "Physical AI": {
        "categories": ["cs.RO", "cs.AI"],
        "keywords": ["embodied", "physical", "robot", "sim-to-real", "manipulation", "locomotion"],
        "papers_per_day": 2,
        "emoji": "🤖",
    },
    "LLM": {
        "categories": ["cs.CL", "cs.LG"],
        "keywords": ["large language model", "LLM", "transformer", "GPT", "reasoning", "RLHF", "alignment", "fine-tuning", "prompt"],
        "papers_per_day": 2,
        "emoji": "🧠",
    },
    "생명과학 & 제약": {
        "categories": ["q-bio.BM", "q-bio.GN", "cs.AI"],
        "keywords": ["drug discovery", "protein", "molecular", "genomics", "pharmaceutical", "biomarker", "clinical trial"],
        "papers_per_day": 1,
        "emoji": "🧬",
    },
    "면역학": {
        "categories": ["q-bio.CB", "q-bio.QM", "q-bio.TO"],
        "keywords": ["immune", "T-cell", "antibody", "immunotherapy", "vaccine", "autoimmune", "inflammation"],
        "papers_per_day": 1,
        "emoji": "🛡️",
    },
    "금융 AI": {
        "categories": ["q-fin.ST", "q-fin.PM", "q-fin.CP"],
        "keywords": ["portfolio", "trading", "risk", "financial", "market", "pricing", "quantitative"],
        "papers_per_day": 1,
        "emoji": "📈",
    },
}

# 하루 총 최대 논문 수
MAX_PAPERS_PER_DAY = sum(f["papers_per_day"] for f in RESEARCH_FIELDS.values())

# ── 요약 설정 ──
MAX_PAPER_TEXT_LENGTH = 30000  # 논문 텍스트 최대 글자수 (Claude 컨텍스트 절약)
MAX_SUMMARY_TOKENS = 4096
