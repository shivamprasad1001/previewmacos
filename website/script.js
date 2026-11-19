/**
 * Preview (macOS Edition) - Official Website Script
 * Lightweight vanilla JavaScript | Zero dependencies | Fast & accessible
 */

document.addEventListener('DOMContentLoaded', () => {
  initTheme();
  initOSDetection();
  initGitHubRelease();
  initGallery();
  initCopyButtons();
  initShortcuts();
  initFAQ();
  initMobileNav();
});

/* ==========================================================================
   1. Theme Management (Dark / Light Mode)
   ========================================================================== */
function initTheme() {
  const toggleBtn = document.getElementById('theme-toggle');
  const savedTheme = localStorage.getItem('preview-theme');
  const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
  const initialTheme = savedTheme || (prefersDark ? 'dark' : 'light');

  applyTheme(initialTheme);

  if (toggleBtn) {
    toggleBtn.addEventListener('click', () => {
      const current = document.documentElement.getAttribute('data-theme') || 'light';
      const next = current === 'dark' ? 'light' : 'dark';
      applyTheme(next);
      localStorage.setItem('preview-theme', next);
    });
  }

  // Follow system theme changes if user hasn't explicitly set a preference
  window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
    if (!localStorage.getItem('preview-theme')) {
      applyTheme(e.matches ? 'dark' : 'light');
    }
  });
}

function applyTheme(theme) {
  document.documentElement.setAttribute('data-theme', theme);
  const toggleBtn = document.getElementById('theme-toggle');
  if (toggleBtn) {
    const isDark = theme === 'dark';
    toggleBtn.setAttribute('aria-label', isDark ? 'Switch to light theme' : 'Switch to dark theme');
    toggleBtn.innerHTML = isDark
      ? '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="5"></circle><line x1="12" y1="1" x2="12" y2="3"></line><line x1="12" y1="21" x2="12" y2="23"></line><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line><line x1="1" y1="12" x2="3" y2="12"></line><line x1="21" y1="12" x2="23" y2="12"></line><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line></svg>'
      : '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path></svg>';
  }
}

/* ==========================================================================
   2. OS Detection for Hero Download Button
   ========================================================================== */
function initOSDetection() {
  const heroDownloadBtn = document.getElementById('hero-download-btn');
  if (!heroDownloadBtn) return;

  const ua = navigator.userAgent;
  const isWindows = ua.indexOf('Win') !== -1;
  const isLinux = ua.indexOf('Linux') !== -1 || ua.indexOf('X11') !== -1;

  if (isWindows) {
    heroDownloadBtn.href = 'https://github.com/shivamprasad1001/previewmacos/releases/download/v1.7.1/Preview-Setup-v1.7.1.exe';
    heroDownloadBtn.innerHTML = `
      <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
        <path d="M0 3.449L9.75 2.1v9.451H0m10.949-9.602L24 0v11.401H10.949M0 12.6h9.75v9.451L0 20.699M10.949 12.6H24V24l-12.949-1.801"/>
      </svg>
      <span>Download for Windows (.exe)</span>
    `;
  } else if (isLinux) {
    heroDownloadBtn.href = 'https://github.com/shivamprasad1001/previewmacos/releases/download/v1.7.1/preview-app_1.7.1_amd64.deb';
    heroDownloadBtn.innerHTML = `
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
        <polyline points="7 10 12 15 17 10"></polyline>
        <line x1="12" y1="15" x2="12" y2="3"></line>
      </svg>
      <span>Download for Linux (.deb)</span>
    `;
  } else {
    // Default fallback
    heroDownloadBtn.href = '#install';
    heroDownloadBtn.innerHTML = `
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
        <polyline points="7 10 12 15 17 10"></polyline>
        <line x1="12" y1="15" x2="12" y2="3"></line>
      </svg>
      <span>Download v1.7.1</span>
    `;
  }
}

/* ==========================================================================
   3. GitHub Releases API Fetcher
   ========================================================================== */
async function initGitHubRelease() {
  const versionBadge = document.getElementById('release-badge-version');
  const debDownloadLink = document.getElementById('deb-download-link');
  const exeDownloadLink = document.getElementById('exe-download-link');
  const heroDownloadBtn = document.getElementById('hero-download-btn');
  const apiStatusNote = document.getElementById('api-status-note');

  try {
    const res = await fetch('https://api.github.com/repos/shivamprasad1001/previewmacos/releases/latest');
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();

    const tagName = data.tag_name || 'v1.7.1';
    if (versionBadge) versionBadge.textContent = `${tagName} Release`;

    if (data.assets && Array.isArray(data.assets)) {
      const debAsset = data.assets.find(a => a.name.endsWith('.deb'));
      const exeAsset = data.assets.find(a => a.name.endsWith('.exe'));

      if (debAsset && debDownloadLink) {
        debDownloadLink.href = debAsset.browser_download_url;
      }
      if (exeAsset && exeDownloadLink) {
        exeDownloadLink.href = exeAsset.browser_download_url;
      }

      // Update hero button if matched
      if (heroDownloadBtn) {
        const ua = navigator.userAgent;
        if (ua.indexOf('Win') !== -1 && exeAsset) {
          heroDownloadBtn.href = exeAsset.browser_download_url;
        } else if ((ua.indexOf('Linux') !== -1 || ua.indexOf('X11') !== -1) && debAsset) {
          heroDownloadBtn.href = debAsset.browser_download_url;
        }
      }
    }

    if (apiStatusNote) {
      apiStatusNote.textContent = `Latest release ${tagName} verified via GitHub Releases.`;
    }
  } catch (err) {
    // Graceful fallback to hardcoded v1.7.1 links
    if (apiStatusNote) {
      apiStatusNote.textContent = 'Version 1.7.1 production packages ready for download.';
    }
  }
}

