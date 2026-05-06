/**
 * prompt-form.js — 프롬프트 등록/수정 페이지 전용
 *
 * 카테고리(slug) ↔ AI 모델 매핑은 prompts.models 의 선택지 및 seed_mockup 의 관례와 맞춘다.
 * 알 수 없는 카테고리 슬러그면 모델 목록 전체를 표시한다.
 */
document.addEventListener('DOMContentLoaded', () => {
  const page     = document.querySelector('.form-page');
  const promptId = page?.dataset.promptId;  // 수정 시 존재
  const isEdit   = !!promptId;
  const form     = document.getElementById('prompt-form');
  const errBox   = document.getElementById('form-error');
  const isFreeEl = document.getElementById('is-free');
  const priceGrp = document.getElementById('price-group');

  /** prompts.models.Prompt.AI_MODEL_CHOICES 와 동일 순서·값 */
  const AI_MODEL_OPTIONS = [
    { value: 'gpt-5-5', label: 'GPT-5.5' },
    { value: 'gpt-5-5-instant', label: 'GPT-5.5 Instant' },
    { value: 'claude-opus-4-7', label: 'Claude Opus 4.7' },
    { value: 'claude-sonnet-4-6', label: 'Claude Sonnet 4.6' },
    { value: 'gemini-3-1-pro', label: 'Gemini 3.1 Pro' },
    { value: 'gemini-3-0-flash', label: 'Gemini 3.0 Flash' },
    { value: 'other', label: '기타' },
  ];

  /** Category.slug → 허용 ai_model 값 목록 (seed: ChatGPT/Claude/Gemini → slugify) */
  const SLUG_TO_MODELS = {
    chatgpt: ['gpt-5-5', 'gpt-5-5-instant', 'other'],
    claude: ['claude-opus-4-7', 'claude-sonnet-4-6', 'other'],
    gemini: ['gemini-3-1-pro', 'gemini-3-0-flash', 'other'],
  };

  /** 모델 → 카테고리 slug 자동 선택 (기타는 API상 카테고리 필수이므로 카테고리는 건드리지 않음) */
  const MODEL_TO_SLUG = {
    'gpt-5-5': 'chatgpt',
    'gpt-5-5-instant': 'chatgpt',
    'claude-opus-4-7': 'claude',
    'claude-sonnet-4-6': 'claude',
    'gemini-3-1-pro': 'gemini',
    'gemini-3-0-flash': 'gemini',
    'other': null,
  };

  // 미로그인 → 리다이렉트
  if (!Auth.isLoggedIn()) { window.location.href = '/accounts/login/'; return; }

  function fillAiModelSelect(selectEl, allowedValues /* null = 전체 */) {
    selectEl.innerHTML = '';
    const ph = document.createElement('option');
    ph.value = '';
    ph.textContent = '모델을 선택하세요';
    selectEl.appendChild(ph);
    const pool = allowedValues == null
      ? AI_MODEL_OPTIONS
      : AI_MODEL_OPTIONS.filter((o) => allowedValues.includes(o.value));
    pool.forEach(({ value, label }) => {
      const opt = document.createElement('option');
      opt.value = value;
      opt.textContent = label;
      selectEl.appendChild(opt);
    });
  }

  function modelsAllowedForCategorySlug(slug) {
    if (!slug) return null;
    const allowed = SLUG_TO_MODELS[slug];
    return allowed || null;
  }

  function pickAiModelValue(aiSel, allowedList, preferredModel, prev) {
    function has(val) {
      return val && [...aiSel.options].some((o) => o.value === val);
    }
    if (has(preferredModel)) return preferredModel;
    if (has(prev)) return prev;
    if (allowedList && allowedList.length) return allowedList[0];
    return '';
  }

  /** 카테고리 선택 기준으로 모델 셀렉트 채우기; 수정 로드 시 preferredModel 우선 */
  function refreshAiModelsForCategory(preferredModel = null) {
    const catSel = document.getElementById('category');
    const aiSel = document.getElementById('ai-model');
    const slug = catSel.selectedOptions[0]?.dataset.slug || '';
    const restricted = modelsAllowedForCategorySlug(slug);
    const allowedList = restricted ? restricted : null;
    const prev = aiSel.value;

    fillAiModelSelect(aiSel, allowedList);

    aiSel.value = pickAiModelValue(aiSel, allowedList, preferredModel, prev);
  }

  /** 모델 선택 → 카테고리 자동 선택 (기타는 현재 카테고리 유지 — 카테고리 필수 검증과 충돌 방지) */
  function applyCategoryFromAiModel() {
    const catSel = document.getElementById('category');
    const aiSel = document.getElementById('ai-model');
    const modelVal = aiSel.value;
    const slug = MODEL_TO_SLUG[modelVal];

    if (slug === undefined) return;

    if (slug === null) {
      refreshAiModelsForCategory();
      return;
    }

    const match = [...catSel.options].find((o) => o.dataset.slug === slug);
    if (match) catSel.value = match.value;
    refreshAiModelsForCategory();
  }

  // 카테고리 동적 로딩
  async function loadCategories() {
    const { data } = await Api.get('/prompts/categories/');
    const sel = document.getElementById('category');
    (data.results || []).forEach((c) => {
      const opt = document.createElement('option');
      opt.value = c.id;
      opt.textContent = c.name;
      if (c.slug) opt.dataset.slug = c.slug;
      sel.appendChild(opt);
    });
  }

  // 수정 모드: 기존 데이터 채우기
  async function loadExisting() {
    if (!isEdit) return;
    const { data: p } = await Api.get(`/prompts/${promptId}/`);
    document.getElementById('title').value       = p.title || '';
    document.getElementById('description').value = p.description || '';
    document.getElementById('content').value     = p.content || '';
    document.getElementById('category').value    = p.category?.id || '';
    refreshAiModelsForCategory(p.ai_model || 'other');
    document.getElementById('is-free').checked   = p.is_free;
    document.getElementById('price').value       = p.price || 0;
    priceGrp.style.display = p.is_free ? 'none' : '';
    // 태그 복원
    (p.tags || []).forEach(t => addTag(t.name, t.id));
  }

  // 무료/유료 토글
  isFreeEl?.addEventListener('change', () => {
    priceGrp.style.display = isFreeEl.checked ? 'none' : '';
  });

  // 태그 관리
  const tagData = [];
  const tagList = document.getElementById('tag-list');
  document.getElementById('tag-input')?.addEventListener('keydown', async (e) => {
    if (e.key !== 'Enter') return;
    e.preventDefault();
    const val = e.target.value.trim();
    if (!val || tagData.find(t => t.name === val)) return;
    // 기존 태그는 ID로, 새 태그는 이름으로 서버에 전달한다.
    const { data } = await Api.get(`/prompts/tags/?search=${encodeURIComponent(val)}`);
    const existing = (data.results || []).find(t => t.name === val);
    addTag(val, existing?.id || null);
    e.target.value = '';
  });

  function addTag(name, id) {
    if (tagData.find(t => t.name === name)) return;
    tagData.push({ name, id });
    updateTagIds();
    const span = document.createElement('span');
    span.className = 'tag tag-item';
    span.innerHTML = `${Api.escapeHtml(name)} <button type="button" class="tag-remove" data-name="${Api.escapeHtml(name)}">×</button>`;
    span.querySelector('.tag-remove').addEventListener('click', () => removeTag(name));
    tagList.appendChild(span);
  }
  function removeTag(name) {
    const idx = tagData.findIndex(t => t.name === name);
    if (idx > -1) tagData.splice(idx, 1);
    updateTagIds();
    tagList.querySelectorAll('.tag-item').forEach(el => {
      if (el.querySelector('.tag-remove').dataset.name === name) el.remove();
    });
  }
  function updateTagIds() {
    document.getElementById('tag-ids').value = tagData.filter(t => t.id).map(t => t.id).join(',');
  }

  // 파일 미리보기
  document.getElementById('file-input')?.addEventListener('change', (e) => {
    const preview = document.getElementById('file-preview');
    preview.innerHTML = '';
    [...e.target.files].forEach(f => {
      const div = document.createElement('div');
      div.className = 'file-item';
      div.textContent = `첨부: ${f.name} (${(f.size/1024).toFixed(1)}KB)`;
      preview.appendChild(div);
    });
  });

  // 폼 제출
  form?.addEventListener('submit', async (e) => {
    e.preventDefault();
    clearErrors();

    const title   = document.getElementById('title').value.trim();
    const content = document.getElementById('content').value.trim();
    const catVal = document.getElementById('category').value;
    const aiVal = document.getElementById('ai-model').value;
    if (!title)   return showFieldError('title-error', '제목을 입력하세요.');
    if (!catVal)  return showFieldError('category-error', '카테고리를 선택하세요.');
    if (!aiVal)   return showFieldError('ai-model-error', 'AI 모델을 선택하세요.');
    if (!content) return showFieldError('content-error', '프롬프트 본문을 입력하세요.');

    const payload = {
      title,
      content,
      description: document.getElementById('description').value.trim(),
      ai_model:    document.getElementById('ai-model').value,
      is_free:     isFreeEl.checked,
      price:       isFreeEl.checked ? 0 : parseFloat(document.getElementById('price').value || 0),
    };
    payload.category = parseInt(catVal);
    const tagIds = tagData.filter(t => t.id).map(t => t.id);
    const tagNames = tagData.filter(t => !t.id).map(t => t.name);
    if (tagIds.length) payload.tag_ids = tagIds;
    if (tagNames.length) payload.tag_names = tagNames;

    try {
      const { res, data } = isEdit
        ? await Api.put(`/prompts/${promptId}/`, payload)
        : await Api.post('/prompts/', payload);

      if (!res.ok) {
        errBox.textContent = Object.values(data).flat().join(' ');
        errBox.style.display = 'block';
        return;
      }

      // 파일 업로드 (별도 요청)
      const files = document.getElementById('file-input').files;
      if (files.length) {
        for (const file of files) {
          const fd = new FormData();
          fd.append('file', file);
          await Api.upload(`/prompts/${data.id}/files/`, fd);
        }
      }

      window.location.href = `/prompts/${data.id}/`;
    } catch {
      errBox.textContent = '서버 오류가 발생했습니다.';
      errBox.style.display = 'block';
    }
  });

  function clearErrors() {
    ['title-error', 'category-error', 'ai-model-error', 'content-error'].forEach(id => {
      const el = document.getElementById(id);
      if (el) el.textContent = '';
    });
    errBox.style.display = 'none';
  }
  function showFieldError(id, msg) {
    const el = document.getElementById(id);
    if (el) el.textContent = msg;
  }

  loadCategories().then(() => {
    const catSel = document.getElementById('category');
    const aiSel = document.getElementById('ai-model');
    catSel?.addEventListener('change', () => refreshAiModelsForCategory());
    aiSel?.addEventListener('change', applyCategoryFromAiModel);
    refreshAiModelsForCategory();
    return loadExisting();
  });
});
