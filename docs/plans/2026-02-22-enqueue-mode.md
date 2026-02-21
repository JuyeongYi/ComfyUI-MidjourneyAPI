# Enqueue Mode Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 모든 잡 서밋 노드에 `enqueue` Boolean 입력을 추가하여, true일 때 폴링 없이 job_id만 즉시 반환하고 이미지 출력은 차단한다.

**Architecture:** `nodes/generation.py` 한 파일만 수정. 각 노드 `define_schema()`에 `enqueue` 입력 추가, `execute()`에서 `enqueue=True`이면 `poll_with_progress` + 다운로드를 스킵하고 이미지 자리에 `ExecutionBlocker(None)`을 채운다. 중복을 줄이기 위해 두 개의 내부 헬퍼(`_enqueue_image_outputs`, `_enqueue_video_outputs`)를 추가한다.

**Tech Stack:** ComfyUI V3 API (`comfy_api.latest.io`), `comfy_execution.graph.ExecutionBlocker` (이미 import됨)

---

### Task 1: 헬퍼 함수 추가

**Files:**
- Modify: `nodes/generation.py` — `_preview_ui()` 아래에 헬퍼 2개 삽입

**Step 1: 헬퍼 코드 삽입**

`_preview_ui` 함수(line 22) 바로 아래에 추가:

```python
def _enqueue_image_outputs(job, n: int = 4) -> io.NodeOutput:
    """enqueue=True일 때: 이미지 n개를 ExecutionBlocker로 차단하고 job_id만 반환."""
    blockers = [ExecutionBlocker(None)] * n
    return io.NodeOutput(*blockers, job.id)


def _enqueue_video_output(job) -> io.NodeOutput:
    """enqueue=True일 때: 비디오 노드용 — job_id만 즉시 반환."""
    return io.NodeOutput(job.id)
```

**Step 2: ComfyUI 재시작 없이 문법 확인**

```bash
cd /mnt/c/Users/Jooyo/source/ComfyUI/custom_nodes/ComfyUI-MidJourney
python -c "from nodes.generation import _enqueue_image_outputs; print('OK')"
```
Expected: `OK`

**Step 3: Commit**

```bash
git add nodes/generation.py
git commit -m "feat: add _enqueue_image_outputs / _enqueue_video_output helpers"
```

---

### Task 2: MidJourneyImagine — enqueue 추가

**Files:**
- Modify: `nodes/generation.py` — `MidJourneyImagine` 클래스

**Step 1: define_schema()에 enqueue 입력 추가**

`MJ_PARAMS.Input("params", optional=True),` 다음 줄에 추가:

```python
io.Boolean.Input("enqueue", default=False,
                 tooltip="True: 잡 서밋 후 즉시 반환 (폴링 없음). job_id로 나중에 MJ_Download"),
```

**Step 2: execute() 시그니처에 enqueue 파라미터 추가**

```python
def execute(cls, prompt, no, params=None, enqueue=False) -> io.NodeOutput:
```

**Step 3: execute() 본문에 enqueue 분기 추가**

`log_job(...)` 다음 줄, `job = poll_with_progress(...)` 위에 삽입:

```python
if enqueue:
    return _enqueue_image_outputs(job, n=4)
```

**Step 4: 문법 확인**

```bash
python -c "from nodes.generation import MidJourneyImagine; print('OK')"
```

**Step 5: Commit**

```bash
git add nodes/generation.py
git commit -m "feat(Imagine): add enqueue mode"
```

---

### Task 3: MidJourneyVary — enqueue 추가

**Files:**
- Modify: `nodes/generation.py` — `MidJourneyVary` 클래스

**Step 1: define_schema()에 enqueue 입력 추가**

`io.Combo.Input("mode", ...)` 다음 줄에 추가:

```python
io.Boolean.Input("enqueue", default=False,
                 tooltip="True: 잡 서밋 후 즉시 반환. job_id로 나중에 MJ_Download"),
```