/* ==========================================================================
   4. Visual Tour / Gallery Tabs & Lightbox Modal
   ========================================================================== */
function initGallery() {
  const tabBtns = document.querySelectorAll('.gallery-tab-btn');
  const slides = document.querySelectorAll('.gallery-slide');
  const lightbox = document.getElementById('gallery-lightbox');
  const lightboxImg = document.getElementById('lightbox-img');
  const lightboxClose = document.getElementById('lightbox-close');

  tabBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      const target = btn.getAttribute('data-gallery-target');
      if (!target) return;

      tabBtns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');

      slides.forEach(slide => {
        if (slide.id === target) {
          slide.classList.add('active');
        } else {
          slide.classList.remove('active');
        }
      });
    });
  });

  // Lightbox click on screenshots
  const galleryImages = document.querySelectorAll('.gallery-zoom-target');
  galleryImages.forEach(img => {
    img.addEventListener('click', () => {
      if (!lightbox || !lightboxImg) return;
      lightboxImg.src = img.src;
      lightboxImg.alt = img.alt;
      lightbox.classList.add('open');
      document.body.style.overflow = 'hidden';
    });
  });

  function closeLightbox() {
    if (!lightbox) return;
    lightbox.classList.remove('open');
    document.body.style.overflow = '';
  }

  if (lightboxClose) lightboxClose.addEventListener('click', closeLightbox);
  if (lightbox) {
    lightbox.addEventListener('click', (e) => {
      if (e.target === lightbox) closeLightbox();
    });
  }

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && lightbox && lightbox.classList.contains('open')) {
      closeLightbox();
    }
  });
}

/* ==========================================================================
   5. Terminal Code Copy Buttons
   ========================================================================== */
function initCopyButtons() {
  const copyBtns = document.querySelectorAll('.btn-copy');

  copyBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      const targetId = btn.getAttribute('data-copy-target');
      let textToCopy = '';

      if (targetId) {
        const codeEl = document.getElementById(targetId);
        if (codeEl) textToCopy = codeEl.innerText.trim();
      } else {
        const parentBox = btn.closest('.code-box');
        if (parentBox) {
          const codeEl = parentBox.querySelector('.code-text');
          if (codeEl) textToCopy = codeEl.innerText.trim();
        }
      }

      if (!textToCopy) return;

      navigator.clipboard.writeText(textToCopy).then(() => {
        const originalHtml = btn.innerHTML;
        btn.classList.add('copied');
        btn.innerHTML = `
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
            <polyline points="20 6 9 17 4 12"></polyline>
          </svg>
          <span>Copied</span>
        `;

        setTimeout(() => {
          btn.classList.remove('copied');
          btn.innerHTML = originalHtml;
        }, 2000);
      }).catch(err => {
        console.error('Clipboard copy failed:', err);
      });
    });
  });
}

/* ==========================================================================
   6. Keyboard Shortcuts Directory & Live Search Filter
   ========================================================================== */
