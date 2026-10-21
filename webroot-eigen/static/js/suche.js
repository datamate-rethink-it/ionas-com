/* Volltextsuche der Wissensartikel ueber Pagefind.
 *
 * Der Index entsteht beim Deploy (npx pagefind --site public) und liegt
 * unter /pagefind/. Ohne diesen Schritt bleibt das Feld sichtbar, meldet
 * aber keine Treffer - deshalb der Hinweis im Fehlerfall.
 */
(function () {
  'use strict';
  var ziel = document.getElementById('suche');
  if (!ziel) return;

  var q = new URLSearchParams(window.location.search).get('q') || '';

  import('/pagefind/pagefind-ui.js').then(function () {
    var ui = new window.PagefindUI({
      element: '#suche',
      showImages: false,
      showSubResults: true,
      translations: {
        placeholder: 'Wissensartikel durchsuchen',
        clear_search: 'Zurücksetzen',
        load_more: 'Weitere Treffer anzeigen',
        search_label: 'Diese Seite durchsuchen',
        filters_label: 'Filter',
        zero_results: 'Keine Treffer für [SEARCH_TERM]',
        many_results: '[COUNT] Treffer für [SEARCH_TERM]',
        one_result: 'Ein Treffer für [SEARCH_TERM]',
        searching: 'Suche nach [SEARCH_TERM] …'
      }
    });
    if (q) ui.triggerSearch(q);
  }).catch(function () {
    ziel.innerHTML = '<p>Die Suche steht gerade nicht zur Verfügung. ' +
      'Die <a href="/wissen/">Artikelübersicht</a> listet alle Beiträge.</p>';
  });
})();
