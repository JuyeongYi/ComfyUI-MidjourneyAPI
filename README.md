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
| **MidJourney Remix** | 새 프롬프트로 변형 | 이미지 4장 + job_id |
| **MidJourney Upscale** | 2× 업스케일 (subtle/creative) | 이미지 1장 + job_id |
| **MidJourney Pan** | 방향별 이미지 확장 | 이미지 4장 + job_id |
| **MidJourney Download** | Job ID로 이미지 다운로드 | 이미지 4장 |

### 비디오 생성

| 노드 | 설명 | 출력 |
|------|------|------|
| **MidJourney Animate** | 이미지 → 비디오 변환 (Imagine job 기준) | job_id |
| **MidJourney Animate From Image** | 이미지 텐서로 비디오 생성 (시작/종료 프레임 지정 가능) | job_id |
| **MidJourney Extend Video** | 완료된 비디오 연장 | job_id |
| **MidJourney Load Video** | 비디오 Job ID로 비디오 로드 | VIDEO |

### 파라미터

| 노드 | 설명 |
|------|------|
| **Imagine V7 Params** | V7 파라미터 설정 (aspect ratio, stylize, chaos, seed, quality, raw, tile, sref, oref, personalize, visibility 등) |
| **Video Params** | 비디오 파라미터 설정 (motion, resolution, batch_size, stealth) |
| **Save Imagine Params** | 파라미터를 JSON 프리셋으로 저장 |
| **Load Imagine Params** | JSON 프리셋에서 파라미터 로드 |

### 스타일 선택

| 노드 | 설명 |
|------|------|
| **Style Select** | 스타일 이미지 파일로부터 `--sref` 코드를 선택 · 미리보기 |

### 키워드

**Keyword Join** — 여러 키워드를 하나의 문자열로 결합 (구분자: `, ` / ` ` / ` | ` / ` + ` 선택 가능, 최대 100개 입력).

**Keyword Random** — 카테고리(파일)를 선택하고 seed를 지정하면 해당 키워드 풀에서 무작위로 1개를 출력. seed가 같으면 항상 같은 키워드를 반환.

**카테고리별 키워드 노드** — 드롭다운에서 선택한 키워드를 String으로 출력. `Midjourney/keywords/<카테고리>` 메뉴에서 찾을 수 있음.

| 카테고리 | 노드 수 | 포함 노드 |
|---------|---------|-----------|
| **Photography** | 9 | Shot Type, Lens, Camera Effect, Film Stock, Camera Body, Composition, Perspective, Post Processing, Detail Quality |
| **Lighting** | 4 | Lighting, Color Tone, Mood, Lighting Setup |
| **Color** | 2 | Color Palette, Color Grading |
| **Video** | 3 | Camera Movement, Subject Motion, Time Motion |
| **Environment** | 7 | Environment, Natural Landscape, Underwater Scene, Urban Setting, Weather, Season, Celestial |
| **Art Style** | 6 | Art Style, Art Medium, Era Aesthetic, Illustration Style, Print Technique, Street Art Style |
| **Digital Fx** | 6 | Render Engine, Game Art Style, Vfx Style, Glitch Aesthetic, Dimensionality, Particle Effects |
| **Character** | 5 | Facial Expression, Hair Style, Makeup Style, Subject Pose, Fashion Clothing |
| **Architecture** | 3 | Architectural Style, Interior Design, Building Type |
| **Culture** | 6 | Cultural Aesthetic, Cultural Ritual, Mythological Theme, Genre Narrative, Music Genre Aesthetic, Artist Reference |
| **Material** | 4 | Texture Material, Material Finish, Pattern Design, Typography Style |
| **Subject** | 7 | Flora Style, Creature Type, Sport Activity, Food Styling, Vehicle Type, Scientific Visualization, Data Visualization |

총 **63개 카테고리 파일, 약 2,040개 키워드**.

---

## 기능

- 모든 생성 노드에 인라인 이미지 미리보기
- 우클릭 컨텍스트 메뉴로 Preview/Save Image 노드 자동 생성·연결
- 컬러 콘솔 로깅 + 파라미터 요약 출력
- 다운로드 이미지 인메모리 처리 (임시 파일 없음)
- 이벤트 기반 진행 상태 보고
- 이미지 누락 슬롯에 `ExecutionBlocker` 적용 (예: Upscale은 1장만 반환, 나머지 3슬롯 블록)
- **Enqueue 모드** — 모든 잡 서밋 노드에 `enqueue` 토글 추가. `true`로 설정하면 잡을 서밋한 뒤 폴링 없이 즉시 `job_id`만 반환 (이미지/비디오 출력은 차단). 미드저니의 큐잉 기능을 활용해 여러 작업을 동시에 쌓아두고 나중에 MJ_Download / MJ_Load Video로 결과를 회수하는 워크플로우에 사용.

---

## Enqueue 워크플로우

모든 잡 서밋 노드(Imagine, Vary, Remix, Upscale, Pan, Animate, AnimateFromImage, ExtendVideo)에 `enqueue` Boolean 입력이 있습니다.

```
enqueue = false (기본값)
  → 잡 서밋 → 폴링 → 완료 시 이미지/비디오 반환

enqueue = true
  → 잡 서밋 → 즉시 job_id 반환 (이미지 출력은 ExecutionBlocker로 차단)
  → 나중에 MJ_Download / MJ_Load Video 노드로 결과 회수
```

여러 Imagine 노드를 enqueue=true로 동시에 실행하면 미드저니 큐에 작업을 쌓아두고 병렬로 처리시킬 수 있습니다.

### enqueue=true가 자동으로 무시되는 경우

enqueue=true로 설정해도 출력이 연결되어 있으면 자동으로 enqueue=false로 동작합니다. 노드 종류에 따라 판단 기준이 다릅니다.

출력 연결 타입에 따라 판단합니다.

| 연결 타입 | 조건 |
|----------|------|
| **Image 출력** | 어디든 연결되면 무시 |
| **job_id 출력** | MJ 잡 서밋 노드(Vary/Remix/Upscale/Pan/Animate/ExtendVideo)에 연결 시만 무시 |

```
Imagine(enqueue=true) → image_0 → PreviewImage
  → enqueue 무시 (Image 출력 연결)

Imagine(enqueue=true) → job_id → MJ_Vary
  → enqueue 무시 (job_id가 MJ 잡 서밋 노드에 연결)

Imagine(enqueue=true) → job_id → MJ_Download
  → enqueue 유지, 즉시 job_id 반환 (Download는 서밋 노드 아님)

Imagine(enqueue=true) → [출력 연결 없음]
  → enqueue 유지, 즉시 job_id 반환
```

콘솔에 `[MJ] <노드명>: enqueue 무시 — ...` 메시지가 출력됩니다.

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