**Step 2: execute() 파라미터 + 분기 추가**

```python
def execute(cls, job_id, index, strong, mode, enqueue=False) -> io.NodeOutput:
    ...
    log_job(...)
    if enqueue:
        return _enqueue_image_outputs(job, n=4)
    job = poll_with_progress(job, mode=mode)
    ...
```

**Step 3: 문법 확인 + Commit**

```bash
python -c "from nodes.generation import MidJourneyVary; print('OK')"
git add nodes/generation.py
git commit -m "feat(Vary): add enqueue mode"
```

---

### Task 4: MidJourneyRemix — enqueue 추가

**Files:**
- Modify: `nodes/generation.py` — `MidJourneyRemix` 클래스

**Step 1: define_schema()에 enqueue 입력 추가**

`MJ_PARAMS.Input("params", optional=True),` 다음 줄에 추가:

```python
io.Boolean.Input("enqueue", default=False,
                 tooltip="True: 잡 서밋 후 즉시 반환. job_id로 나중에 MJ_Download"),
```

**Step 2: execute() 파라미터 + 분기 추가**

```python
def execute(cls, job_id, index, prompt, no, strong, params=None, enqueue=False) -> io.NodeOutput:
    ...
    log_job(...)
    if enqueue:
        return _enqueue_image_outputs(job, n=4)
    job = poll_with_progress(job, mode=mode)
    ...
```

**Step 3: 문법 확인 + Commit**

```bash
python -c "from nodes.generation import MidJourneyRemix; print('OK')"
git add nodes/generation.py
git commit -m "feat(Remix): add enqueue mode"
```

---

### Task 5: MidJourneyUpscale — enqueue 추가

**Files:**
- Modify: `nodes/generation.py` — `MidJourneyUpscale` 클래스

**Step 1: define_schema()에 enqueue 입력 추가**

`io.Combo.Input("mode", ...)` 다음 줄에 추가:

```python
io.Boolean.Input("enqueue", default=False,
                 tooltip="True: 잡 서밋 후 즉시 반환. job_id로 나중에 MJ_Download"),
```

**Step 2: execute() 파라미터 + 분기 추가**

Upscale은 이미지 출력이 1개(`image`, not 4개):

```python
def execute(cls, job_id, index, upscale_type, mode, enqueue=False) -> io.NodeOutput:
    ...
    log_job(...)
    if enqueue:
        return _enqueue_image_outputs(job, n=1)
    job = poll_with_progress(job, mode=mode)
    ...
```

**Step 3: 문법 확인 + Commit**

```bash
python -c "from nodes.generation import MidJourneyUpscale; print('OK')"
git add nodes/generation.py
git commit -m "feat(Upscale): add enqueue mode"
```

---

### Task 6: MidJourneyPan — enqueue 추가

**Files:**
- Modify: `nodes/generation.py` — `MidJourneyPan` 클래스

**Step 1: define_schema()에 enqueue 입력 추가**

`io.Combo.Input("mode", ...)` 다음 줄에 추가:

```python
io.Boolean.Input("enqueue", default=False,
                 tooltip="True: 잡 서밋 후 즉시 반환. job_id로 나중에 MJ_Download"),
```

**Step 2: execute() 파라미터 + 분기 추가**

```python
def execute(cls, job_id, index, direction, prompt="", no="", mode=SpeedMode.FAST, enqueue=False) -> io.NodeOutput:
    ...
    log_job(...)
    if enqueue:
        return _enqueue_image_outputs(job, n=4)
    job = poll_with_progress(job, mode=mode)
    ...
```

**Step 3: 문법 확인 + Commit**

```bash
python -c "from nodes.generation import MidJourneyPan; print('OK')"
git add nodes/generation.py
git commit -m "feat(Pan): add enqueue mode"
```

---

### Task 7: 비디오 노드 3개 — enqueue 추가

