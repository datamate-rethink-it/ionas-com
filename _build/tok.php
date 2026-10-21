<?php
// Zerlegt eine PHP-Datei in abwechselnd INLINE_HTML und PHP-Codeabschnitte.
$f = $argv[1];
$toks = token_get_all(file_get_contents($f));
$parts = array(); $cur = null;
foreach ($toks as $t) {
    if (is_array($t)) { $name = token_name($t[0]); $txt = $t[1]; $line = $t[2]; }
    else { $name = 'CHAR'; $txt = $t; $line = -1; }
    $kind = ($name === 'T_INLINE_HTML') ? 'html' : 'php';
    if ($cur === null || $cur['kind'] !== $kind) {
        if ($cur !== null) $parts[] = $cur;
        $cur = array('kind' => $kind, 'text' => '', 'line' => $line);
    }
    $cur['text'] .= $txt;
}
if ($cur !== null) $parts[] = $cur;
echo json_encode($parts, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
