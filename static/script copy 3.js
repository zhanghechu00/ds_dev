// ====== DOM 引用 ======
const chatbox = document.getElementById('chatbox');
const userInput = document.getElementById('userInput');
const sendButton = document.getElementById('sendButton');
const modelSelect = document.getElementById('modelSelect');
const newChatBtn = document.getElementById('newChatBtn');
const conversationList = document.getElementById('conversationList');
const toggleThemeBtn = document.getElementById('toggleThemeBtn');
const exportBtn = document.getElementById('exportBtn');
const clearBtn = document.getElementById('clearBtn');

// ====== 状态（本地持久化） ======
let state = {
  conversations: JSON.parse(localStorage.getItem('convos') || '[]'),
  activeId: null,
};
function uid() { return Math.random().toString(36).slice(2, 10); }
function saveState() { localStorage.setItem('convos', JSON.stringify(state.conversations)); }
function getActive() { return state.conversations.find(c => c.id === state.activeId); }
function ensureActive() {
  if (!state.activeId || !getActive()) {
    const id = uid();
    state.conversations.unshift({ id, title: '未命名对话', model: modelSelect.value, messages: [] });
    state.activeId = id;
    saveState(); renderSidebar();
  }
}

// ====== 渲染：Sidebar / 主区 ======
function renderSidebar() {
  conversationList.innerHTML = '';
  state.conversations.forEach(c => {
    const el = document.createElement('div');
    el.className = 'convo-item' + (c.id === state.activeId ? ' active' : '');
    el.textContent = c.title || '未命名对话';
    el.onclick = () => { state.activeId = c.id; renderAll(); };
    conversationList.appendChild(el);
  });
}
function renderAll() {
  renderSidebar();
  chatbox.innerHTML = '';
  const convo = getActive(); if (!convo) return;
  modelSelect.value = convo.model || modelSelect.value;
  convo.messages.forEach(m => appendMessage(m.role, m.content, m.toolOutput,m.needParams));
  chatbox.scrollTop = chatbox.scrollHeight;
}

// ====== 富渲染：Markdown / Prism / KaTeX / Mermaid / 复制 / 灯箱 ======
if (window.mermaid) { mermaid.initialize({ startOnLoad: false, theme: "dark" }); }

function renderMarkdown(mdText) {
  if (!mdText) return "";
  marked.setOptions({ gfm: true, breaks: true, mangle: false, headerIds: true });

  const renderer = new marked.Renderer();
  renderer.code = (code, lang = "") => {
    if ((lang || "").toLowerCase() === "mermaid") {
      return `<pre class="mermaid">${escapeHtml(code)}</pre>`;
    }
    const languageClass = lang ? `language-${lang}` : "";
    return `<pre class="line-numbers"><code class="${languageClass}">${escapeHtml(code)}</code><button class="copy-btn" data-copy="${encodeURIComponent(code)}">复制</button></pre>`;
  };
  renderer.image = (href, title, text) => {
    const alt = text || "";
    const t = title ? `title="${escapeHtml(title)}"` : "";
    return `<span class="img-wrap"><img src="${href}" alt="${escapeHtml(alt)}" ${t}></span>`;
  };

  const html = marked.parse(mdText, { renderer });
  return `<div class="markdown-body">${html}</div>`;
}

