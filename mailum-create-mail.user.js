// ==UserScript==
// @name         Mailum - Auto "Create mail"
// @namespace    https://github.com/cristiantemp04-ui/test
// @version      1.0.0
// @description  Trova rapidamente il pulsante/scritta "Create mail" su mailum.com (anche con finestra ridotta) e lo clicca.
// @match        *://mailum.com/*
// @match        *://*.mailum.com/*
// @run-at       document-start
// @grant        none
// ==/UserScript==

(function () {
  'use strict';

  // ---- Configurazione ------------------------------------------------------
  const CONFIG = {
    // Testi da cercare (confronto case-insensitive, spazi normalizzati).
    texts: ['create mail', 'create email', 'crea mail', 'nuova mail', 'compose'],
    autoClick: true,         // clicca automaticamente appena trovato
    timeoutMs: 15000,        // smette di cercare dopo questo tempo
    hotkey: { alt: true, key: 'c' }, // Alt+C per cercarlo e cliccarlo a mano
    debug: false,
  };
  // -------------------------------------------------------------------------

  const log = (...a) => CONFIG.debug && console.log('[mailum-create]', ...a);
  const norm = (s) => (s || '').replace(/\s+/g, ' ').trim().toLowerCase();
  const matches = (s) => {
    const t = norm(s);
    return t && CONFIG.texts.some((x) => t === x || (t.length <= 40 && t.includes(x)));
  };

  const CLICKABLE = 'button, a, [role="button"], [role="menuitem"], input[type="button"], input[type="submit"], [onclick], [tabindex]';

  function isVisible(el) {
    if (!el.isConnected) return false;
    const r = el.getBoundingClientRect();
    if (r.width === 0 && r.height === 0) return false;
    const cs = getComputedStyle(el);
    return cs.visibility !== 'hidden' && cs.display !== 'none' && cs.opacity !== '0';
  }

  function labelOf(el) {
    return [el.innerText, el.value, el.getAttribute('aria-label'), el.getAttribute('title')]
      .filter(Boolean);
  }

  function findButton(root = document) {
    // 1) Elementi cliccabili con testo/aria-label/title corrispondente.
    for (const el of root.querySelectorAll(CLICKABLE)) {
      if (labelOf(el).some(matches) && isVisible(el)) return el;
    }
    // 2) Fallback: qualsiasi nodo di testo "Create mail" -> risale al contenitore cliccabile.
    const walker = document.createTreeWalker(root.body || root, NodeFilter.SHOW_TEXT);
    let node;
    while ((node = walker.nextNode())) {
      if (!matches(node.nodeValue)) continue;
      const el = node.parentElement;
      if (!el || !isVisible(el)) continue;
      return el.closest(CLICKABLE) || el;
    }
    return null;
  }

  function clickEl(el) {
    log('click su', el);
    el.scrollIntoView({ block: 'center', inline: 'center' });
    const opts = { bubbles: true, cancelable: true, view: window };
    // Sequenza completa per framework che ascoltano pointer/mouse events.
    el.dispatchEvent(new PointerEvent('pointerdown', opts));
    el.dispatchEvent(new MouseEvent('mousedown', opts));
    el.dispatchEvent(new PointerEvent('pointerup', opts));
    el.dispatchEvent(new MouseEvent('mouseup', opts));
    el.click();
  }

  function tryClick() {
    const el = findButton();
    if (el) { clickEl(el); return true; }
    return false;
  }

  // ---- Ricerca automatica veloce (MutationObserver, niente polling lento) --
  let done = false;
  function startAuto() {
    if (!CONFIG.autoClick || done) return;
    if (tryClick()) { done = true; return; }

    let scheduled = false;
    const obs = new MutationObserver(() => {
      if (scheduled || done) return;
      scheduled = true;
      requestAnimationFrame(() => {
        scheduled = false;
        if (!done && tryClick()) { done = true; obs.disconnect(); }
      });
    });
    obs.observe(document.documentElement, {
      childList: true, subtree: true, attributes: true,
      attributeFilter: ['class', 'style', 'hidden', 'aria-hidden'],
    });
    setTimeout(() => { obs.disconnect(); log('timeout, pulsante non trovato'); }, CONFIG.timeoutMs);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', startAuto, { once: true });
  } else {
    startAuto();
  }

  // Se la finestra viene ridotta dopo il caricamento, il pulsante può comparire ora.
  window.addEventListener('resize', () => { if (!done && CONFIG.autoClick && tryClick()) done = true; });

  // ---- Scorciatoia manuale -------------------------------------------------
  window.addEventListener('keydown', (e) => {
    const h = CONFIG.hotkey;
    if (!!h.alt === e.altKey && e.key.toLowerCase() === h.key) {
      e.preventDefault();
      if (!tryClick()) console.warn('[mailum-create] "Create mail" non trovato');
    }
  }, true);
})();
