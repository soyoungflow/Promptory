/**
 * prompt-detail.js — 프롬프트 상세 페이지 전용
 * 프롬프트 로딩, 좋아요/북마크 토글, 댓글 CRUD
 */
document.addEventListener('DOMContentLoaded', () => {
  const page      = document.querySelector('.detail-page');
  const promptId  = page?.dataset.promptId;
  if (!promptId) return;

  const detailEl  = document.getElementById('prompt-detail');
  const actionBar = document.getElementById('action-bar');
  const likeBtn   = document.getElementById('like-btn');
  const likeCount = document.getElementById('like-count');
  const bmBtn     = document.getElementById('bookmark-btn');
  const authorAct = document.getElementById('author-actions');
  const commentList = document.getElementById('comment-list');
  const commentForm = document.getElementById('comment-form');
  const loginPrompt = document.getElementById('comment-login-prompt');
  const parentInput = document.getElementById('comment-parent-id');
  const replyInd    = document.getElementById('reply-indicator');
  const replyToText = document.getElementById('reply-to-text');
  const cancelReply = document.getElementById('cancel-reply-btn');

  if (!Auth.isLoggedIn()) {
    if (commentForm) commentForm.style.display = 'none';
    if (loginPrompt) loginPrompt.style.display = '';
  }

  // 프롬프트 상세 로딩
  async function loadPrompt() {
    try {
      const { data: p } = await Api.get(`/prompts/${promptId}/`);

      const isAuthor = String(Auth.getUserId()) === String(p.user_id);
      const editUrl  = `/prompts/${promptId}/edit/`;
      const filesHtml = (p.files || []).map(f =>
        `<a class="file-link" href="${Api.safeUrl(f.file)}" target="_blank" rel="noopener">첨부: ${Api.escapeHtml(f.file_name)}</a>`
      ).join('');

      const isPaid = !p.is_free;
      const previewContent = isPaid ? getPaidPreviewContent(p.content, 3) : Api.escapeHtml(p.content);

      detailEl.innerHTML = `
        <div class="detail-header">
          <div class="detail-meta">
            <span class="detail-model">${p.ai_model}</span>
            ${p.is_free
              ? '<span class="tag tag-free">무료</span>'
              : `<span class="tag tag-paid">₩${Number(p.price).toLocaleString()}</span>`}
            <span class="detail-category">${p.category?.name || ''}</span>
          </div>
          <h1 class="detail-title">${Api.escapeHtml(p.title)}</h1>
          <div class="detail-author-row">
            <span class="avatar">${Api.escapeHtml((p.author || '?').charAt(0).toUpperCase())}</span>
            <div>
              <p class="detail-author">by ${Api.escapeHtml(p.author)}</p>
              <p class="detail-date">${new Date(p.created_at).toLocaleDateString('ko-KR')} · 조회 ${p.view_count}</p>
            </div>
          </div>
          ${p.description ? `<p class="detail-desc">${Api.escapeHtml(p.description)}</p>` : ''}
        </div>
        <div class="detail-divider"></div>
        <div class="prompt-content-box ${isPaid ? 'is-paid-preview' : ''}">
          <div class="content-label">프롬프트 본문</div>
          <pre class="prompt-content">${previewContent}</pre>
          ${isPaid ? `
            <div class="paid-overlay">
              <p class="paid-overlay-msg">결제 후에 보기 가능합니다.</p>
            </div>
          ` : ''}
          ${isPaid ? '' : '<button class="btn btn-copy" id="copy-btn">복사</button>'}
        </div>
        ${(p.tags||[]).length ? `<div class="detail-tags">${p.tags.map(t=>`<span class="tag">#${Api.escapeHtml(t.name)}</span>`).join('')}</div>` : ''}
        ${filesHtml ? `<div class="detail-files"><strong>첨부 파일:</strong> ${filesHtml}</div>` : ''}
      `;

      document.querySelector('#comment-count').textContent = `(${p.comment_count})`;

      // 복사 버튼
      document.getElementById('copy-btn')?.addEventListener('click', () => {
        navigator.clipboard.writeText(p.content).then(() => {
          const btn = document.getElementById('copy-btn');
          btn.textContent = '복사됨 ✓';
          setTimeout(() => { btn.textContent = '복사'; }, 2000);
        });
      });

      // 액션 바
      likeCount.textContent = p.like_count;
      likeBtn.classList.toggle('active', p.is_liked);
      bmBtn.classList.toggle('active', p.is_bookmarked);
      actionBar.style.display = 'flex';
      if (isAuthor) {
        authorAct.style.display = 'flex';
        document.getElementById('edit-btn').href = editUrl;
        document.getElementById('delete-btn')?.addEventListener('click', () => deletePrompt());
      }

      setupAgentSection(p, isAuthor);
      loadComments();
    } catch {
      detailEl.innerHTML = '<div class="error-state">프롬프트를 불러오지 못했습니다.</div>';
    }
  }

  function getPaidPreviewContent(content, lines = 3) {
    const raw = String(content || '');
    const preview = raw.split('\n').slice(0, lines).join('\n');
    return Api.escapeHtml(preview);
  }

  // 좋아요 토글
  likeBtn?.addEventListener('click', async () => {
    if (!Auth.isLoggedIn()) return (location.href = '/accounts/login/');
    const { data } = await Api.post(`/prompts/${promptId}/like/`);
    likeCount.textContent = data.like_count;
    likeBtn.classList.toggle('active', data.liked);
  });

  // 북마크 토글
  bmBtn?.addEventListener('click', async () => {
    if (!Auth.isLoggedIn()) return (location.href = '/accounts/login/');
    const { data } = await Api.post(`/prompts/${promptId}/bookmark/`);
    bmBtn.classList.toggle('active', data.bookmarked);
    bmBtn.querySelector('.bookmark-icon').textContent = data.bookmarked ? '🔖' : '🔖';
  });

  // 댓글 목록 로딩
  async function loadComments() {
    try {
      const { data } = await Api.get(`/prompts/${promptId}/comments/`);
      if (!data.length) {
        commentList.innerHTML = '<p class="empty-state">첫 댓글을 작성해보세요.</p>';
        return;
      }
      commentList.innerHTML = data.map(renderComment).join('');
      // 대댓글 버튼 바인딩
      commentList.querySelectorAll('.reply-btn').forEach(btn => {
        btn.addEventListener('click', () => setReply(btn.dataset.id, btn.dataset.author));
      });
      // 댓글 삭제 버튼
      commentList.querySelectorAll('.comment-delete-btn').forEach(btn => {
        btn.addEventListener('click', () => deleteComment(btn.dataset.id));
      });
    } catch {
      commentList.innerHTML = '<div class="error-state">댓글을 불러오지 못했습니다.</div>';
    }
  }

  function renderComment(c) {
    const isOwn = Auth.getUserId() !== null && String(Auth.getUserId()) === String(c.user_id);
    const replies = (c.replies||[]).map(r => `
      <div class="comment reply-comment">
        <div class="comment-header">
          <span class="avatar-sm">${Api.escapeHtml((r.author || '?').charAt(0).toUpperCase())}</span>
          <span class="comment-author">↳ ${Api.escapeHtml(r.author)}</span>
          <span class="comment-date">${new Date(r.created_at).toLocaleDateString('ko-KR')}</span>
        </div>
        <p class="comment-body">${r.is_deleted ? '<em class="deleted-comment">삭제된 댓글입니다.</em>' : Api.escapeHtml(r.content)}</p>
      </div>`).join('');
    return `
      <div class="comment">
        <div class="comment-header">
          <span class="avatar-sm">${Api.escapeHtml((c.author || '?').charAt(0).toUpperCase())}</span>
          <span class="comment-author">${Api.escapeHtml(c.author)}</span>
          <span class="comment-date">${new Date(c.created_at).toLocaleDateString('ko-KR')}</span>
          <div class="comment-actions">
            ${Auth.isLoggedIn() ? `<button class="btn-text-link reply-btn" data-id="${c.id}" data-author="${Api.escapeHtml(c.author)}">답글</button>` : ''}
            ${isOwn ? `<button class="btn-text-link comment-delete-btn" data-id="${c.id}">삭제</button>` : ''}
          </div>
        </div>
        <p class="comment-body">${c.is_deleted ? '<em class="deleted-comment">삭제된 댓글입니다.</em>' : Api.escapeHtml(c.content)}</p>
        ${replies}
      </div>`;
  }

  // 대댓글 모드 설정
  function setReply(parentId, author) {
    parentInput.value = parentId;
    replyToText.textContent = `@${author} 에게 답글 중`;
    replyInd.style.display = 'inline-flex';
    document.getElementById('comment-content').focus();
  }
  cancelReply?.addEventListener('click', () => {
    parentInput.value = '';
    replyInd.style.display = 'none';
  });

  // 댓글 등록
  commentForm?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const content  = document.getElementById('comment-content').value.trim();
    const parentId = parentInput.value || null;
    if (!content) return;

    const body = { content };
    if (parentId) body.parent = parentId;

    try {
      const { res } = await Api.post(`/prompts/${promptId}/comments/`, body);
      if (res.ok) {
        document.getElementById('comment-content').value = '';
        parentInput.value = '';
        replyInd.style.display = 'none';
        loadComments();
      }
    } catch {}
  });

  // 댓글 Soft Delete
  async function deleteComment(id) {
    if (!confirm('댓글을 삭제하시겠습니까?')) return;
    await Api.delete(`/comments/${id}/`);
    loadComments();
  }

  // 프롬프트 Soft Delete
  async function deletePrompt() {
    if (!confirm('프롬프트를 삭제하시겠습니까?')) return;
    const { res } = await Api.delete(`/prompts/${promptId}/`);
    if (res.ok) window.location.href = '/';
  }

  // ── Phase 4: 에이전트 변환 (인라인, 작성자만 버튼) ──
  const agentSection = document.getElementById('agent-section');
  const transformBtn = document.getElementById('transform-btn');
  const transformStatus = document.getElementById('transform-status');
  const transformResult = document.getElementById('transform-result');
  const transformError = document.getElementById('transform-error');
  const elapsedEl = document.getElementById('elapsed');
  let taskSocket = null;
  let pollTimer = null;

  function setupAgentSection(prompt, isAuthor) {
    if (!agentSection) return;
    agentSection.style.display = '';
    if (transformBtn) {
      transformBtn.style.display = isAuthor && Auth.isLoggedIn() ? '' : 'none';
    }
    loadLatestAgentResult();
    if (isAuthor && transformBtn) {
      transformBtn.onclick = startTransform;
    }
  }

  async function loadLatestAgentResult() {
    try {
      const { res, data } = await Api.get(`/prompts/${promptId}/agent/`);
      if (res.ok && data) renderAgentResult(data);
    } catch {
      /* no transformation yet */
    }
  }

  function renderAgentResult(agent) {
    if (!transformResult) return;
    transformStatus.style.display = 'none';
    transformError.style.display = 'none';
    transformResult.style.display = '';
    const stepsEl = document.getElementById('agent-steps');
    const steps = agent.decomposed_steps || [];
    stepsEl.innerHTML = steps.map(s => `
      <li>
        <strong>${Api.escapeHtml(s.name || `Step ${s.step}`)}</strong>
        <p>${Api.escapeHtml(s.system_message || '')}</p>
        ${s.tool ? `<small>도구: ${Api.escapeHtml(s.tool)}</small>` : ''}
      </li>
    `).join('');
    document.getElementById('confidence').textContent =
      Math.round((agent.confidence_score || 0) * 100) + '%';
    loadSimilarPrompts();
  }

  async function loadSimilarPrompts() {
    const box = document.getElementById('similar-prompts');
    const list = document.getElementById('similar-list');
    if (!box || !list) return;
    try {
      const { res, data } = await Api.get(`/prompts/${promptId}/similar/`);
      if (!res.ok || !data?.length) return;
      box.style.display = '';
      list.innerHTML = data.map(item => `
        <li><a href="/prompts/${item.id}/">${Api.escapeHtml(item.title)}</a>
        <span class="text-muted"> (${(item.similarity * 100).toFixed(1)}%)</span></li>
      `).join('');
    } catch {
      /* optional */
    }
  }

  function connectTaskWebSocket(taskId) {
    if (!Auth.isLoggedIn()) return;
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const token = encodeURIComponent(Auth.getAccess() || '');
    const url = `${protocol}//${window.location.host}/ws/tasks/?token=${token}`;
    try {
      taskSocket = new WebSocket(url);
      taskSocket.onmessage = (event) => {
        const msg = JSON.parse(event.data);
        if (msg.task_id !== taskId) return;
        if (msg.status === 'SUCCESS' || msg.status === 'FAIL') {
          onTaskFinished(msg);
        }
      };
      const hint = document.getElementById('transform-ws-hint');
      if (hint) hint.textContent = '실시간 알림 연결됨';
    } catch {
      /* polling fallback only */
    }
  }

  async function onTaskFinished(taskPayload) {
    if (pollTimer) clearInterval(pollTimer);
    if (taskSocket) {
      taskSocket.close();
      taskSocket = null;
    }
    if (taskPayload.status === 'FAIL') {
      transformStatus.style.display = 'none';
      transformError.style.display = '';
      transformError.textContent = taskPayload.error_message || '변환에 실패했습니다.';
      if (transformBtn) transformBtn.disabled = false;
      return;
    }
    const { res, data } = await Api.get(`/prompts/${promptId}/agent/`);
    if (res.ok) renderAgentResult(data);
    if (transformBtn) transformBtn.disabled = false;
  }

  async function pollTaskStatus(taskId) {
    const started = Date.now();
    const maxWait = 120000;
    pollTimer = setInterval(async () => {
      elapsedEl.textContent = Math.floor((Date.now() - started) / 1000);
      try {
        const { res, data } = await Api.get(`/tasks/${taskId}/status/`);
        if (!res.ok) return;
        if (data.status === 'SUCCESS' || data.status === 'FAIL') {
          onTaskFinished({
            task_id: taskId,
            status: data.status,
            error_message: data.error_message,
          });
        }
      } catch {
        /* retry on next tick */
      }
      if (Date.now() - started > maxWait) {
        clearInterval(pollTimer);
        transformStatus.style.display = 'none';
        transformError.style.display = '';
        transformError.textContent = '변환 시간이 초과되었습니다.';
        if (transformBtn) transformBtn.disabled = false;
      }
    }, 1000);
  }

  async function startTransform() {
    if (!Auth.isLoggedIn()) {
      location.href = '/accounts/login/';
      return;
    }
    transformError.style.display = 'none';
    transformResult.style.display = 'none';
    transformBtn.disabled = true;
    transformStatus.style.display = '';
    elapsedEl.textContent = '0';

    try {
      const { res, data } = await Api.post(`/prompts/${promptId}/transform/`, {});
      if (!res.ok) {
        transformStatus.style.display = 'none';
        transformError.style.display = '';
        transformError.textContent = data?.detail || '변환 요청에 실패했습니다.';
        transformBtn.disabled = false;
        return;
      }
      connectTaskWebSocket(data.task_id);
      pollTaskStatus(data.task_id);
    } catch {
      transformStatus.style.display = 'none';
      transformError.style.display = '';
      transformError.textContent = '서버 오류가 발생했습니다.';
      transformBtn.disabled = false;
    }
  }

  loadPrompt();
});
