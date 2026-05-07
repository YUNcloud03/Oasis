let API_BASE = localStorage.getItem("oasis.api.base") || "http://127.0.0.1:8001";
const STORAGE = {
  appToken: "oasis.app.token",
  model: "oasis.openai.model",
  background: "oasis.structured.background",
  supplements: "oasis.match.supplements",
  authToken: "oasis.auth.token",
  userName: "oasis.user.name",
  userEmail: "oasis.user.email"
};

const SECTION_LABELS = {
  education: "學歷",
  courses: "修過的課",
  experiences: "工作經驗",
  projects: "專案",
  certifications: "證照",
  languages: "語言",
  others: "其他"
};

const SECTION_HINTS = {
  education: "例：國立台灣大學 資訊管理學系",
  courses: "例：資料庫系統、統計學、機器學習",
  experiences: "例：資料分析實習生",
  projects: "例：求職推薦系統專案",
  certifications: "例：Google Data Analytics Certificate",
  languages: "例：英文 TOEIC 850、日文 N3",
  others: "例：社團、競賽、志工、作品集"
};

const DEFAULT_BACKGROUND = Object.fromEntries(Object.keys(SECTION_LABELS).map((key) => [key, []]));
const applications = readJson("oasis.garden.applications", []);
let matchResult = null;

const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => Array.from(document.querySelectorAll(selector));

const store = {
  get(key, fallback = "") {
    try {
      return localStorage.getItem(key) || fallback;
    } catch {
      return fallback;
    }
  },
  set(key, value) {
    try {
      localStorage.setItem(key, value);
    } catch {}
  },
  remove(key) {
    try {
      localStorage.removeItem(key);
    } catch {}
  }
};

function readJson(key, fallback) {
  try {
    return JSON.parse(store.get(key, ""));
  } catch {
    return fallback;
  }
}

function writeJson(key, value) {
  store.set(key, JSON.stringify(value));
}

function getBackground() {
  return readJson(STORAGE.background, structuredClone(DEFAULT_BACKGROUND));
}

function saveBackground(background) {
  writeJson(STORAGE.background, background);
}

function getSupplements() {
  return readJson(STORAGE.supplements, []);
}

function saveSupplements(supplements) {
  writeJson(STORAGE.supplements, supplements);
}

function saveApplications() {
  writeJson("oasis.garden.applications", applications);
}

function getAppToken() {
  return store.get(STORAGE.appToken);
}

function getModel() {
  return store.get(STORAGE.model, "gpt-4o");
}

