import { app } from "../../scripts/app.js";

function loadPreviewForNode(node, styleName) {
    if (!styleName || styleName === "(none)") {
        node.imgs = null;
        app.graph?.setDirtyCanvas(true);
        return;
    }
    const img = new Image();
    img.onload = () => {
        node.imgs = [img];
        app.graph?.setDirtyCanvas(true);
    };
    img.onerror = () => {
        node.imgs = null;
        app.graph?.setDirtyCanvas(true);
    };
    img.src = `/mj/style_image?name=${encodeURIComponent(styleName)}`;
}

app.registerExtension({
    name: "Midjourney.StylePreview",

    async nodeCreated(node) {
        if (node.comfyClass !== "MJ_StyleSelect") return;

        const styleWidget = node.widgets?.find(w => w.name === "style");
        if (!styleWidget) return;

        // 드롭다운 값 변경 시 즉시 미리보기 갱신
        const origCallback = styleWidget.callback;
        styleWidget.callback = function (value) {
            origCallback?.call(this, value);
            loadPreviewForNode(node, value);
        };

        // 저장된 워크플로우 로드 시 복원된 값으로 미리보기
        const origConfigure = node.onConfigure;
        node.onConfigure = function (info) {
            origConfigure?.apply(this, arguments);
            const w = this.widgets?.find(w => w.name === "style");
            loadPreviewForNode(this, w?.value);
        };

        // 노드를 캔버스에 새로 올렸을 때 기본값으로 미리보기
        loadPreviewForNode(node, styleWidget.value);
    },
});
