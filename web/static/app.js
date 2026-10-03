const RANGE_HINT = "留空表示整份。只填一边时，另一边取文档的起端或末端。";

function pageRange(hint) {
  return [
    { key: "page_start", label: "起始页", placeholder: "全部" },
    { key: "page_end", label: "结束页", placeholder: "全部", hint: hint || RANGE_HINT },
  ];
}

const TOOLS = [
  {
    id: "preview",
    name: "预览",
    blurb: "按页查看一份 PDF。可以对正在看的这一页加水印、提取文字、旋转或删除。",
    main: [],
    advanced: [],
  },
  {
    id: "to_text",
    name: "转文字",
    blurb: "识别每一页上的文字，收成一份文本。",
    main: [],
    advanced: [
      ...pageRange(),
      { key: "skip_pages", label: "跳过页", placeholder: "1, 4, 5", hint: "列举页码，不写区间。范围外的页码会忽略。" },
      { key: "min_text_length", label: "最短文字长度", value: "50", hint: "少于此字数的页不写入。" },
    ],
  },
  {
    id: "to_image",
    name: "转图片",
    blurb: "把每一页存成一张图片。可以在页面里翻看，也可以打包下载。",
    main: [],
    advanced: [
      ...pageRange(),
      { key: "image_format", label: "格式", kind: "select", options: ["png", "jpg"], value: "png" },
      { key: "dpi", label: "清晰度", value: "200", hint: "数字越大，图片越清晰。" },
    ],
  },
  {
    id: "split",
    name: "拆分",
    blurb: "按页切开，得到多份 PDF，完成后打包下载。",
    main: [{ key: "pages_per_file", label: "每份页数", value: "1" }],
    advanced: pageRange(),
  },
  {
    id: "merge",
    name: "合并",
    blurb: "按名单从上到下的顺序，接成一份 PDF。",
    main: [],
    advanced: [],
  },
  {
    id: "delete",
    name: "删页",
    blurb: "去掉填写的页，另存一份 PDF。",
    main: [{ key: "delete_pages", label: "要删除的页码", placeholder: "1, 4, 5", hint: "列举页码，不写区间。超出文档的页码会忽略。" }],
    advanced: pageRange("留空表示整份。填写后，结果只包含这一段，并去掉要删除的页。"),
  },
  {
    id: "compress",
    name: "压缩",
    blurb: "得到一份体积更小的 PDF。",
    main: [],
    advanced: [
      ...pageRange("留空表示整份。填写后，结果只包含这一段。"),
      {
        key: "compression_level",
        label: "压缩级别",
        value: "3",
        hint: "1 清理结构，3 优化图片，5 更小，图片也可能更模糊。",
      },
    ],
  },
  {
    id: "to_word",
    name: "转 Word",
    blurb: "使用 PDF 里已经有的文字和图片。只有扫描图像的页会先识别，再写入文档。",
    main: [],
    advanced: [...pageRange(), { key: "include_images", label: "包含图片", kind: "check", checked: true }],
  },
  {
    id: "to_excel",
    name: "转 Excel",
    blurb: "使用 PDF 里已经有的文字。只有扫描图像的页会先识别，再按行写入。",
    main: [],
    advanced: [
      ...pageRange(),
      {
        key: "table_only",
        label: "只导出表格",
        kind: "check",
        checked: false,
        hint: "有文字层的页只保留表格。扫描页仍写入识别出的文字。",
      },
    ],
  },
  {
    id: "rotate",
    name: "旋转",
    blurb: "把页面顺时针转一个角度，另存一份 PDF。",
    main: [
      {
        key: "angle",
        label: "角度",
        kind: "select",
        options: ["90", "180", "270"],
        value: "90",
        hint: "顺时针。",
      },
    ],
    advanced: pageRange("留空表示整份。填写后，只转这一段，其余页不变。"),
  },
  {
    id: "watermark",
    name: "水印",
    blurb: "在页面上加上一条斜放的文字，另存一份 PDF。",
    main: [{ key: "watermark_text", label: "水印文字", kind: "text", placeholder: "草稿" }],
    advanced: pageRange("留空表示整份。填写后，只加在这一段，其余页不变。"),
  },
  {
    id: "encrypt",
    name: "加密",
    blurb: "给 PDF 加上口令。没有口令就打不开。",
    main: [{ key: "password", label: "口令", kind: "secret" }],
    advanced: [],
  },
  {
    id: "decrypt",
    name: "解密",
    blurb: "用口令去掉加密，另存一份没有口令的 PDF。",
    main: [{ key: "password", label: "口令", kind: "secret" }],
    advanced: [],
  },
];

const STATUS = {
  queued: "等候",
  running: "进行中",
  pending: "等候",
  completed: "完成",
  failed: "失败",
  cancelled: "已取消",
  stopped: "已停止",
};