async function apiPost(path, payload) {
  const token = getAppToken();
  if (!token) {
    throw new Error("請先到「設定」輸入 OASIS App Token。這不是 OpenAI API Key。");
  }
  const response = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`
    },
    body: JSON.stringify({ ...payload, model: getModel() })
  });
  if (!response.ok) {
    let message = `HTTP ${response.status}`;
    try {
      const body = await response.json();
      message = body.detail || body.error || message;
    } catch {}
    throw new Error(Array.isArray(message) ? message.map((item) => item.msg || JSON.stringify(item)).join("; ") : message);
  }
  const data = await response.json();
  return data.content || "";
}

async function apiV1(path, options = {}) {
  const token = store.get(STORAGE.authToken);
  const headers = {
    "Content-Type": "application/json",
    ...(options.headers || {})
  };
  if (token) headers.Authorization = `Bearer ${token}`;
  const response = await fetch(`${API_BASE}/api/v1${path}`, { ...options, headers });
  if (!response.ok) {
    let message = `HTTP ${response.status}`;
    try {
      const body = await response.json();
      message = body.detail || message;
    } catch {}
    throw new Error(Array.isArray(message) ? message.map((item) => item.msg || JSON.stringify(item)).join("; ") : message);
  }
  if (response.status === 204) return null;
  return response.json();
}

function escapeHtml(value) {
  return String(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

function stripInternalTags(value) {
  // Remove [section-N] style internal IDs that occasionally leak into output.
  return String(value || "").replace(/\s*\[[a-z]+-\d+\]\s*/g, " ").replace(/\s+/g, " ").trim();
}

function inlineMarkdown(value) {
  return escapeHtml(stripInternalTags(value))
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    .replace(/\*(.+?)\*/g, "<em>$1</em>");
}

function markdownToHtml(markdown) {
  const lines = String(markdown || "").split("\n");
  const output = [];
  let listOpen = false;
  const closeList = () => {
    if (listOpen) {
      output.push("</ul>");
      listOpen = false;
    }
  };
  for (const rawLine of lines) {
    const line = rawLine.trimEnd();
    if (line.startsWith("### ")) {
      closeList();
      output.push(`<h3>${escapeHtml(stripInternalTags(line.slice(4)))}</h3>`);
    } else if (line.startsWith("## ")) {
      closeList();
      output.push(`<h2>${escapeHtml(stripInternalTags(line.slice(3)))}</h2>`);
    } else if (/^[-*] /.test(line)) {
      if (!listOpen) {
        output.push("<ul>");
        listOpen = true;
      }
      output.push(`<li>${inlineMarkdown(line.slice(2))}</li>`);
    } else if (!line.trim()) {
      closeList();
    } else {
      closeList();
      output.push(`<p>${inlineMarkdown(line)}</p>`);
    }
  }
  closeList();
  return output.join("");
}

function setView(name) {
  $$(".content-panel").forEach((panel) => panel.classList.toggle("hidden", panel.id !== `${name}View`));
  $$(".nav-item").forEach((button) => button.classList.toggle("active", button.dataset.view === name));
}

function updateUserIdentity() {
  const name = store.get(STORAGE.userName, "使用者");
  const email = store.get(STORAGE.userEmail, "");
  const avatar = (name || email || "O").trim().slice(0, 2).toUpperCase();
  $("#userDisplayName").textContent = name;
  $("#userAvatar").textContent = avatar;
  setHint("#authStatus", email ? `目前登入：${name}（${email}）` : "尚未登入。", email ? "success" : "");
}

function updateOsiMessage(message) {
  const node = $("#osiCompanionMessage");
  if (node) node.textContent = message;
}

function updateFitScore(score, text) {
  const ring = $("#fitScoreRing");
  const value = $("#fitScoreValue");
  if (!ring || !value) return;
  if (typeof score !== "number") {
    ring.classList.add("is-empty");
    ring.style.setProperty("--score", 0);
    value.textContent = "--";
  } else {
    ring.classList.remove("is-empty");
    ring.style.setProperty("--score", score);
    value.textContent = String(score);
  }
  $("#fitScoreText").textContent = text;
}

function calculateFitScore(result) {
  const direct = result?.direct?.length || 0;
  const implicit = result?.implicit?.length || 0;
  const gap = result?.gap?.length || 0;
  const total = Math.max(1, direct + implicit + gap);
  return Math.max(10, Math.min(98, Math.round(((direct + implicit * 0.55) / total) * 100)));
}

function setHint(selector, message, state = "") {
  const node = $(selector);
  if (!node) return;
  node.textContent = message || "";
  if (state) node.dataset.state = state;
  else node.removeAttribute("data-state");
}

function formatBackground(background) {
  const rows = [];
  Object.entries(SECTION_LABELS).forEach(([key, label]) => {
    const items = background[key] || [];
    if (!items.length) return;
    rows.push(`## ${label}`);
    items.forEach((item, index) => {
      const id = item.id || `${key}-${index + 1}`;
      const description = item.description ? `：${item.description}` : "";
      rows.push(`- [${id}] **${item.name}**${description}`);
    });
    rows.push("");
  });
  return rows.join("\n").trim();
}

function renderBackgroundEditor() {
  const background = getBackground();
  const container = $("#backgroundSections");
  container.innerHTML = Object.entries(SECTION_LABELS)
    .map(([key, label]) => {
      const items = background[key] || [];
      const itemMarkup = items
        .map(
          (item, index) => `
            <article class="background-item" data-section="${key}" data-index="${index}">
              <input class="bg-name" value="${escapeHtml(item.name || "")}" placeholder="${SECTION_HINTS[key]}" />
              <textarea class="bg-description" rows="3" placeholder="描述你的任務、行動、工具、成果。有數字請直接寫，沒有也可以先留空。">${escapeHtml(item.description || "")}</textarea>
              <button class="secondary-button remove-bg-item" type="button">刪除</button>
            </article>
          `
        )
        .join("");
      return `
        <section class="background-section" data-section="${key}">
          <div class="section-heading compact">
            <h3>${label}</h3>
            <button class="secondary-button add-bg-item" data-section="${key}" type="button">新增</button>
          </div>
          <div class="background-items">${itemMarkup || `<p class="muted-text">尚未新增${label}。</p>`}</div>
        </section>
      `;
    })
    .join("");
  $("#backgroundMarkdown").textContent = formatBackground(background) || "尚未建立背景。";
}

