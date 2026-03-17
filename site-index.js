const dashboard = {
    members: [
        { name: '悠仁', href: '悠仁.html', image: 'yujin.jpg', papers: 21, role: '跨领域追踪', note: '关注推理、协作与开放任务中的人机互动。' },
        { name: '野蔷薇', href: '野蔷薇.html', image: 'panda.jpg', papers: 21, role: '批判性观察', note: '擅长从论文缺口、方法局限与研究机会切入。' },
        { name: '惠', href: '惠.html', image: 'megumi.jpg', papers: 21, role: '写作与方法论', note: '聚焦论文写作、研究表达与博士训练过程。' },
        { name: '五条悟', href: '五条悟.html', image: 'gojo.jpg', papers: 21, role: '前沿研判', note: '偏重推理、安全、多模态与学术评审洞见。' }
    ],
    topics: [
        { name: 'AI', href: 'AI.html', count: 21, accent: '#ff6b35', tags: ['多模态', '推理', 'Agent'] },
        { name: 'NLP', href: 'NLP.html', count: 19, accent: '#ff8c42', tags: ['语言模型', '文本理解', '对话'] },
        { name: 'CV', href: 'CV.html', count: 16, accent: '#ffa07a', tags: ['视觉生成', '3D', 'Diffusion'] },
        { name: 'ML', href: 'ML.html', count: 9, accent: '#ffb366', tags: ['训练范式', '优化', '表示学习'] },
        { name: 'HCI', href: 'HCI.html', count: 4, accent: '#88ccff', tags: ['交互', '协作', '用户研究'] },
        { name: 'UX', href: 'UX.html', count: 1, accent: '#cc88ff', tags: ['体验设计', '产品表达'] }
    ],
    recent: [
        { date: '2026-03-17 20:00', title: '惠完成新一轮升级迭代与论文总结', href: '惠.html#entry-0' },
        { date: '2026-03-17 19:00', title: '五条悟新增最新一轮能力进化记录', href: '五条悟.html#entry-0' },
        { date: '2026-03-17 14:00', title: '野蔷薇完成批判性复盘与升级', href: '野蔷薇.html#entry-0' },
        { date: '2026-03-17 13:00', title: '悠仁补充当日论文总结与研究线索', href: '悠仁.html#entry-0' }
    ],
    charts: {
        trend: [3, 5, 4, 6, 4, 5, 3],
        distribution: [21, 19, 16, 9, 4, 1],
        labels: ['AI', 'NLP', 'CV', 'ML', 'HCI', 'UX'],
        colors: ['#ff6b35', '#ff8c42', '#ffa07a', '#ffb366', '#88ccff', '#cc88ff']
    }
};

function renderTopics() {
    const root = document.getElementById('topicGrid');
    root.innerHTML = dashboard.topics.map((topic) => `
        <a class="topic-card" href="${topic.href}" style="--accent:${topic.accent}; --accent-soft:${topic.accent}22;">
            <div class="topic-head">
                <div>
                    <div class="topic-name">${topic.name}</div>
                    <div class="card-meta">聚合该方向的重要论文总结与近期洞察</div>
                </div>
                <div class="topic-count">${topic.count}</div>
            </div>
            <div class="topic-tags">
                ${topic.tags.map((tag) => `<span class="topic-tag">${tag}</span>`).join('')}
            </div>
        </a>
    `).join('');
}

function renderMembers() {
    const root = document.getElementById('memberGrid');
    root.innerHTML = dashboard.members.map((member) => `
        <a class="member-card" href="${member.href}">
            <div class="member-head">
                <div class="member-profile">
                    <img class="member-avatar" src="${member.image}" alt="${member.name}">
                    <div>
                        <div class="member-name">${member.name}</div>
                        <div class="member-role">${member.role}</div>
                    </div>
                </div>
                <div class="member-count">${member.papers} 篇</div>
            </div>
            <div class="member-snippet">${member.note}</div>
        </a>
    `).join('');
}

function renderRecent() {
    const root = document.getElementById('recentList');
    root.innerHTML = dashboard.recent.map((entry) => `
        <article class="entry-card">
            <div class="entry-date">${entry.date}</div>
            <a class="entry-link" href="${entry.href}">
                <h3 class="entry-title">${entry.title}</h3>
                <div class="entry-meta">点击进入对应记录页，继续阅读完整内容。</div>
            </a>
            <div class="entry-arrow">↗</div>
        </article>
    `).join('');
}

function buildCharts() {
    if (typeof Chart === 'undefined') return;

    const labelColor = '#94a3b8';
    const gridColor = 'rgba(148, 163, 184, 0.12)';

    new Chart(document.getElementById('trendChart'), {
        type: 'line',
        data: {
            labels: ['周一', '周二', '周三', '周四', '周五', '周六', '周日'],
            datasets: [{
                label: '阅读量',
                data: dashboard.charts.trend,
                borderColor: '#ff6b35',
                backgroundColor: 'rgba(255, 107, 53, 0.16)',
                fill: true,
                tension: 0.42,
                borderWidth: 2,
                pointRadius: 3,
                pointBackgroundColor: '#ff6b35'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
                x: { ticks: { color: labelColor }, grid: { color: gridColor } },
                y: { ticks: { color: labelColor }, grid: { color: gridColor }, beginAtZero: true }
            }
        }
    });

    new Chart(document.getElementById('distributionChart'), {
        type: 'doughnut',
        data: {
            labels: dashboard.charts.labels,
            datasets: [{
                data: dashboard.charts.distribution,
                backgroundColor: dashboard.charts.colors,
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: { color: labelColor, padding: 16 }
                }
            },
            cutout: '62%'
        }
    });

    new Chart(document.getElementById('radarChart'), {
        type: 'radar',
        data: {
            labels: dashboard.charts.labels,
            datasets: [{
                label: '论文篇数',
                data: dashboard.charts.distribution,
                backgroundColor: 'rgba(255, 107, 53, 0.18)',
                borderColor: '#ff6b35',
                pointBackgroundColor: '#ff6b35',
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
                r: {
                    angleLines: { color: gridColor },
                    grid: { color: gridColor },
                    pointLabels: { color: labelColor },
                    ticks: {
                        color: labelColor,
                        backdropColor: 'transparent'
                    },
                    suggestedMin: 0
                }
            }
        }
    });
}

renderTopics();
renderMembers();
renderRecent();
buildCharts();
