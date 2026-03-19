function escapeHtml(str) {
    var div = document.createElement('div');
    div.appendChild(document.createTextNode(str));
    return div.innerHTML;
}

function extractHeading(content) {
    const match = content.match(/^#\s+(.+)$/m);
    return match ? match[1].trim() : '未命名记录';
}

function formatDateLabel(value) {
    if (!value) return '未标注时间';
    if (/^\d{4}-\d{2}-\d{2} \d{2}:\d{2}$/.test(value)) return value;
    return value.replace('T', ' ');
}

function normalizeText(entry) {
    return `${entry.date || ''} ${entry.title || ''} ${entry.content || ''} ${entry.source_dir || ''} ${entry.file_name || ''}`.toLowerCase();
}

(function initDetailPage() {
    if (!Array.isArray(entries) || !entries.length) return;

    const navRoot = document.getElementById('navList');
    const articleRoot = document.getElementById('content');
    const articleTitle = document.getElementById('articleTitle');
    const articleIntro = document.getElementById('articleIntro');
    const articleMeta = document.getElementById('articleMeta');
    const filterInput = document.getElementById('filterInput');
    const resultCount = document.getElementById('resultCount');
    const latestMeta = document.getElementById('latestMeta');
    const totalMeta = document.getElementById('totalMeta');
    const currentMeta = document.getElementById('currentMeta');
    const menuToggle = document.getElementById('menuToggle');
    const closeMenu = document.getElementById('closeMenu');

    const state = {
        activeIndex: 0,
        query: ''
    };

    entries.forEach((entry, index) => {
        entry.title = entry.title || extractHeading(entry.content);
        entry.searchText = normalizeText(entry);
        entry.hash = `entry-${index}`;
    });

    if (latestMeta) latestMeta.textContent = `最新记录 ${formatDateLabel(entries[0].date)}`;
    if (totalMeta) totalMeta.textContent = `${entries.length} 条记录`;

    function visibleEntries() {
        if (!state.query) return entries.map((entry, index) => ({ entry, index }));
        return entries
            .map((entry, index) => ({ entry, index }))
            .filter(({ entry }) => entry.searchText.includes(state.query));
    }

    function renderNav() {
        const list = visibleEntries();
        navRoot.innerHTML = list.length ? list.map(({ entry, index }) => `
            <li>
                <div class="nav-item ${index === state.activeIndex ? 'active' : ''}" data-index="${index}">
                    <span class="nav-date">${escapeHtml(formatDateLabel(entry.date))}</span>
                    <span class="nav-title">${escapeHtml(entry.title)}</span>
                </div>
            </li>
        `).join('') : '<li class="empty-state">没有找到匹配的记录，试试更短的关键词。</li>';

        if (resultCount) {
            resultCount.textContent = state.query ? `匹配 ${list.length} 条` : `共 ${entries.length} 条`;
        }

        navRoot.querySelectorAll('.nav-item').forEach((node) => {
            node.addEventListener('click', () => {
                const index = Number(node.dataset.index);
                setActive(index, true);
                closeSidebar();
            });
        });
    }

    function renderArticle(index) {
        const entry = entries[index];
        if (!entry) return;

        articleRoot.innerHTML = DOMPurify.sanitize(marked.parse(entry.content, { breaks: false, gfm: true }));
        articleTitle.textContent = entry.title;
        articleIntro.textContent = entry.excerpt || `${pageConfig.subtitle} · 当前阅读的是第 ${index + 1} 条归档记录。`;

        const chips = [
            `<span class="meta-chip">${escapeHtml(formatDateLabel(entry.date))}</span>`,
            entry.source_dir ? `<span class="meta-chip">${escapeHtml(entry.source_dir)}</span>` : '',
            entry.file_name ? `<span class="meta-chip">${escapeHtml(entry.file_name)}</span>` : ''
        ].filter(Boolean);

        articleMeta.innerHTML = chips.join('');

        if (currentMeta) {
            currentMeta.textContent = `当前 ${index + 1}/${entries.length}`;
        }

        document.title = `${pageConfig.title} - ${entry.title}`;
    }

    function setActive(index, updateHash) {
        state.activeIndex = index;
        renderNav();
        renderArticle(index);
        if (updateHash) {
            history.replaceState(null, '', `#${entries[index].hash}`);
        }
    }

    function closeSidebar() {
        document.body.classList.remove('nav-open');
    }

    function openFromHash() {
        const hash = window.location.hash.replace('#', '');
        if (!hash) return false;
        const matchIndex = entries.findIndex((entry) => entry.hash === hash);
        if (matchIndex >= 0) {
            state.activeIndex = matchIndex;
            return true;
        }
        return false;
    }

    if (filterInput) {
        filterInput.addEventListener('input', (event) => {
            state.query = event.target.value.trim().toLowerCase();
            const visible = visibleEntries();
            if (visible.length && !visible.some(({ index }) => index === state.activeIndex)) {
                state.activeIndex = visible[0].index;
            }
            renderNav();
            renderArticle(state.activeIndex);
        });
    }

    if (menuToggle) {
        menuToggle.addEventListener('click', () => {
            document.body.classList.add('nav-open');
        });
    }

    if (closeMenu) {
        closeMenu.addEventListener('click', closeSidebar);
    }

    var overlay = document.getElementById('navOverlay');
    if (overlay) {
        overlay.addEventListener('click', closeSidebar);
    }

    document.addEventListener('keydown', (event) => {
        if (event.key === 'Escape') {
            closeSidebar();
        }
    });

    navRoot.setAttribute('role', 'listbox');
    navRoot.setAttribute('aria-label', '记录导航列表');

    window.addEventListener('hashchange', () => {
        if (openFromHash()) {
            setActive(state.activeIndex, false);
        }
    });

    openFromHash();
    renderNav();
    renderArticle(state.activeIndex);
})();
