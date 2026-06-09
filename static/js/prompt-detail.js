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

  const PROMPT_TYPE_LABELS = {
    single_prompt: '단일 프롬프트',
    agent_recipe: '에이전트 레시피',
    mcp_package: 'MCP 패키지',
  };
  const AGENT_PATTERN_LABELS = {
    sequential: 'Sequential',
    react: 'ReAct',
    reflection: 'Reflection',
    multi_agent: 'Multi-agent',
  };

  const I18N = {
    previous_output: {
      full: '이전 결과 전체 전달',
      summarize_500: '500자 요약 전달',
      selective: '핵심만 추출 전달',
      vector_query: '벡터 DB 검색 후 필요한 부분만',
      none: '이전 결과 사용 안 함',
    },
    memory_scope: {
      this_step_only: '이 단계만',
      all_previous: '이전 모든 단계 참고',
      user_session: '사용자 세션 전체',
    },
    fallback_action: {
      skip_step: '실패 시 건너뛰기',
      use_default: '실패 시 기본값 사용',
      fail_fast: '즉시 중단',
    },
    pattern: {
      Sequential: '순차 실행',
      ReAct: '판단·실행 반복',
      Reflection: '자기 검토',
      MultiAgent: '멀티 에이전트',
    },
    evaluator: {
      rule: '규칙 기반 자동',
      llm_judge: 'AI 자동 채점',
      human: '사람 검토 필요',
      none: '검증 없음',
    },
    on_fail: {
      retry: '재시도',
      skip: '건너뛰기',
      escalate: '상위 보고',
    },
    knowledge_type: {
      url: '웹 링크',
      document: '문서',
      dataset: '데이터셋',
      api: 'API',
      rag_collection: '지식 베이스',
    },
    knowledge_usage: {
      always: '항상 참고',
      if_needed: '필요 시',
      fallback: '대체용',
    },
  };

  function t(category, value) {
    return I18N[category]?.[value] || value;
  }

  function renderBlueprintStepDetails(s) {
    const cp = s.context_policy || {};
    const hp = s.harness_policy || {};
    const krefs = s.knowledge_refs || [];
    const vc = s.verification_criteria || {};
    return `
      ${krefs.length ? `
      <details class="step-policy" open>
        <summary>참고 자료 (${krefs.length}개)</summary>
        <div class="policy-block">
          ${krefs.map(k => `
            <div class="knowledge-item">
              <span class="kn-type">${Api.escapeHtml(t('knowledge_type', k.type || 'document'))}</span>
              <strong>${Api.escapeHtml(k.source || '')}</strong>
              <span class="kn-usage">(${Api.escapeHtml(t('knowledge_usage', k.usage || 'always'))})</span>
              ${k.description ? `<div class="kn-desc">${Api.escapeHtml(k.description)}</div>` : ''}
            </div>
          `).join('')}
        </div>
      </details>` : ''}
      <details class="step-policy">
        <summary>연결 방식 (이전 단계 → 이 단계)</summary>
        <div class="policy-block">
          <div><span class="policy-key">전달 방식:</span> ${Api.escapeHtml(t('previous_output', cp.previous_output_strategy || 'full'))}</div>
          <div><span class="policy-key">참고 범위:</span> ${Api.escapeHtml(t('memory_scope', cp.memory_scope || 'all_previous'))}</div>
          ${cp.reason ? `<div class="policy-reason">${Api.escapeHtml(cp.reason)}</div>` : ''}
        </div>
      </details>
      <details class="step-policy">
        <summary>운영 가이드</summary>
        <div class="policy-block">
          <div><span class="policy-key">제한 시간:</span> ${hp.timeout_seconds || 30}초</div>
          <div><span class="policy-key">재시도:</span> 최대 ${hp.max_retries ?? 2}번</div>
          <div><span class="policy-key">실패 처리:</span> ${Api.escapeHtml(t('fallback_action', hp.fallback_action || 'skip_step'))}</div>
          <div><span class="policy-key">사용 예산:</span> ${(hp.cost_budget_tokens || 2000).toLocaleString()} 토큰</div>
        </div>
      </details>
      <details class="step-policy">
        <summary>완료 판단 기준</summary>
        <div class="policy-block">
          ${(vc.success_signals || []).length ? `
            <div><span class="policy-key">성공 신호:</span></div>
            <ul class="signal-list signal-ok">
              ${vc.success_signals.map(sig => `<li>${Api.escapeHtml(sig)}</li>`).join('')}
            </ul>
          ` : ''}
          ${(vc.failure_signals || []).length ? `
            <div><span class="policy-key">실패 신호:</span></div>
            <ul class="signal-list signal-bad">
              ${vc.failure_signals.map(sig => `<li>${Api.escapeHtml(sig)}</li>`).join('')}
            </ul>
          ` : ''}
          <div><span class="policy-key">검증 방식:</span> ${Api.escapeHtml(t('evaluator', vc.evaluator || 'rule'))}</div>
          <div><span class="policy-key">최소 품질:</span> ${Math.round((vc.min_quality_score || 0.7) * 100)}점</div>
          <div><span class="policy-key">미달 시:</span> ${Api.escapeHtml(t('on_fail', vc.on_fail || 'retry'))}</div>
        </div>
      </details>
    `;
  }

  function renderWorkflowSteps(steps) {
    if (!steps?.length) return '';
    return `
      <ol class="recipe-steps">
        ${steps.map(s => `
          <li class="recipe-step-card">
            <div class="recipe-step-head">
              <span class="recipe-step-num">Step ${s.step || '?'}</span>
              <strong>${Api.escapeHtml(s.name || '')}</strong>
              ${s.tool ? `<span class="tag tag-tool">${Api.escapeHtml(s.tool)}</span>` : ''}
            </div>
            <p class="recipe-step-msg">${Api.escapeHtml(s.system_message || '')}</p>
            ${renderBlueprintStepDetails(s)}
            ${s.code ? `<pre class="recipe-step-code">${Api.escapeHtml(s.code)}</pre>` : ''}
          </li>
        `).join('')}
      </ol>
    `;
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
      const isRecipe = p.prompt_type === 'agent_recipe';
      const previewContent = isPaid ? getPaidPreviewContent(p.content, 3) : Api.escapeHtml(p.content);
      const typeLabel = PROMPT_TYPE_LABELS[p.prompt_type] || p.prompt_type;
      const patternLabel = p.agent_pattern ? (AGENT_PATTERN_LABELS[p.agent_pattern] || p.agent_pattern) : '';
      const recipeCategoryName = p.recipe_category?.name || '';
      const workflowHtml = isRecipe && (p.workflow_steps || []).length
        ? `
          <div class="recipe-workflow-section">
            <h3 class="section-title">자동화 단계 (5-Layer Blueprint)</h3>
            ${patternLabel ? `<p class="recipe-pattern"><span class="tag tag-agent">패턴: ${Api.escapeHtml(patternLabel)}</span></p>` : ''}
            ${renderWorkflowSteps(p.workflow_steps)}
          </div>
          <div class="detail-divider"></div>
        `
        : '';

      detailEl.innerHTML = `
        <div class="detail-header">
          <div class="detail-meta">
            <span class="tag ${isRecipe ? 'tag-agent' : 'tag-type'}">${Api.escapeHtml(typeLabel)}</span>
            ${isRecipe && recipeCategoryName
              ? `<span class="detail-model">${Api.escapeHtml(recipeCategoryName)}</span>`
              : !isRecipe ? `<span class="detail-model">${p.ai_model}</span>` : ''}
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
        ${workflowHtml}
        <div class="prompt-content-box ${isPaid ? 'is-paid-preview' : ''}">
          <div class="content-label">${isRecipe ? '시스템 프롬프트 / 컨텍스트' : '프롬프트 본문'}</div>
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
      loadSimilarRecipes();
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
    const isRecipeAuthor = prompt.prompt_type === 'agent_recipe' && isAuthor && Auth.isLoggedIn();
    if (!isRecipeAuthor) {
      agentSection.style.display = 'none';
      return;
    }
    agentSection.style.display = '';
    if (transformBtn) {
      transformBtn.style.display = '';
      transformBtn.onclick = startTransform;
    }
    loadLatestAgentResult();
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
    const steps = agent.decomposed_steps || [];
    transformStatus.style.display = 'none';
    if (!steps.length) {
      transformResult.style.display = 'none';
      transformError.style.display = '';
      transformError.textContent =
        '변환은 완료됐지만 단계가 비어 있습니다. 다시 「설계서로 변환하기」를 눌러 주세요.';
      return;
    }
    transformError.style.display = 'none';
    transformResult.style.display = '';
    const overallPatternEl = document.getElementById('overall-pattern');
    const knowledgeSummaryEl = document.getElementById('knowledge-summary');
    const contextSummaryEl = document.getElementById('context-summary');
    const harnessSummaryEl = document.getElementById('harness-summary');
    const qualitySummaryEl = document.getElementById('quality-summary');
    if (overallPatternEl) {
      overallPatternEl.textContent = t('pattern', agent.overall_pattern || 'Sequential');
    }
    const knowledgeSet = new Set();
    steps.forEach(s => {
      (s.knowledge_refs || []).forEach(k => {
        if (k.source) knowledgeSet.add(k.source);
      });
    });
    if (knowledgeSummaryEl) {
      knowledgeSummaryEl.textContent = knowledgeSet.size
        ? Array.from(knowledgeSet).join(', ')
        : '범용 도구 사용';
    }
    if (contextSummaryEl) {
      contextSummaryEl.textContent = agent.context_strategy_summary || '—';
    }
    if (harnessSummaryEl) {
      harnessSummaryEl.textContent = agent.harness_strategy_summary || '—';
    }
    if (qualitySummaryEl) {
      qualitySummaryEl.textContent = agent.quality_strategy_summary || '—';
    }
    const stepsEl = document.getElementById('agent-steps');
    stepsEl.innerHTML = steps.map(s => `
      <li class="agent-step-card">
        <div class="step-header">
          <strong>${Api.escapeHtml(s.name || `Step ${s.step}`)}</strong>
          ${s.tool ? `<span class="step-tool">${Api.escapeHtml(s.tool)}</span>` : ''}
        </div>
        <p class="step-instruction">${Api.escapeHtml(s.system_message || '')}</p>
        ${renderBlueprintStepDetails(s)}
      </li>
    `).join('');
    document.getElementById('confidence').textContent =
      Math.round((agent.confidence_score || 0) * 100) + '%';
    if (agentSection) agentSection.style.display = '';
  }

  async function loadSimilarRecipes() {
    const section = document.getElementById('similar-recipes-section');
    const list = document.getElementById('similar-recipes-list');
    if (!section || !list) return;
    try {
      const { res, data } = await Api.get(`/prompts/${promptId}/similar/`);
      if (!res.ok || !data?.length) return;
      section.style.display = '';
      list.innerHTML = data.map(item => {
        const typeTag = item.prompt_type === 'agent_recipe'
          ? '<span class="tag tag-agent tag-sm">레시피</span>'
          : '<span class="tag tag-type tag-sm">프롬프트</span>';
        const pattern = item.agent_pattern
          ? ` · ${Api.escapeHtml(AGENT_PATTERN_LABELS[item.agent_pattern] || item.agent_pattern)}`
          : '';
        return `
          <li class="similar-recipe-item">
            <a href="/prompts/${item.id}/">${Api.escapeHtml(item.title)}</a>
            ${typeTag}
            <span class="text-muted">유사도 ${(item.similarity * 100).toFixed(1)}%${pattern}</span>
          </li>
        `;
      }).join('');
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
    const maxWait = 300000;
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
          return;
        }
      } catch {
        /* retry on next tick */
      }
      if (Date.now() - started > maxWait) {
        clearInterval(pollTimer);
        try {
          const { res, data } = await Api.get(`/prompts/${promptId}/agent/`);
          if (res.ok && data?.decomposed_steps?.length) {
            renderAgentResult(data);
            if (transformBtn) transformBtn.disabled = false;
            return;
          }
        } catch {
          /* fall through to timeout message */
        }
        transformStatus.style.display = 'none';
        transformError.style.display = '';
        transformError.textContent =
          '변환 시간이 초과되었습니다. 잠시 후 새로고침하거나 다시 시도해 주세요.';
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