const ICONS = {
  preview: '<path d="M6 4h9l3 3v13H6zM15 4v3h3M9 11h6M9 15h4"/>',
  to_text: '<path d="M7 3.5h7l4.5 4.5V20H7z"/><path d="M14 3.5V8h4.5M10 12h5M10 16h3"/>',
  to_image: '<rect x="4" y="5" width="16" height="14" rx="2"/><path d="M8 15l2.5-2.5L14 16l2-2 2 2"/>',
  split: '<path d="M5 6h6v12H5zM13 6h6v12h-6"/>',
  merge: '<path d="M7 7h4v10H7zM13 7h4v10h-4M4 12h16"/>',
  delete: '<path d="M7 4h10v16H7zM10 9v6M14 9v6"/>',
  compress: '<path d="M8 8L4 12l4 4M16 8l4 4-4 4M4 12h16"/>',
  to_word: '<path d="M7 4h8l4 4v12H7zM15 4v4h4M9 13l1.2 4L12 13l1.8 4L15 13"/>',
  to_excel: '<path d="M5 5h14v14H5zM5 10h14M5 15h14M10 5v14M15 5v14"/>',
  rotate: '<path d="M16 6a6.5 6.5 0 1 0 1.6 4.2M17 3.5V7h-3.5"/>',
  watermark: '<path d="M6 17l12-10M8 17h8"/>',
  encrypt: '<rect x="6" y="11" width="12" height="8" rx="1.5"/><path d="M9 11V8a3 3 0 0 1 6 0v3"/>',
  decrypt: '<rect x="6" y="11" width="12" height="8" rx="1.5"/><path d="M9 11V8a3 3 0 0 1 5.2-2"/>',
};

const STORAGE = "pdf-workbench-advanced";
const NAV_KEY = "pdf-workbench-nav";
const narrowQuery = window.matchMedia("(max-width: 860px)");

const drafts = {};
const readers = {};
let tasks = [];
let previews = [];
let openPreviewId = "";
let previewPage = 1;
let previewViewKey = "";
const seenPreview = {};
let current = "to_text";
let sending = false;

const nav = document.getElementById("nav");
const workspace = document.getElementById("workspace");
const addresses = document.getElementById("addresses");
const offline = document.getElementById("offline");
const modal = document.getElementById("modal");
const modalText = document.getElementById("modal-text");
const modalYes = document.getElementById("modal-yes");
const modalNo = document.getElementById("modal-no");

TOOLS.forEach((tool) => {
  drafts[tool.id] = [];
});

function el(tag, attrs, children) {
  const node = document.createElement(tag);
  Object.entries(attrs || {}).forEach(([key, value]) => {
    if (value == null || value === false) return;
    if (key === "class") node.className = value;
    else if (key === "text") node.textContent = value;
    else node.setAttribute(key, value);
  });
  (children || []).forEach((child) => {
    if (child) node.append(child);
  });
  return node;
}

function icon(name) {
  const wrap = document.createElement("span");
  wrap.className = "icon";
  wrap.innerHTML = `<svg viewBox="0 0 24 24" aria-hidden="true">${ICONS[name] || ""}</svg>`;
  return wrap;
}

function fieldInput(tool, field) {
  if (field.kind === "check") {
    const input = el("input", { id: `field-${tool.id}-${field.key}`, type: "checkbox" });
    input.checked = Boolean(field.checked);
    const box = el("label", { class: "check" }, [input, el("span", { text: field.label })]);
    if (!field.hint) return box;
    return el("div", { class: "field" }, [box, el("small", { class: "hint", text: field.hint })]);
  }
  if (field.kind === "select") {
    const select = el("select", { id: `field-${tool.id}-${field.key}` });
    field.options.forEach((option) => {
      const node = el("option", { value: option, text: option });
      if (option === field.value) node.selected = true;
      select.append(node);
    });
    const nodes = [el("span", { text: field.label }), select];
    if (field.hint) nodes.push(el("small", { class: "hint", text: field.hint }));
    return el("label", { class: "field" }, nodes);
  }
  if (field.kind === "text" || field.kind === "secret") {
    const input = el("input", {
      id: `field-${tool.id}-${field.key}`,
      type: field.kind === "secret" ? "password" : "text",
      placeholder: field.placeholder || "",
      value: field.value || "",
      autocomplete: "off",
    });
    const nodes = [el("span", { text: field.label }), input];
    if (field.hint) nodes.push(el("small", { class: "hint", text: field.hint }));
    return el("label", { class: "field" }, nodes);
  }
  const input = el("input", {
    id: `field-${tool.id}-${field.key}`,
    type: "text",
    inputmode: "numeric",
    placeholder: field.placeholder || "",
    value: field.value || "",
  });
  const nodes = [el("span", { text: field.label }), input];
  if (field.hint) nodes.push(el("small", { class: "hint", text: field.hint }));
  return el("label", { class: "field" }, nodes);
}

