/**
 * login.js — 로그인 페이지 전용
 * POST /api/accounts/login/ → JWT 저장 → 리다이렉트
 */
document.addEventListener('DOMContentLoaded', () => {
  const form    = document.getElementById('login-form');
  const errBox  = document.getElementById('login-error');
  const btn     = document.getElementById('login-btn');

  const pendingError = sessionStorage.getItem(AuthErrors.PENDING_KEY);
  if (pendingError && errBox) {
    errBox.textContent = pendingError;
    errBox.style.display = 'block';
    sessionStorage.removeItem(AuthErrors.PENDING_KEY);
  }

  form?.addEventListener('submit', async (e) => {
    e.preventDefault();
    clearErrors();
    setLoading(btn, true);

    const email    = document.getElementById('email').value.trim();
    const password = document.getElementById('password').value;

    // 클라이언트 검증
    if (!email)    return showFieldError('email-error', '이메일을 입력하세요.');
    if (!password) return showFieldError('password-error', '비밀번호를 입력하세요.');

    try {
      const { res, data } = await Api.post('/accounts/login/', { email, password });

      if (!res.ok) {
        errBox.textContent = AuthErrors.normalize(data.detail);
        errBox.style.display = 'block';
        return;
      }

      Auth.save(data.access, data.refresh, { email });
      window.location.href = '/';
    } catch {
      errBox.textContent = '서버 오류가 발생했습니다. 잠시 후 다시 시도해주세요.';
      errBox.style.display = 'block';
    } finally {
      setLoading(btn, false);
    }
  });

  function setLoading(btn, loading) {
    btn.querySelector('.btn-text').style.display = loading ? 'none' : '';
    btn.querySelector('.btn-loading').style.display = loading ? '' : 'none';
    btn.disabled = loading;
  }
  function clearErrors() {
    ['email-error', 'password-error'].forEach(id => {
      const el = document.getElementById(id);
      if (el) el.textContent = '';
    });
    errBox.style.display = 'none';
  }
  function showFieldError(id, msg) {
    const el = document.getElementById(id);
    if (el) el.textContent = msg;
    setLoading(btn, false);
  }
});
