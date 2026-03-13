---
layout: default
title: Home
---

# 📚 arxiv Digest

AI가 매일 선별하고 한국어로 요약하는 최신 논문 다이제스트입니다.

**관심 분야**: 🤖 Physical AI · 🧠 LLM · 🧬 생명과학 & 제약 · 🛡️ 면역학 · 📈 금융 AI

---

{% for post in site.posts limit:20 %}
### [{{ post.title }}]({{ post.url | relative_url }})
<small>{{ post.date | date: "%Y년 %m월 %d일" }} · {{ post.tags | join: ", " }}</small>

{% endfor %}

{% if site.posts.size > 20 %}
[더 보기 →](/arxiv-digest/archive)
{% endif %}