비디오 노드(Animate, AnimateFromImage, ExtendVideo)는 원래 job_id만 반환하므로
enqueue=True일 때 `_enqueue_video_output(job)` 호출 = poll 스킵만 하면 됨.

**Files:**
- Modify: `nodes/generation.py` — `MidJourneyAnimate`, `MidJourneyAnimateFromImage`, `MidJourneyExtendVideo`

**Step 1: MidJourneyAnimate**

define_schema() — `io.String.Input("no", ...)` 다음 줄에 추가:
```python
io.Boolean.Input("enqueue", default=False,
                 tooltip="True: 잡 서밋 후 즉시 반환 (폴링 없음)"),
```

execute():
```python
def execute(cls, job_id, index, video_params=None, prompt="", no="", enqueue=False) -> io.NodeOutput:
    ...
    log_job(...)
    if enqueue:
        return _enqueue_video_output(job)
    job = poll_with_progress(job, mode=kw["mode"])
    return io.NodeOutput(job.id)
```

**Step 2: MidJourneyAnimateFromImage** — 동일 패턴

define_schema() — `io.String.Input("no", ...)` 다음 줄:
```python
io.Boolean.Input("enqueue", default=False,
                 tooltip="True: 잡 서밋 후 즉시 반환 (폴링 없음)"),
```

execute():
```python
def execute(cls, start_image, end_image=None, loop=False, video_params=None,
            prompt="", no="", enqueue=False) -> io.NodeOutput:
    ...
    log_job(...)
    if enqueue:
        return _enqueue_video_output(job)
    job = poll_with_progress(job, mode=kw["mode"])
    return io.NodeOutput(job.id)
```

**Step 3: MidJourneyExtendVideo** — 동일 패턴

define_schema() — `io.String.Input("no", ...)` 다음 줄:
```python
io.Boolean.Input("enqueue", default=False,
                 tooltip="True: 잡 서밋 후 즉시 반환 (폴링 없음)"),
```

execute():
```python
def execute(cls, job_id, index, loop=False, video_params=None,
            end_image=None, prompt="", no="", enqueue=False) -> io.NodeOutput:
    ...
    log_job(...)
    if enqueue:
        return _enqueue_video_output(job)
    job = poll_with_progress(job, mode=kw["mode"])
    return io.NodeOutput(job.id)
```

**Step 4: 전체 문법 확인 + Commit**

```bash
python -c "from nodes import generation; print('OK')"
git add nodes/generation.py
git commit -m "feat(video nodes): add enqueue mode to Animate / AnimateFromImage / ExtendVideo"
```

---

### Task 8: 최종 검증

**Step 1: 전체 임포트 확인**

```bash
python -c "
from nodes.generation import (
    MidJourneyImagine, MidJourneyVary, MidJourneyRemix,
    MidJourneyUpscale, MidJourneyPan,
    MidJourneyAnimate, MidJourneyAnimateFromImage, MidJourneyExtendVideo
)
print('ALL OK')
"
```

**Step 2: 스키마 확인 — enqueue 입력 존재 여부**

```bash
python -c "
from nodes.generation import MidJourneyImagine
schema = MidJourneyImagine.define_schema()
names = [i.name for i in schema.inputs]
assert 'enqueue' in names, f'enqueue 없음: {names}'
print('enqueue input confirmed:', names)
"
```

**Step 3: ComfyUI 재시작 후 수동 확인 체크리스트**

- [ ] MidJourney Imagine 노드에 `enqueue` Boolean 위젯 표시
- [ ] enqueue=false → 기존 동작 그대로 (이미지 4장 출력)
- [ ] enqueue=true → 워크플로우 실행 시 즉시 job_id 반환, 이미지 다운스트림 차단
- [ ] MJ_Download 노드에 enqueue 결과 job_id 연결해 이미지 취득 가능
- [ ] 비디오 노드 enqueue=true → job_id 즉시 반환, MJ_LoadVideo로 취득 가능
