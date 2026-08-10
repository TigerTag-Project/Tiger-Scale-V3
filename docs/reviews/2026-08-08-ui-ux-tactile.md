# Revue UI/UX tactile — panel 3.5" (v3.1.3, banc via live view)

Date : 2026-08-08 · Périmètre : interface embarquée LVGL (écran principal, tous les
sous-écrans de Réglages, workflow de pesée avec opérateur au banc) · Méthode :
live view `http://<ip>/live` (taps uniquement), croisement code en lecture seule.
Captures : dossier de session hors dépôt, référencées ici par nom de fichier.
Convention d'annotation : après action, marquer chaque constat **fixed / deferred / rejected**.

## Résumé exécutif

L'interface est cohérente et lisible (bandeau-retour systématique, cartes, rail
de défilement, valeurs affichées directement dans la liste Réglages) et le
workflow nominal de pesée fonctionne vite (~6 s détection, ~10 s données cloud,
re-pose instantanée grâce au cache). Les deux vrais manques sont des manques de
*feedback* : un objet sans tag ne provoque strictement aucun message, et l'envoi
cloud réussi (ou abandonné) n'est jamais confirmé à l'écran. Le reste est de la
finition à fort rendement : scroll de la liste Réglages perdu à chaque retour,
régénération du code LAN sans confirmation, libellés non traduits ou tronqués.

## Statut (2026-08-08, après action)

Les 10 quick wins sont traités : 9 **fixed**, 1 **rejected** (n° 3, voir sa ligne).
Tout le reste — supplément Latin-1 Montserrat (cause racine des accents), refonte de
l'écran Compte (maquette d'abord), et les accroches par écran non reprises dans les
quick wins — est **deferred** : réel, non contesté, pour une passe suivante.

## Quick wins

Classés par impact décroissant ; chaque item ≈ une heure ou moins sauf mention.

