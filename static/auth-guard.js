async function requestAuthJson(url, options = {}) {
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

function safeNextPath() {
  return `${window.location.pathname}${window.location.search}${window.location.hash}`;
}

function redirectToLogin() {
  const next = encodeURIComponent(safeNextPath());
  window.location.replace(`/login.html?next=${next}`);
}

function authRoleLabel(role) {
  return role === "admin" ? "管理员" : "剪辑";
}

async function initAuthGuard() {
  let auth = null;
  try {
    const payload = await requestAuthJson("/api/auth/status");
    auth = payload.auth || null;
    if (!auth?.authenticated) {
      redirectToLogin();
      return;
    }
  } catch {
    redirectToLogin();
    return;
  }

  document.querySelectorAll("[data-auth-admin-only]").forEach((element) => {
    element.hidden = !auth.canManageUsers;
  });
  document.querySelectorAll("[data-auth-username]").forEach((element) => {
    element.textContent = auth.username || "已登录";
    element.title = auth.username || "";
  });
  document.querySelectorAll("[data-auth-role]").forEach((element) => {
    element.textContent = authRoleLabel(auth.role);
  });
  window.seedanceAuth = auth;
  window.dispatchEvent(new CustomEvent("seedance:auth", { detail: auth }));

  if (window.location.pathname.endsWith("/accounts.html") && !auth.canManageUsers) {
    window.location.replace("/materials.html");
    return;
  }

  document.querySelectorAll("[data-auth-logout]").forEach((button) => {
    button.addEventListener("click", async () => {
      button.disabled = true;
      try {
        await requestAuthJson("/api/auth/logout", { method: "POST", body: "{}" });
      } catch {
        // Clearing server-side cookie is best effort; redirect still sends the user to the login gate.
      } finally {
        window.location.replace("/login.html");
      }
    });
  });
}

initAuthGuard();