function collectBackgroundFromDom() {
  const background = structuredClone(DEFAULT_BACKGROUND);
  $$(".background-item").forEach((item) => {
    const key = item.dataset.section;
    const index = background[key].length + 1;
    const name = item.querySelector(".bg-name").value.trim();
    const description = item.querySelector(".bg-description").value.trim();
    if (!name && !description) return;
    background[key].push({
      id: `${key}-${index}`,
      name: name || "未命名項目",
      description
    });
  });
  return background;
}

function addBackgroundItem(section) {
  const background = collectBackgroundFromDom();
  const index = (background[section] || []).length + 1;
  background[section].push({ id: `${section}-${index}`, name: "", description: "" });
  saveBackground(background);
  renderBackgroundEditor();
}

function saveBackgroundFromDom() {
  const background = collectBackgroundFromDom();
  saveBackground(background);
  renderBackgroundEditor();
  setHint("#backgroundStatus", "已儲存結構化背景，履歷生成與 JD match 會使用這些資料。", "success");
}

function renderSupplements(result) {
  const panel = $("#matchSupplementPanel");
  if (!result) {
    panel.innerHTML = `<p class="muted-text">先執行 JD Match，Osi 會列出需要補答的問題。</p>`;
    return;
  }
  // Build lookup tables so we can show human-readable labels instead of internal IDs.
  const reqLookup = new Map((result.key_requirements || []).map((req) => [req.id, req.text || ""]));
  const bgLookup = new Map(
    (result.implicit || []).map((item) => [item.background_id, item.background_name || ""])
  );

  const implicitItems = result.implicit || [];
  const fallback = (result.supplement_questions || []).map((q) => ({
    requirement_id: q.requirement_id,
    background_id: q.background_id,
    supplement_question: q.question,
  }));
  const questions = implicitItems.length ? implicitItems : fallback;

  if (!questions.length) {
    panel.innerHTML = `<p class="muted-text">目前沒有需要補答的問題，已對應的部分已足夠生成履歷。</p>`;
    saveSupplements([]);
    return;
  }

  panel.innerHTML = questions
    .map((item, index) => {
      const reqText = reqLookup.get(item.requirement_id) || "";
      const bgName = item.background_name || bgLookup.get(item.background_id) || "";
      const headParts = [];
      if (reqText) headParts.push(`<span class="supplement-req">JD 需求：${escapeHtml(reqText)}</span>`);
      if (bgName) headParts.push(`<span class="supplement-bg">對應你的：${escapeHtml(bgName)}</span>`);
      const head = headParts.length
        ? headParts.join("")
        : `<span class="supplement-req">補答 ${index + 1}</span>`;
      return `
        <label class="supplement-question">
          <strong>補答 ${index + 1}</strong>
          ${head}
          <span>${escapeHtml(item.supplement_question || item.question || "請補充更具體的成果、工具、情境或數字。")}</span>
          <textarea rows="3" data-requirement-id="${escapeHtml(item.requirement_id || "")}" data-background-id="${escapeHtml(item.background_id || "")}" placeholder="你的補答會在履歷生成時優先採用"></textarea>
        </label>
      `;
    })
    .join("");
}