| # | Constat (capture) | Recommandation | Effort |
|---|---|---|---|
| 1 | Objet sans tag : poids affiché mais badge bloqué sur « Pret », **aucun message même après 15 s** (`objet-sans-tag-288g-toujours-rien`). Un utilisateur avec une bobine non taggée ne sait ni ce qui se passe, ni quoi faire. §21 `handleWeighWorkflow` | Après ~5 s de poids stable (> `MIN_WEIGHT_TO_SEND_G`) sans UID : badge orange « Aucun TigerTag detecte » (+ éventuel hint « Presentez la puce vers un lecteur »). Retour à « Pret » au retrait. **fixed** (badge orange `OLED_STATE_NO_TAG`, tenu tant que le poids est là) | S |
| 2 | Confirmation d'envoi invisible : les états `WEIGHING`/`SENDING`/`SYNCED` existent (.ino:12760–12767) mais le badge observé passe de « Pret » (pendant toute la montée du poids, `pesee-montee-827g-badge-pret`) directement à « Retirer materiau ». Pesée interrompue = abandon **silencieux** (confirmé opérateur : rien à l'écran, poids non envoyé). | Tenir « Synchronise! » ≥ 2 s avant « Retirer materiau » ; en cas d'abandon (retrait avant stabilisation), badge « Pesee annulee — non envoyee » 2 s ; passer le badge en « Pesee... » dès que le poids monte. **fixed** (« Pesee... » dès l'ouverture de session ; SENDING/SYNCED/ERROR prioritaires sur « Retirer materiau » ; « Pesee annulee » 2 s si UID lu) | S |
| 3 | Le « 0.0 » au-dessus de TARE est un libellé statique jamais mis à jour (.ino:12690) — il ressemble à une donnée vivante mais ment dès qu'une tare est posée. | Afficher l'offset de tare réel, ou supprimer le chiffre et ne garder que « TARE ». **rejected** — le « 0.0 » statique est l'iconographie du bouton zéro d'une balance de cuisine, voulu tel quel | S |
| 4 | La liste Réglages repart en haut à chaque retour d'un sous-écran (`runSettingsMenu` reconstruit tout, .ino:5540+). Preuve involontaire : un tap sur la position mémorisée de LAN a rouvert Calibrage (`scroll-reset-mistap-calibrage`). Atteindre Veille = 4 taps ▼ à chaque fois. | Mémoriser l'offset de scroll (static) et le restaurer après reconstruction. **fixed** (offset conservé le temps du menu, remis à zéro à la sortie) | S |
| 5 | LAN : le bouton de régénération du code (38×38 px, .ino:4642) jouxte le code et **agit sans confirmation** (.ino:4685–4690) — un tap accidentel coupe tous les viewers en cours. | Confirmation `lvglAskYesNo` (contexte boucle bloquante, pas un callback → autorisé) + cible portée à ≥ 44 px. | S |
| 6 | WiFi : le réseau actuellement connecté n'est **ni coché ni épinglé** dans la liste (`wifi-liste-initiale`), et l'ordre change à chaque scan (`wifi-liste-apres-rescan`). Le picker Langue a déjà le pattern ✓ (contour bleu + coche, `langue-francais-coche`). | Réutiliser ce pattern : SSID connecté épinglé en tête avec coche verte. **fixed** (épinglé en tête, bordure accent + coche verte) | S/M |
| 7 | « Son: » codé en dur (.ino:3717) : l'écran Volume reste en français quand l'appareil est en anglais (`volume-son-non-traduit-mode-EN`). | Nouvelle clé i18n (8 langues) + `bash scripts/check-i18n.sh`. | S |
| 8 | Écran RFID : la ligne s'appelle « RFID » (.ino:5794, chevron sans valeur, ligne déséquilibrée) mais l'écran s'intitule « MATERIEL » (I18N_HARDWARE, .ino:4130) ; « PUISSANCE RFID : 3 » sans échelle (3 sur combien ?) ; TEST échoue en « PN532-x no ack » alors que le prérequis « plateau vide » n'est écrit qu'en commentaire source (.ino:10561). | Même libellé ligne/titre ; afficher « 3/5 » ; avant le test, si poids > 0 : « Retirez tout objet du plateau » au lieu de lancer un test qui échouera en jargon. **fixed** (titre « RFID » des deux côtés — le libellé universel plutôt que MATERIEL ; « 3/4 » avec son échelle ; « PUISSANCE RFID » passe aussi par i18n ; le TEST a finalement été **supprimé entièrement** — il n'a jamais passé au banc, et un diagnostic qui ne sait qu'échouer apprend surtout au client que son matériel serait cassé) | S |
| 9 | Noms marque/matière tronqués en dur à 10 caractères sans ellipse (.ino:12827–12828) : « PLA High Speed » → « PLA High S » (`pesee-donnees-cloud-completes`). | `LV_LABEL_LONG_DOT` (ou défilement circulaire) au lieu de `substring(0,10)`. **fixed** (LONG_DOT \+ max_width, chemin LVGL ; la troncature du chemin raw-gfx hérité reste) | S |
| 10 | Apostrophes incohérentes : « Code d'acces » (avec) vs « L ecran reste allume », « minutes d inactivite » (i18n.h:486 et voisines, `veille`) — la police possède l'apostrophe. | Uniformiser toutes les chaînes FR avec apostrophe. **fixed** (les deux chaînes fautives) | S |

## Constats par écran

