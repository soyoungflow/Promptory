/**
 * blueprint-design.js — 설계서 만들기 전용 위저드
 */
document.addEventListener('DOMContentLoaded', () => {
  const page = document.querySelector('.blueprint-page');
  if (!page) return;

  const designIdFromPage = page.dataset.designId || '';
  let currentDesignId = designIdFromPage || null;

  const wizard = document.getElementById('blueprint-wizard');
  const form = document.getElementById('blueprint-form');
  const formError = document.getElementById('blueprint-form-error');
  const processing = document.getElementById('blueprint-processing');
  const resultSection = document.getElementById('blueprint-result');
  const pageError = document.getElementById('blueprint-error');
  const elapsedEl = document.getElementById('blueprint-elapsed');
  const publishBtn = document.getElementById('publish-recipe-btn');
  const prefillBtn = document.getElementById('prefill-recipe-btn');
  const publishError = document.getElementById('publish-error');
  const publishSuccess = document.getElementById('publish-success');
  const blueprintActions = document.getElementById('blueprint-actions');
  const deleteBtn = document.getElementById('blueprint-delete-btn');
  const wsHint = document.getElementById('blueprint-ws-hint');

  let pollTimer = null;
  let transformEnqueueInFlight = false;

  const TASK_STORAGE_PREFIX = 'promptory_blueprint_task_';

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

  function requireLogin() {
    if (Auth.isLoggedIn()) return true;
    location.href = '/accounts/login/?next=' + encodeURIComponent(location.pathname + location.search);
    return false;
  }

  function renderBlueprintStepDetails(s) {
    const cp = s.context_policy || {};
    const hp = s.harness_policy || {};
    const krefs = s.knowledge_refs || [];
    const vc = s.verification_criteria || {};
    return `
      ${krefs.length ? `
      <details class="step-policy" open>
        <summary>📚 참고 자료 (${krefs.length}개)</summary>
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
        <summary>🎯 이전 단계와 어떻게 연결되나요?</summary>
        <div class="policy-block">
          <div><span class="policy-key">전달 방식:</span> ${Api.escapeHtml(t('previous_output', cp.previous_output_strategy || 'full'))}</div>
          <div><span class="policy-key">참고 범위:</span> ${Api.escapeHtml(t('memory_scope', cp.memory_scope || 'all_previous'))}</div>
          ${cp.reason ? `<div class="policy-reason">${Api.escapeHtml(cp.reason)}</div>` : ''}
        </div>
      </details>
      <details class="step-policy">
        <summary>🔧 안전하게 실행하기</summary>
        <div class="policy-block">
          <div><span class="policy-key">재시도:</span> ${hp.max_retries ?? 0}회</div>
          <div><span class="policy-key">실패 시:</span> ${Api.escapeHtml(t('fallback_action', hp.fallback_action || 'fail_fast'))}</div>
          ${hp.timeout_seconds ? `<div><span class="policy-key">타임아웃:</span> ${hp.timeout_seconds}초</div>` : ''}
        </div>
      </details>
      ${vc.evaluator && vc.evaluator !== 'none' ? `
      <details class="step-policy">
        <summary>✅ 잘 됐는지 어떻게 알 수 있나요?</summary>
        <div class="policy-block">
          <div><span class="policy-key">방식:</span> ${Api.escapeHtml(t('evaluator', vc.evaluator))}</div>
          ${vc.criteria ? `<div class="policy-reason">${Api.escapeHtml(vc.criteria)}</div>` : ''}
          <div><span class="policy-key">미달 시:</span> ${Api.escapeHtml(t('on_fail', vc.on_fail || 'retry'))}</div>
        </div>
      </details>` : ''}
    `;
  }

  function renderTransformation(agent) {
    const steps = agent?.decomposed_steps || [];
    if (!steps.length) {
      showPageError('설계는 완료됐지만 단계가 비어 있습니다. 다시 시도해 주세요.');
      return;
    }
    wizard.style.display = 'none';
    processing.style.display = 'none';
    pageError.style.display = 'none';
    resultSection.style.display = '';

    document.getElementById('bp-overall-pattern').textContent =
      t('pattern', agent.overall_pattern || 'Sequential');

    const knowledgeSet = new Set();
    steps.forEach(s => {
      (s.knowledge_refs || []).forEach(k => {
        if (k.source) knowledgeSet.add(k.source);
      });
    });
    document.getElementById('bp-knowledge-summary').textContent = knowledgeSet.size
      ? Array.from(knowledgeSet).join(', ')
      : '범용 도구 사용';
    document.getElementById('bp-context-summary').textContent = agent.context_strategy_summary || '—';
    document.getElementById('bp-harness-summary').textContent = agent.harness_strategy_summary || '—';
    document.getElementById('bp-quality-summary').textContent = agent.quality_strategy_summary || '—';

    document.getElementById('bp-agent-steps').innerHTML = steps.map(s => `
      <li class="agent-step-card">
        <div class="step-header">
          <strong>${Api.escapeHtml(s.name || `Step ${s.step}`)}</strong>
          ${s.tool ? `<span class="step-tool">${Api.escapeHtml(s.tool)}</span>` : ''}
        </div>
        <p class="step-instruction">${Api.escapeHtml(s.system_message || '')}</p>
        ${renderBlueprintStepDetails(s)}
      </li>
    `).join('');
    document.getElementById('bp-confidence').textContent =
      Math.round((agent.confidence_score || 0) * 100) + '%';
  }

  function showPageError(msg) {
    processing.style.display = 'none';
    pageError.style.display = '';
    pageError.textContent = msg;
  }

  function saveTaskForDesign(designId, taskId) {
    try {
      sessionStorage.setItem(`${TASK_STORAGE_PREFIX}${designId}`, taskId);
    } catch {
      /* ignore */
    }
  }

  function loadTaskForDesign(designId) {
    try {
      return sessionStorage.getItem(`${TASK_STORAGE_PREFIX}${designId}`);
    } catch {
      return null;
    }
  }

  function clearTaskForDesign(designId) {
    try {
      sessionStorage.removeItem(`${TASK_STORAGE_PREFIX}${designId}`);
    } catch {
      /* ignore */
    }
  }

  async function fetchDesignResult(designId) {
    const { res, data } = await Api.get(`/blueprints/design/${designId}/`);
    if (!res.ok || data.status !== 'success' || !data.transformation) {
      showPageError(data?.detail || '설계 결과를 불러오지 못했습니다.');
      wizard.style.display = '';
      return false;
    }
    clearTaskForDesign(designId);
    renderTransformation(data.transformation);
    return true;
  }

  async function enqueueBlueprintTransform(design) {
    const promptId = design?.source_prompt_id;
    const designId = design?.id;
    if (!promptId || !designId || transformEnqueueInFlight) {
      return { ok: false };
    }
    if (design.status === 'success') {
      return { ok: true, taskId: null };
    }

    transformEnqueueInFlight = true;
    try {
      const { res, data } = await Api.post(`/prompts/${promptId}/transform/`, {
        blueprint_design_id: designId,
      });
      if (!res.ok) {
        console.warn('transform enqueue failed', data);
        return { ok: false, detail: data?.detail };
      }
      const taskId = data.task_id;
      if (taskId) saveTaskForDesign(designId, taskId);
      return { ok: true, taskId, statusUrl: data.status_url };
    } catch {
      return { ok: false };
    } finally {
      transformEnqueueInFlight = false;
    }
  }

  async function loadDesign(id) {
    if (!requireLogin()) return;
    try {
      const { res, data } = await Api.get(`/blueprints/design/${id}/`);
      if (!res.ok) {
        showPageError(data?.detail || '설계서를 불러오지 못했습니다.');
        return;
      }
      currentDesignId = data.id;
      blueprintActions.style.display = '';
      if (data.status === 'success' && data.transformation) {
        renderTransformation(data.transformation);
        if (data.recipe) {
          publishSuccess.style.display = '';
          publishSuccess.innerHTML =
            `이미 마켓에 등록됨 — <a href="/prompts/${data.recipe}/">보기</a>`;
          publishBtn.disabled = true;
          prefillBtn.disabled = true;
        }
      } else if (data.status === 'processing' || data.status === 'pending') {
        let taskId = loadTaskForDesign(id);
        if (!taskId) {
          const enq = await enqueueBlueprintTransform(data);
          if (!enq.ok) {
            showPageError(enq.detail || 'AI 변환 요청에 실패했습니다.');
            wizard.style.display = '';
            return;
          }
          taskId = enq.taskId;
        }
        startTaskPolling(id, taskId);
      } else if (data.status === 'fail') {
        showPageError('설계 생성에 실패했습니다. 새로 시도해 주세요.');
        wizard.style.display = '';
      }
    } catch {
      showPageError('서버 오류가 발생했습니다.');
    }
  }

  function stopPolling() {
    if (pollTimer) {
      clearInterval(pollTimer);
      pollTimer = null;
    }
  }

  function startTaskPolling(designId, taskId) {
    if (!taskId) {
      showPageError('변환 작업 ID를 찾을 수 없습니다. 다시 시도해 주세요.');
      wizard.style.display = '';
      return;
    }
    wizard.style.display = 'none';
    processing.style.display = '';
    elapsedEl.textContent = '0';
    if (wsHint) {
      wsHint.textContent = `GET /api/tasks/${taskId}/status/ 폴링 중…`;
    }
    pollTaskUntilReady(designId, taskId);
  }

  async function pollTaskUntilReady(designId, taskId) {
    const started = Date.now();
    const maxWait = 300000;
    stopPolling();
    pollTimer = setInterval(async () => {
      elapsedEl.textContent = Math.floor((Date.now() - started) / 1000);
      try {
        const { res, data } = await Api.get(`/tasks/${taskId}/status/`);
        if (!res.ok) return;

        const taskStatus = data.status;
        if (wsHint) {
          wsHint.textContent = `Task ${taskStatus} · GET /api/tasks/${taskId}/status/`;
        }

        if (taskStatus === 'SUCCESS') {
          stopPolling();
          await fetchDesignResult(designId);
        } else if (taskStatus === 'FAIL') {
          stopPolling();
          clearTaskForDesign(designId);
          showPageError(data.error_message || '설계 생성에 실패했습니다.');
          wizard.style.display = '';
        }
      } catch {
        /* retry */
      }
      if (Date.now() - started > maxWait) {
        stopPolling();
        showPageError('예상보다 오래 걸리네요. 다시 시도하거나 잠시 후 새로고침해 주세요.');
      }
    }, 1500);
  }

  form?.addEventListener('submit', async (e) => {
    e.preventDefault();
    if (!requireLogin()) return;

    const brief = document.getElementById('design-brief').value.trim();
    const title = document.getElementById('design-title').value.trim();
    const extra = document.getElementById('design-context').value.trim();

    formError.style.display = 'none';
    if (brief.length < 10) {
      formError.style.display = '';
      formError.textContent = '자동화 요청을 10자 이상 입력해 주세요.';
      return;
    }

    const submitBtn = document.getElementById('blueprint-submit-btn');
    submitBtn.disabled = true;

    try {
      const { res, data } = await Api.post('/blueprints/design/', {
        title,
        brief,
        extra_context: extra,
      });
      if (!res.ok) {
        formError.style.display = '';
        formError.textContent = data?.detail || data?.brief?.[0] || '설계서 생성에 실패했습니다.';
        submitBtn.disabled = false;
        return;
      }
      currentDesignId = data.id;
      if (data.id && !designIdFromPage) {
        history.replaceState(null, '', `/blueprints/${data.id}/`);
      }

      const enq = await enqueueBlueprintTransform({
        id: data.id,
        source_prompt_id: data.prompt_id,
        status: 'pending',
      });
      if (!enq.ok) {
        formError.style.display = '';
        formError.textContent = enq.detail || 'AI 변환 요청에 실패했습니다. 잠시 후 다시 시도해 주세요.';
        submitBtn.disabled = false;
        return;
      }

      startTaskPolling(currentDesignId, enq.taskId);
    } catch {
      formError.style.display = '';
      formError.textContent = '서버 오류가 발생했습니다.';
      submitBtn.disabled = false;
    }
  });

  const BLUEPRINT_PREFILL_KEY = 'promptory_blueprint_prefill';

  async function stashBlueprintForForm() {
    const { res, data } = await Api.get(`/blueprints/design/${currentDesignId}/`);
    if (!res.ok || data.status !== 'success' || !data.transformation) {
      throw new Error('설계서 데이터를 불러오지 못했습니다.');
    }
    const category = document.getElementById('publish-category')?.value.trim() || '';
    sessionStorage.setItem(BLUEPRINT_PREFILL_KEY, JSON.stringify({
      design_id: currentDesignId,
      title: data.title || '',
      brief: data.brief || '',
      extra_context: data.extra_context || '',
      recipe_category_name: category,
      transformation: data.transformation,
      saved_at: Date.now(),
    }));
  }

  prefillBtn?.addEventListener('click', async () => {
    if (!currentDesignId) return;
    if (!requireLogin()) return;
    prefillBtn.disabled = true;
    try {
      await stashBlueprintForForm();
      location.href = `/prompts/new/?from_blueprint=${currentDesignId}`;
    } catch {
      publishError.style.display = '';
      publishError.textContent = '등록 폼으로 데이터를 옮기지 못했습니다. 잠시 후 다시 시도해 주세요.';
      prefillBtn.disabled = false;
    }
  });

  deleteBtn?.addEventListener('click', async () => {
    if (!currentDesignId || !requireLogin()) return;
    const hasRecipe = publishSuccess.style.display !== 'none';
    const msg = hasRecipe
      ? '이 설계서와 마켓에 등록된 에이전트 설계서를 모두 삭제할까요?'
      : '이 설계서를 삭제할까요?';
    if (!window.confirm(msg)) return;
    deleteBtn.disabled = true;
    try {
      const { res, data } = await Api.delete(`/blueprints/design/${currentDesignId}/`);
      if (!res.ok) {
        showPageError(data?.detail || '설계서 삭제에 실패했습니다.');
        deleteBtn.disabled = false;
        return;
      }
      window.location.href = '/library/';
    } catch {
      showPageError('서버 오류가 발생했습니다.');
      deleteBtn.disabled = false;
    }
  });

  publishBtn?.addEventListener('click', async () => {
    if (!currentDesignId || !requireLogin()) return;
    publishError.style.display = 'none';
    publishSuccess.style.display = 'none';
    publishBtn.disabled = true;

    const category = document.getElementById('publish-category').value.trim();
    try {
      const { res, data } = await Api.post(
        `/blueprints/design/${currentDesignId}/publish-recipe/`,
        { recipe_category_name: category },
      );
      if (!res.ok) {
        publishError.style.display = '';
        publishError.textContent = data?.detail || '마켓 등록에 실패했습니다.';
        publishBtn.disabled = false;
        return;
      }
      publishSuccess.style.display = '';
      publishSuccess.innerHTML =
        `에이전트 설계서가 등록되었습니다 — <a href="${data.recipe_url}">보기</a> · <a href="${data.edit_url}">수정</a>`;
    } catch {
      publishError.style.display = '';
      publishError.textContent = '서버 오류가 발생했습니다.';
      publishBtn.disabled = false;
    }
  });

  if (designIdFromPage) {
    loadDesign(designIdFromPage);
  } else if (!Auth.isLoggedIn()) {
    form.style.opacity = '0.6';
    formError.style.display = '';
    formError.textContent = '설계서를 만들려면 로그인이 필요합니다.';
  }
});
