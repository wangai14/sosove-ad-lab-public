const authElements = {
  form: document.querySelector("#auth-form"),
  username: document.querySelector("#auth-username"),
  password: document.querySelector("#auth-password"),
  passwordToggle: document.querySelector("#auth-password-toggle"),
  submit: document.querySelector("#auth-submit-btn"),
  message: document.querySelector("#auth-message"),
  title: document.querySelector("#auth-title"),
  subtitle: document.querySelector("#auth-subtitle"),
  kicker: document.querySelector("#auth-mode-kicker"),
};

const authState = {
  setupRequired: false,
};

function authNextPath() {
  const params = new URLSearchParams(window.location.search);
  const next = params.get("next") || "/materials.html";
  return next.startsWith("/") && !next.startsWith("//") ? next : "/materials.html";
}

function setAuthMessage(message, tone = "") {
  authElements.message.textContent = message || "";
  authElements.message.dataset.tone = tone;
}

async function authJson(url, options = {}) {
  const response = await fetch(url, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
  });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok || payload.ok === false) {
    throw new Error(payload.error || `请求失败：${response.status}`);
  }
  return payload;
}

function renderAuthMode() {
  if (authState.setupRequired) {
    authElements.kicker.textContent = "首次初始化";
    authElements.title.textContent = "创建管理员账号";
    authElements.subtitle.textContent = "先设置一个账号和密码，后续访问素材库、上传视频和 Skill 分析都需要登录。";
    authElements.submit.textContent = "创建并登录";
    authElements.password.autocomplete = "new-password";
    authElements.username.value = authElements.username.value || "admin";
    return;
  }
  authElements.kicker.textContent = "账号登录";
  authElements.title.textContent = "登录素材工作台";
  authElements.subtitle.textContent = "输入账号和密码后才能访问视频素材库、上传接口和 AI 分析结果。";
  authElements.submit.textContent = "登录";
  authElements.password.autocomplete = "current-password";
}

function setPasswordVisible(visible) {
  if (!authElements.passwordToggle) return;
  authElements.password.type = visible ? "text" : "password";
  authElements.passwordToggle.textContent = visible ? "隐藏" : "显示";
  authElements.passwordToggle.setAttribute("aria-label", visible ? "隐藏密码" : "显示密码");
  authElements.passwordToggle.setAttribute("aria-pressed", String(visible));
}

async function loadAuthStatus() {
  try {
    const payload = await authJson("/api/auth/status");
    authState.setupRequired = Boolean(payload.auth?.setupRequired);
    if (payload.auth?.authenticated) {
      window.location.replace(authNextPath());
      return;
    }
    renderAuthMode();
  } catch (error) {
    setAuthMessage(error.message, "error");
  }
}

authElements.form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const username = authElements.username.value.trim();
  const password = authElements.password.value;
  authElements.submit.disabled = true;
  setAuthMessage(authState.setupRequired ? "正在创建账号..." : "正在登录...");
  try {
    await authJson("/api/auth/login", {
      method: "POST",
      body: JSON.stringify({
        username,
        password,
        setup: authState.setupRequired,
      }),
    });
    setAuthMessage("登录成功，正在进入工作台。", "success");
    window.location.replace(authNextPath());
  } catch (error) {
    setAuthMessage(error.message, "error");
    authElements.password.select();
  } finally {
    authElements.submit.disabled = false;
  }
});

authElements.passwordToggle?.addEventListener("click", () => {
  setPasswordVisible(authElements.password.type !== "text");
  authElements.password.focus();
});

setPasswordVisible(false);
loadAuthStatus();
