---
name: token-stats
description: 현재 Antigravity 대화 세션의 로컬 transcript.jsonl 로그에서 모델별 입력·출력·캐시 토큰량과 생성 코드 밀도를 즉시 집계합니다.
---

# /token-stats — 로컬 세션 토큰 & 코드 밀도 측정 스킬

사용자가 `/token-stats` 를 호출하거나 방금 실행한 프롬프트의 토큰 사용량 비교를 요청하면 다음 절차를 수행하세요:

1. 현재 대화의 `transcript.jsonl` 경로(`<appDataDir>/brain/<conversation-id>/.system_generated/logs/transcript.jsonl` 또는 `~/.gemini/antigravity/brain/<conversation-id>/.system_generated/logs/transcript.jsonl`)를 확인합니다.
2. Python 표준 라이브러리(`json`, `pathlib`) 한 줄 스크립트로 각 `PLANNER_RESPONSE` 스텝의 모델명, `input_tokens`, `cache_read_tokens`, `output_tokens`, `thinking_tokens` 합계를 추출합니다.
3. 방금 생성하거나 수정한 파일의 총 코드 줄 수(LOC)를 함께 세어 **1K Output 토큰당 코드 줄 수(밀도)** 와 함께 간결한 마크다운 표로 출력합니다.
