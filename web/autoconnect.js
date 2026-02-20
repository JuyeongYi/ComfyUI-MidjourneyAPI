import { app } from "../../scripts/app.js";

// node_type → { imageCount, jobIdSlot (output index of job_id, -1 if none) }
const MJ_NODES = {
    "MJ_Imagine":  { imageCount: 4, jobIdSlot: 4 },
    "MJ_Vary":     { imageCount: 4, jobIdSlot: 4 },
    "MJ_Pan":      { imageCount: 4, jobIdSlot: 4 },
    "MJ_Upscale":  { imageCount: 1, jobIdSlot: 1 },
    "MJ_Download": { imageCount: 4, jobIdSlot: -1 },
};

app.registerExtension({
    name: "Midjourney.AutoConnect",

    async nodeCreated(node) {
        const cfg = MJ_NODES[node.comfyClass];
        if (!cfg) return;

        const origGetExtraMenuOptions = node.getExtraMenuOptions;
        node.getExtraMenuOptions = function (_, options) {
            if (origGetExtraMenuOptions) {
                origGetExtraMenuOptions.apply(this, arguments);
            }

            const count = cfg.imageCount;
            const plural = count > 1 ? "s" : "";
            const menuItems = [
                {
                    content: `Connect Preview Image${plural}`,
                    callback: () => addImageNodes(this, "PreviewImage", count, cfg.jobIdSlot),
                },
                {
                    content: `Connect Save Image${plural}`,
                    callback: () => addImageNodes(this, "SaveImage", count, cfg.jobIdSlot),
                },
            ];

            if (cfg.jobIdSlot >= 0) {
                menuItems.push({
                    content: "Midjourney",
                    submenu: {
                        options: [
                            {
                                content: "Vary",
                                submenu: {
                                    options: [
                                        {
                                            content: "Strong",
                                            callback: () => addJobNodes(this, "MJ_Vary", cfg.jobIdSlot, cfg.imageCount, { strong: true }),
                                        },
                                        {
                                            content: "Subtle",
                                            callback: () => addJobNodes(this, "MJ_Vary", cfg.jobIdSlot, cfg.imageCount, { strong: false }),
                                        },
                                    ],
                                },
                            },
                            {
                                content: "Upscale",
                                submenu: {
                                    options: [
                                        {
                                            content: "Subtle",
                                            callback: () => addJobNodes(this, "MJ_Upscale", cfg.jobIdSlot, cfg.imageCount, { upscale_type: "v7_2x_subtle" }),
                                        },
                                        {
                                            content: "Creative",
                                            callback: () => addJobNodes(this, "MJ_Upscale", cfg.jobIdSlot, cfg.imageCount, { upscale_type: "v7_2x_creative" }),
                                        },
                                    ],
                                },
                            },
                            {
                                content: "Pan",
                                submenu: {
                                    options: [
                                        { arrow: "↑", dir: "up" },
                                        { arrow: "↓", dir: "down" },
                                        { arrow: "←", dir: "left" },
                                        { arrow: "→", dir: "right" },
                                    ].map(({ arrow, dir }) => ({
                                        content: arrow,
                                        callback: () => addJobNodes(this, "MJ_Pan", cfg.jobIdSlot, cfg.imageCount, { direction: dir }),
                                    })),
                                },
                            },
                        ],
                    },
                });
            }

            options.unshift(...menuItems);
        };
    },
});

function addJobNodes(sourceNode, nodeType, jobIdSlot, count, widgetOverrides = {}) {
    const graph = app.graph;
    const gap = 150;
    const startX = sourceNode.pos[0] + sourceNode.size[0] + 200;
    const startY = sourceNode.pos[1];

    for (let i = 0; i < count; i++) {
        const newNode = LiteGraph.createNode(nodeType);
        if (!newNode) return;
        graph.add(newNode);

        newNode.pos = [startX, startY + i * (newNode.size[1] + gap)];

        // job_id 출력 → 새 노드의 job_id 입력(슬롯 0) 연결
        sourceNode.connect(jobIdSlot, newNode, 0);

        // index 위젯 설정
        const indexWidget = newNode.widgets?.find(w => w.name === "index");
        if (indexWidget) indexWidget.value = i;

        // widgetOverrides 적용 (strong, direction 등)
        for (const [name, value] of Object.entries(widgetOverrides)) {
            const w = newNode.widgets?.find(w => w.name === name);
            if (w) w.value = value;
        }
    }

    graph.setDirtyCanvas(true, true);
}

function addImageNodes(sourceNode, nodeType, count, jobIdSlot) {
    const graph = app.graph;
    const gap = 150;
    const startX = sourceNode.pos[0] + sourceNode.size[0] + 200;
    const startY = sourceNode.pos[1];

    let maxX = startX;
    let maxY = startY;

    if (count === 1) {
        const newNode = LiteGraph.createNode(nodeType);
        if (!newNode) return;
        graph.add(newNode);
        newNode.pos = [startX, startY];
        sourceNode.connect(0, newNode, 0);
        if (nodeType === "SaveImage" && jobIdSlot >= 0) {
            sourceNode.connect(jobIdSlot, newNode, 1);
        }
        maxX = startX + newNode.size[0];
        maxY = startY + newNode.size[1];
    } else {
        for (let i = 0; i < count; i++) {
            const col = i % 2;
            const row = Math.floor(i / 2);

            const newNode = LiteGraph.createNode(nodeType);
            if (!newNode) return;

            graph.add(newNode);

            const w = newNode.size[0];
            const h = newNode.size[1];
            newNode.pos = [
                startX + col * (w + gap),
                startY + row * (h + gap),
            ];

            sourceNode.connect(i, newNode, 0);
            if (nodeType === "SaveImage" && jobIdSlot >= 0) {
                sourceNode.connect(jobIdSlot, newNode, 1);
            }

            maxX = Math.max(maxX, newNode.pos[0] + w);
            maxY = Math.max(maxY, newNode.pos[1] + h);
        }
    }

    graph.setDirtyCanvas(true, true);
}
