/**
 * prompt-form.js — 프롬프트 생성/수정 페이지
 */
document.addEventListener('DOMContentLoaded', () => {
  if (typeof Auth === 'undefined' || typeof Api === 'undefined') return;

  const page = document.querySelector('.form-page');
  const form = document.getElementById('prompt-form');
  if (!page || !form) return;

  const loggedIn = Auth.isLoggedIn();

  const promptId = page.dataset.promptId;
  const isEdit = page.dataset.mode === 'edit' && !!promptId;

  const promptTypeEl = document.getElementById('prompt-type');
  const categoryEl = document.getElementById('category');
  const aiModelEl = document.getElementById('ai-model');
  const titleEl = document.getElementById('title');
  const descriptionEl = document.getElementById('description');
  const contentEl = document.getElementById('content');
  const isFreeEl = document.getElementById('is-free');
  const priceEl = document.getElementById('price');
  const priceGroup = document.getElementById('price-group');
  const fileInput = document.getElementById('file-input');
  const tagInput = document.getElementById('tag-input');
  const tagList = document.getElementById('tag-list');
  const formError = document.getElementById('form-error');
  const submitBtn = document.getElementById('submit-btn');
  const btnText = submitBtn?.querySelector('.btn-text');
  const btnLoading = submitBtn?.querySelector('.btn-loading');

  const CATEGORY_AI_MODELS = {
    ChatGPT: ['gpt-5-5', 'gpt-5-5-instant'],
    Claude: ['claude-opus-4-7', 'claude-sonnet-4-6'],
    Gemini: ['gemini-3-1-pro', 'gemini-3-0-flash'],
  };

  const AI_MODEL_OPTIONS = [
    { value: 'gpt-5-5', label: 'GPT-5.5' },
    { value: 'gpt-5-5-instant', label: 'GPT-5.5 Instant' },
    { value: 'claude-opus-4-7', label: 'Claude Opus 4.7' },
    { value: 'claude-sonnet-4-6', label: 'Claude Sonnet 4.6' },
    { value: 'gemini-3-1-pro', label: 'Gemini 3.1 Pro' },
    { value: 'gemini-3-0-flash', label: 'Gemini 3.0 Flash' },
    { value: 'other', label: '기타' },
  ];

  const state = {
    tags: [],
  };

  function showTopError(msg) {
    formError.style.display = '';
    formError.textContent = msg;
  }

  function clearTopError() {
    formError.style.display = 'none';
    formError.textContent = '';
  }

  function setSubmitting(on) {
    if (!submitBtn) return;
    submitBtn.disabled = on;
    if (btnText) btnText.style.display = on ? 'none' : '';
    if (btnLoading) btnLoading.style.display = on ? '' : 'none';
  }

  function togglePrice() {
    const free = !!isFreeEl.checked;
    priceGroup.style.display = free ? 'none' : '';
    if (free) priceEl.value = '0';
  }

  function getCategoryNameById(categoryId) {
    const opt = categoryEl.querySelector(`option[value="${categoryId}"]`);
    return (opt?.textContent || '').trim();
  }

  function syncAiModels(categoryId, keepValue = '') {
    const categoryName = getCategoryNameById(categoryId);
    const allowed = categoryName ? CATEGORY_AI_MODELS[categoryName] : null;
    const list = allowed?.length
      ? AI_MODEL_OPTIONS.filter(m => allowed.includes(m.value))
      : AI_MODEL_OPTIONS;

    aiModelEl.innerHTML = '<option value="">모델을 선택하세요</option>';
    list.forEach(({ value, label }) => {
      const opt = document.createElement('option');
      opt.value = value;
      opt.textContent = label;
      aiModelEl.appendChild(opt);
    });

    if (keepValue && list.some(x => x.value === keepValue)) {
      aiModelEl.value = keepValue;
    }
  }

  function renderTags() {
    tagList.innerHTML = state.tags.map(tag => `
      <span class="tag tag-item">
        #${Api.escapeHtml(tag)}
        <button type="button" class="tag-remove" data-tag="${Api.escapeHtml(tag)}">×</button>
      </span>
    `).join('');
  }

  async function loadCategories() {
    const { res, data } = await Api.get('/prompts/categories/');
    if (!res.ok) throw new Error('카테고리를 불러오지 못했습니다.');
    (data.results || []).forEach(cat => {
      const opt = document.createElement('option');
      opt.value = String(cat.id);
      opt.textContent = cat.name;
      categoryEl.appendChild(opt);
    });
    syncAiModels(categoryEl.value || '');
  }

  async function loadPromptForEdit() {
    if (!isEdit) return;
    const { res, data } = await Api.get(`/prompts/${promptId}/`);
    if (!res.ok || !data) throw new Error('기존 프롬프트를 불러오지 못했습니다.');

    titleEl.value = data.title || '';
    descriptionEl.value = data.description || '';
    contentEl.value = data.content || '';
    isFreeEl.checked = !!data.is_free;
    priceEl.value = data.price ?? 0;
    togglePrice();

    const categoryId = data.category?.id ? String(data.category.id) : '';
    categoryEl.value = categoryId;
    syncAiModels(categoryId, data.ai_model || '');
    if (promptTypeEl) promptTypeEl.value = data.prompt_type || 'single_prompt';

    state.tags = (data.tags || []).map(t => t.name).filter(Boolean);
    renderTags();
  }

  async function uploadFiles(createdId) {
    const files = Array.from(fileInput.files || []);
    if (!files.length) return;

    for (const file of files) {
      const fd = new FormData();
      fd.append('file', file);
      const { res, data } = await Api.upload(`/prompts/${createdId}/files/`, fd);
      if (!res.ok) {
        throw new Error(data?.file?.[0] || data?.detail || '첨부 파일 업로드에 실패했습니다.');
      }
    }
  }

  function clearFieldErrors() {
    document.querySelectorAll('.field-error').forEach(el => { el.textContent = ''; });
  }

  function applyFieldErrors(data) {
    if (!data || typeof data !== 'object') return false;
    let hasAny = false;
    const mapping = {
      title: 'title-error',
      category: 'category-error',
      ai_model: 'ai-model-error',
      content: 'content-error',
      price: 'price-error',
    };
    Object.entries(mapping).forEach(([field, errorId]) => {
      const el = document.getElementById(errorId);
      if (!el) return;
      const v = data[field];
      if (Array.isArray(v) && v.length) {
        el.textContent = v[0];
        hasAny = true;
      } else if (typeof v === 'string' && v) {
        el.textContent = v;
        hasAny = true;
      }
    });
    return hasAny;
  }

  async function onSubmit(e) {
    e.preventDefault();
    clearTopError();
    clearFieldErrors();
    setSubmitting(true);

    if (!loggedIn) {
      setSubmitting(false);
      showTopError('로그인이 필요합니다.');
      return;
    }

    const payload = {
      title: titleEl.value.trim(),
      description: descriptionEl.value.trim(),
      content: contentEl.value.trim(),
      category: categoryEl.value ? Number(categoryEl.value) : null,
      ai_model: aiModelEl.value,
      prompt_type: promptTypeEl?.value || 'single_prompt',
      workflow_steps: [],
      agent_pattern: '',
      is_free: !!isFreeEl.checked,
      price: isFreeEl.checked ? '0' : (priceEl.value || '0'),
      tag_names: state.tags,
    };

    try {
      const req = isEdit
        ? Api.put(`/prompts/${promptId}/`, payload)
        : Api.post('/prompts/', payload);
      const { res, data } = await req;
      if (!res.ok) {
        if (!applyFieldErrors(data)) {
          showTopError(data?.detail || '저장에 실패했습니다.');
        }
        return;
      }

      const targetId = data?.id || Number(promptId);
      if (!isEdit && targetId) {
        await uploadFiles(targetId);
      }
      window.location.href = targetId ? `/prompts/${targetId}/` : '/prompts/';
    } catch (err) {
      showTopError(err.message || '요청 중 오류가 발생했습니다.');
    } finally {
      setSubmitting(false);
    }
  }

  categoryEl.addEventListener('change', () => {
    syncAiModels(categoryEl.value || '', aiModelEl.value);
  });
  isFreeEl.addEventListener('change', togglePrice);
  form.addEventListener('submit', onSubmit);

  tagInput.addEventListener('keydown', e => {
    if (e.key !== 'Enter') return;
    e.preventDefault();
    const value = tagInput.value.trim();
    if (!value) return;
    if (!state.tags.includes(value)) state.tags.push(value);
    tagInput.value = '';
    renderTags();
  });

  tagList.addEventListener('click', e => {
    const btn = e.target.closest('.tag-remove');
    if (!btn) return;
    const tag = btn.dataset.tag;
    state.tags = state.tags.filter(t => t !== tag);
    renderTags();
  });

  (async () => {
    try {
      await loadCategories();
      await loadPromptForEdit();
      togglePrice();
    } catch (err) {
      showTopError(err.message || '폼 초기화에 실패했습니다.');
    }
  })();
});
