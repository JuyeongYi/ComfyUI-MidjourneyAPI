# ComfyUI — 로컬 파일을 노드 안에 즉시 미리보기

워크플로우 실행 없이, 노드를 캔버스에 올리거나 위젯 값을 바꾸는 즉시
이미지를 노드 안에 표시하는 방법.

---

## 핵심 메커니즘

### `node.imgs = [HTMLImageElement]`

LiteGraph / ComfyUI가 노드 하단에 이미지를 렌더링하는 **네이티브 메커니즘**.

```javascript
const img = new Image();
img.onload = () => {
    node.imgs = [img];
    app.graph?.setDirtyCanvas(true); // 캔버스 리드로우
};
img.src = "...";
```

- `node.imgs`에 배열로 할당 → 노드 하단에 이미지가 그려짐
- `null`로 초기화하면 이미지 제거
- Load Image, PreviewImage, WebcamCapture 노드가 모두 이 방식 사용

---

## 로컬 파일 서빙 — 백엔드 API 라우트

ComfyUI `/view` 엔드포인트는 `input/output/temp` 폴더만 지원.
플러그인 자체 디렉터리의 파일은 `PromptServer.instance.routes`로 별도 라우트 등록.

```python
# node_*.py (모듈 임포트 시 실행)
from server import PromptServer
from aiohttp import web as aiohttp_web

_CONTENT_TYPES = {
    ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
    ".png": "image/png",  ".webp": "image/webp", ".gif": "image/gif",
}

@PromptServer.instance.routes.get("/mj/style_image")
async def _mj_style_image_api(request):
    name = request.rel_url.query.get("name", "")
    path = _get_file_path(name)          # 내부 함수로 경로 결정
    if path is None:
        return aiohttp_web.Response(status=404)
    ct = _CONTENT_TYPES.get(path.suffix.lower(), "application/octet-stream")
    return aiohttp_web.Response(body=path.read_bytes(), content_type=ct)
```

> **타이밍**: ComfyUI는 서버 시작 후 커스텀 노드를 로드하므로
> `PromptServer.instance`는 모듈 임포트 시점에 이미 존재.

---

## JS 확장 — 즉시 미리보기

### 패턴 요약

```javascript
// web/xxx_preview.js
import { app } from "../../scripts/app.js";

function loadPreview(node, value) {
    if (!value || value === "(none)") {
        node.imgs = null;
        app.graph?.setDirtyCanvas(true);
        return;
    }
    const img = new Image();
    img.onload  = () => { node.imgs = [img]; app.graph?.setDirtyCanvas(true); };
    img.onerror = () => { node.imgs = null;  app.graph?.setDirtyCanvas(true); };
    img.src = `/my/api?name=${encodeURIComponent(value)}`;
}

app.registerExtension({
    name: "MyPlugin.Preview",
    async nodeCreated(node) {
        if (node.comfyClass !== "MY_NODE_ID") return;

        const widget = node.widgets?.find(w => w.name === "my_combo");
        if (!widget) return;

        // 1. 드롭다운 변경 시 즉시 갱신
        const origCb = widget.callback;
        widget.callback = function(value) {
            origCb?.call(this, value);
            loadPreview(node, value);
        };

        // 2. 저장된 워크플로우 로드 시 복원값으로 갱신
        const origConfigure = node.onConfigure;
        node.onConfigure = function(info) {
            origConfigure?.apply(this, arguments);
            const w = this.widgets?.find(w => w.name === "my_combo");
            loadPreview(this, w?.value);
        };

        // 3. 노드를 캔버스에 처음 올릴 때 기본값으로 표시
        loadPreview(node, widget.value);
    },
});
```

### 세 가지 타이밍 처리

| 상황 | 훅 |
|------|-----|
| 노드를 새로 캔버스에 올림 | `nodeCreated` → 즉시 `loadPreview(widget.value)` |
| 드롭다운 값 변경 | `widget.callback` 인터셉트 |
| 저장된 워크플로우 로드 | `node.onConfigure` 훅 |

---

## 주의사항

- `is_output_node=True` + `ui.PreviewImage` 는 **워크플로우 실행 후**에만 표시됨
  → 즉시 미리보기가 필요하면 이 방식을 사용하지 말 것
- `widget.callback`은 콤보 위젯의 값이 UI에서 변경될 때 호출됨
  (Python `execute`가 아닌 프론트엔드 이벤트)
- webp 포함 모든 이미지 포맷은 브라우저가 직접 디코딩하므로 별도 변환 불필요

---

## 실제 구현 예시

- 백엔드: `node_style.py` — `_collect_styles()` + `GET /mj/style_image`
- 프론트엔드: `web/style_preview.js` — `MJ_StyleSelect` 노드 미리보기