function renderMatchDecision(result) {
  if (!result) return "";
  const reqLookup = new Map((result.key_requirements || []).map((req) => [req.id, req.text || ""]));
  const direct = result.direct || [];
  const implicit = result.implicit || [];
  const gap = result.gap || [];

  const summaryBits = [];
  if (result.jd_summary) summaryBits.push(`<p class="match-summary"><strong>JD 摘要：</strong>${escapeHtml(result.jd_summary)}</p>`);
  if (result.tone_inference) summaryBits.push(`<p class="match-summary"><strong>建議語氣：</strong>${escapeHtml(result.tone_inference)}</p>`);

  const renderItem = (item, kind) => {
    const reqText = reqLookup.get(item.requirement_id) || item.requirement_id || "";
    const bgName = item.background_name || "";
    const detail = item.rationale || item.suggested_action || item.note || "";
    if (kind === "gap") {
      return `<li><strong>JD 需求：${escapeHtml(reqText)}</strong><br><span>${escapeHtml(detail)}</span></li>`;
    }
    return `<li><strong>JD 需求：${escapeHtml(reqText)}</strong>${bgName ? `<br>對應到你的：<em>${escapeHtml(bgName)}</em>` : ""}<br><span>${escapeHtml(detail)}</span></li>`;
  };

  const list = (items, kind, emptyText) =>
    items.length ? `<ul>${items.map((item) => renderItem(item, kind)).join("")}</ul>` : `<p class="muted-text">${emptyText}</p>`;

  const encouragement = result.encouragement
    ? `<p class="match-encouragement">${escapeHtml(result.encouragement)}</p>`
    : "";

  return `
    ${summaryBits.join("")}
    <div class="match-decision-grid">
      <article class="match-card direct"><h4>已經對應上的</h4>${list(direct, "direct", "目前沒有明確對應的項目。")}</article>
      <article class="match-card implicit"><h4>需要補答才能更精準</h4>${list(implicit, "implicit", "目前沒有需要補答的項目。")}</article>
      <article class="match-card gap"><h4>背景中還沒有的</h4>${list(gap, "gap", "目前沒有明顯缺口。")}</article>
    </div>
    ${encouragement}
  `;
}

function collectSupplementsFromDom() {
  const supplements = $$("#matchSupplementPanel textarea")
    .map((textarea) => ({
      requirement_id: textarea.dataset.requirementId || "",
      background_id: textarea.dataset.backgroundId || "",
      user_answer: textarea.value.trim()
    }))
    .filter((item) => item.user_answer);
  saveSupplements(supplements);
  return supplements;
}

async function runResumeGenerate(endpoint = "/api/resume/generate") {
  const form = $("#resumeForm");
  const formData = new FormData(form);
  const sections = formData.getAll("sections");
  const lengthOverrides = {};
  $$("[data-length-key]").forEach((input) => {
    const value = input.value.trim();
    if (value) lengthOverrides[input.dataset.lengthKey] = value;
  });
  $("#resumePreview").innerHTML = `<p>Osi 正在生成履歷...</p>`;
  setHint("#resumeApiHint", "生成中，請稍候...", "loading");
  try {
    const content = await apiPost(endpoint, {
      background: getBackground(),
      target_role: formData.get("targetRole") || "",
      company: formData.get("company") || "",
      jd: formData.get("jd") || "",
      sections,
      custom_section: formData.get("customSection") || "",
      length_overrides: lengthOverrides,
      supplements: collectSupplementsFromDom().length ? collectSupplementsFromDom() : getSupplements()
    });
    $("#resumePreview").innerHTML = markdownToHtml(content);
    setHint("#resumeApiHint", "已完成。", "success");
  } catch (error) {
    $("#resumePreview").innerHTML = `<p class="error-text">${escapeHtml(error.message)}</p>`;
    setHint("#resumeApiHint", error.message, "error");
  }
}

async function runOnePage() {
  const formData = new FormData($("#resumeForm"));
  $("#resumePreview").innerHTML = `<p>Osi 正在整理 One Page CV...</p>`;
  try {
    const content = await apiPost("/api/resume/onepage", {
      background: getBackground(),
      target_role: formData.get("targetRole") || "",
      company: formData.get("company") || "",
      jd: formData.get("jd") || "",
      supplements: collectSupplementsFromDom().length ? collectSupplementsFromDom() : getSupplements()
    });
    $("#resumePreview").innerHTML = markdownToHtml(content);
  } catch (error) {
    $("#resumePreview").innerHTML = `<p class="error-text">${escapeHtml(error.message)}</p>`;
  }
}

async function runStar() {
  const formData = new FormData($("#resumeForm"));
  $("#resumePreview").innerHTML = `<p>Osi 正在改寫 STAR...</p>`;
  try {
    const content = await apiPost("/api/resume/star", {
      background: getBackground(),
      target_role: formData.get("targetRole") || "",
      jd: formData.get("jd") || ""
    });
    $("#resumePreview").innerHTML = markdownToHtml(content);
  } catch (error) {
    $("#resumePreview").innerHTML = `<p class="error-text">${escapeHtml(error.message)}</p>`;
  }
}