const SHORTCUTS_DATA = [
  // File & Export
  { cat: 'file', label: 'Open Document or Image', keys: ['Ctrl', 'O'] },
  { cat: 'file', label: 'Open in New Window', keys: ['Ctrl', 'Shift', 'O'] },
  { cat: 'file', label: 'Save Document', keys: ['Ctrl', 'S'] },
  { cat: 'file', label: 'Save As Copy', keys: ['Ctrl', 'Shift', 'S'] },
  { cat: 'file', label: 'Export Sheet (DPI / Format)', keys: ['Ctrl', 'E'] },
  { cat: 'file', label: 'Quick Export as PDF', keys: ['Ctrl', 'Shift', 'E'] },
  { cat: 'file', label: 'Print Document', keys: ['Ctrl', 'P'] },
  { cat: 'file', label: 'Print Preview Sheet', keys: ['Ctrl', 'Shift', 'P'] },
  { cat: 'file', label: 'Extract Text to Clipboard', keys: ['Ctrl', 'Shift', 'C'] },
  { cat: 'file', label: 'Quit Application', keys: ['Ctrl', 'Q'] },

  // Viewing & Navigation
  { cat: 'view', label: 'Zoom In', keys: ['Ctrl', '+'] },
  { cat: 'view', label: 'Zoom Out', keys: ['Ctrl', '-'] },
  { cat: 'view', label: 'Actual Size (100%)', keys: ['Ctrl', '0'] },
  { cat: 'view', label: 'Zoom to Fit Window', keys: ['Ctrl', '9'] },
  { cat: 'view', label: 'Toggle Thumbnail Sidebar', keys: ['Ctrl', 'B'] },
  { cat: 'view', label: 'Fullscreen Slideshow', keys: ['F11'] },
  { cat: 'view', label: 'Summon Optical Loupe Lens', keys: ['~'] },
  { cat: 'view', label: 'Pan Document (Hand Tool)', keys: ['Space', 'Drag'] },
  { cat: 'view', label: 'Rotate 90° Left', keys: ['Ctrl', 'L'] },
  { cat: 'view', label: 'Rotate 90° Right', keys: ['Ctrl', 'R'] },
  { cat: 'view', label: 'Next / Previous Page', keys: ['↓ / ↑', 'or', '→ / ←'] },

  // Markup & Adjustments
  { cat: 'markup', label: 'Toggle Markup Toolbar', keys: ['Ctrl', 'Shift', 'A'] },
  { cat: 'markup', label: 'Crop Marquee Selection', keys: ['Ctrl', 'K'] },
  { cat: 'markup', label: 'Adjust Color & Histogram', keys: ['Ctrl', 'Alt', 'C'] },
  { cat: 'markup', label: 'Adjust Size & Resolution', keys: ['Ctrl', 'Alt', 'S'] },
  { cat: 'markup', label: 'Show Metadata Inspector', keys: ['Ctrl', 'I'] },
  { cat: 'markup', label: 'Undo Action', keys: ['Ctrl', 'Z'] },
  { cat: 'markup', label: 'Redo Action', keys: ['Ctrl', 'Shift', 'Z'] },
  { cat: 'markup', label: 'Delete Selected Annotation', keys: ['Delete'] }
];

function initShortcuts() {
  const container = document.getElementById('shortcuts-container');
  const searchInput = document.getElementById('shortcuts-search-input');
  const tabBtns = document.querySelectorAll('.shortcuts-tab-btn');

  if (!container) return;

  let activeCategory = 'all';
  let searchQuery = '';

  function render() {
    const filtered = SHORTCUTS_DATA.filter(item => {
      const matchCat = activeCategory === 'all' || item.cat === activeCategory;
      const matchQuery = searchQuery === '' ||
        item.label.toLowerCase().includes(searchQuery) ||
        item.keys.join(' ').toLowerCase().includes(searchQuery);
      return matchCat && matchQuery;
    });

    if (filtered.length === 0) {
      container.innerHTML = `
        <div style="grid-column: 1 / -1; text-align: center; padding: 36px; color: var(--text-tertiary); font-size: 14px;">
          No matching keyboard shortcuts found for "${escapeHtml(searchQuery)}".
        </div>
      `;
      return;
    }

    container.innerHTML = filtered.map(item => `
      <div class="shortcut-item">
        <span class="shortcut-label">${escapeHtml(item.label)}</span>
        <div class="shortcut-keys">
          ${item.keys.map(k => `<kbd>${escapeHtml(k)}</kbd>`).join('')}
        </div>
      </div>
    `).join('');
  }

  if (searchInput) {
    searchInput.addEventListener('input', (e) => {
      searchQuery = e.target.value.toLowerCase().trim();
      render();
    });
  }

  tabBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      tabBtns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      activeCategory = btn.getAttribute('data-shortcuts-cat') || 'all';
      render();
    });
  });

  render();
}

/* ==========================================================================
   7. FAQ Accordion
   ========================================================================== */
function initFAQ() {
  const items = document.querySelectorAll('.faq-item');

  items.forEach(item => {
    const questionBtn = item.querySelector('.faq-question');
    if (!questionBtn) return;

    questionBtn.addEventListener('click', () => {
      const isOpen = item.classList.contains('open');

      // Close all items first for clean accordion
      items.forEach(i => {
        i.classList.remove('open');
        const btn = i.querySelector('.faq-question');
        if (btn) btn.setAttribute('aria-expanded', 'false');
      });

      if (!isOpen) {
        item.classList.add('open');
        questionBtn.setAttribute('aria-expanded', 'true');
      }
    });
  });
}

/* ==========================================================================
   8. Mobile Navigation Toggle
   ========================================================================== */
function initMobileNav() {
  const toggleBtn = document.getElementById('nav-mobile-toggle');
  const navMenu = document.getElementById('nav-menu');
  const navLinks = document.querySelectorAll('.nav-link');

  if (!toggleBtn || !navMenu) return;

  toggleBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    const isOpen = navMenu.classList.contains('open');
    navMenu.classList.toggle('open');
    toggleBtn.setAttribute('aria-expanded', !isOpen ? 'true' : 'false');
  });

  navLinks.forEach(link => {
    link.addEventListener('click', () => {
      navMenu.classList.remove('open');
      toggleBtn.setAttribute('aria-expanded', 'false');
    });
  });

  document.addEventListener('click', (e) => {
    if (navMenu.classList.contains('open') && !navMenu.contains(e.target) && e.target !== toggleBtn) {
      navMenu.classList.remove('open');
      toggleBtn.setAttribute('aria-expanded', 'false');
    }
  });
}

function escapeHtml(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}