function fieldGroup(tool, fields) {
  return el("div", { class: "fields" }, fields.map((field) => fieldInput(tool, field)));
}

function buildNav() {
  TOOLS.forEach((tool) => {
    const button = el("button", {
      type: "button",
      class: "nav-item",
      "data-tool": tool.id,
      title: tool.name,
    });
    button.append(icon(tool.id), el("span", { class: "label", text: tool.name }));
    const mark = el("span", { class: "nav-mark", "data-mark": tool.id });
    mark.hidden = true;
    button.append(mark);
    button.addEventListener("click", () => selectTool(tool.id));
    nav.append(button);
  });
}

function buildPanels() {
  TOOLS.forEach((tool) => {
    const panel = el("section", { class: "panel", id: `panel-${tool.id}` });
    panel.hidden = true;
    const picker = el("div", { class: "picker" });
    const input = el("input", {
      class: "file-input",
      id: `files-${tool.id}`,
      type: "file",
      accept: ".pdf,application/pdf",
    });
    if (tool.id !== "preview") input.multiple = true;
    const pick = el("button", { type: "button", class: "pick", "data-act": "pick", "data-tool": tool.id, text: "选择文件" });
    picker.append(input, pick, el("ul", { class: "files", id: `list-${tool.id}` }));
    if (tool.id === "merge") picker.append(el("p", { class: "hint", text: "至少两份。用上移、下移调整顺序。" }));
    if (tool.id === "preview") picker.append(el("p", { class: "hint", text: "一次打开一份。打开后按页查看，操作只作用于当前这一页。" }));
    panel.append(el("h1", { text: tool.name }), el("p", { class: "blurb", text: tool.blurb }), picker);
    if (tool.main.length) panel.append(fieldGroup(tool, tool.main));
    if (tool.advanced.length) {
      const advanced = el("details", { class: "advanced" });
      advanced.append(el("summary", { text: "高级" }), fieldGroup(tool, tool.advanced));
      panel.append(advanced);
    }
    const reader = el("section", { class: "reader", id: `reader-${tool.id}` });
    reader.hidden = true;
    const start = el("button", {
      type: "button",
      class: "start",
      "data-act": "start",
      "data-tool": tool.id,
      text: tool.id === "preview" ? "打开" : "开始",
    });
    panel.append(el("p", { class: "form-error", id: `error-${tool.id}` }), start);
    if (tool.id === "preview") panel.append(el("div", { id: "preview-view" }));
    panel.append(
      el("div", { class: "task-head" }, [
        el("h2", { text: "任务" }),
        el("span", { class: "task-meta", text: "结束超过一天会自动删除" }),
      ]),
      el("div", { id: `tasks-${tool.id}` }),
      reader
    );
    workspace.append(panel);
    input.addEventListener("change", () => addFiles(tool.id, input));
  });
  restoreAdvanced();
  workspace.addEventListener("input", storeAdvanced);
  workspace.addEventListener("change", storeAdvanced);
}

function restoreAdvanced() {
  let stored = {};
  try {
    stored = JSON.parse(localStorage.getItem(STORAGE) || "{}");
  } catch (error) {
    stored = {};
  }
  TOOLS.forEach((tool) => {
    const values = stored[tool.id] || {};
    tool.main.concat(tool.advanced).forEach((field) => {
      const input = document.getElementById(`field-${tool.id}-${field.key}`);
      if (!input || values[field.key] == null) return;
      if (field.kind === "check") input.checked = Boolean(values[field.key]);
      else input.value = values[field.key];
    });
  });
}

function storeAdvanced() {
  const stored = {};
  TOOLS.forEach((tool) => {
    stored[tool.id] = {};
    tool.main.concat(tool.advanced).forEach((field) => {
      if (field.kind === "secret") return;
      const input = document.getElementById(`field-${tool.id}-${field.key}`);
      if (!input) return;
      stored[tool.id][field.key] = field.kind === "check" ? input.checked : input.value;
    });
  });
  localStorage.setItem(STORAGE, JSON.stringify(stored));
}

function selectTool(id) {
  current = id;
  TOOLS.forEach((tool) => {
    document.getElementById(`panel-${tool.id}`).hidden = tool.id !== id;
    const button = nav.querySelector(`[data-tool="${tool.id}"]`);
    if (tool.id === id) button.setAttribute("aria-current", "page");
    else button.removeAttribute("aria-current");
  });
  if (narrowQuery.matches) document.body.classList.add("collapsed");
}