### Écran principal (`main-0g`, `pesee-donnees-cloud-completes`)
**Marche bien** : hiérarchie claire (poids énorme à gauche, méta à droite), badge
d'état coloré, TARE 2/3 + Parametres 1/3 avec de larges cibles (~285×92 et
143×92 px), icônes WiFi/compte vertes en bandeau.
**Accroche** : les icônes maison/flèche avec « -- » sont cryptiques avant la
première pesée (aucune légende ; c'est rack + emplacement, on ne le découvre
qu'une bobine posée). Le « 0.0 » du bouton TARE (quick win 3). « Retirer
materiau » comme état terminal est ambigu : il se lit comme une erreur alors
qu'il signifie « pesée terminée » — préférer « Synchronise — retirez la
bobine » (voir quick win 2).

### Réglages (`settings-list-haut`, `settings-list-bas`)
**Marche bien** : chaque ligne montre sa valeur courante (SSID, compte, 60 %,
406.00, Francais, v3.1.3, Oui/Non) — la liste répond à la plupart des questions
sans rien ouvrir. Icônes colorées par état (vert connecté / rouge déconnecté).
**Accroche** : scroll perdu à chaque retour (quick win 4) ; ligne RFID seule
sans valeur, chevron flottant (quick win 8) ; « Calibrer : 406.00 » expose un
facteur interne sans unité — un utilisateur attendrait plutôt la date du dernier
calibrage ou rien ; rail ▲/▼ ~39 px de large (sous la cible 44 px) et sans état
désactivé en butée (un tap en fin de liste ne produit aucun feedback).

### WiFi (`wifi-liste-initiale`, `wifi-recherche-spinner`, `wifi-ip-mac`)
**Marche bien** : spinner « Recherche... » pendant le re-scan (bon état de
chargement), verrou + barres de signal par réseau, IP/MAC en fin de liste,
re-scan accessible dans le bandeau.
**Accroche** : réseau courant non signalé + ordre instable (quick win 6) ;
annuler depuis le clavier ramène à la liste **Réglages**, pas au picker WiFi —
pour corriger une erreur de sélection il faut re-rentrer et re-scanner.

### Clavier (`clavier-minuscules-vide` → `clavier-symboles`)
**Marche bien** : 3 modes complets (min/MAJ/&123), touche de mode active en
surbrillance bleue, œil afficher/masquer fonctionnel (`clavier-masque`),
« Valider » explicite dans le bandeau, masquage LVGL avec fenêtre de 900 ms sur
le dernier caractère (.ino:2727) — comportement standard.
**Accroche** : deux affordances de validation redondantes (« Valider » bandeau +
✓ bleu clavier) ; en mode &123, les symboles `<` `>` cohabitent avec les
chevrons de déplacement du curseur sur la même rangée visuelle — confusion
possible ; l'annulation (tap bandeau) n'est indiquée nulle part par un libellé.

### Compte (`compte-deconnexion`)
Écran presque vide : icône cloud, nom du compte, bouton rouge « Deconnexion ».
~80 % de l'espace inutilisé alors que l'utilisateur voudrait : e-mail du compte,
état/heure de la dernière synchro, nombre de bobines. Le seul élément actionnable
est destructif. Effort M — à traiter avec la maquette d'abord (règle du dépôt).

### Calibrage (`calibrage-etape1`)
**Marche bien** : « Calibrage (1/4) » dans le bandeau (progression claire),
instructions numérotées, facteur actuel affiché, gros bouton SUIVANT.
**Non testé au-delà de l'étape 1** (consigne). Pas de bouton Annuler explicite —
le retour bandeau fonctionne mais rien ne l'indique pendant un assistant où
l'utilisateur craint de « casser » le réglage en cours.

### RFID / MATERIEL (`rfid-materiel`)
**Marche bien** : badges LECTEURS 1/2 bleus (détection à l'init), Scanner ⇄
Arret avec changement de couleur rouge — bon feedback d'activité.
**Accroche** : quick win 8 (titre, échelle, prérequis TEST). Pendant mon test,
l'écran affichait **simultanément** LECTEURS 1 et 2 en bleu (« détectés ») et
« PN532-1/2 no ack » en rouge — deux vérités contradictoires sans explication ;
l'utilisateur ne peut pas savoir si son matériel est en panne (probable cause :
plateau non vide, cf. .ino:10561 — jamais dit à l'écran). « Scanner » (mixte) vs
« TEST » (capitales) : casse incohérente. Le scan n'a pas de timeout visible.

### Mise à jour (`maj-a-jour`)
Sobre et juste (« v3.1.3 / A jour » en vert), mais : pas de bouton « Vérifier
maintenant », pas d'horodatage de dernière vérification, écran aux trois quarts
vide. Install non testé (consigne).

### LAN (`lan-code-acces`)
**Marche bien** : IP, code, toggle Vue live vert — tout tient sur un écran.
**Accroche** : quick win 5 (regen sans confirmation) ; l'écran n'explique pas
*comment utiliser* le code — afficher l'URL complète `http://<ip>/live` rendrait
la fonction auto-suffisante ; la valeur « Oui » de la ligne LAN dans Réglages
désigne en fait « Vue live activée » — libellé à préciser.

### Veille (`veille`)
**Marche bien** : toggle + chips de délai + phrase d'état (« L ecran reste
allume »).
**Accroche** : chips 1/2/5/10/15/30 sans unité tant que la veille est coupée
(l'unité « minutes » n'apparaît que via la phrase d'état une fois activée) ;
état désactivé des chips peu différencié du normal ; apostrophes (quick win 10).

### Workflow de pesée (opérateur au banc)
Chronologie mesurée (bobine ~788 g, 2 puces TigerTag) :
pose → **~4–6 s** badge « Retirer materiau » + logo bobine + « R3D PLA High S »
(`pesee-tag-detecte-787g`) → **~10 s** CONTENEUR 278 g / FILAMENT 510 g /
Rack 4 / D7 (`pesee-donnees-cloud-completes`). Retrait → retour « Pret »/0 g
immédiat et propre (`pesee-retrait-retour-pret`). Re-pose : données complètes
dès la première capture (cache métadonnées efficace,
`pesee-repose-cache-instantane`). Retrait prématuré (~2 s après bip) : abandon
propre sans état bloqué, mais silencieux (quick win 2).
**Trous de feedback** : pendant les 4–6 premières secondes le badge reste
« Pret » (l'utilisateur ne sait pas si la lecture est en cours) ; entre
détection et données cloud, CONTENEUR/FILAMENT restent « -- » sans indicateur
d'activité ; le bip n'est pas un signal fiable (0, 1 ou 2 bips selon le lecteur
qui accroche, twin-UID récupéré côté cloud — confirmé opérateur) donc l'écran
est le seul canal de confirmation, ce qui renforce le quick win 2. Noté aussi :
la live view a affiché « reconnecting » pendant la requête cloud (cœur occupé) —
sans impact panel, mais symptôme de charge à ce moment-là.

## Incohérences code/UI relevées en passant

- `TigerTagSplashESP32.ino:3717` — « Son: » littéral, seul libellé non-i18n de
  l'écran Volume (visible en mode EN).
- `TigerTagSplashESP32.ino:12690` — valeur « 0.0 » du bouton TARE créée une fois,
  jamais rafraîchie (pointeur local, aucun update ailleurs).
- `TigerTagSplashESP32.ino:5794` vs `:4130` — ligne « RFID » (littéral) ouvre un
  écran titré `t(I18N_HARDWARE)` = « MATERIEL ».
- `TigerTagSplashESP32.ino:12827–12828` — `substring(0,10)` sur marque et
  matière : troncature sans ellipse (« PLA High S »).
- `TigerTagSplashESP32.ino:4642, 4685–4690` — régénération du code LAN : bouton
  38×38, action immédiate sans confirmation, dans une boucle bloquante où
  `lvglAskYesNo` serait pourtant utilisable.
- `TigerTagSplashESP32.ino:12760–12767` — états WEIGHING/SENDING/SYNCED définis
  mais fenêtre d'affichage trop courte pour être vue (badge observé : Pret →
  Retirer materiau).
- `TigerTagSplashESP32.ino:10561` — le prérequis « plateau vide » du self-test
  RF n'existe qu'en commentaire ; à l'écran, badges « détectés » et « no ack »
  coexistent sans explication.
- `i18n.h:486` (et chaîne SLEEP_MINUTES voisine) — apostrophes remplacées par
  des espaces, alors que `LAN_CODE` (« Code d'acces ») prouve que la police les
  rend.
- Cause racine des accents absents partout : polices LVGL built-in Montserrat
  (ASCII seul, `.ino:629–631`). Le pipeline de sous-ensembles existe déjà pour
  le CJK (`scripts/make-cjk-font.sh`) — le même mécanisme peut produire un
  Montserrat Latin-1 et rendre « Paramètres », « Déconnexion », « À jour »,
  « Français », « Español », « Português » corrects dans 6 des 8 langues.
  Effort M (flash + vérif `check-i18n`), compatible LVGL v8.

## Ce qui n'a pas pu être testé, et pourquoi

- **Glissés** : le protocole live view ne transmet que des taps — ressenti du
  scroll au doigt, drag éventuel de la jauge Volume, inertie des listes : non
  évalués. Les doubles taps rapides (< ~600 ms) sont perdus via la live view
  (injection tenue 2 lectures/30 ms, `.ino:2277–2289`) ; les frappes rapides au
  clavier sont donc à re-vérifier au doigt avant de conclure à un défaut.
- **Audio** : bips inaudibles à distance ; comportement décrit par l'opérateur
  (0–2 bips non déterministes selon les lecteurs).
- **Veille réelle** : non activée (réglage persistant, appareil de banc).
- **Interdits respectés** : pas de validation WiFi, pas d'Install OTA, pas de
  Logout, pas de régénération du code LAN, calibrage arrêté à l'étape 1.
- **Gauche/droite RFID** : non discriminable — la bobine porte 2 puces et le
  premier lecteur qui accroche gagne.
- **Transitoire du retrait prématuré** : ma session live view s'est déconnectée
  à cet instant ; état final vérifié (retour « Pret » propre), transition décrite
  par l'opérateur (effacement dès que le poids approche 0, aucun message).
- **Artefacts visuels notés mais imputables à la live view** (bandes mélangées
  pendant les animations de scroll, ex. `settings-scroll-artefact-bandes`) : le
  panel physique n'est probablement pas concerné — à confirmer d'un coup d'œil
  au banc.
- **Multi-viewers / 503** : non provoqué volontairement.
