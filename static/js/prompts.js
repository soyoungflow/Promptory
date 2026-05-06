/**
 * prompts.js — 프롬프트 목록 페이지 전용
 * GET /api/prompts/ + 필터/검색/페이지네이션
 */

/** 사이드바 카테고리명 → 해당 벤더 AI 모델 값 (전체 선택 시에는 전부 표시) */
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

document.addEventListener('DOMContentLoaded', () => {
  const grid       = document.getElementById('prompt-grid');
  const pagination = document.getElementById('pagination');
  const countEl    = document.getElementById('result-count');

  let currentPage = 1;

  // 필터 요소들
  const searchInput   = document.getElementById('search-input');
  const categoryEl    = document.getElementById('filter-category');
  const categorySidebar = document.getElementById('category-sidebar');
  const aiModelEl     = document.getElementById('filter-ai-model');
  const isFreeEl      = document.getElementById('filter-is-free');
  const orderingEl    = document.getElementById('filter-ordering');
  const initialParams = new URLSearchParams(window.location.search);

  if (initialParams.get('search')) searchInput.value = initialParams.get('search');
  if (initialParams.get('ai_model')) aiModelEl.value = initialParams.get('ai_model');
  if (initialParams.get('is_free')) isFreeEl.value = initialParams.get('is_free');
  if (initialParams.get('ordering')) orderingEl.value = initialParams.get('ordering');

  // 카테고리 목록 동적 로딩
  async function loadCategories() {
    try {
      const { data } = await Api.get('/prompts/categories/');
      data.results?.forEach(cat => {
        const opt = document.createElement('option');
        opt.value = cat.id;
        opt.textContent = cat.name;
        categoryEl.appendChild(opt);

        if (categorySidebar) {
          const btn = document.createElement('button');
          btn.className = 'sidebar-item';
          btn.type = 'button';
          btn.dataset.category = cat.id;
          btn.innerHTML = `${Api.escapeHtml(cat.name)} <span>${cat.id}</span>`;
          btn.addEventListener('click', () => selectCategory(cat.id, btn));
          categorySidebar.appendChild(btn);
        }
      });
      const initialCategory = initialParams.get('category');
      if (initialCategory) {
        categoryEl.value = initialCategory;
        categorySidebar?.querySelectorAll('.sidebar-item').forEach(btn => {
          btn.classList.toggle('active', btn.dataset.category === initialCategory);
        });
      }
      syncAiModelOptionsForCategory(categoryEl.value || '');
      const urlAi = initialParams.get('ai_model');
      if (urlAi && Array.from(aiModelEl.options).some(o => o.value === urlAi)) {
        aiModelEl.value = urlAi;
      } else if (urlAi) {
        aiModelEl.value = '';
      }
    } catch {}
  }

  function getCategoryNameById(categoryId) {
    if (!categoryId) return '';
    const opt = categoryEl.querySelector(`option[value="${categoryId}"]`);
    return (opt?.textContent || '').trim();
  }

  /** 카테고리에 맞게 AI 모델 셀렉트 옵션만 갱신 (현재 값이 목록에 없으면 초기화) */
  function syncAiModelOptionsForCategory(categoryId) {
    const name = getCategoryNameById(categoryId);
    const allowed = name ? CATEGORY_AI_MODELS[name] : null;
    const list = allowed?.length
      ? AI_MODEL_OPTIONS.filter(m => allowed.includes(m.value))
      : AI_MODEL_OPTIONS;

    const prev = aiModelEl.value;
    aiModelEl.innerHTML = '';
    const allOpt = document.createElement('option');
    allOpt.value = '';
    allOpt.textContent = '전체 모델';
    aiModelEl.appendChild(allOpt);
    list.forEach(({ value, label }) => {
      const o = document.createElement('option');
      o.value = value;
      o.textContent = label;
      aiModelEl.appendChild(o);
    });
    if (prev && list.some(m => m.value === prev)) {
      aiModelEl.value = prev;
    } else {
      aiModelEl.value = '';
    }
  }

  function selectCategory(categoryId, activeButton) {
    categoryEl.value = categoryId;
    categorySidebar?.querySelectorAll('.sidebar-item').forEach(btn => {
      btn.classList.toggle('active', btn === activeButton);
    });
    syncAiModelOptionsForCategory(categoryId);
    currentPage = 1;
    fetchPrompts();
  }

  // URL 파라미터 수집
  function buildParams() {
    const params = new URLSearchParams();
    const search   = searchInput.value.trim();
    const category = categoryEl.value;
    const aiModel  = aiModelEl.value;
    const isFree   = isFreeEl.value;
    const ordering = orderingEl.value;

    if (search)   params.set('search', search);
    if (category) params.set('category', category);
    if (aiModel)  params.set('ai_model', aiModel);
    if (isFree)   params.set('is_free', isFree);
    if (ordering) params.set('ordering', ordering);
    params.set('page', currentPage);
    return params;
  }

  // 프롬프트 카드 렌더링
  function renderCard(p) {
    const freeTag = p.is_free
      ? `<span class="tag tag-free">무료</span>`
      : `<span class="tag tag-paid">₩${Number(p.price).toLocaleString()}</span>`;
    const tags = (p.tags || []).map(t => `<span class="tag">#${Api.escapeHtml(t.name)}</span>`).join('');

    return `
      <a class="prompt-card" href="/prompts/${p.id}/">
        <div class="card-header">
          <span class="card-model">${Api.escapeHtml(p.ai_model)}</span>
          ${freeTag}
        </div>
        <h3 class="card-title">${Api.escapeHtml(p.title)}</h3>
        <p class="card-desc">${Api.escapeHtml(p.description || '')}</p>
        <div class="card-tags">${tags}</div>
        <div class="card-footer">
          <span class="card-author"><span class="avatar-sm">${Api.escapeHtml((p.author || '?').charAt(0).toUpperCase())}</span>${Api.escapeHtml(p.author || '')}</span>
          <span class="card-stats">♥ ${p.like_count} · 조회 ${p.view_count}</span>
        </div>
      </a>`;
  }

  // 페이지네이션 렌더링
  function renderPagination(count, currentPage) {
    const totalPages = Math.ceil(count / 12);
    if (totalPages <= 1) { pagination.innerHTML = ''; return; }

    let html = '';
    for (let i = 1; i <= totalPages; i++) {
      html += `<button class="page-btn${i === currentPage ? ' active' : ''}" data-page="${i}">${i}</button>`;
    }
    pagination.innerHTML = html;
    pagination.querySelectorAll('.page-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        currentPage = parseInt(btn.dataset.page);
        fetchPrompts();
        window.scrollTo({ top: 0, behavior: 'smooth' });
      });
    });
  }

  // 목록 API 호출
  async function fetchPrompts() {
    grid.innerHTML = '<div class="loading-spinner">불러오는 중...</div>';
    try {
      const { data } = await Api.get(`/prompts/?${buildParams()}`);
      const results = data.results || [];

      countEl.textContent = `총 ${data.count || 0}개`;

      if (!results.length) {
        grid.innerHTML = '<div class="empty-state">검색 결과가 없습니다.</div>';
        pagination.innerHTML = '';
        return;
      }

      grid.innerHTML = results.map(renderCard).join('');
      renderPagination(data.count, currentPage);
    } catch {
      grid.innerHTML = '<div class="error-state">데이터를 불러오지 못했습니다.</div>';
    }
  }

  // 이벤트 바인딩
  document.getElementById('search-btn')?.addEventListener('click', () => {
    currentPage = 1; fetchPrompts();
  });
  categorySidebar?.querySelector('[data-category=""]')?.addEventListener('click', e => {
    selectCategory('', e.currentTarget);
  });
  searchInput?.addEventListener('keydown', e => {
    if (e.key === 'Enter') { currentPage = 1; fetchPrompts(); }
  });
  categoryEl?.addEventListener('change', () => {
    syncAiModelOptionsForCategory(categoryEl.value || '');
    currentPage = 1;
    fetchPrompts();
  });
  [aiModelEl, isFreeEl, orderingEl].forEach(el => {
    el?.addEventListener('change', () => { currentPage = 1; fetchPrompts(); });
  });

  // 초기 로드
  loadCategories().then(fetchPrompts);
});