function renderFiles(toolId) {
  const list = document.getElementById(`list-${toolId}`);
  list.replaceChildren();
  drafts[toolId].forEach((file, index) => {
    const actions = el("div", { class: "file-actions" });
    const up = el("button", { type: "button", class: "text-button", text: "上移" });
    const down = el("button", { type: "button", class: "text-button", text: "下移" });
    const remove = el("button", { type: "button", class: "text-button", text: "移除" });
    up.disabled = index === 0;
    down.disabled = index === drafts[toolId].length - 1;
    up.addEventListener("click", () => moveFile(toolId, index, -1));
    down.addEventListener("click", () => moveFile(toolId, index, 1));
    remove.addEventListener("click", () => {
      drafts[toolId].splice(index, 1);
      renderFiles(toolId);
    });
    actions.append(up, down, remove);
    list.append(el("li", { class: "file" }, [el("span", { class: "file-name", text: file.name }), actions]));
  });
}

function addFiles(toolId, input) {
  const picked = Array.from(input.files || []);
  const rejected = picked.find((file) => !file.name.toLowerCase().endsWith(".pdf"));
  const error = document.getElementById(`error-${toolId}`);
  if (rejected) {
    error.textContent = `只接受 PDF 文件：${rejected.name}`;
    input.value = "";
    return;
  }
  error.textContent = "";
  drafts[toolId].push(...picked);
  input.value = "";
  renderFiles(toolId);
}

function moveFile(toolId, index, delta) {
  const next = index + delta;
  const files = drafts[toolId];
  if (next < 0 || next >= files.length) return;
  const [file] = files.splice(index, 1);
  files.splice(next, 0, file);
  renderFiles(toolId);
}

function parsePages(value) {
  const raw = String(value || "").replace(/[，、；;]/g, ",").trim();
  if (!raw) return [];
  const pages = [];
  raw.split(/[\s,]+/).forEach((part) => {
    if (!part) return;
    if (part.includes("-") || part.includes("—") || part.includes("－")) {
      throw new Error("请列举页码，例如 1, 4, 5");
    }
    if (!/^[1-9]\d*$/.test(part)) throw new Error("页码须是从 1 开始的正整数");
    pages.push(Number(part));
  });
  return pages;
}

function parseOptionalPage(value, label) {
  const text = String(value || "").trim();
  if (!text) return null;
  if (!/^[1-9]\d*$/.test(text)) throw new Error(`${label}须是从 1 开始的正整数`);
  return Number(text);
}

function collectParams(tool) {
  const params = {};
  tool.main.concat(tool.advanced).forEach((field) => {
    const input = document.getElementById(`field-${tool.id}-${field.key}`);
    if (field.kind === "check") params[field.key] = input.checked;
    else if (field.kind === "secret") params[field.key] = input.value;
    else if (field.kind === "select") params[field.key] = input.value;
    else params[field.key] = input.value.trim();
  });
  return params;
}

function validate(tool, params, files) {
  if (!files.length) return "请选择 PDF 文件";
  const rejected = files.find((file) => !file.name.toLowerCase().endsWith(".pdf"));
  if (rejected) return `只接受 PDF 文件：${rejected.name}`;
  if (tool.id === "merge" && files.length < 2) return "合并至少需要两份 PDF";
  if (tool.id === "preview" && files.length !== 1) return "预览一次打开一份 PDF";
  try {
    if ("page_start" in params || "page_end" in params) {
      const start = parseOptionalPage(params.page_start, "起始页");
      const end = parseOptionalPage(params.page_end, "结束页");
      if (start != null && end != null && start > end) return "起始页不能大于结束页";
      params.page_start = start;
      params.page_end = end;
    }
    if ("skip_pages" in params) params.skip_pages = parsePages(params.skip_pages).join(",");
    if ("delete_pages" in params) {
      const pages = parsePages(params.delete_pages);
      if (!pages.length) {
        return String(params.delete_pages || "").trim() ? "请列举页码，例如 1, 4, 5" : "请填写要删除的页码";
      }
      params.delete_pages = pages.join(",");
    }
    if ("min_text_length" in params) {
      const text = String(params.min_text_length || "").trim();
      if (text && !/^\d+$/.test(text)) return "最短文字长度须是大于等于 0 的整数";
      params.min_text_length = text ? Number(text) : null;
    }
    if ("dpi" in params) {
      const text = String(params.dpi || "").trim();
      if (text && !/^[1-9]\d*$/.test(text)) return "清晰度须是正整数";
      params.dpi = text ? Number(text) : null;
    }
    if ("pages_per_file" in params) {
      const text = String(params.pages_per_file || "").trim();
      if (text && !/^[1-9]\d*$/.test(text)) return "每份页数须是正整数";
      params.pages_per_file = text ? Number(text) : null;
    }
    if ("compression_level" in params) {
      const text = String(params.compression_level || "").trim();
      if (text && !/^[1-5]$/.test(text)) return "压缩级别须在 1 到 5 之间";
      params.compression_level = text ? Number(text) : null;
    }
    if ("angle" in params && !["90", "180", "270"].includes(String(params.angle))) {
      return "角度只接受 90、180 或 270";
    }
    if ("angle" in params) params.angle = Number(params.angle);
    if ("watermark_text" in params) {
      if (!params.watermark_text) return "请填写水印文字";
      if ([...params.watermark_text].length > 80) return "水印文字不能超过 80 个字";
    }
    if ("password" in params && !params.password.trim()) return "请填写口令";
  } catch (error) {
    return error.message;
  }
  return "";
}

