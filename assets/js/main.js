/* Omokage — comportements de la page.
   Script classique (pas de module) pour fonctionner aussi en ouvrant index.html directement. */
(function () {
  'use strict';

  var doc = document;
  var root = doc.documentElement;
  var reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)');

  /* ---------- Apparitions ---------- */

  var revealed = doc.querySelectorAll('[data-reveal]');
  if ('IntersectionObserver' in window) {
    var revealObserver = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        entry.target.classList.add('is-in');
        revealObserver.unobserve(entry.target);
      });
    }, { rootMargin: '0px 0px -8% 0px', threshold: 0.08 });
    revealed.forEach(function (el) { revealObserver.observe(el); });
  } else {
    revealed.forEach(function (el) { el.classList.add('is-in'); });
  }

  /* ---------- En-tête, progression, fil de la lignée, mode nuit ---------- */

  var header = doc.querySelector('.entete');
  var progress = doc.querySelector('.progression');
  var fil = doc.querySelector('.fil');
  var filInk = doc.querySelector('.fil__encre');
  var filLinks = fil ? Array.prototype.slice.call(fil.querySelectorAll('a')) : [];
  var sections = filLinks.map(function (a) { return doc.querySelector(a.getAttribute('href')); });
  var night = doc.querySelector('[data-nuit]');
  var omokage = doc.querySelector('[data-omokage]');
  var hayato = omokage ? omokage.querySelector('.omokage__hayato') : null;
  var ticking = false;

  function clamp(v, a, b) { return Math.min(b, Math.max(a, v)); }

  function onScroll() {
    ticking = false;
    var y = window.scrollY || window.pageYOffset;
    var vh = window.innerHeight;
    var max = Math.max(1, doc.documentElement.scrollHeight - vh);
    var p = clamp(y / max, 0, 1);

    if (header) header.classList.toggle('is-scrolled', y > 40);
    if (progress) progress.style.setProperty('--p', p.toFixed(4));

    // Section active : la dernière dont le haut a franchi le tiers de l'écran.
    var active = 0;
    sections.forEach(function (s, i) {
      if (s && s.getBoundingClientRect().top < vh * 0.34) active = i;
    });
    filLinks.forEach(function (a, i) {
      a.classList.toggle('is-active', i === active);
      if (i === active) a.setAttribute('aria-current', 'true'); else a.removeAttribute('aria-current');
    });
    if (filInk && filLinks.length > 1) {
      filInk.style.setProperty('--p', (active / (filLinks.length - 1)).toFixed(4));
    }

    if (night) {
      var r = night.getBoundingClientRect();
      root.classList.toggle('mode-nuit', r.top < vh * 0.2 && r.bottom > 64);
    }

    if (hayato && !reduceMotion.matches) {
      var o = omokage.getBoundingClientRect();
      // 0 quand le bloc entre par le bas, 1 quand il atteint le tiers supérieur.
      var t = clamp((vh - o.top) / (vh * 0.75), 0, 1);
      var ease = 1 - Math.pow(1 - t, 3);
      var shift = (1 - ease) * Math.min(window.innerWidth * 0.32, 340);
      hayato.style.setProperty('--dx', shift.toFixed(1) + 'px');
      hayato.style.setProperty('--o', (0.12 + ease * 0.5).toFixed(3));
      hayato.style.setProperty('--b', ((1 - ease) * 6).toFixed(2) + 'px');
    }
  }

  function requestTick() {
    if (!ticking) { ticking = true; window.requestAnimationFrame(onScroll); }
  }
  window.addEventListener('scroll', requestTick, { passive: true });
  window.addEventListener('resize', requestTick);
  onScroll();

  if (hayato && reduceMotion.matches) {
    hayato.style.setProperty('--dx', '0.12em');
    hayato.style.setProperty('--o', '0.5');
  }

  /* ---------- La planche de photographies ---------- */

  var planche = doc.querySelector('[data-planche]');
  var afterChoice = doc.getElementById('apres-choix');

  function revealAfterChoice(focus) {
    if (!afterChoice) return;
    afterChoice.classList.add('is-visible');
    afterChoice.querySelectorAll('[data-reveal]').forEach(function (el) { el.classList.add('is-in'); });
    if (focus) afterChoice.focus({ preventScroll: true });
  }

  if (planche) {
    var photos = Array.prototype.slice.call(planche.querySelectorAll('.planche__photo'));
    var note = planche.querySelector('.planche__note');
    var skip = planche.querySelector('[data-planche-passer]');

    photos.forEach(function (btn) {
      btn.addEventListener('click', function () {
        if (planche.classList.contains('is-choisi')) return;
        var li = btn.closest('li');
        li.classList.add('is-choisi');
        var name = btn.querySelector('.planche__nom > span');
        name.classList.remove('illisible');
        name.textContent = 'Uchiha Hayato';
        planche.classList.add('is-choisi');
        photos.forEach(function (b) { b.setAttribute('aria-disabled', 'true'); });
        btn.setAttribute('aria-pressed', 'true');
        if (note) note.textContent = 'Sur cette page, chacun des six était le bon. Sur le carton du vieil homme, un seul l’était.';
        if (skip) skip.hidden = true;
        revealAfterChoice(true);
      });
    });

    if (skip) {
      skip.addEventListener('click', function () {
        skip.hidden = true;
        if (note) note.textContent = 'Il pose le doigt sur l’un d’eux.';
        revealAfterChoice(true);
      });
    }
  }

  /* ---------- Musique de fond ----------
     Les navigateurs interdisent le son avant un geste du visiteur :
     la musique démarre au premier clic (ou Entrée / Espace), sauf si le visiteur l'a coupée. */

  var music = doc.getElementById('musique');
  var musicBtn = doc.querySelector('[data-musique]');

  if (music && musicBtn) {
    var PREF_KEY = 'omokage-musique';
    var VOLUME = 0.35;
    var wanted = true;
    var fadeTimer = null;
    var pausedByHide = false;

    try { wanted = localStorage.getItem(PREF_KEY) !== 'off'; } catch (e) { /* stockage indisponible */ }

    var remember = function (on) {
      try { localStorage.setItem(PREF_KEY, on ? 'on' : 'off'); } catch (e) { /* stockage indisponible */ }
    };

    var setUi = function (on) {
      musicBtn.classList.toggle('is-playing', on);
      musicBtn.setAttribute('aria-pressed', on ? 'true' : 'false');
    };

    var fadeTo = function (target, ms, done) {
      clearInterval(fadeTimer);
      var start = music.volume;
      var steps = Math.max(1, Math.round(ms / 50));
      var i = 0;
      fadeTimer = setInterval(function () {
        i += 1;
        music.volume = clamp(start + (target - start) * (i / steps), 0, 1);
        if (i >= steps) {
          clearInterval(fadeTimer);
          if (done) done();
        }
      }, 50);
    };

    var playMusic = function () {
      music.volume = 0;
      var attempt = music.play();
      var started = function () { setUi(true); fadeTo(VOLUME, 2500); };
      if (attempt && typeof attempt.then === 'function') {
        attempt.then(started, function () { setUi(false); });
      } else {
        started();
      }
    };

    var pauseMusic = function () {
      setUi(false);
      fadeTo(0, 600, function () { music.pause(); });
    };

    musicBtn.addEventListener('click', function () {
      if (musicBtn.getAttribute('aria-pressed') === 'true') {
        wanted = false;
        remember(false);
        pauseMusic();
      } else {
        wanted = true;
        remember(true);
        playMusic();
      }
    });

    var stopListening = function () {
      doc.removeEventListener('pointerdown', firstGesture, true);
      doc.removeEventListener('keydown', firstGesture, true);
    };
    var firstGesture = function (e) {
      if (e.type === 'keydown' && e.key !== 'Enter' && e.key !== ' ') return;
      stopListening();
      // Un premier clic sur le bouton lui-même est géré par son propre gestionnaire.
      if (e.target.closest && e.target.closest('[data-musique]')) return;
      if (wanted && music.paused) playMusic();
    };
    doc.addEventListener('pointerdown', firstGesture, true);
    doc.addEventListener('keydown', firstGesture, true);

    doc.addEventListener('visibilitychange', function () {
      if (doc.hidden && !music.paused) {
        pausedByHide = true;
        music.pause();
      } else if (!doc.hidden && pausedByHide) {
        pausedByHide = false;
        if (wanted) music.play().catch(function () { setUi(false); });
      }
    });
  }

  /* ---------- Dialogues ---------- */

  function openDialog(id) {
    var dlg = doc.getElementById(id);
    if (!dlg) return;
    if (typeof dlg.showModal === 'function') dlg.showModal(); else dlg.setAttribute('open', '');
    if (id === 'version-texte') loadText();
  }
  function closeDialog(dlg) {
    if (typeof dlg.close === 'function') dlg.close(); else dlg.removeAttribute('open');
  }

  doc.querySelectorAll('[data-ouvre]').forEach(function (btn) {
    btn.addEventListener('click', function () { openDialog(btn.getAttribute('data-ouvre')); });
  });
  doc.querySelectorAll('dialog').forEach(function (dlg) {
    dlg.addEventListener('click', function (e) {
      if (e.target === dlg || e.target.closest('[data-ferme]')) closeDialog(dlg);
      if (e.target.closest('.toc a')) closeDialog(dlg);
    });
  });

  /* ---------- Version texte ---------- */

  var textArea = doc.getElementById('texte-candidature');
  var textStatus = doc.querySelector('.dialogue__statut');
  var textLoaded = false;

  // Repli quand candidature.txt n'est pas accessible (page ouverte en file://).
  function textFromPage() {
    var clone = doc.getElementById('contenu').cloneNode(true);
    clone.querySelectorAll('[data-export="skip"], [aria-hidden="true"], figcaption').forEach(function (n) { n.remove(); });
    clone.querySelectorAll('.apres-choix').forEach(function (n) { n.classList.add('is-visible'); });
    clone.querySelectorAll('del').forEach(function (n) { n.textContent = '[barré : ' + n.textContent + ']'; });
    var holder = doc.createElement('div');
    holder.style.cssText = 'position:absolute;left:-99999px;top:0;width:40rem;white-space:normal';
    holder.appendChild(clone);
    doc.body.appendChild(holder);
    var text = clone.innerText.replace(/\n{3,}/g, '\n\n').trim();
    holder.remove();
    return text;
  }

  function loadText() {
    if (textLoaded || !textArea) return;
    textLoaded = true;
    var fallback = function () { textArea.value = textFromPage(); };
    if (location.protocol === 'file:' || !window.fetch) { fallback(); return; }
    fetch('candidature.txt', { cache: 'no-cache' })
      .then(function (r) { if (!r.ok) throw new Error(r.status); return r.text(); })
      .then(function (t) { textArea.value = t; })
      .catch(fallback);
  }

  var copyBtn = doc.querySelector('[data-copier]');
  if (copyBtn) {
    copyBtn.addEventListener('click', function () {
      var done = function () { if (textStatus) textStatus.textContent = 'Copié.'; };
      var legacy = function () {
        textArea.focus();
        textArea.select();
        try { doc.execCommand('copy'); done(); } catch (e) { if (textStatus) textStatus.textContent = 'Sélectionnez le texte et copiez-le.'; }
      };
      if (navigator.clipboard && window.isSecureContext) {
        navigator.clipboard.writeText(textArea.value).then(done, legacy);
      } else {
        legacy();
      }
    });
  }
})();
