/* Bildvergroesserung fuer die Wissensartikel.
 *
 * Ersetzt das WordPress-Plugin simple-lightbox (217 KB, neun Skriptdateien,
 * jQuery-abhaengig). Greift dieselbe Auszeichnung ab, die in den Artikeln
 * steht - ein <a href="...bild.jpg"> um ein <img> -, sodass kein Beitrag
 * angefasst werden musste. Ohne JavaScript bleibt der Link ein Link und
 * oeffnet das Bild direkt.
 */
(function () {
  'use strict';

  var ENDUNGEN = /\.(jpe?g|png|gif|webp)(\?|#|$)/i;
  var dialog = null;

  function erzeugeDialog() {
    if (dialog) return dialog;
    dialog = document.createElement('dialog');
    dialog.className = 'ionas-lightbox';
    dialog.innerHTML =
      '<button type="button" class="ionas-lightbox-zu" aria-label="Schließen">&times;</button>' +
      '<img alt="">' +
      '<p class="ionas-lightbox-text"></p>';
    document.body.appendChild(dialog);

    dialog.querySelector('.ionas-lightbox-zu').addEventListener('click', function () {
      dialog.close();
    });
    // Klick auf die Flaeche neben dem Bild schliesst ebenfalls
    dialog.addEventListener('click', function (e) {
      if (e.target === dialog) dialog.close();
    });
    return dialog;
  }

  function oeffne(href, text) {
    var d = erzeugeDialog();
    var img = d.querySelector('img');
    var p = d.querySelector('.ionas-lightbox-text');
    img.src = href;
    img.alt = text || '';
    p.textContent = text || '';
    p.hidden = !text;
    if (typeof d.showModal === 'function') {
      d.showModal();
    } else {
      window.location.href = href;   // sehr alte Browser
    }
  }

  document.addEventListener('click', function (e) {
    var a = e.target.closest ? e.target.closest('a') : null;
    if (!a || !a.getAttribute('href')) return;
    if (!ENDUNGEN.test(a.getAttribute('href'))) return;
    if (!a.querySelector('img')) return;
    if (e.metaKey || e.ctrlKey || e.shiftKey || e.button !== 0) return;
    e.preventDefault();
    var img = a.querySelector('img');
    oeffne(a.href, img.getAttribute('alt') || img.getAttribute('title') || '');
  });
})();
