# 기능 브레인스토밍 (2026-02-21)

> API 개선 이후 구현 검토 예정

## A. 워크플로우 편의

- **Job ID 히스토리 노드** — 최근 실행한 job_id 목록을 드롭다운으로 선택. 이전 결과로 Vary/Pan하려면 job_id를 직접 붙여넣어야 하는 번거로움 해소
- **Batch Imagine 노드** — 프롬프트 여러 줄 → 각 줄마다 Imagine 실행, 결과 이미지 배열 출력
- **Remix 노드** — Vary와 유사하지만 프롬프트도 같이 변경 (MJ의 Remix 기능)

## B. 스타일 시스템 확장

- **Style Capture 노드** — 업스케일된 이미지의 job_id를 받아서 sref 코드를 추출, 스타일 파일로 저장
- **StyleSelect 다중 선택** — 여러 스타일 선택 → `--sref code1 code2` 형태로 조합 출력

## C. 파라미터 UX

- **Quick Params 노드** — ImagineV7Params의 가장 자주 쓰는 것만 뽑은 경량 버전 (AR, stylize, seed만)
- **Params Diff 노드** — 두 params를 받아 다른 값만 표시 (프리셋 비교용)

## D. 결과 관리

- **MJ Job Browser** — ComfyUI 사이드패널에서 내 MJ 잡 히스토리 탐색 (API의 list_jobs 활용)
- **Auto-Save 노드** — 생성 즉시 지정 폴더에 job_id 기반 파일명으로 저장