async function startTool(tool) {
  const error = document.getElementById(`error-${tool.id}`);
  const params = collectParams(tool);
  const message = validate(tool, params, drafts[tool.id]);
  if (message) {
    error.textContent = message;
    return;
  }
  error.textContent = "";
  const body = new FormData();
  if (tool.id !== "preview") {
    body.set("tool", tool.id);
    body.set("params", JSON.stringify(params));
  }
  drafts[tool.id].forEach((file) => body.append("file", file, file.name));
  sending = true;
  document.querySelectorAll(".start").forEach((button) => {
    button.disabled = true;
  });
  try {
    const response = await fetch(tool.id === "preview" ? "/api/previews" : "/api/tasks", { method: "POST", body });
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.error || "处理失败");
    drafts[tool.id] = [];
    renderFiles(tool.id);
    if (tool.id === "preview" && payload.preview) {
      openPreviewId = payload.preview.id;
      previewPage = 1;
      delete seenPreview[openPreviewId];
    }
    await refresh();
  } catch (fetchError) {
    error.textContent = fetchError.message || "无法连接工作台";
  } finally {
    sending = false;
    document.querySelectorAll(".start").forEach((button) => {
      button.disabled = false;
    });
  }
}

function stamp(value) {
  return (value || "").replace("T", " ");
}

function renderTasks() {
  TOOLS.forEach((tool) => {
    const host = document.getElementById(`tasks-${tool.id}`);
    const mine = tasks.filter((task) => task.tool === tool.id);
    host.replaceChildren();
    if (!mine.length) {
      host.append(el("p", { class: "empty", text: "还没有任务" }));
      return;
    }
    const list = el("div", { class: "tasks" });
    mine.forEach((task) => list.append(renderTask(task)));
    host.append(list);
    const reader = readers[tool.id];
    if (reader && !mine.some((task) => task.id === reader.taskId && task.items.some((item) => item.id === reader.itemId && item.preview))) {
      hideReader(tool.id);
    }
  });
  TOOLS.forEach((tool) => {
    const mark = nav.querySelector(`[data-mark="${tool.id}"]`);
    const mine = tasks.filter((task) => task.tool === tool.id);
    mark.hidden = true;
    mark.className = "nav-mark";
    if (mine.some((task) => task.status === "running")) {
      mark.hidden = false;
      mark.classList.add("running");
    } else if (mine.some((task) => task.status === "queued")) {
      mark.hidden = false;
      mark.classList.add("waiting");
    }
  });
}

function renderTask(task) {
  const meta = [STATUS[task.status] || task.status, stamp(task.finished_at || task.created_at)];
  if (task.stop_requested && task.status === "running") meta[0] = "正在停止";
  const head = el("div", { class: "task-meta", text: meta.join(" · ") });
  const actions = el("div", { class: "task-actions" });
  if (task.status === "queued") {
    const cancel = el("button", { type: "button", class: "text-button", text: "取消" });
    cancel.addEventListener("click", () => postCancel(task.id));
    actions.append(cancel);
  } else if (task.status === "running") {
    const stop = el("button", { type: "button", class: "text-button", text: task.stop_requested ? "正在停止" : "停止" });
    stop.disabled = task.stop_requested;
    stop.addEventListener("click", () => stopTask(task.id));
    actions.append(stop);
  }
  const box = el("article", { class: "task" }, [head, actions]);
  if (task.tool === "merge") {
    box.append(el("p", { class: "item-meta", text: task.inputs.map((item) => item.name).join("、") }));
  }
  if (task.error) box.append(el("p", { class: "item-error", text: task.error }));
  task.items.forEach((item, index) => box.append(renderItem(task, item, index)));
  return box;
}

