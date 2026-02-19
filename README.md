# ComfyUI-MidJourney

[midjourney-api](https://github.com/JuyeongYi/PythonMidjourneyAPIClient)를 통해 ComfyUI에서 Midjourney 이미지를 생성하는 커스텀 노드 패키지.

> 영문 문서: [README.en.md](README.en.md)

---

## 설치

1. `ComfyUI/custom_nodes/` 디렉터리에 클론:
   ```bash
   cd ComfyUI/custom_nodes
   git clone https://github.com/JuyeongYi/ComfyUI-MidJourney.git
   ```

2. 의존성 설치:
   ```bash
   pip install -r ComfyUI-MidJourney/requirements.txt
   ```

3. ComfyUI **루트** 디렉터리에 `.env` 파일을 배치해 인증 설정.
   인증 방법은 [PythonMidjourneyAPIClient](https://github.com/JuyeongYi/PythonMidjourneyAPIClient) 참고.

---

## 노드 목록

### 이미지 생성

| 노드 | 설명 | 출력 |
|------|------|------|
| **MidJourney Imagine** | 텍스트→이미지 생성 | 이미지 4장 + job_id |
| **MidJourney Vary** | Strong/Subtle 변형 | 이미지 4장 + job_id |
| **MidJourney Upscale** | 2× 업스케일 (subtle/creative) | 이미지 1장 + job_id |
| **MidJourney Pan** | 방향별 이미지 확장 | 이미지 4장 + job_id |
| **MidJourney Download** | Job ID로 이미지 다운로드 | 이미지 4장 |

### 파라미터

| 노드 | 설명 |
|------|------|
| **Imagine V7 Params** | V7 파라미터 설정 (aspect ratio, stylize, chaos, seed, quality, raw, tile, sref, oref, personalize, visibility 등) |
| **Save Imagine Params** | 파라미터를 JSON 프리셋으로 저장 |
| **Load Imagine Params** | JSON 프리셋에서 파라미터 로드 |

### 스타일 선택

| 노드 | 설명 |
|------|------|
| **Style Select** | 스타일 이미지 파일로부터 `--sref` 코드를 선택 · 미리보기 |

### 키워드

**Keyword Join** — 여러 키워드를 하나의 문자열로 결합 (구분자: `, ` / ` ` / ` | ` / ` + ` 선택 가능, 최대 100개 입력).

**카테고리별 키워드 노드** — 드롭다운에서 선택한 키워드를 String으로 출력. `Midjourney/keywords/<카테고리>` 메뉴에서 찾을 수 있음.

| 카테고리 | 노드 수 | 포함 노드 |
|---------|---------|-----------|
| **Photography** | 9 | Shot Type, Lens, Camera Effect, Film Stock, Camera Body, Composition, Perspective, Post Processing, Detail Quality |
| **Lighting** | 3 | Lighting, Color Tone, Mood |
| **Environment** | 7 | Environment, Natural Landscape, Underwater Scene, Urban Setting, Weather, Season, Celestial |
| **Art Style** | 6 | Art Style, Art Medium, Era Aesthetic, Illustration Style, Print Technique, Street Art Style |
| **Digital Fx** | 6 | Render Engine, Game Art Style, Vfx Style, Glitch Aesthetic, Dimensionality, Particle Effects |
| **Character** | 5 | Facial Expression, Hair Style, Makeup Style, Subject Pose, Fashion Clothing |
| **Architecture** | 3 | Architectural Style, Interior Design, Building Type |
| **Culture** | 6 | Cultural Aesthetic, Cultural Ritual, Mythological Theme, Genre Narrative, Music Genre Aesthetic, Artist Reference |
| **Material** | 4 | Texture Material, Material Finish, Pattern Design, Typography Style |
| **Subject** | 7 | Flora Style, Creature Type, Sport Activity, Food Styling, Vehicle Type, Scientific Visualization, Data Visualization |

총 **56개 카테고리 파일, 약 1,845개 키워드**.

---

## 기능

- 모든 생성 노드에 인라인 이미지 미리보기
- 우클릭 컨텍스트 메뉴로 Preview/Save Image 노드 자동 생성·연결
- 컬러 콘솔 로깅 + 파라미터 요약 출력
- 다운로드 이미지 인메모리 처리 (임시 파일 없음)
- 이벤트 기반 진행 상태 보고
- 이미지 누락 슬롯에 `ExecutionBlocker` 적용 (예: Upscale은 1장만 반환, 나머지 3슬롯 블록)

---

## 우클릭 메뉴

Imagine, Vary, Pan, Upscale, Download 노드에서:

- **Connect Preview Image(s)** — PreviewImage 노드를 2×2 그리드로 생성·연결
- **Connect Save Image(s)** — SaveImage 노드를 2×2 그리드로 생성·연결

---

## 커스터마이징

### 스타일 파일 추가

`mj/style/` 또는 `<ComfyUI 루트>/user/mj/style/` 에 이미지 파일을 저장:

```
<스타일 이름>__<sref코드>.<확장자>

예) Glitch Noir__2206414533.webp
    Golden Hour__1938472650.png
```

- 지원 확장자: `.jpg` `.jpeg` `.png` `.webp` `.gif`
- 동일 이름의 파일이 있으면 `user/` 경로가 우선 적용됨
- Style Select 노드는 **노드를 캔버스에 올리는 즉시** 선택된 스타일의 미리보기를 표시

### 키워드 파일 추가

`<ComfyUI 루트>/user/mj/keywords/<서브카테고리>/` 에 `.txt` 파일 추가:

```
user/mj/keywords/
  photography/
    my_custom.txt    ← 새 카테고리 노드로 등록됨
  lighting/
    lighting.txt     ← 기존 lighting 키워드에 추가 병합됨
```

- 파일명이 노드 표시 이름이 됨 (`my_custom.txt` → **My Custom** 노드)
- 폴더명이 ComfyUI 메뉴 서브카테고리가 됨
- 동일 파일명이면 user 파일의 키워드가 plugin 키워드 뒤에 병합 (덮어쓰기 아님)
- 한 줄에 하나씩, `#`으로 시작하는 줄은 주석으로 무시

---

## 라이선스

MIT
