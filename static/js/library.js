/**
 * library.js — 보관함: 북마크, 좋아요, 내 프롬프트, 내 댓글 관리
 */
document.addEventListener('DOMContentLoaded', () => {
  const guest = document.getElementById('library-guest');
  const main = document.getElementById('library-main');
  const bookmarkGrid = document.getElementById('bookmark-grid');
  const likeGrid = document.getElementById('like-grid');
  const mineGrid = document.getElementById('mine-grid');
  const transformsList = document.getElementById('transforms-list');
  const transformsCount = document.getElementById('transforms-count');
  const commentsList = document.getElementById('comments-list');
  const bookmarkCount = document.getElementById('bookmark-count');
  const likeCount = document.getElementById('like-count');
  const mineCount = document.getElementById('mine-count');
  const commentsCount = document.getElementById('comments-count');
  const tabButtons = document.querySelectorAll('.library-tabs [data-tab]');

  const panels = {
    bookmarks: document.getElementById('panel-bookmarks'),
    likes: document.getElementById('panel-likes'),
    mine: document.getElementById('panel-mine'),
    transforms: document.getElementById('panel-transforms'),
    comments: document.getElementById('panel-comments'),
  };

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

  const EMPTY_GRID_MESSAGES = {
    bookmarks: '관심 있는 프롬프트를 저장해보세요. 나중에 한곳에서 다시 찾을 수 있어요.',
    likes: '도움이 된 프롬프트에 「도움됐어요」를 눌러보세요.',
    mine: '아직 등록한 프롬프트가 없어요. + 프롬프트 등록으로 첫 콘텐츠를 올려보세요.',
  };

  function renderGrid(grid, items, errorMsg, emptyMsg) {
    if (errorMsg) {
      grid.innerHTML = `<div class="error-state">${Api.escapeHtml(errorMsg)}</div>`;
      return;
    }
    if (!items?.length) {
      grid.innerHTML = `<div class="empty-state">${Api.escapeHtml(emptyMsg || '항목이 없습니다.')}</div>`;
      return;
    }
    grid.innerHTML = items.map(renderCard).join('');
  }

  function formatDt(iso) {
    if (!iso) return '';
    try {
      return new Date(iso).toLocaleString('ko-KR', {
        dateStyle: 'short',
        timeStyle: 'short',
      });
    } catch {
      return iso;
    }
  }

  function renderComments(items, errorMsg) {
    if (errorMsg) {
      commentsList.innerHTML = `<div class="error-state">${Api.escapeHtml(errorMsg)}</div>`;
      return;
    }
    if (!items?.length) {
      commentsList.innerHTML = '<div class="empty-state">작성한 댓글이 없습니다.</div>';
      return;
    }
    commentsList.innerHTML = items
      .map(c => {
        const replyTag = c.parent
          ? '<span class="tag tag-item" style="font-size:11px;">대댓글</span>'
          : '';
        return `
      <article class="library-comment-row" data-comment-id="${c.id}">
        <div class="library-comment-meta">
          <a href="/prompts/${c.prompt_id}/" class="library-comment-prompt">${Api.escapeHtml(c.prompt_title || '')}</a>
          ${replyTag}
          <span class="library-comment-date">${Api.escapeHtml(formatDt(c.created_at))}</span>
        </div>
        <p class="library-comment-body">${Api.escapeHtml(c.content || '')}</p>
        <div class="library-comment-actions">
          <button type="button" class="btn btn-sm btn-secondary library-comment-delete">삭제 (숨김)</button>
        </div>
      </article>`;
      })
      .join('');
  }

  function setTab(tab) {
    tabButtons.forEach(btn => {
      const on = btn.dataset.tab === tab;
      btn.classList.toggle('active', on);
      btn.setAttribute('aria-selected', on ? 'true' : 'false');
    });
    Object.entries(panels).forEach(([key, el]) => {
      if (el) el.hidden = key !== tab;
    });
  }

  tabButtons.forEach(btn => {
    btn.addEventListener('click', () => setTab(btn.dataset.tab));
  });

  commentsList.addEventListener('click', async e => {
    const btn = e.target.closest('.library-comment-delete');
    if (!btn) return;
    const row = btn.closest('.library-comment-row');
    const id = row?.dataset.commentId;
    if (!id || !window.confirm('이 댓글을 삭제(숨김)할까요?')) return;
    btn.disabled = true;
    const { res } = await Api.delete(`/comments/${id}/`);
    if (res.ok) {
      await loadCommentsOnly();
    } else {
      btn.disabled = false;
      alert('삭제에 실패했습니다.');
    }
  });

  if (!Auth.isLoggedIn()) {
    guest.style.display = '';
    return;
  }

  guest.style.display = 'none';
  main.style.display = '';

  async function loadCommentsOnly() {
    const r = await Api.get('/accounts/me/comments/');
    const list = r.res.ok && Array.isArray(r.data) ? r.data : null;
    if (list) {
      commentsCount.textContent = `내 댓글 ${list.length}개`;
      renderComments(list);
    } else {
      commentsCount.textContent = '';
      renderComments([], '댓글 목록을 불러오지 못했습니다.');
    }
  }

  function renderTransforms(items, errorMsg) {
    if (errorMsg) {
      transformsList.innerHTML = `<div class="error-state">${Api.escapeHtml(errorMsg)}</div>`;
      return;
    }
    if (!items?.length) {
      transformsList.innerHTML = `
        <div class="empty-state">
          <p>아직 만든 설계서가 없어요.</p>
          <p>프롬프트 하나를 골라 <strong>에이전트 설계서로 변환</strong>해보세요.</p>
          <p style="margin-top:12px;">
            <a href="/blueprints/new/" class="btn btn-primary">설계서 만들기</a>
            <a href="/prompts/" class="btn btn-secondary">설계서 둘러보기</a>
          </p>
        </div>`;
      return;
    }
    transformsList.innerHTML = items.map(row => {
      const steps = (row.decomposed_steps || []).length;
      return `
      <article class="library-transform-row">
        <a href="/prompts/${row.prompt_id}/" class="library-comment-prompt">${Api.escapeHtml(row.prompt_title)}</a>
        <p class="text-muted">${steps}단계 · ${Api.escapeHtml(row.overall_pattern || 'Sequential')} · 신뢰도 ${Math.round((row.confidence_score || 0) * 100)}% · ${Api.escapeHtml(row.model_used || '')}</p>
        <p class="text-muted">${Api.escapeHtml(formatDt(row.created_at))}</p>
      </article>`;
    }).join('');
  }

  async function load() {
    bookmarkGrid.innerHTML = '<div class="loading-spinner">불러오는 중...</div>';
    likeGrid.innerHTML = '<div class="loading-spinner">불러오는 중...</div>';
    mineGrid.innerHTML = '<div class="loading-spinner">불러오는 중...</div>';
    transformsList.innerHTML = '<div class="loading-spinner">불러오는 중...</div>';
    commentsList.innerHTML = '<div class="loading-spinner">불러오는 중...</div>';

    const [bm, lk, mine, tr, cm] = await Promise.all([
      Api.get('/accounts/me/bookmarks/'),
      Api.get('/accounts/me/likes/'),
      Api.get('/accounts/me/prompts/'),
      Api.get('/accounts/me/transformations/'),
      Api.get('/accounts/me/comments/'),
    ]);

    const bookmarks = bm.res.ok && Array.isArray(bm.data) ? bm.data : null;
    const likes = lk.res.ok && Array.isArray(lk.data) ? lk.data : null;
    const mineList = mine.res.ok && Array.isArray(mine.data) ? mine.data : null;
    const transforms = tr.res.ok && Array.isArray(tr.data) ? tr.data : null;
    const comments = cm.res.ok && Array.isArray(cm.data) ? cm.data : null;

    if (bookmarks) {
      bookmarkCount.textContent = `저장 ${bookmarks.length}개`;
      renderGrid(bookmarkGrid, bookmarks, null, EMPTY_GRID_MESSAGES.bookmarks);
    } else {
      bookmarkCount.textContent = '';
      renderGrid(bookmarkGrid, [], '저장 목록을 불러오지 못했습니다.');
    }

    if (likes) {
      likeCount.textContent = `도움됐어요 ${likes.length}개`;
      renderGrid(likeGrid, likes, null, EMPTY_GRID_MESSAGES.likes);
    } else {
      likeCount.textContent = '';
      renderGrid(likeGrid, [], '목록을 불러오지 못했습니다.');
    }

    if (mineList) {
      mineCount.textContent = `내 프롬프트 ${mineList.length}개`;
      renderGrid(mineGrid, mineList, null, EMPTY_GRID_MESSAGES.mine);
    } else {
      mineCount.textContent = '';
      renderGrid(mineGrid, [], '내 프롬프트를 불러오지 못했습니다.');
    }

    if (transforms) {
      transformsCount.textContent = `내 설계서 ${transforms.length}개`;
      renderTransforms(transforms);
    } else {
      transformsCount.textContent = '';
      renderTransforms([], '변환 목록을 불러오지 못했습니다.');
    }

    if (comments) {
      commentsCount.textContent = `내 댓글 ${comments.length}개`;
      renderComments(comments);
    } else {
      commentsCount.textContent = '';
      renderComments([], '댓글 목록을 불러오지 못했습니다.');
    }
  }

  load();
});