function renderItem(task, item, index) {
  const bits = [item.name, STATUS[item.status] || item.status];
  if (item.status === "running" && (task.tool === "to_text" || task.tool === "to_word" || task.tool === "to_excel") && item.page_count) {
    bits.push(`第 ${item.page} / ${item.page_count} 页`);
  } else if (item.status === "running" && task.items.length > 1) {
    bits.push(`第 ${index + 1} / ${task.items.length} 份`);
  }
  if (typeof item.ratio === "number") bits.push(`压缩率 ${item.ratio}%`);
  const row = el("div", { class: "item" }, [el("div", { class: "item-name", text: bits.join(" · ") })]);
  if (item.error) row.append(el("p", { class: "item-error", text: item.error }));
  (item.page_errors || []).forEach((entry) => {
    row.append(el("p", { class: "item-error", text: `第 ${entry.page} 页：${entry.message}` }));
  });
  const actions = el("div", { class: "item-actions" });
  if (item.download) {
    actions.append(el("a", {
      class: "text-button",
      href: `/api/tasks/${task.id}/items/${item.id}/download`,
      text: "下载",
    }));
  }
  if (item.preview) {
    const read = el("button", { type: "button", class: "text-button", text: item.image_count ? "翻看" : "阅读" });
    read.addEventListener("click", () => openReader(task, item));
    actions.append(read);
  }
  const terminal = ["completed", "failed", "cancelled", "stopped"].includes(task.status);
  if (item.download && terminal) {
    const remove = el("button", { type: "button", class: "text-button", text: "删除" });
    remove.addEventListener("click", () => removeItem(task, item));
    actions.append(remove);
  }
  if (actions.childNodes.length) row.append(actions);
  return row;
}

async function openReader(task, item) {
  if (item.image_count) {
    showImages(task, item, 1);
    return;
  }
  const reader = document.getElementById(`reader-${task.tool}`);
  try {
    const response = await fetch(`/api/tasks/${task.id}/items/${item.id}/text`);
    if (!response.ok) {
      const payload = await response.json();
      throw new Error(payload.error || "结果不存在");
    }
    const text = await response.text();
    readers[task.tool] = { taskId: task.id, itemId: item.id };
    reader.hidden = false;
    reader.replaceChildren(
      el("div", { class: "reader-head" }, [
        el("h2", { text: item.name }),
        (() => {
          const close = el("button", { type: "button", class: "text-button", text: "关闭" });
          close.addEventListener("click", () => hideReader(task.tool));
          return close;
        })(),
      ]),
      el("pre", { text })
    );
    reader.scrollIntoView({ block: "nearest" });
  } catch (error) {
    document.getElementById(`error-${task.tool}`).textContent = error.message;
  }
}

function showImages(task, item, page) {
  const reader = document.getElementById(`reader-${task.tool}`);
  const total = item.image_count;
  readers[task.tool] = { taskId: task.id, itemId: item.id, page };
  reader.hidden = false;
  const prev = el("button", { type: "button", class: "text-button", text: "上一页" });
  const next = el("button", { type: "button", class: "text-button", text: "下一页" });
  prev.disabled = page <= 1;
  next.disabled = page >= total;
  prev.addEventListener("click", () => showImages(task, item, page - 1));
  next.addEventListener("click", () => showImages(task, item, page + 1));
  const image = el("img", {
    class: "page-view",
    alt: `第 ${page} 页`,
    src: `/api/tasks/${task.id}/items/${item.id}/images/${page}`,
  });
  const note = el("p", { class: "item-error" });
  note.hidden = true;
  image.addEventListener("error", () => {
    note.hidden = false;
    note.textContent = "这一页无法显示";
  });
  reader.replaceChildren(
    el("div", { class: "reader-head" }, [
      el("h2", { text: item.name }),
      (() => {
        const close = el("button", { type: "button", class: "text-button", text: "关闭" });
        close.addEventListener("click", () => hideReader(task.tool));
        return close;
      })(),
    ]),
    el("div", { class: "reader-nav" }, [
      prev,
      el("span", { text: `第 ${page} / ${total} 页` }),
      next,
    ]),
    image,
    note
  );
  if (page === 1) reader.scrollIntoView({ block: "nearest" });
}

function hideReader(toolId) {
  delete readers[toolId];
  const reader = document.getElementById(`reader-${toolId}`);
  reader.hidden = true;
  reader.replaceChildren();
}

function ask(text, yesLabel) {
  modalText.textContent = text;
  modalYes.textContent = yesLabel;
  modal.hidden = false;
  return new Promise((resolve) => {
    const finish = (value) => {
      modal.hidden = true;
      modalYes.removeEventListener("click", onYes);
      modalNo.removeEventListener("click", onNo);
      resolve(value);
    };
    const onYes = () => finish(true);
    const onNo = () => finish(false);
    modalYes.addEventListener("click", onYes);
    modalNo.addEventListener("click", onNo);
  });
}

async function stopTask(taskId) {
  const agreed = await ask("停止正在处理的这一份？已完成的会留下，这一份不会保留。", "停止");
  if (!agreed) return;
  await postCancel(taskId);
}

async function removeItem(task, item) {
  const agreed = await ask(`删除「${item.name}」的结果？此操作不能撤销。`, "删除");
  if (!agreed) return;
  const response = await fetch(`/api/tasks/${task.id}/items/${item.id}`, { method: "DELETE" });
  const payload = await response.json();
  if (!response.ok) {
    document.getElementById(`error-${task.tool}`).textContent = payload.error || "处理失败";
    return;
  }
  await refresh();
}

