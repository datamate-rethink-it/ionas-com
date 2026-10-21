<?php
$_GET["p"] = $argv[1];

$page = "startseite";
if(isset($_GET['p'])){
    $page = trim(strtolower($_GET['p']));
    if (substr($page, -1) == "/"){
        $page = substr($page, 0, -1);
    }

    // sonderzeichen
    $page = urlencode($page);
    $page = str_replace(
        array('%2F', '%E3%BC', '%E3%B6', '%E3%A4', '%E3%84', '%C3%B6', '%C3%BC', '%C3%A4', '%C3%84'),
        array('/',   'ü',      'ö',      'ä',      'Ä',      'ö',      'ü',      'ä',      'Ä'),
        $page
    );

}

$canonical = "";

switch ($page){
    case '/test':
        $include = './pages/test.php';
        $title = "PC Hilfe per Telefon an 7 Tagen die Woche | ionas - Ihr Online Assistent";
        $description = "ionas - Ihr Online Assistent bietet PC Service, Computerhilfe, PC Fernwartung und vieles mehr. Professionelle Dienstleistung von Experten per Telefon.";
        break;

    case '/weihnachten':
    case '/computerhilfe-fuer-eltern':
        $include = './pages/weihnachten2015.php';
        $title = "Computerhilfe für Eltern, Bekannte und Verwandte | ionas";
        $description = "Sie leisten regelmäßig Computerhilfe bei Eltern, Bekannten und Verwandten - Ihnen wird das aber zu viel? Dann verschenken Sie Computersorgenfreiheit von ionas.";
        $canonical = "computerhilfe-fuer-eltern";
        break;

    case 'startseite':
        $include = './pages/startseite.php';
        $title = "PC Hilfe per Telefon an 7 Tagen die Woche | ionas - Ihr Online Assistent";
        $description = "ionas - Ihr Online Assistent bietet PC Service, Computerhilfe, PC Fernwartung und vieles mehr. Professionelle Dienstleistung von Experten per Telefon.";
        break;

    case '/dienstleistung':
        $include = './pages/leistungen.php';
        $title = "ionas Computerhilfe - Ihr Online Assistent";
        $description = "Brauchen Sie Hilfe mit Ihrem Computer? Die Computerhilfe von ionas hilft sofort per Fernwartung auf Ihrem Rechner.";
        break;

    case '/assistenz':
        $include = './pages/leistungen_assistenz.php';
        $title = "ionas PC Hilfe - Assistenz";
        $description = "Schnelle Hilfe, wenn es brennt. IT-Support von den IT-Profis aus Mainz. ionas - Ihr Online Assistent.";
        break;

    case '/inspektion':
        $include = './pages/leistungen_inspektion.php';
        $title = "ionas PC Service - Inspektion";
        $description = "Vorsorge ist besser als Nachsorge? Das gilt auch für Computer. Lassen Sie jetzt Ihren Computer von den Experten überprüfen.";
        break;

    case '/it-berater':
        $include = './pages/it-berater.php';
        $title = "PC Service ionas - Ihr IT-Berater";
        $description = "Unsere IT-Berater stehen Ihnen bei allen Fragen und Problemen zur Seite. Schnell, unkompliziert, fair und transparent. Nie ware es einfacher.";
        break;

    case '/datensicherung':
        $include = './pages/leistungen_datensicherung.php';
        $title = "ionas Datensicherung - günstig und zuverlässig";
        $description = "Sind Ihre Daten und Informationen sicher gespeichert? Haben Sie ein Backup? Wenn nein, rufen Sie uns jetzt an. Wir beraten Sie gerne.";
        break;

    case '/usb-stick':
    case '/rescue-stick':
        $include = './pages/leistungen_usb-stick.php';
        $title = "ionas USB-Stick - professionelles Rettungstool";
        $description = "Ein USB-Stick für Installation, Überprüfung und Fernzugriff. Das ist der ionas USB-Stick von den IT-Profis aus Mainz.";
        break;

    case '/so-funktionierts':
        $include = './pages/so-funktionierts.php';
        $title = "Computerhilfe per Fernwartung - So funktioniert's";
        $description = "Vergessen Sie lange Anfahrtszeiten. Die Computerhilfe von ionas hilft sofort dank TeamViewer Fernwartungssoftware. Nie war es einfacher.";
        break;

    case '/supportsitzung':
        $include = './pages/so-funktionierts-supportsitzung.php';
        $title = "Ablauf einer Supportsitzung – ionas – Ihr Online Assistent";
        $description = "Support per Fernwartung ist kinderleicht. Einfach TeamViewer von unserer Webseite laden und ausführen, schon kann unser Experte Ihnen helfen.";
        break;

    case '/kundenkomfort':
        $include = './pages/kundenkomfort.php';
        $title = "PC Hilfe von ionas - Kundenkomfort - ionas";
        $description = "Wir bieten Qualität und Zuverlässigkeit für einen geringen Preis. Testen Sie die Computerhilfe und den IT-Support von ionas.";
        break;

    case '/pc-fernwartung':
        $include = './pages/pc-fernwartung.php';
        $title = "TeamViewer-Fernwartungssoftware - höchste Sicherheit";
        $description = "ionas – Ihr Online Assistent setzt die Fernwartungssoftware der deutschen TeamViewer GmbH ein. Diese erfüllt höchste Sicherheitsstandards.";
        $keywords = "TeamViewer, Fernwartungssoftware, Remote Control Software, Fernwartung";
        break;

    case '/kundenkomfort':
        $include = './pages/kundenkomfort.php';
        $title = "PC-Service vom Profi - Kundenkomfort der Extraklasse";
        $description = "Service und Komfort sind zwei wichtige Säulen unserer Dienstleistung. ionas bietet IT-Support der Extraklasse.";
        break;

    case '/preise':
        $include = './pages/preise.php';
        $title = "PC Hilfe zu günstigen Preisen - ionas";
        $description = "Soforthilfe und profesioneller IT-Support zur fairen und transparenten Preisen. Rufen Sie an! Wir helfen Ihnen!";
        break;

    case '/unternehmen':
        $include = './pages/unternehmen.php';
        $title = "Das Computerhilfe Angebot aus Mainz | ionas - Ihre Online Assistent";
        $description = "Suchen Sie professionelle Computerhilfe? ionas - Ihr Online Assistent ist jederzeit per Telefon und Fernwartung für Sie da! Wir stellen uns vor.";
        break;

    case '/ueber-uns':
        $include = './pages/unternehmen_ueber-uns.php';
        $title = "ionas - Über uns - Die PC Experten";
        $description = "Genervt von unzuverlässigen Computerhelfern vor Ort? Ein Anruf und schon hilft Ihnen Ihr Online Assistent von ionas.";
        break;

    case '/team':
        $include = './pages/unternehmen_team.php';
        $title = "Support Hotline ionas - unser Team";
        $description = "Computerprobleme und keine Lösung? ionas hilft am Telefon und per Fernwartung. Jetzt anrufen und Soforthilfe bekommen.";
        break;

    case '/social-media':
        $include = './pages/unternehmen_folgen-sie-uns.php';
        $title = "ionas - Social Media - folgen Sie uns";
        $description = "Interessiert an Computerthemen? Werden Sie Fan und lesen Sie die Wissensartikel von den IT-Profis.";
        break;

    case '/partner':
        $include = './pages/unternehmen_partner.php';
        $title = "PC Service ionas - unsere Partner";
        $description = "Zusammen mit unserem Partnernetzwerk liefern wir hochwertigen IT-Support für Deutschland, Schweiz und Österreich.";
        break;

    case '/bewertungen':
        $include = './pages/bewertungen.php';
        $title = "Computerhilfe ionas - Bewertungen und zufriedene Kunden";
        $description = "Sofortige Online-Computerhilfe per Fernwartung. ionas hilft günstig und an 365 Tagen im Jahr. Nur einen Anruf entfernt.";
        $canonical = "bewertungen";
        break;

    case '/presse':
        $include = './pages/unternehmen_presse.php';
        $title = "Presse | ionas - Ihr Online Assistent";
        $description = "Dies ist der Pressebereich von ionas - Ihr Online Assistent. Hier finden Sie Artikel, Informationen und Ansprechpartner der ionas OHG.";
        $canonical = "bewertungen";
        break;

    case '/datenschutz':
        $include = './pages/datenschutz.php';
        $title = "Datenschutz";
        $description = "Professionelle Hilfe bei Fragen und Problemen rund um Computer und Internet. Unsere Experten arbeiten schnell, fair und zuverlässig.";
        $canonical = 'datenschutz';
        break;

    case '/impressum':
        $include = './pages/impressum.php';
        $title = "Impressum | ionas - Ihr Online Assistent";
        $description = "Die Computerhilfe Experten von ionas - Ihr Online Assistent unterstützen Sie bei PC Problemen aller Art - telefonisch und per Fernwartung. So erreichen Sie uns. ";
        break;

    case '/vertragsabschluss':
        $include = './pages/vertragsabschluss.php';
        $title = "Vertragsabschluss | ionas - Ihr Online Assistent";
        $description = "Jetzt zu deutschlands bester Computerhilfe wechseln. Wir lösen Ihre Probleme per Telefon und Fernwartung an 365 Tagen im Jahr.";
        break;

    /*
    case '/vertragsabschluss2':
        $include = './pages/vertragsabschluss2.php';
        $title = "Vertragsabschluss | ionas - Ihr Online Assistent";
        $description = "Jetzt zu deutschlands bester Computerhilfe wechseln. Wir lösen Ihre Probleme per Telefon und Fernwartung an 365 Tagen im Jahr.";
        break;
        */

    case '/kontoaenderung':
        $include = './pages/kontoaenderung.php';
        $title = "Kontoänderung | ionas - Ihr Online Assistent";
        $description = "Bequem und einfach die Kontoverbindung ändern. Einfach das Formular ausfüllen und das SEPA-Lastschriftmandat akzeptieren.";
        break;

    case '/portscan':
        $include = './pages/portscan.php';
        $title = "Portscan | ionas - Ihr Online Assistent";
        $description = "Prüfen, ob Ports freigegeben sind ...";
        break;

    case '/lets-encrypt':
        $include = './pages/check-lets-encrypt.php';
        $title = "Let's Encrypt Prüfung | ionas - Ihr Online Assistent";
        $description = "Prüfen, ob die gewünschte Subdomain für let's encrypt vorbereitet ist.";
        break;

    /*
    case '/kontoaenderung2':
        $include = './pages/kontoaenderung2.php';
        $title = "Kontoänderung | ionas - Ihr Online Assistent";
        $description = "Bequem und einfach die Kontoverbindung ändern. Einfach das Formular ausfüllen und das SEPA-Lastschriftmandat akzeptieren.";
        break;
        */

    case '/malware-entfernen':
    case '/malware-entfernen/spyware':
    case '/malware-entfernen/browser-toolbar':
    case '/it-support':
    case '/computerservice':
    case '/pc-reparatur':
    case '/pc-reparieren':
    case '/pc-notdienst':  
    case '/pc-aufräumen':
    case '/pc-doktor':
    case '/pc-service':
    case '/pc-support':
    case '/computer-inspektion':
    case '/notebook-reparatur':
    case '/online-assistent':
    case '/pc-langsam':
    case '/windows-hilfe':
    case '/computer-hotline':
    case '/windows-support':
    //case '/laptop-hilfe':
    //case '/pc-hotline':
        include './themen/hilfethemen-texte.php';
        $include = './themen/hilfethemen.php';
        $canonical = substr($page, 1);
        break;

    case '/pc-hilfe':
    case '/pc-hilfe/berlin':
        case '/pc-hilfe/pankow':
        case '/pc-hilfe/reinickendorf':
        case '/pc-hilfe/prenzlauer_berg':
        case '/pc-hilfe/charlottenburg':
        case '/pc-hilfe/steglitz':
        case '/pc-hilfe/tempelhof':
    case '/pc-hilfe/hamburg':
    case '/pc-hilfe/münchen':
        case '/pc-hilfe/muenchen':
    case '/pc-hilfe/köln':
        case '/pc-hilfe/koeln':
    case '/pc-hilfe/frankfurt':
    case '/pc-hilfe/stuttgart':
    case '/pc-hilfe/düsseldorf':
        case '/pc-hilfe/duesseldorf':
    case '/pc-hilfe/dortmund':
    case '/pc-hilfe/essen':
    case '/pc-hilfe/bremen':
    case '/pc-hilfe/leipzig':
    case '/pc-hilfe/dresden':
    case '/pc-hilfe/hannover':
    case '/pc-hilfe/nürnberg':
        case '/pc-hilfe/nuernberg':
    case '/pc-hilfe/duisburg':
    case '/pc-hilfe/bochum':
    case '/pc-hilfe/wuppertal':
    case '/pc-hilfe/bielefeld':
    case '/pc-hilfe/bonn':
    case '/pc-hilfe/münster':
        case '/pc-hilfe/muenster':
    case '/pc-hilfe/karlsruhe':
    case '/pc-hilfe/mannheim':
    case '/pc-hilfe/augsburg':
    case '/pc-hilfe/wiesbaden':
    case '/pc-hilfe/gelsenkirchen':
    case '/pc-hilfe/mönchengladbach':
        case '/pc-hilfe/moenchengladbach':
    case '/pc-hilfe/braunschweig':
    case '/pc-hilfe/chemnitz':
    case '/pc-hilfe/aachen':
    case '/pc-hilfe/kiel':
    case '/pc-hilfe/magdeburg':
    case '/pc-hilfe/krefeld':
    case '/pc-hilfe/freiburg':
    case '/pc-hilfe/lübeck':
        case '/pc-hilfe/luebeck':
    case '/pc-hilfe/erfurt':
    case '/pc-hilfe/halle':
    case '/pc-hilfe/rostock':
    case '/pc-hilfe/oberhausen':
    case '/pc-hilfe/saarbrücken':
        case '/pc-hilfe/saarbruecken':
    case '/pc-hilfe/kassel':
    case '/pc-hilfe/ludwigshafen':
    case '/pc-hilfe/hagen':
    case '/pc-hilfe/mülheim':
        case '/pc-hilfe/muelheim':
    case '/pc-hilfe/oldenburg':
    case '/pc-hilfe/osnabrueck':
        case '/pc-hilfe/osnabrück':
    case '/pc-hilfe/potsdam':
    case '/pc-hilfe/hamm':
    case '/pc-hilfe/leverkusen':
    case '/pc-hilfe/mainz':


        //$url = explode("/", str_replace("/index.php?p=", "", $_SERVER['REQUEST_URI']));
        $url = explode("/", $page);
        $stadtname = ucfirst($url[2]);

        //$stadtname = ucfirst($url[2]);
        $search = array('Koeln', 'Nuernberg', 'Muenchen', 'Moenchengladbach', 'Duesseldorf', 'Muenster', 'Luebeck', 'Saarbruecken', 'Muelheim', 'Prenzlauer_berg', 'Osnabrueck');
        $replace = array('Köln', 'Nürnberg', 'München', 'Mönchengladbach', 'Düsseldorf', 'Münster', 'Lübeck', 'Saarbrücken', 'Mülheim', 'Prenzlauer Berg', 'Osnabrück');
        $stadtname = str_replace($search, $replace, $stadtname);

        $search = array('Prenzlauer Berg');
        $replace = array('Prenzlauer_Berg'); 
        $stadtname_canonical = str_replace($search, $replace, $stadtname);
        //echo $url[2];
        //echo $stadtname;

        include "./staedte/pc-hilfe-texte.php";
        $include = './staedte/pc-hilfe.php';
        $canonical = "pc-hilfe/". strtolower($stadtname_canonical);
        break;

    /*
    case '/test':
        $include = './pages/startseite2.php';
        $title = "ionas - Ihr Online Assistent";
        $description = "ionas bietet PC Service, Computerhilfe, PC Fernwartung und vieles mehr. Professionelle Dienstleistung vom Experten.";
        break;
    */

    default:

        
        //$output = str_replace("%2F", "/", $output);
        //$output = str_replace("%E3%BC", "ü", $output);
        //"", "ö"
        //echo $page;

        header("HTTP/1.0 404 Not Found");
        $title = "ionas - PC Service, Computerhilfe und PC Fernwartung vom Profi - Error 404";
        $description = "ionas bietet PC Service, Computerhilfe, PC Fernwartung und vieles mehr. Professionelle Dienstleistung vom Experten.";
        $include = './pages/error.php';
        break;
}


$out = array(
    'route'       => $page,
    'include'     => isset($include) ? $include : null,
    'title'       => isset($title) ? $title : null,
    'description' => isset($description) ? $description : null,
    'keywords'    => isset($keywords) ? $keywords : null,
    'canonical'   => isset($canonical) ? $canonical : null,
    'stadtname'   => isset($stadtname) ? $stadtname : null,
    'lat'         => isset($lat) ? $lat : null,
    'lon'         => isset($lon) ? $lon : null,
    'text1'       => isset($text1) ? $text1 : null,
    'text2'       => isset($text2) ? $text2 : null,
    'text3'       => isset($text3) ? $text3 : null,
);
echo json_encode($out, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES | JSON_PRETTY_PRINT);