async function runMatch() {
  const formData = new FormData($("#matchForm"));
  $("#matchResult").innerHTML = `<p>Osi 正在分析 JD 與背景匹配...</p>`;
  setHint("#matchApiHint", "正在分析職缺與背景的對應關係…", "loading");
  try {
    const content = await apiPost("/api/jd/match", {
      background: getBackground(),
      target_role: formData.get("targetRole") || "",
      company: formData.get("company") || "",
      jd: formData.get("jd") || ""
    });
    matchResult = JSON.parse(content);
    $("#matchResult").innerHTML = renderMatchDecision(matchResult);
    renderSupplements(matchResult);
    const score = calculateFitScore(matchResult);
    updateFitScore(
      score,
      `已對應 ${matchResult.direct?.length || 0} 項、需要補答 ${matchResult.implicit?.length || 0} 項、缺口 ${matchResult.gap?.length || 0} 項。補答後履歷會更貼近 JD。`
    );
    updateOsiMessage(score >= 75 ? "這個職缺跟你的背景蠻有連結的，補答幾個細節就能更有說服力。" : "目前有幾項缺口，可以先把缺的部分當成學習目標，再決定要不要投。");
    setHint("#matchApiHint", "分析完成。補答完之後再到「履歷生成」生成履歷。", "success");
  } catch (error) {
    $("#matchResult").innerHTML = `<p class="error-text">${escapeHtml(error.message)}</p>`;
    setHint("#matchApiHint", error.message, "error");
  }
}

async function runConvert() {
  const formData = new FormData($("#convertForm"));
  $("#convertPreview").innerHTML = `<p>Osi 正在轉換履歷...</p>`;
  setHint("#convertApiHint", "轉換中...", "loading");
  try {
    const content = await apiPost("/api/convert", {
      mode: formData.get("convertMode"),
      original_resume: formData.get("originalResume") || "",
      background: getBackground(),
      from_domain: formData.get("fromDomain") || "",
      to_domain: formData.get("toDomain") || "",
      target_jd: formData.get("targetJd") || ""
    });
    $("#convertPreview").innerHTML = markdownToHtml(content);
    setHint("#convertApiHint", "轉換完成。", "success");
  } catch (error) {
    $("#convertPreview").innerHTML = `<p class="error-text">${escapeHtml(error.message)}</p>`;
    setHint("#convertApiHint", error.message, "error");
  }
}

function renderGarden() {
  const garden = $("#gardenVisual");
  if (!applications.length) {
    garden.innerHTML = `
      <section class="empty-garden">
        <div class="empty-osi sprite-figure osi-seed" style="--sprite-color:#bdf1f4">
          <i class="osi-body-gloss"></i><span class="osi-face"></span><i class="osi-foot left"></i><i class="osi-foot right"></i>
        </div>
        <div>
          <strong>還沒有投遞紀錄</strong>
          <p>建立第一筆職缺後，Osi 會把它種成求職花園裡的第一顆種子。</p>
        </div>
      </section>
    `;
    return;
  }
  garden.innerHTML = applications
    .map(
      (item, index) => `
        <article class="plant-card garden-status-${item.statusKey || "applied"}">
          <div class="plant">${renderPlantVisual(item.statusKey || "applied")}</div>
          <div class="job-ticket">
            <span class="tag">${escapeHtml(item.status)}</span>
            <strong>${escapeHtml(item.company)}</strong>
            <span>${escapeHtml(item.role)}</span>
            <small>${escapeHtml(item.date)}</small>
            <div class="garden-status-actions">
              <button type="button" data-garden-status="applied" data-index="${index}">種子</button>
              <button type="button" data-garden-status="invited" data-index="${index}">邀約</button>
              <button type="button" data-garden-status="interviewing" data-index="${index}">面試</button>
              <button type="button" data-garden-status="offer" data-index="${index}">錄取</button>
              <button type="button" data-garden-status="rejected" data-index="${index}">未錄取</button>
              <button type="button" data-garden-status="fertilizer" data-index="${index}">化肥</button>
            </div>
          </div>
        </article>
      `
    )
    .join("");
}