async function postCancel(taskId) {
  const response = await fetch(`/api/tasks/${taskId}/cancel`, { method: "POST" });
  const payload = await response.json();
  if (!response.ok) {
    const task = tasks.find((item) => item.id === taskId);
    if (task) document.getElementById(`error-${task.tool}`).textContent = payload.error || "处理失败";
    return;
  }
  await refresh();
}

function renderAddresses(data) {
  addresses.replaceChildren();
  addresses.append(el("p", { text: `这台电脑 ${data.local}` }));
  if (!data.lan || !data.lan.length) {
    addresses.append(el("p", { text: "当前只能在这台电脑上打开" }));
    return;
  }
  data.lan.forEach((url) => {
    const link = el("a", { href: url, text: url });
    const line = el("p", { text: "局域网 " });
    line.append(link);
    addresses.append(line);
  });
}

async function refresh() {
  try {
    const response = await fetch("/api/state");
    if (!response.ok) throw new Error();
    const data = await response.json();
    tasks = data.tasks || [];
    previews = data.previews || [];
    if (openPreviewId && !previews.some((item) => item.id === openPreviewId)) {
      openPreviewId = "";
      previewPage = 1;
    }
    offline.hidden = true;
    renderAddresses(data);
    renderTasks();
    renderPreview();
  } catch (error) {
    offline.hidden = false;
  }
}

function adjustPreviewPage(preview) {
  const seen = seenPreview[preview.id];
  if (seen && seen.revision !== preview.revision && preview.last_action === "delete" && previewPage > preview.last_page) {
    previewPage -= 1;
  }
  if (previewPage > preview.page_count) previewPage = preview.page_count || 1;
  if (previewPage < 1) previewPage = 1;
  seenPreview[preview.id] = { revision: preview.revision };
}

function previewStatusText(preview) {
  if (preview.status !== "busy") return "";
  const job = tasks.find((item) => item.preview_id === preview.id && (item.status === "queued" || item.status === "running"));
  const labels = { rotate: "旋转", watermark: "水印", delete: "删除", text: "提取文字" };
  const label = labels[preview.action] || "处理";
  const page = preview.action_page || previewPage;
  return `${job && job.status === "queued" ? "等候" : "正在"}${label} · 第 ${page} 页`;
}

function previewChoices() {
  if (!previews.length) return el("p", { class: "empty", text: "还没有打开的 PDF" });
  if (previews.length === 1 && previews[0].id === openPreviewId) return null;
  const list = el("div", { class: "preview-list" });
  previews.forEach((item) => {
    const button = el("button", { type: "button", class: "text-button", text: item.name });
    button.disabled = item.id === openPreviewId;
    button.addEventListener("click", () => {
      openPreviewId = item.id;
      previewPage = 1;
      previewViewKey = "";
      renderPreview();
    });
    list.append(button);
  });
  return list;
}

function previewViewer(preview, typed) {
  const busy = preview.status === "busy";
  const prev = el("button", { type: "button", class: "text-button", text: "上一页", disabled: previewPage <= 1 });
  const next = el("button", { type: "button", class: "text-button", text: "下一页", disabled: previewPage >= preview.page_count });
  prev.addEventListener("click", () => {
    previewPage -= 1;
    renderPreview();
  });
  next.addEventListener("click", () => {
    previewPage += 1;
    renderPreview();
  });
  const image = el("img", {
    class: "page-view",
    alt: `第 ${previewPage} 页`,
    src: `/api/previews/${preview.id}/pages/${previewPage}?v=${preview.revision}`,
  });
  const note = el("p", { class: "item-error", text: "这一页无法显示" });
  note.hidden = true;
  image.addEventListener("error", () => {
    note.hidden = false;
  });
  const rotate = el("button", { type: "button", class: "text-button", text: "旋转", disabled: busy });
  const watermark = el("input", {
    id: "preview-watermark",
    type: "text",
    placeholder: "水印文字",
    value: typed,
    autocomplete: "off",
    disabled: busy,
  });
  const stampButton = el("button", { type: "button", class: "text-button", text: "加水印", disabled: busy });
  const extract = el("button", { type: "button", class: "text-button", text: "提取文字", disabled: busy });
  const remove = el("button", { type: "button", class: "text-button", text: "删除这一页", disabled: busy });
  rotate.addEventListener("click", () => previewAct("rotate"));
  stampButton.addEventListener("click", () => {
    const value = watermark.value.trim();
    const error = document.getElementById("error-preview");
    if (!value) {
      error.textContent = "请填写水印文字";
      return;
    }
    if ([...value].length > 80) {
      error.textContent = "水印文字不能超过 80 个字";
      return;
    }
    error.textContent = "";
    previewAct("watermark", { watermark_text: value });
  });
  extract.addEventListener("click", () => previewAct("text"));
  remove.addEventListener("click", async () => {
    const agreed = await ask(`删除第 ${previewPage} 页？此操作不能撤销。`, "删除");
    if (agreed) previewAct("delete");
  });
  const download = el("a", { class: "text-button", href: `/api/previews/${preview.id}/download`, text: "下载" });
  const close = el("button", { type: "button", class: "text-button", text: "关闭", disabled: busy });
  close.addEventListener("click", () => closePreview(preview.id));
  const statusText = previewStatusText(preview);
  const status = el("p", { class: "task-meta", text: statusText });
  status.hidden = !statusText;
  const nodes = [
    el("div", { class: "reader-head" }, [
      el("h2", { text: preview.name }),
      el("div", { class: "reader-nav" }, [download, close]),
    ]),
    el("div", { class: "reader-nav" }, [
      prev,
      el("span", { text: `第 ${previewPage} / ${preview.page_count} 页` }),
      next,
    ]),
    image,
    note,
    el("div", { class: "preview-actions" }, [rotate, watermark, stampButton, extract, remove]),
    status,
  ];
  if (preview.error) nodes.push(el("p", { class: "item-error", text: preview.error }));
  if (preview.text_page === previewPage && preview.status === "ready") {
    nodes.push(el("pre", { class: "preview-text", text: preview.text || "这一页没有文字" }));
  }
  return el("section", { class: "reader" }, nodes);
}