function enhanceRichContent(container) {
  if (!container) return;
  if (window.Prism) Prism.highlightAllUnder(container);

  if (window.renderMathInElement) {
    renderMathInElement(container, {
      delimiters: [
        { left: "$$", right: "$$", display: true },
        { left: "$", right: "$", display: false },
        { left: "\\(", right: "\\)", display: false },
        { left: "\\[", right: "\\]", display: true }
      ],
      throwOnError: false
    });
  }

  const mermaids = container.querySelectorAll("pre.mermaid");
  if (mermaids.length && window.mermaid) {
    mermaids.forEach((el) => {
      const code = el.textContent;
      const wrapper = document.createElement("div");
      wrapper.className = "mermaid";
      wrapper.textContent = code;
      el.replaceWith(wrapper);
    });
    mermaid.run({ querySelector: ".mermaid" });
  }

  container.querySelectorAll(".copy-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      const code = decodeURIComponent(btn.getAttribute("data-copy") || "");
      navigator.clipboard.writeText(code);
      btn.textContent = "已复制";
      setTimeout(() => (btn.textContent = "复制"), 1200);
    });
  });

  const lb = document.getElementById("lightbox");
  container.querySelectorAll(".img-wrap img").forEach(img => {
    img.addEventListener("click", () => {
      lb.querySelector("img").src = img.src;
      lb.style.display = "flex";
    });
  });
  lb.addEventListener("click", () => (lb.style.display = "none"));
}

// ====== 消息渲染 ======
function appendMessage(role, content, toolOutput, needParams) {
  const wrap = document.createElement('div');
  wrap.className = `message ${role}`;
  let extra = '';
  if (needParams && needParams.fields) {
    extra = `<form class="param-form">` +
      needParams.fields.map(f =>
        `<label>${escapeHtml(f.label || f.name)}：
           <input name="${f.name}" placeholder="${escapeHtml(f.placeholder || '')}" value="${escapeHtml(f.value || '')}">
         </label>`
      ).join('') +
      `<button type="submit">确定</button>` +
      `</form>`;
  } else if (toolOutput) {
    extra = `<pre class="tool-block">${escapeHtml(String(toolOutput))}</pre>`;
  }
  wrap.innerHTML = `
    <div class="avatar">${role === 'user' ? '🧑' : '🤖'}</div>
    <div class="bubble">
      <div class="content"></div>
      ${extra}
      <div class="message-actions">
        <button class="action-btn" data-act="copy">复制</button>
        ${role === 'assistant' ? '<button class="action-btn" data-act="regen">重试</button>' : ''}
      </div>
    </div>`;
  // wrap.innerHTML = `
  //   <div class="avatar">${role === 'user' ? '🧑' : '🤖'}</div>
  //   <div class="bubble">
  //     <div class="content"></div>
  //     ${toolOutput ? `<pre class="tool-block">${escapeHtml(String(toolOutput))}</pre>` : ''}
  //     <div class="message-actions">
  //       <button class="action-btn" data-act="copy">复制</button>
  //       ${role === 'assistant' ? '<button class="action-btn" data-act="regen">重试</button>' : ''}
  //     </div>
  //   </div>`;

  const contentEl = wrap.querySelector('.content');
  contentEl.innerHTML = renderMarkdown(content || "");
  chatbox.appendChild(wrap);
  enhanceRichContent(contentEl);

  if (needParams && needParams.fields) {
    const form = wrap.querySelector('.param-form');
    form.onsubmit = async (e) => {
      e.preventDefault();
      const params = {};
      needParams.fields.forEach(f => {
        params[f.name] = form.querySelector(`[name="${f.name}"]`).value.trim();
      });
      await sendParamForm(needParams.tool, params);
    };
  }
  wrap.querySelectorAll('.action-btn').forEach(btn => {
    btn.onclick = () => onAction(btn.dataset.act, { role, content });
  });

  chatbox.scrollTop = chatbox.scrollHeight;
}
async function sendParamForm(tool, params) {
  ensureActive();
  const convo = getActive();
  const pending = { role: 'assistant', content: '…', __pending: true };
  convo.messages.push(pending);
  const pendingIndex = convo.messages.length - 1;
  appendMessage('assistant', '继续执行中…');
  saveState();

  try {
    const res = await fetch('/chat', {
      method: 'POST',
      headers: { 'Content-Type':'application/json' },
      body: JSON.stringify({ action: 'provide_tool_params', tool, params })
    });
    const data = await res.json();
    const reply = data.reply || data.final_response || "";
    const toolOutput = data.tool_output || data.tool_result || null;
    convo.messages[pendingIndex] = { role: 'assistant', content: reply || '(空)', toolOutput };
    renderAll();
  } catch (e) {
    convo.messages[pendingIndex] = { role: 'assistant', content: `出错：${e.message}` };
    renderAll();
  }
}
async function sendToServer(prompt, model, isRegen = false) {
  ensureActive();
  const convo = getActive();
  if (!isRegen) {
    convo.messages.push({ role: 'user', content: prompt });
    appendMessage('user', prompt);
  }
  saveState();

  const pending = { role: 'assistant', content: '…', __pending: true };
  convo.messages.push(pending);
  const pendingIndex = convo.messages.length - 1;
  appendMessage('assistant', '思考中…');
  chatbox.scrollTop = chatbox.scrollHeight;

  try {
    const res = await fetch('/chat', {
      method: 'POST',
      headers: { 'Content-Type':'application/json' },
      body: JSON.stringify({ message: prompt, model: model || modelSelect.value })
    });
    const data = await res.json();

    // 如果缺参，直接渲染表单气泡
    if (data.need_params) {
      convo.messages[pendingIndex] = {
        role: 'assistant',
        content: data.need_params.message || "请提供参数",
        toolOutput: null,
        needParams: data.need_params
      };
      chatbox.innerHTML = ''; // 重新渲染，确保表单显示
      renderAll();
      return;
    }

    const reply = data.reply || data.final_response || "";
    const toolOutput = data.tool_output || data.tool_result || null;
    convo.messages[pendingIndex] = { role: 'assistant', content: reply || '(空)', toolOutput };
    renderAll();

    const title = (data.title || reply || "对话").slice(0, 20);
    if (!convo.title || convo.title === '未命名对话') {
      convo.title = title; saveState(); renderSidebar();
    }
  } catch (e) {
    convo.messages[pendingIndex] = { role: 'assistant', content: `出错：${e.message}` };
    renderAll();
  }
}