function renderPlantVisual(statusKey) {
  if (statusKey === "offer") {
    return `<span class="dirt"></span><span class="stem tall"></span><span class="leaf one"></span><span class="leaf two"></span><span class="flower">✿</span>`;
  }
  if (statusKey === "interviewing") {
    return `<span class="dirt"></span><span class="stem tall"></span><span class="leaf one"></span><span class="leaf two"></span><span class="leaf three"></span>`;
  }
  if (statusKey === "invited") {
    return `<span class="dirt"></span><span class="stem"></span><span class="leaf one"></span><span class="leaf two"></span>`;
  }
  if (statusKey === "rejected") {
    return `<span class="dirt"></span><span class="stem wilted"></span><span class="wilt-mark">枯</span>`;
  }
  if (statusKey === "fertilizer") {
    return `<span class="dirt fertilizer"></span><span class="fertilizer-spark">養</span>`;
  }
  return `<span class="dirt"></span><span class="seed-dot"></span>`;
}

function updateGardenStatus(index, statusKey) {
  const item = applications[index];
  if (!item) return;
  const labels = {
    applied: "已投遞",
    invited: "收到邀約",
    interviewing: "面試成長",
    offer: "錄取開花",
    rejected: "未錄取",
    fertilizer: "化為肥料"
  };
  item.statusKey = statusKey;
  item.status = labels[statusKey] || labels.applied;
  saveApplications();
  renderGarden();
  const messages = {
    applied: "履歷已投出，新的種子種下了。接著可以等待回覆，也可以先準備下一份更貼近 JD 的版本。",
    invited: "太好了，這顆種子發芽了。Osi 建議你把面試需要的故事先整理成 STAR。",
    interviewing: "面試讓葉子長出來了。把每一輪問題記下來，這些都會成為下一次的養分。",
    offer: "開花了！這份努力被看見了。可以回顧哪段經歷最有幫助，留給下一次複製成功。",
    rejected: "未錄取會有點失落。先別急著丟掉，這段經驗可以轉成肥料，幫下一顆種子長更好。",
    fertilizer: "這次沒有開花也不是浪費，Osi 會把它變成養分，幫你找出下一次要補強的地方。"
  };
  updateOsiMessage(messages[statusKey] || "新的投遞已種下，先讓它在花園裡慢慢長。");
}

function saveAppToken() {
  const token = $("#apiKeyInput").value.trim();
  const apiBase = $("#apiBaseInput")?.value.trim() || API_BASE;
  const model = $("#modelSelect").value;
  if (token.length < 8) {
    setHint("#apiKeyStatus", "Token 太短，請填後端 .env 的 APP_TOKEN。", "error");
    return;
  }
  API_BASE = apiBase.replace(/\/$/, "");
  store.set(STORAGE.appToken, token);
  store.set("oasis.api.base", API_BASE);
  store.set(STORAGE.model, model);
  loadSettings();
}

function loadSettings() {
  const token = getAppToken();
  $("#apiKeyInput").value = token;
  $("#apiBaseInput").value = API_BASE;
  $("#modelSelect").value = getModel();
  setHint("#apiKeyStatus", token ? `已儲存 APP TOKEN：****${token.slice(-4)}，後端：${API_BASE}。OpenAI API KEY 只存在後端 .env。` : "尚未儲存 App Token。", token ? "success" : "");
}

async function testApiToken() {
  saveAppToken();
  try {
    const response = await fetch(`${API_BASE}/api/health`, {
      headers: { Authorization: `Bearer ${getAppToken()}` }
    });
    if (!response.ok) throw new Error(`連線失敗：HTTP ${response.status}`);
    const data = await response.json();
    setHint("#apiKeyStatus", `APP TOKEN 可連線，模型：${data.model || getModel()}。`, "success");
  } catch (error) {
    setHint("#apiKeyStatus", `${error.message}。請確認後端 port 與 APP_TOKEN 是否一致。`, "error");
  }
}

async function registerUser() {
  const name = $("#authNameInput").value.trim() || "使用者";
  const email = $("#authEmailInput").value.trim();
  const password = $("#authPasswordInput").value;
  try {
    await apiV1("/auth/register", {
      method: "POST",
      body: JSON.stringify({ name, email, password })
    });
    setHint("#authStatus", "註冊完成，請登入。", "success");
  } catch (error) {
    setHint("#authStatus", error.message, "error");
  }
}

