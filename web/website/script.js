(function () {
  'use strict';

  var REPO_OWNER = 'shivamprasad1001';
  var REPO_NAME = 'previewmacos';
  var FALLBACK_RELEASE = {
    version: 'v1.7.1',
    debName: 'preview-app_1.7.1_amd64.deb',
    debUrl: 'https://github.com/shivamprasad1001/previewmacos/releases/download/v1.7.1/preview-app_1.7.1_amd64.deb',
    exeName: 'Preview-Setup-v1.7.1.exe',
    exeUrl: 'https://github.com/shivamprasad1001/previewmacos/releases/download/v1.7.1/Preview-Setup-v1.7.1.exe'
  };

  var GALLERY_SLIDES = [
    {
      src: 'assets/preview_main_dark.png',
      width: 1180,
      height: 780,
      windowTitle: 'preview_main_dark.png',
      alt: 'macOS Sequoia dark mode with traffic-light controls and thumbnail sidebar',
      caption: 'macOS Sequoia dark mode with traffic-light controls and thumbnail sidebar.'
    },
    {
      src: 'assets/preview_main_light.png',
      width: 1180,
      height: 780,
      windowTitle: 'preview_main_light.png',
      alt: 'Preview in clean macOS Sequoia light mode',
      caption: 'Light mode interface with crisp toolbar and page thumbnails.'
    },
    {
      src: 'assets/preview_markup_showcase.png',
      width: 1180,
      height: 780,
      windowTitle: 'preview_markup_showcase.png',
      alt: 'Markup toolbar with redaction marker, sticky notes, and vector shapes',
      caption: 'Markup suite featuring redaction blackout, sticky notes, and vector shapes.'
    },
    {
      src: 'assets/preview_adjust_color.png',
      width: 320,
      height: 480,
      windowTitle: 'preview_adjust_color.png',
      alt: 'Adjust Color dialog showing live RGB histogram and auto levels',
      caption: 'Adjust Color panel with real-time RGB histogram, exposure sliders, and Auto Levels.'
    },
    {
      src: 'assets/preview_updater.png',
      width: 540,
      height: 500,
      windowTitle: 'preview_updater.png',
      alt: 'Sparkle-style in-app software updater dialog with download progress',
      caption: 'Sparkle-style in-app updater with release notes and live download progress.'
    }
  ];

  var currentRelease = {
    version: FALLBACK_RELEASE.version,
    debName: FALLBACK_RELEASE.debName,
    debUrl: FALLBACK_RELEASE.debUrl,
    exeName: FALLBACK_RELEASE.exeName,
    exeUrl: FALLBACK_RELEASE.exeUrl
  };

  /* -------------------------------------------------------------------------- */
  /* Theme Toggle                                                               */
  /* -------------------------------------------------------------------------- */
  function initTheme() {
    var toggle = document.getElementById('theme-toggle');
    if (!toggle) return;

    function applyTheme(theme) {
      document.documentElement.setAttribute('data-theme', theme);
      toggle.setAttribute('aria-pressed', theme === 'dark' ? 'true' : 'false');
      toggle.setAttribute('aria-label', theme === 'dark' ? 'Switch to light theme' : 'Switch to dark theme');
    }

    var current = document.documentElement.getAttribute('data-theme') || 'light';
    applyTheme(current);

    toggle.addEventListener('click', function () {
      var active = document.documentElement.getAttribute('data-theme') === 'dark' ? 'dark' : 'light';
      var next = active === 'dark' ? 'light' : 'dark';
      applyTheme(next);
      try {
        localStorage.setItem('preview-theme', next);
      } catch (e) {
        /* ignore storage restrictions */
      }
    });
  }

  /* -------------------------------------------------------------------------- */
  /* Mobile Navigation                                                          */
  /* -------------------------------------------------------------------------- */
  function initMobileNav() {
    var toggle = document.getElementById('mobile-menu-toggle');
    var menu = document.getElementById('mobile-nav');
    if (!toggle || !menu) return;

    function setOpen(open) {
      menu.hidden = !open;
      toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
    }

    toggle.addEventListener('click', function () {
      var isOpen = toggle.getAttribute('aria-expanded') === 'true';
      setOpen(!isOpen);
    });

    menu.addEventListener('click', function (e) {
      if (e.target && e.target.tagName === 'A') {
        setOpen(false);
      }
    });

    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && toggle.getAttribute('aria-expanded') === 'true') {
        setOpen(false);
        toggle.focus();
      }
    });
  }

  /* -------------------------------------------------------------------------- */
  /* OS Detection & GitHub Latest Release API                                   */
  /* -------------------------------------------------------------------------- */
  function detectPlatform() {
    var uaDataPlatform = (navigator.userAgentData && navigator.userAgentData.platform) || '';
    var raw = (uaDataPlatform + ' ' + (navigator.platform || '') + ' ' + (navigator.userAgent || '')).toLowerCase();

    if (/android|iphone|ipad|ipod/.test(raw)) return 'mobile';
    if (/win/.test(raw)) return 'windows';
    if (/linux|x11/.test(raw)) return 'linux';
    if (/mac/.test(raw)) return 'macos';
    return 'other';
  }

  function updateHeroDownloadCTA() {
    var btn = document.getElementById('hero-download-btn');
    var label = document.getElementById('hero-download-label');
    if (!btn || !label) return;

    var os = detectPlatform();
    if (os === 'linux') {
      label.textContent = 'Download for Linux (.deb)';
      btn.setAttribute('href', currentRelease.debUrl);
    } else if (os === 'windows') {
      label.textContent = 'Download for Windows (.exe)';
      btn.setAttribute('href', currentRelease.exeUrl);
    } else {
      label.textContent = 'Download ' + currentRelease.version;
      btn.setAttribute('href', '#install');
    }
  }

  function renderReleaseLinks() {
    var heroVer = document.getElementById('hero-version');
    var releaseVer = document.getElementById('release-version-text');
    var debName = document.getElementById('deb-filename');
    var debLink = document.getElementById('deb-download-link');
    var debCmd = document.getElementById('cmd-deb');
    var exeName = document.getElementById('exe-filename');
    var exeLink = document.getElementById('exe-download-link');

    if (heroVer) heroVer.textContent = currentRelease.version;
    if (releaseVer) releaseVer.textContent = currentRelease.version;
    if (debName) debName.textContent = currentRelease.debName;
    if (debLink) debLink.setAttribute('href', currentRelease.debUrl);
    if (debCmd) {
      debCmd.textContent =
        'wget ' +
        currentRelease.debUrl +
        ' && sudo dpkg -i ' +
        currentRelease.debName +
        ' || sudo apt-get install -f -y';
    }
    if (exeName) exeName.textContent = currentRelease.exeName;
    if (exeLink) exeLink.setAttribute('href', currentRelease.exeUrl);

    updateHeroDownloadCTA();
  }

  function fetchLatestRelease() {
    if (typeof fetch !== 'function') return;

    var releaseApi = 'https://api.github.com/repos/' + REPO_OWNER + '/' + REPO_NAME + '/releases/latest';
    var repoApi = 'https://api.github.com/repos/' + REPO_OWNER + '/' + REPO_NAME;

    fetch(releaseApi, { headers: { Accept: 'application/vnd.github+json' } })
      .then(function (res) {
        if (!res.ok) throw new Error('Release API status ' + res.status);
        return res.json();
      })
      .then(function (data) {
        if (!data || !data.tag_name) return;
        currentRelease.version = data.tag_name;

        var assets = Array.isArray(data.assets) ? data.assets : [];
        for (var i = 0; i < assets.length; i++) {
          var asset = assets[i];
          if (!asset || !asset.name || !asset.browser_download_url) continue;
          if (/\.deb$/i.test(asset.name)) {
            currentRelease.debName = asset.name;
            currentRelease.debUrl = asset.browser_download_url;
          } else if (/\.exe$/i.test(asset.name)) {
            currentRelease.exeName = asset.name;
            currentRelease.exeUrl = asset.browser_download_url;
          }
        }
        renderReleaseLinks();
      })
      .catch(function () {
        /* Keep v1.7.0 fallback links silently */
      });

    fetch(repoApi, { headers: { Accept: 'application/vnd.github+json' } })
      .then(function (res) {
        if (!res.ok) return null;
        return res.json();
      })
      .then(function (data) {
        var starEl = document.getElementById('github-star-count');
        if (!starEl || !data || typeof data.stargazers_count !== 'number') return;
        if (data.stargazers_count > 0) {
          starEl.textContent = String(data.stargazers_count);
          starEl.hidden = false;
        }
      })
      .catch(function () {
        /* Keep star button clean without count */
      });
  }

  /* -------------------------------------------------------------------------- */
  /* Copy Buttons                                                               */
  /* -------------------------------------------------------------------------- */
  function fallbackCopy(text) {
    return new Promise(function (resolve, reject) {
      try {
        var area = document.createElement('textarea');
        area.value = text;
        area.setAttribute('readonly', '');
        area.style.position = 'fixed';
        area.style.left = '-9999px';
        document.body.appendChild(area);
        area.select();
        var ok = document.execCommand('copy');
        document.body.removeChild(area);
        if (ok) {
          resolve();
        } else {
          reject(new Error('Copy command failed'));
        }
      } catch (err) {
        reject(err);
      }
    });
  }

  function copyText(text) {
    if (navigator.clipboard && typeof navigator.clipboard.writeText === 'function') {
      return navigator.clipboard.writeText(text).catch(function () {
        return fallbackCopy(text);
      });
    }
    return fallbackCopy(text);
  }

  function initCopyButtons() {
    var buttons = document.querySelectorAll('.copy-btn');
    for (var i = 0; i < buttons.length; i++) {
      (function (btn) {
        btn.addEventListener('click', function () {
          var targetId = btn.getAttribute('data-copy-target');
          var targetEl = targetId ? document.getElementById(targetId) : null;
          if (!targetEl) return;

          var text = targetEl.textContent ? targetEl.textContent.trim() : '';
          copyText(text)
            .then(function () {
              var original = btn.textContent;
              btn.textContent = 'Copied';
              btn.classList.add('is-copied');
              window.setTimeout(function () {
                btn.textContent = original || 'Copy';
                btn.classList.remove('is-copied');
              }, 1800);
            })
            .catch(function () {
              btn.textContent = 'Failed';
            });
        });
      })(buttons[i]);
    }
  }

  /* -------------------------------------------------------------------------- */
  /* Gallery & Lightbox                                                         */
  /* -------------------------------------------------------------------------- */
  function initGallery() {
    var mainImg = document.getElementById('gallery-main-img');
    var winTitle = document.getElementById('gallery-window-title');
    var captionEl = document.getElementById('gallery-caption');
    var tabs = document.querySelectorAll('.gallery-tab');
    var thumbs = document.querySelectorAll('.gallery-thumb');
    var prevBtn = document.getElementById('gallery-prev');
    var nextBtn = document.getElementById('gallery-next');
    var openBtn = document.getElementById('gallery-open-lightbox');
    var expandBtn = document.getElementById('gallery-expand-btn');
    var updaterLink = document.querySelector('.updater-link');

    var lightbox = document.getElementById('lightbox');
    var lightboxBackdrop = document.getElementById('lightbox-backdrop');
    var lightboxClose = document.getElementById('lightbox-close');
    var lightboxImg = document.getElementById('lightbox-img');
    var lightboxCaption = document.getElementById('lightbox-caption');
    var lightboxCounter = document.getElementById('lightbox-counter');
    var lightboxPrev = document.getElementById('lightbox-prev');
    var lightboxNext = document.getElementById('lightbox-next');

    if (!mainImg || !lightbox) return;

    var activeIndex = 0;
    var lastFocused = null;

    function setSlide(index) {
      var total = GALLERY_SLIDES.length;
      activeIndex = ((index % total) + total) % total;
      var slide = GALLERY_SLIDES[activeIndex];

      mainImg.src = slide.src;
      mainImg.alt = slide.alt;
      mainImg.width = slide.width;
      mainImg.height = slide.height;
      if (winTitle) winTitle.textContent = slide.windowTitle;
      if (captionEl) captionEl.textContent = slide.caption;

      for (var i = 0; i < tabs.length; i++) {
        var isCurrent = Number(tabs[i].getAttribute('data-slide')) === activeIndex;
        tabs[i].classList.toggle('is-active', isCurrent);
        tabs[i].setAttribute('aria-selected', isCurrent ? 'true' : 'false');
      }

      for (var j = 0; j < thumbs.length; j++) {
        var thumbCurrent = Number(thumbs[j].getAttribute('data-slide')) === activeIndex;
        thumbs[j].classList.toggle('is-active', thumbCurrent);
      }

      if (!lightbox.hidden) {
        updateLightbox();
      }
    }

    function updateLightbox() {
      var slide = GALLERY_SLIDES[activeIndex];
      lightboxImg.src = slide.src;
      lightboxImg.alt = slide.alt;
      lightboxImg.width = slide.width;
      lightboxImg.height = slide.height;
      lightboxCaption.textContent = slide.caption;
      lightboxCounter.textContent = (activeIndex + 1) + ' / ' + GALLERY_SLIDES.length;
    }

    function openLightbox() {
      lastFocused = document.activeElement;
      updateLightbox();
      lightbox.hidden = false;
      document.body.style.overflow = 'hidden';
      lightboxClose.focus();
    }

    function closeLightbox() {
      lightbox.hidden = true;
      document.body.style.overflow = '';
      if (lastFocused && typeof lastFocused.focus === 'function') {
        lastFocused.focus();
      }
    }

    for (var i = 0; i < tabs.length; i++) {
      (function (tab) {
        tab.addEventListener('click', function () {
          setSlide(Number(tab.getAttribute('data-slide')));
        });
      })(tabs[i]);
    }

    for (var j = 0; j < thumbs.length; j++) {
      (function (thumb) {
        thumb.addEventListener('click', function () {
          setSlide(Number(thumb.getAttribute('data-slide')));
        });
      })(thumbs[j]);
    }

    if (prevBtn) prevBtn.addEventListener('click', function () { setSlide(activeIndex - 1); });
    if (nextBtn) nextBtn.addEventListener('click', function () { setSlide(activeIndex + 1); });
    if (openBtn) openBtn.addEventListener('click', openLightbox);
    if (expandBtn) expandBtn.addEventListener('click', openLightbox);
    if (updaterLink) {
      updaterLink.addEventListener('click', function () {
        setSlide(4);
      });
    }

    if (lightboxBackdrop) lightboxBackdrop.addEventListener('click', closeLightbox);
    if (lightboxClose) lightboxClose.addEventListener('click', closeLightbox);
    if (lightboxPrev) lightboxPrev.addEventListener('click', function () { setSlide(activeIndex - 1); });
    if (lightboxNext) lightboxNext.addEventListener('click', function () { setSlide(activeIndex + 1); });

    document.addEventListener('keydown', function (e) {
      if (lightbox.hidden) return;
      if (e.key === 'Escape') {
        closeLightbox();
      } else if (e.key === 'ArrowLeft') {
        setSlide(activeIndex - 1);
      } else if (e.key === 'ArrowRight') {
        setSlide(activeIndex + 1);
      }
    });
  }

  /* -------------------------------------------------------------------------- */
  /* Keyboard Shortcuts Filter & Tabs                                           */
  /* -------------------------------------------------------------------------- */
  function initShortcuts() {
    var tabs = document.querySelectorAll('.shortcut-tab');
    var searchInput = document.getElementById('shortcut-search');
    var tbody = document.getElementById('shortcut-tbody');
    var statusEl = document.getElementById('shortcut-status');
    var emptyEl = document.getElementById('shortcut-empty');
    if (!tbody || !searchInput) return;

    var rows = tbody.querySelectorAll('tr');
    var activeCategory = 'file';
    var categoryNames = {
      file: 'File & Export',
      view: 'Viewing & Navigation',
      markup: 'Markup & Image Adjustments'
    };

    function applyFilter() {
      var query = searchInput.value.trim().toLowerCase();
      var visibleCount = 0;

      for (var i = 0; i < rows.length; i++) {
        var row = rows[i];
        var cat = row.getAttribute('data-cat');
        var text = (row.textContent || '').toLowerCase();
        var matches = query ? text.indexOf(query) !== -1 : cat === activeCategory;
        row.hidden = !matches;
        if (matches) visibleCount++;
      }

      if (emptyEl) {
        emptyEl.hidden = visibleCount > 0;
      }

      if (statusEl) {
        if (query) {
          statusEl.textContent = visibleCount + ' matching shortcut' + (visibleCount === 1 ? '' : 's') + ' across all categories';
        } else {
          statusEl.textContent = 'Showing ' + visibleCount + ' shortcuts in ' + (categoryNames[activeCategory] || activeCategory);
        }
      }
    }

    for (var i = 0; i < tabs.length; i++) {
      (function (tab) {
        tab.addEventListener('click', function () {
          activeCategory = tab.getAttribute('data-category') || 'file';
          for (var j = 0; j < tabs.length; j++) {
            var isSelected = tabs[j] === tab;
            tabs[j].classList.toggle('is-active', isSelected);
            tabs[j].setAttribute('aria-selected', isSelected ? 'true' : 'false');
          }
          if (searchInput.value.trim()) {
            searchInput.value = '';
          }
          applyFilter();
        });
      })(tabs[i]);
    }

    searchInput.addEventListener('input', applyFilter);
    applyFilter();
  }

  /* -------------------------------------------------------------------------- */
  /* Scroll Reveal (IntersectionObserver)                                       */
  /* -------------------------------------------------------------------------- */
  function initScrollReveal() {
    // Apply staggered reveal classes to card and list grids for fluid Apple-style sequencing
    var staggerSelectors = [
      '.download-grid > .download-card',
      '.feature-grid > .feature-card',
      '.tech-strip > li',
      '.arch-grid > .arch-box',
      '.contrib-grid > .contrib-card',
      '.faq-list > .faq-item'
    ];

    for (var s = 0; s < staggerSelectors.length; s++) {
      var groupItems = document.querySelectorAll(staggerSelectors[s]);
      for (var g = 0; g < groupItems.length; g++) {
        var item = groupItems[g];
        item.classList.add('reveal');
        // Stagger siblings within the same grid container (capped at 200ms)
        var parent = item.parentElement;
        var siblingIndex = 0;
        if (parent) {
          for (var c = 0; c < parent.children.length; c++) {
            if (parent.children[c] === item) {
              siblingIndex = c;
              break;
            }
          }
        }
        var delayMs = Math.min(siblingIndex * 50, 200);
        item.style.setProperty('--reveal-delay', delayMs + 'ms');
      }
    }

    // Avoid double-hiding parent wrappers whose direct children now animate individually
    var wrapperSelectors = ['.feature-group', '.tech-strip', '.arch-grid', '.contrib-grid', '.faq-list'];
    for (var w = 0; w < wrapperSelectors.length; w++) {
      var wrappers = document.querySelectorAll(wrapperSelectors[w]);
      for (var k = 0; k < wrappers.length; k++) {
        wrappers[k].classList.remove('reveal');
      }
    }

    // Also include group titles so headings lead cleanly ahead of their cards
    var groupTitles = document.querySelectorAll('.feature-group-title');
    for (var t = 0; t < groupTitles.length; t++) {
      groupTitles[t].classList.add('reveal');
    }

    var els = document.querySelectorAll('.reveal');
    if (!els.length) return;

    function markSettled(el) {
      el.classList.add('reveal-settled');
    }

    function revealElement(el, immediate) {
      if (el.classList.contains('revealed')) return;
      if (immediate) {
        el.style.setProperty('--reveal-delay', '0ms');
      }
      el.classList.add('revealed');
      var onEnd = function (evt) {
        if (evt.target !== el) return;
        el.removeEventListener('transitionend', onEnd);
        markSettled(el);
      };
      el.addEventListener('transitionend', onEnd);
      window.setTimeout(function () {
        el.removeEventListener('transitionend', onEnd);
        markSettled(el);
      }, 1000);
    }

    var mql = window.matchMedia ? window.matchMedia('(prefers-reduced-motion: reduce)') : null;
    if ((mql && mql.matches) || typeof IntersectionObserver !== 'function') {
      for (var f = 0; f < els.length; f++) {
        els[f].classList.add('revealed', 'reveal-settled');
      }
      return;
    }

    var observer = new IntersectionObserver(
      function (entries) {
        for (var i = 0; i < entries.length; i++) {
          if (entries[i].isIntersecting) {
            revealElement(entries[i].target, false);
            observer.unobserve(entries[i].target);
          }
        }
      },
      {
        threshold: 0.01,
        rootMargin: '0px 0px -12px 0px'
      }
    );

    var vh = window.innerHeight || 900;
    for (var i = 0; i < els.length; i++) {
      var rect = els[i].getBoundingClientRect();
      // Reveal anything already above or inside the current viewport immediately
      if (rect.top < vh * 0.92) {
        revealElement(els[i], true);
      } else {
        observer.observe(els[i]);
      }
    }

    // Ensure anchor jumps immediately reveal the destination section
    function revealHashTarget() {
      var hash = window.location.hash;
      if (!hash || hash.length < 2) return;
      var target = document.getElementById(hash.slice(1));
      if (!target) return;
      var nested = target.querySelectorAll('.reveal');
      for (var n = 0; n < nested.length; n++) {
        revealElement(nested[n], false);
        observer.unobserve(nested[n]);
      }
      if (target.classList.contains('reveal')) {
        revealElement(target, false);
        observer.unobserve(target);
      }
    }

    window.addEventListener('hashchange', revealHashTarget);
    if (window.location.hash) {
      revealHashTarget();
    }

    // Respect runtime changes to reduced-motion preference
    if (mql && typeof mql.addEventListener === 'function') {
      mql.addEventListener('change', function (e) {
        if (!e.matches) return;
        observer.disconnect();
        for (var r = 0; r < els.length; r++) {
          revealElement(els[r], true);
        }
      });
    }
  }

  /* -------------------------------------------------------------------------- */
  /* Boot                                                                       */
  /* -------------------------------------------------------------------------- */
  document.addEventListener('DOMContentLoaded', function () {
    initTheme();
    initMobileNav();
    renderReleaseLinks();
    fetchLatestRelease();
    initCopyButtons();
    initGallery();
    initShortcuts();
    initScrollReveal();
  });
})();
