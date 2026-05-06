/**
 * auth.js — 인증 상태 관리 + 네비게이션 렌더링
 * 모든 페이지에서 base.html을 통해 로드됨
 */

const Auth = (() => {
  const TOKEN_KEY = 'promptory_access';
  const REFRESH_KEY = 'promptory_refresh';
  const USER_EMAIL_KEY = 'promptory_user_email';

  function decodeJwt(token) {
    if (!token) return {};
    try {
      const payload = token.split('.')[1];
      const base64 = payload.replace(/-/g, '+').replace(/_/g, '/');
      return JSON.parse(atob(base64));
    } catch {
      return {};
    }
  }

  return {
    getAccess:  () => localStorage.getItem(TOKEN_KEY),
    getRefresh: () => localStorage.getItem(REFRESH_KEY),
    getUserId() {
      return decodeJwt(this.getAccess()).user_id || null;
    },
    getUserEmail() {
      return localStorage.getItem(USER_EMAIL_KEY);
    },

    save(access, refresh, user = {}) {
      localStorage.setItem(TOKEN_KEY, access);
      if (refresh) localStorage.setItem(REFRESH_KEY, refresh);
      if (user.email) localStorage.setItem(USER_EMAIL_KEY, user.email);
    },

    clear() {
      localStorage.removeItem(TOKEN_KEY);
      localStorage.removeItem(REFRESH_KEY);
      localStorage.removeItem(USER_EMAIL_KEY);
    },

    isLoggedIn() {
      return !!localStorage.getItem(TOKEN_KEY);
    },

    /** 모든 API 호출에 붙이는 Authorization 헤더 */
    headers(extra = {}, body = null) {
      const token = this.getAccess();
      const headers = {
        ...(body instanceof FormData ? {} : { 'Content-Type': 'application/json' }),
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        ...extra,
      };
      if (headers['Content-Type'] === null) delete headers['Content-Type'];
      return headers;
    },

    /** Access Token 만료 시 Refresh Token으로 재발급 */
    async refresh() {
      const refresh = this.getRefresh();
      if (!refresh) return false;
      try {
        const res = await fetch(`${window.PROMPTORY.apiBase}/accounts/token/refresh/`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ refresh }),
        });
        if (!res.ok) { this.clear(); return false; }
        const data = await res.json();
        this.save(data.access, data.refresh || refresh);
        return true;
      } catch {
        return false;
      }
    },

    /** 401 응답 시 재시도 래퍼 */
    async fetchWithAuth(url, options = {}) {
      options.headers = this.headers(options.headers || {}, options.body);
      let res = await fetch(url, options);
      if (res.status === 401) {
        const ok = await this.refresh();
        if (ok) {
          options.headers.Authorization = `Bearer ${this.getAccess()}`;
          res = await fetch(url, options);
        }
      }
      return res;
    },

    async logout() {
      const refresh = this.getRefresh();
      if (refresh) {
        await fetch(`${window.PROMPTORY.apiBase}/accounts/logout/`, {
          method: 'POST',
          headers: this.headers(),
          body: JSON.stringify({ refresh }),
        }).catch(() => {});
      }
      this.clear();
      window.location.href = '/';
    },
  };
})();

/**
 * Api — 공통 API 클라이언트 + 안전한 렌더링 헬퍼.
 * JSON 요청과 multipart 업로드의 헤더 차이를 한 곳에서 처리한다.
 */
const Api = (() => {
  const apiBase = () => window.PROMPTORY?.apiBase || '/api';

  function escapeHtml(value) {
    return String(value ?? '')
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }

  function safeUrl(value) {
    const url = String(value ?? '');
    if (!url) return '#';
    try {
      const parsed = new URL(url, window.location.origin);
      if (!['http:', 'https:'].includes(parsed.protocol)) return '#';
      return parsed.href;
    } catch {
      return '#';
    }
  }

  async function request(path, options = {}) {
    const url = path.startsWith('http') ? path : `${apiBase()}${path}`;
    return Auth.fetchWithAuth(url, options);
  }

  async function json(path, options = {}) {
    const res = await request(path, options);
    const data = await res.json().catch(() => null);
    return { res, data };
  }

  return {
    escapeHtml,
    safeUrl,
    request,
    json,
    get: path => json(path),
    post: (path, body = {}) => json(path, { method: 'POST', body: JSON.stringify(body) }),
    put: (path, body = {}) => json(path, { method: 'PUT', body: JSON.stringify(body) }),
    delete: path => json(path, { method: 'DELETE' }),
    upload: (path, formData) => json(path, { method: 'POST', body: formData }),
  };
})();

/** 네비게이션 로그인/로그아웃 영역 렌더링 */
document.addEventListener('DOMContentLoaded', () => {
  const area = document.getElementById('nav-auth-area');
  if (!area) return;

  if (Auth.isLoggedIn()) {
    document.querySelectorAll('.auth-only').forEach(el => { el.style.display = ''; });
    area.innerHTML = `
      <button id="logout-nav-btn" class="btn btn-sm btn-secondary">로그아웃</button>
    `;
    document.getElementById('logout-nav-btn')
      ?.addEventListener('click', () => Auth.logout());
  } else {
    area.innerHTML = `
      <a href="/accounts/login/" class="btn btn-sm btn-secondary">로그인</a>
      <a href="/accounts/register/" class="btn btn-sm btn-primary">회원가입</a>
    `;
  }
});