function onAction(act, msg) {
  if (act === 'copy') {
    navigator.clipboard.writeText(msg.content || "");
  } else if (act === 'regen') {
    const convo = getActive();
    const lastUser = [...convo.messages].reverse().find(m => m.role === 'user');
    if (lastUser) sendToServer(lastUser.content, convo.model, true);
  }
}



// ====== 事件绑定 ======
sendButton.onclick = () => {
  const text = userInput.value.trim();
  if (!text) return;
  const model = modelSelect.value;
  userInput.value = '';
  autoResize();
  sendToServer(text, model);
};
userInput.addEventListener('keydown', (e) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault(); sendButton.click();
  }
});
userInput.addEventListener('input', autoResize);
function autoResize() {
  userInput.style.height = 'auto';
  userInput.style.height = Math.min(userInput.scrollHeight, 160) + 'px';
}

newChatBtn.onclick = () => { state.activeId = null; ensureActive(); renderAll(); };
modelSelect.onchange = () => { const c = getActive(); if (c) { c.model = modelSelect.value; saveState(); } };
toggleThemeBtn.onclick = () => { document.body.classList.toggle('theme-dark'); };
exportBtn.onclick = () => {
  const c = getActive(); if (!c) return;
  const blob = new Blob([JSON.stringify(c, null, 2)], { type: 'application/json' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = `chat-${c.id}.json`; a.click();
};
clearBtn.onclick = () => { const c = getActive(); if (!c) return; c.messages = []; saveState(); renderAll(); };

// 顶部 Banner 关闭
document.getElementById('bannerClose')?.addEventListener('click', () => {
  document.getElementById('appBanner').hidden = true;
});

// ====== 启动 ======
ensureActive(); renderAll(); autoResize();

// ====== Utils ======
function escapeHtml(s = "") {
  return s.replace(/[&<>"']/g, m => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]));
}
