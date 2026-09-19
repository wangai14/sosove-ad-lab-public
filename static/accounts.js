const accountElements = {
  currentUser: document.querySelector("#account-current-user"),
  currentRole: document.querySelector("#account-current-role"),
  form: document.querySelector("#account-create-form"),
  username: document.querySelector("#account-new-username"),
  displayName: document.querySelector("#account-new-display-name"),
  password: document.querySelector("#account-new-password"),
  role: document.querySelector("#account-new-role"),
  createBtn: document.querySelector("#account-create-btn"),
  message: document.querySelector("#account-create-message"),
  passwordForm: document.querySelector("#account-password-form"),
  currentPassword: document.querySelector("#account-current-password"),
  nextPassword: document.querySelector("#account-next-password"),
  passwordBtn: document.querySelector("#account-password-btn"),
  passwordMessage: document.querySelector("#account-password-message"),
  refreshBtn: document.querySelector("#account-refresh-btn"),
  list: document.querySelector("#account-list"),
};

const accountState = {
  users: [],
  auth: null,
};

async function accountJson(url, options = {}) {
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

function setAccountMessage(message, tone = "") {
  accountElements.message.textContent = message || "";
  accountElements.message.dataset.tone = tone;
}

function setPasswordMessage(message, tone = "") {
  accountElements.passwordMessage.textContent = message || "";
  accountElements.passwordMessage.dataset.tone = tone;
}

function roleLabel(role) {
  return role === "admin" ? "管理员" : "剪辑";
}

function formatAccountDate(value) {
  if (!value) return "暂无";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "暂无";
  return `${date.getMonth() + 1}/${date.getDate()} ${String(date.getHours()).padStart(2, "0")}:${String(date.getMinutes()).padStart(2, "0")}`;
}

function escapeAccountHtml(value) {
  return String(value).replace(/[&<>"']/g, (char) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[char]));
}

function renderAccounts() {
  accountElements.currentUser.textContent = accountState.auth?.username || "管理员";
  accountElements.currentRole.textContent = roleLabel(accountState.auth?.role);
  if (!accountState.users.length) {
    accountElements.list.innerHTML = `<div class="material-workbench-empty"><strong>暂无剪辑账号</strong><small>创建剪辑账号后会显示在这里。</small></div>`;
    return;
  }
  accountElements.list.innerHTML = accountState.users.map((user) => {
    const username = String(user.username || "");
    const displayName = String(user.displayName || username);
    const isCurrentUser = username.toLowerCase() === String(accountState.auth?.username || "").toLowerCase();
    return `
      <article class="account-card ${user.enabled ? "" : "is-disabled"}">
        <div>
          <strong>${escapeAccountHtml(displayName)}</strong>
          <small>${escapeAccountHtml(username)} · ${escapeAccountHtml(roleLabel(user.role))} · ${user.enabled ? "已启用" : "已停用"} · 最近登录 ${escapeAccountHtml(formatAccountDate(user.lastLoginAt))} · 密码更新 ${escapeAccountHtml(formatAccountDate(user.passwordUpdatedAt))}</small>
        </div>
        <div class="account-card-actions">
          <div class="account-reset-row">
            <input type="password" autocomplete="new-password" placeholder="新密码" data-action="reset-password-input" data-username="${escapeAccountHtml(username)}">
            <button class="mini-action" type="button" data-action="reset-password" data-username="${escapeAccountHtml(username)}">重置</button>
          </div>
          <div class="account-button-row">
            <button class="soft-action ${user.enabled ? "danger" : ""}" type="button" data-action="toggle-user" data-username="${escapeAccountHtml(username)}" data-enabled="${user.enabled ? "0" : "1"}">
              ${user.enabled ? "停用" : "启用"}
            </button>
            <button class="soft-action danger" type="button" data-action="delete-user" data-username="${escapeAccountHtml(username)}" ${isCurrentUser ? "disabled title=\"当前登录账号不能删除\"" : ""}>
              删除
            </button>
          </div>
        </div>
      </article>
    `;
  }).join("");
  accountElements.list.querySelectorAll("[data-action='reset-password']").forEach((button) => {
    button.addEventListener("click", async () => {
      const card = button.closest(".account-card");
      const input = card?.querySelector("[data-action='reset-password-input']");
      const password = input?.value || "";
      button.disabled = true;
      setAccountMessage(`正在重置 ${button.dataset.username || ""} 的密码...`);
      try {
        const payload = await accountJson("/api/auth/users/reset-password", {
          method: "POST",
          body: JSON.stringify({
            username: button.dataset.username,
            password,
          }),
        });
        accountState.users = payload.users || accountState.users;
        accountState.auth = payload.auth || accountState.auth;
        renderAccounts();
        setAccountMessage(`已重置账号「${payload.user?.username || button.dataset.username}」的密码，旧登录态已失效。`, "success");
      } catch (error) {
        setAccountMessage(error.message, "error");
        input?.select();
      } finally {
        button.disabled = false;
      }
    });
  });
  accountElements.list.querySelectorAll("[data-action='toggle-user']").forEach((button) => {
    button.addEventListener("click", async () => {
      button.disabled = true;
      try {
        const payload = await accountJson("/api/auth/users/set-enabled", {
          method: "POST",
          body: JSON.stringify({
            username: button.dataset.username,
            enabled: button.dataset.enabled === "1",
          }),
        });
        accountState.users = payload.users || accountState.users;
        renderAccounts();
        setAccountMessage("账号状态已更新。", "success");
      } catch (error) {
        setAccountMessage(error.message, "error");
      } finally {
        button.disabled = false;
      }
    });
  });
  accountElements.list.querySelectorAll("[data-action='delete-user']").forEach((button) => {
    button.addEventListener("click", async () => {
      const username = button.dataset.username || "";
      if (!username) return;
      const confirmed = window.confirm(`确定删除账号「${username}」吗？删除后这个账号不能再登录，历史任务记录会保留。`);
      if (!confirmed) return;
      button.disabled = true;
      setAccountMessage(`正在删除账号 ${username}...`);
      try {
        const payload = await accountJson("/api/auth/users/delete", {
          method: "POST",
          body: JSON.stringify({ username }),
        });
        accountState.users = payload.users || accountState.users;
        accountState.auth = payload.auth || accountState.auth;
        renderAccounts();
        setAccountMessage(`已删除账号「${payload.deletedUser?.username || username}」。`, "success");
      } catch (error) {
        setAccountMessage(error.message, "error");
      } finally {
        button.disabled = false;
      }
    });
  });
}

async function loadAccounts() {
  try {
    const payload = await accountJson("/api/auth/users");
    accountState.users = payload.users || [];
    accountState.auth = payload.auth || accountState.auth;
    renderAccounts();
  } catch (error) {
    accountElements.list.innerHTML = `<div class="material-workbench-empty"><strong>无法读取账号</strong><small>${escapeAccountHtml(error.message)}</small></div>`;
  }
}

accountElements.form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const username = accountElements.username.value.trim();
  const displayName = accountElements.displayName.value.trim();
  const password = accountElements.password.value;
  const role = accountElements.role.value;
  accountElements.createBtn.disabled = true;
  setAccountMessage("正在创建账号...");
  try {
    const payload = await accountJson("/api/auth/users", {
      method: "POST",
      body: JSON.stringify({ username, displayName, password, role }),
    });
    accountState.users = payload.users || [];
    accountElements.password.value = "";
    accountElements.username.value = "";
    accountElements.displayName.value = "";
    accountElements.role.value = "customer";
    renderAccounts();
    setAccountMessage(`已创建 ${roleLabel(payload.user?.role)}账号「${payload.user?.username || username}」，请保存好初始密码。`, "success");
  } catch (error) {
    setAccountMessage(error.message, "error");
    accountElements.password.select();
  } finally {
    accountElements.createBtn.disabled = false;
  }
});

accountElements.passwordForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const currentPassword = accountElements.currentPassword.value;
  const newPassword = accountElements.nextPassword.value;
  accountElements.passwordBtn.disabled = true;
  setPasswordMessage("正在更新密码...");
  try {
    const payload = await accountJson("/api/auth/change-password", {
      method: "POST",
      body: JSON.stringify({ currentPassword, newPassword }),
    });
    accountState.auth = payload.auth || accountState.auth;
    if (payload.user) {
      accountState.users = accountState.users.map((user) => (
        String(user.username).toLowerCase() === String(payload.user.username).toLowerCase() ? payload.user : user
      ));
    }
    accountElements.currentPassword.value = "";
    accountElements.nextPassword.value = "";
    renderAccounts();
    setPasswordMessage("密码已更新，旧登录态已自动失效。", "success");
  } catch (error) {
    setPasswordMessage(error.message, "error");
    accountElements.nextPassword.select();
  } finally {
    accountElements.passwordBtn.disabled = false;
  }
});

accountElements.refreshBtn.addEventListener("click", loadAccounts);

loadAccounts();