async function loginUser() {
  const email = $("#authEmailInput").value.trim();
  const password = $("#authPasswordInput").value;
  try {
    const token = await apiV1("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password })
    });
    store.set(STORAGE.authToken, token.access_token);
    const me = await apiV1("/auth/me");
    store.set(STORAGE.userName, me.name || "使用者");
    store.set(STORAGE.userEmail, me.email || email);
    updateUserIdentity();
    updateOsiMessage(`${me.name || "你"}，歡迎回來。Osi 會陪你把每次投遞都變成可累積的成長紀錄。`);
  } catch (error) {
    setHint("#authStatus", error.message, "error");
  }
}

function logoutUser() {
  store.remove(STORAGE.authToken);
  store.remove(STORAGE.userName);
  store.remove(STORAGE.userEmail);
  updateUserIdentity();
  updateOsiMessage("已登出。你的 APP TOKEN 與本機背景資料仍保留在這台瀏覽器。");
}

function bootstrap() {
  $$("[data-view]").forEach((button) => button.addEventListener("click", () => setView(button.dataset.view)));
  $("#backgroundSections")?.addEventListener("click", (event) => {
    if (event.target.matches(".add-bg-item")) addBackgroundItem(event.target.dataset.section);
    if (event.target.matches(".remove-bg-item")) {
      const item = event.target.closest(".background-item");
      item.remove();
      saveBackgroundFromDom();
    }
  });
  $("#saveBackgroundBtn")?.addEventListener("click", saveBackgroundFromDom);
  $("#clearBackgroundBtn")?.addEventListener("click", () => {
    saveBackground(structuredClone(DEFAULT_BACKGROUND));
    renderBackgroundEditor();
    setHint("#backgroundStatus", "已清空背景。");
  });
  $("#resumeForm")?.addEventListener("submit", (event) => {
    event.preventDefault();
    runResumeGenerate();
  });
  $("#onePageBtn")?.addEventListener("click", runOnePage);
  $("#starBtn")?.addEventListener("click", runStar);
  $("#matchForm")?.addEventListener("submit", (event) => {
    event.preventDefault();
    runMatch();
  });
  $("#saveSupplementsBtn")?.addEventListener("click", () => {
    const count = collectSupplementsFromDom().length;
    setHint("#matchApiHint", `已儲存 ${count} 筆補答，生成履歷時會優先採用。`, "success");
  });
  $("#convertForm")?.addEventListener("submit", (event) => {
    event.preventDefault();
    runConvert();
  });
  $("#saveApiKeyBtn")?.addEventListener("click", saveAppToken);
  $("#testApiTokenBtn")?.addEventListener("click", testApiToken);
  $("#registerBtn")?.addEventListener("click", registerUser);
  $("#loginBtn")?.addEventListener("click", loginUser);
  $("#logoutBtn")?.addEventListener("click", logoutUser);
  $("#profileButton")?.addEventListener("click", () => setView("settings"));
  $("#gardenVisual")?.addEventListener("click", (event) => {
    const button = event.target.closest("[data-garden-status]");
    if (!button) return;
    updateGardenStatus(Number(button.dataset.index), button.dataset.gardenStatus);
  });
  $("#addApplicationBtn")?.addEventListener("click", () => {
    applications.unshift({
      company: "尚未命名公司",
      role: "待分析職缺",
      status: "已投遞",
      statusKey: "applied",
      date: new Intl.DateTimeFormat("zh-TW").format(new Date())
    });
    saveApplications();
    renderGarden();
    updateOsiMessage("新的種子已種下。接下來可以分析 JD，看看它最需要哪些養分。");
  });

  renderBackgroundEditor();
  renderSupplements(null);
  renderGarden();
  loadSettings();
  updateUserIdentity();
  updateFitScore(null, "執行 JD Match 後，Osi 會根據背景估算適配分數。");
  $("#resumePreview").innerHTML = `<p>先建立結構化背景，再貼上 JD 生成客製化履歷。</p>`;
  $("#convertPreview").innerHTML = `<p>貼上既有履歷後，可轉換成新領域版本或依背景重寫。</p>`;
  $("#matchResult").innerHTML = `<p>貼上 JD 後按下分析，Osi 會列出哪些已對應、哪些需要補答、哪些還沒有對應材料。</p>`;
}

bootstrap();