function renderPreview() {
  const host = document.getElementById("preview-view");
  if (!host) return;
  const preview = previews.find((item) => item.id === openPreviewId);
  if (!preview) {
    previewViewKey = "";
    host.replaceChildren(previewChoices());
    return;
  }
  adjustPreviewPage(preview);
  const key = [
    previews.map((item) => `${item.id}:${item.revision}:${item.status}`).join(","),
    preview.revision,
    preview.page_count,
    preview.status,
    preview.error,
    preview.action,
    preview.action_page,
    preview.text_page,
    preview.text,
    previewPage,
  ].join("\n");
  if (key === previewViewKey) return;
  const draft = document.getElementById("preview-watermark");
  const typed = draft ? draft.value : "";
  const focused = Boolean(draft && document.activeElement === draft);
  previewViewKey = key;
  const choices = previewChoices();
  host.replaceChildren(previewViewer(preview, typed));
  if (choices) host.append(choices);
  if (focused) {
    const input = document.getElementById("preview-watermark");
    if (input) input.focus();
  }
}

async function previewAct(action, extra) {
  const response = await fetch(`/api/previews/${openPreviewId}/actions`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(Object.assign({ action, page: previewPage }, extra || {})),
  });
  const payload = await response.json();
  const error = document.getElementById("error-preview");
  if (!response.ok) {
    if (error) error.textContent = payload.error || "处理失败";
    return;
  }
  if (error) error.textContent = "";
  await refresh();
}

async function closePreview(id) {
  const response = await fetch(`/api/previews/${id}`, { method: "DELETE" });
  const payload = await response.json();
  if (!response.ok) {
    const error = document.getElementById("error-preview");
    if (error) error.textContent = payload.error || "处理失败";
    return;
  }
  if (openPreviewId === id) {
    openPreviewId = "";
    previewPage = 1;
  }
  await refresh();
}

function applyNav() {
  const stored = localStorage.getItem(NAV_KEY) === "1";
  document.body.classList.toggle("collapsed", narrowQuery.matches ? true : stored);
}

document.getElementById("collapse").addEventListener("click", () => {
  const collapsed = !document.body.classList.contains("collapsed");
  document.body.classList.toggle("collapsed", collapsed);
  if (!narrowQuery.matches) localStorage.setItem(NAV_KEY, collapsed ? "1" : "0");
});

document.getElementById("menu").addEventListener("click", () => {
  document.body.classList.remove("collapsed");
});

document.getElementById("backdrop").addEventListener("click", () => {
  document.body.classList.add("collapsed");
});

document.addEventListener("click", (event) => {
  const start = event.target.closest("[data-act='start']");
  if (start && !sending) {
    const tool = TOOLS.find((item) => item.id === start.getAttribute("data-tool"));
    startTool(tool);
    return;
  }
  const pick = event.target.closest("[data-act='pick']");
  if (pick) document.getElementById(`files-${pick.getAttribute("data-tool")}`).click();
});

document.addEventListener("keydown", (event) => {
  if (event.key === "Escape" && !modal.hidden) modalNo.click();
});

if (narrowQuery.addEventListener) narrowQuery.addEventListener("change", applyNav);
else narrowQuery.addListener(applyNav);

buildNav();
buildPanels();
applyNav();
selectTool("to_text");
refresh();
setInterval(refresh, 1000);
