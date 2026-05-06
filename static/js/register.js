/**
 * register.js — 회원가입 페이지 전용
 * POST /api/accounts/register/ → 성공 시 로그인 페이지로 이동
 */
document.addEventListener('DOMContentLoaded', () => {
  const form   = document.getElementById('register-form');
  const errBox = document.getElementById('register-error');

  form?.addEventListener('submit', async (e) => {
    e.preventDefault();
    clearErrors();

    const username  = document.getElementById('username').value.trim();
    const email     = document.getElementById('email').value.trim();
    const password  = document.getElementById('password').value;
    const password2 = document.getElementById('password2').value;

    // 클라이언트 검증
    let valid = true;
    if (!username) { showFieldError('username-error', '사용자명을 입력하세요.'); valid = false; }
    if (!email)    { showFieldError('email-error', '이메일을 입력하세요.'); valid = false; }
    if (password.length < 8) { showFieldError('password-error', '비밀번호는 8자 이상이어야 합니다.'); valid = false; }
    if (password !== password2) { showFieldError('password2-error', '비밀번호가 일치하지 않습니다.'); valid = false; }
    if (!valid) return;

    try {
      const { res, data } = await Api.post('/accounts/register/', { username, email, password, password2 });

      if (!res.ok) {
        // DRF 필드별 에러를 매핑
        const fieldMap = { username: 'username-error', email: 'email-error', password: 'password-error' };
        let shown = false;
        for (const [field, elId] of Object.entries(fieldMap)) {
          if (data[field]) { showFieldError(elId, data[field][0]); shown = true; }
        }
        if (!shown) {
          errBox.textContent = '가입 처리 중 오류가 발생했습니다.';
          errBox.style.display = 'block';
        }
        return;
      }

      // 가입 즉시 JWT 저장 후 메인으로
      Auth.save(data.access, data.refresh, data.user);
      window.location.href = '/';
    } catch {
      errBox.textContent = '서버 오류가 발생했습니다.';
      errBox.style.display = 'block';
    }
  });

  function clearErrors() {
    ['username-error','email-error','password-error','password2-error'].forEach(id => {
      const el = document.getElementById(id);
      if (el) el.textContent = '';
    });
    errBox.style.display = 'none';
  }
  function showFieldError(id, msg) {
    const el = document.getElementById(id);
    if (el) el.textContent = msg;
  }
});
