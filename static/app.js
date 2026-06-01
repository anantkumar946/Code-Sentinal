/* ══════════════════════════════════════════════════════════════════════════
   app.js — CodeSentinel Web UI Client Logic
   ══════════════════════════════════════════════════════════════════════════ */

document.addEventListener('DOMContentLoaded', () => {
  const codeInput    = document.getElementById('code-input');
  const analyzeBtn   = document.getElementById('analyze-btn');
  const resultsDiv   = document.getElementById('results');
  const lineNumbers  = document.getElementById('line-numbers');
  const langBtns     = document.querySelectorAll('.lang-btn');
  const editorTitle  = document.getElementById('editor-title');

  let currentLang = 'python';

  // ── Language Toggle ────────────────────────────────────────────────────
  langBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      langBtns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      currentLang = btn.dataset.lang;

      editorTitle.textContent = currentLang === 'python' ? 'main.py' : 'query.sql';

      // Update placeholder
      if (currentLang === 'python') {
        codeInput.placeholder = '# Paste your Python code here...\nimport os\n\ndef main():\n    pass';
      } else {
        codeInput.placeholder = '-- Paste your SQL query here...\nSELECT * FROM users WHERE id = 1;';
      }
    });
  });

  // ── Line Numbers ───────────────────────────────────────────────────────
  function updateLineNumbers() {
    const lines = codeInput.value.split('\n');
    const count = Math.max(lines.length, 20);
    let html = '';
    for (let i = 1; i <= count; i++) {
      html += i + '\n';
    }
    lineNumbers.textContent = html;
  }

  codeInput.addEventListener('input', updateLineNumbers);
  codeInput.addEventListener('scroll', () => {
    lineNumbers.scrollTop = codeInput.scrollTop;
  });

  // Tab key support
  codeInput.addEventListener('keydown', (e) => {
    if (e.key === 'Tab') {
      e.preventDefault();
      const start = codeInput.selectionStart;
      const end = codeInput.selectionEnd;
      codeInput.value = codeInput.value.substring(0, start) + '    ' + codeInput.value.substring(end);
      codeInput.selectionStart = codeInput.selectionEnd = start + 4;
      updateLineNumbers();
    }
  });

  updateLineNumbers();

  // ── Analyze ────────────────────────────────────────────────────────────
  analyzeBtn.addEventListener('click', async () => {
    const code = codeInput.value.trim();
    if (!code) return;

    analyzeBtn.classList.add('loading');
    resultsDiv.classList.remove('visible');

    try {
      const resp = await fetch('/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code, language: currentLang }),
      });

      if (!resp.ok) {
        const err = await resp.json();
        showError(err.error || 'Analysis failed');
        return;
      }

      const data = await resp.json();
      renderResults(data);
    } catch (err) {
      showError('Failed to connect to the server.');
    } finally {
      analyzeBtn.classList.remove('loading');
    }
  });

  // ── Render Results ─────────────────────────────────────────────────────
  function renderResults(data) {
    const issues = data.issues || [];
    const score  = data.score ?? 0;

    const grade = score >= 80 ? 'A' : score >= 60 ? 'B' : score >= 40 ? 'C' : 'F';
    const scoreColor = score >= 80 ? '#34d399' : score >= 60 ? '#fbbf24' : score >= 40 ? '#fb923c' : '#f87171';

    // Determine categories
    const allCats = currentLang === 'sql'
      ? ['SQL']
      : ['Syntax', 'Semantic', 'Complexity', 'Style', 'Security'];

    const catCounts = {};
    allCats.forEach(c => {
      catCounts[c] = issues.filter(i => i.category === c).length;
    });

    // Severity counts
    const sevCounts = { ERROR: 0, HIGH: 0, WARNING: 0, MEDIUM: 0, INFO: 0 };
    issues.forEach(i => { sevCounts[i.severity] = (sevCounts[i.severity] || 0) + 1; });

    // Build score ring
    const circumference = 2 * Math.PI * 54;
    const offset = circumference - (score / 100) * circumference;

    let html = '';

    // Score section
    html += `
      <div class="score-section">
        <div class="score-ring">
          <svg viewBox="0 0 120 120">
            <circle class="bg" cx="60" cy="60" r="54"/>
            <circle class="progress" cx="60" cy="60" r="54"
                    style="stroke:${scoreColor}; stroke-dashoffset:${offset}"/>
          </svg>
          <div class="score-value">
            <div class="score-num" style="color:${scoreColor}">${score}</div>
            <div class="score-grade">Grade ${grade}</div>
          </div>
        </div>
        <div class="score-details">
          <div class="score-detail">
            <span class="dot" style="background:#f87171"></span>
            <span class="count">${sevCounts.ERROR + sevCounts.HIGH}</span>
            <span>Critical / High</span>
          </div>
          <div class="score-detail">
            <span class="dot" style="background:#fbbf24"></span>
            <span class="count">${sevCounts.WARNING + sevCounts.MEDIUM}</span>
            <span>Warnings</span>
          </div>
          <div class="score-detail">
            <span class="dot" style="background:#38bdf8"></span>
            <span class="count">${sevCounts.INFO}</span>
            <span>Info</span>
          </div>
          <div class="score-detail">
            <span class="dot" style="background:#5a6380"></span>
            <span class="count">${issues.length}</span>
            <span>Total Issues</span>
          </div>
        </div>
      </div>`;

    // Stats grid
    const gridCols = allCats.length;
    html += `<div class="stats-grid" style="grid-template-columns:repeat(${gridCols},1fr)">`;
    allCats.forEach(cat => {
      html += `
        <div class="stat-card">
          <div class="stat-num">${catCounts[cat]}</div>
          <div class="stat-label">${cat}</div>
        </div>`;
    });
    html += '</div>';

    // Issue cards per category
    allCats.forEach((cat, catIdx) => {
      const catIssues = issues.filter(i => i.category === cat);
      html += `
        <div class="issue-card" style="animation: cardIn 0.4s ease-out ${0.1 * catIdx}s both">
          <div class="issue-card-header">
            <span class="issue-card-title">${cat}</span>
            <span class="issue-card-count">${catIssues.length} issue${catIssues.length !== 1 ? 's' : ''}</span>
          </div>`;

      if (catIssues.length === 0) {
        html += '<div class="no-issues">✅ No issues found</div>';
      } else {
        catIssues.sort((a, b) => (a.line || 0) - (b.line || 0));
        catIssues.forEach(issue => {
          const badgeClass = 'badge-' + issue.severity.toLowerCase();
          const suggestion = issue.suggestion || '';
          const suggestionHtml = suggestion
            ? `<div class="issue-suggestion">
                 <span class="fix-label">💡 FIX</span>
                 <span>${escapeHtml(suggestion)}</span>
               </div>`
            : '';

          html += `
            <div class="issue-row">
              <span class="badge ${badgeClass}">${issue.severity}</span>
              <span class="issue-line">L${issue.line}</span>
              <div class="issue-content">
                <div class="issue-msg">${escapeHtml(issue.message)}</div>
                ${suggestionHtml}
              </div>
            </div>`;
        });
      }
      html += '</div>';
    });

    resultsDiv.innerHTML = html;
    resultsDiv.classList.add('visible');

    // Animate score ring
    requestAnimationFrame(() => {
      const progress = resultsDiv.querySelector('.progress');
      if (progress) {
        progress.style.strokeDashoffset = offset;
      }
    });

    // Scroll to results
    resultsDiv.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }

  function showError(msg) {
    resultsDiv.innerHTML = `<div class="error-msg">⚠️ ${escapeHtml(msg)}</div>`;
    resultsDiv.classList.add('visible');
  }

  function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
  }
});
