# Roadmap — le travail identifié et pas encore fait

Ce que quelqu'un a trouvé, jugé réel, et remis à plus tard. Une ligne y entre au
moment où le constat est fait, pas au moment où on décide de le traiter : un
constat qui attend d'être planifié pour être écrit est un constat oublié.

**Ce n'est pas un backlog de fonctionnalités.** Les idées produit vivent ailleurs.
Ici : les défauts connus, les dettes assumées, et les alignements décidés.

**Ce n'est pas non plus un rapport de revue.** Les revues vivent dans
[`reviews/`](reviews/) et sont annotées sur place. Quand un constat de revue est
différé et qu'il survivra à la revue, il est repris ici en une ligne qui pointe
vers le rapport.

## Ce qui a le droit d'entrer

Le danger d'une roadmap n'est pas qu'on y oublie une ligne, c'est qu'on y en mette
trop : une liste où tout entre est une liste que plus personne ne lit, et le vrai
défaut s'y noie au milieu des préférences. D'où un critère d'admission, à passer
**avant** d'écrire la ligne.

1. **C'est vérifié, pas soupçonné.** On ouvre le code, on mesure, on nomme le
   fichier et la ligne. Un constat écrit de mémoire est un constat que le suivant
   devra re-vérifier — il aura coûté du temps au lieu d'en faire gagner.
2. **La conséquence se nomme.** Ce qui casse, pour qui, et dans quel cas concret.
   Une entrée sans conséquence est une préférence, et les préférences n'ont pas
   à survivre à leur auteur.
3. **Ce n'est pas déjà tenu ailleurs.** Si un garde, un test ou le code
   l'empêchent déjà, la ligne est du bruit — et une deuxième source de vérité.
4. **Ça ne se fait pas maintenant.** Si le correctif tient dans le périmètre de la
   tâche en cours, on le fait ; on ne l'écrit pas. La roadmap n'est pas un endroit
   où déposer ce qu'on n'a pas envie de faire.
5. **Ça survit à la session.** Un contretemps d'environnement, une manipulation à
   refaire, une question en attente de réponse : ça n'a rien à faire ici.

Une entrée dit donc trois choses, et le **pourquoi** de chacune : ce qui ne va
pas, ce que ça coûte de ne pas le faire, et ce qui a justifié le report. Le
troisième point est celui qu'on saute et c'est le plus utile : sans lui, la
session suivante rouvre l'arbitrage depuis zéro.

---

## Gardes — des trous connus

### 1. `check-ui-translated.py` ne suit pas les libellés passés à un helper

Le garde inspecte les appels à `lv_*_set_text*`. Or trois fonctions posent du
texte sur la dalle sans que l'appelant touche un setter : `lvglAddHeader()` pour
les titres d'écran, `makeRow()` pour les lignes de réglages, et
`lvglConfirm()` / `lvglAskYesNo()` pour les confirmations. Le littéral y est un
argument ; c'est le corps du helper qui appelle le setter, sur une variable.

**Conséquence :** tout le menu Réglages et tous les titres d'écran sont hors de
portée du garde — exactement là où vivait le bug « LECTEURS » qu'il a été écrit
pour attraper. Aujourd'hui le trou est vide : trois littéraux le traversent
(`"Wi-Fi (2.4G)"`, `"RFID"` ×2), tous légitimement neutres.

**Le correctif, en deux temps** — parce qu'une liste de helpers écrite à la main
est exactement ce qu'on vient de retirer de `llms.txt` :

1. le garde suit les littéraux dans les helpers connus ;
2. il **découvre** ces helpers : toute fonction dont le corps passe un de ses
   propres paramètres `const char*` à un setter de texte en est un, et doit être
   dans la liste. Un quatrième helper écrit demain fait échouer le garde en le
   nommant, au lieu de rouvrir le trou en silence.

**Reporté** le 2026-09-04 : trou réel mais vide, et le correctif mérite son propre
commit avec son test dans les deux sens. Environ une heure.

### 2. `check-ui-fonts.py` ne regarde que la table de traduction

Il collecte les chaînes avec `/* KEY */ "..."` — c'est-à-dire uniquement
`i18n.h`. Il ne voit ni les `LV_SYMBOL_*` de LVGL, ni les `TT_SYMBOL_*` maison
écrits en octets échappés (`"\xEF\x80\xA3"`), ni aucun littéral dessiné hors de
la table.

**Conséquence :** une icône absente de toutes les faces se dessine en case vide,
en silence, exactement comme un accent absent — et c'est précisément le silence
que ce garde existe pour rompre. Aujourd'hui les trois `TT_SYMBOL_*` (U+F023,
U+F185, U+F1A0) sont bien dans la plage de `font_cjk_*`, vérifié par
`check-generated.py`. Mais un quatrième ajouté hors sous-ensemble ne serait
signalé par rien.

Signalé par l'agent TigerSpool le 2026-09-04, en retour du trou n° 1 que je lui
avais décrit. **Reporté** : même passe que le n° 1, les deux gardes partagent le
besoin de décoder les échappements et de suivre les macros.

### 3. `check-ui-fonts.py` lit un seul `--symbols`

`-r` est lu avec `findall` (tous), `--symbols` avec `search` (le premier). Une
ligne `Opts` peut enchaîner plusieurs `--font`, chacun avec le sien — c'est déjà
le cas des faces CJK, qui prennent le Han dans Noto, deux icônes dans FontAwesome
et le G de Google dans fa-brands.

**Conséquence :** correct aujourd'hui (une seule section `--symbols` par face),
faux le jour où une face en portera deux. C'est le défaut exact qui a fait
signaler à tort U+F1A0 par la première version de `check-generated.py`.

**Reporté :** une ligne à changer, sans urgence, mais à ne pas changer seule —
modifier un garde qui marche demande son test.

---

## Architecture

### 4. Pas de couche de tokens visuels

Les couleurs sont onze constantes nommées ; les tailles et les espacements sont
des nombres écrits au site d'appel. Symptôme mesurable : `ROW_H` est déclaré
**trois fois** localement, avec deux valeurs (`34`, `56`, `56`), lignes 2077,
4428 et 6709 du `.ino`.

**Conséquence :** changer la densité de l'interface est un travail de recherche,
pas un changement de valeur. Rien ne relie la ligne de l'écran Langue à celle du
menu Réglages ; elles sont d'accord par coïncidence.

**Reporté :** le TigerSpool a résolu ça proprement avec `src/ui/theme.h`. Chez
nous c'est une refonte transversale d'un fichier de 16 000 lignes, donc une
opération à part entière, pas un à-côté.

**Piège à connaître avant de commencer cette refonte** — signalé par l'agent
TigerSpool le 2026-09-04, qui l'a créé chez lui en la faisant. Nos écrans passent
leurs libellés en paramètres directs : `makeRow(icon, sym, col, t(...),
String(valeur), action)`. Un temporaire `String` y survit jusqu'à la fin de
l'expression d'appel, donc le `c_str()` est valide. **Regrouper ces arguments dans
une struct casse exactement ça** :

```c
row.network = WiFi.SSID().c_str();   // le temporaire meurt ici
```

La struct porte alors un pointeur vers de la mémoire libérée. Le symptôme n'est
pas un crash : sur ESP32 on relit le plus souvent des octets intacts ou un zéro,
donc **le champ s'affiche vide** — et un champ vide sur la ligne Wi-Fi ressemble à
un problème de réseau, pas à un bug. Invisible à la compilation, invisible à la
relecture, trouvé chez eux seulement en comparant deux captures d'écran.

Vérifié le 2026-09-04 : nous ne l'avons pas aujourd'hui (deux `c_str()` dans le
`.ino`, tous deux copiés dans une `String` dans la même expression, lignes 8266 et
8283). Le jour où cette entrée sera traitée, garder les `String` dans des locales
nommées.

### 5. Les fichiers générés n'ont pas de source commitée

Les trois en-têtes RGB565 sont produits depuis des PNG qui ne sont pas dans le
dépôt, et les six faces de police depuis un TTF téléchargé dans un dossier
temporaire (la ligne `Opts` en garde la trace : un chemin sous `/var/folders`).

**Conséquence :** aucun de ces fichiers ne peut être régénéré depuis ce dépôt.
`check-generated.py` se rabat donc sur la cohérence interne — un tableau contre
son `_W`×`_H`, une table de glyphes contre sa plage déclarée — là où le TigerSpool
peut relancer son générateur et comparer.

**Reporté :** commiter les sources rendrait la vérification forte possible. La
question est la taille (le splash 480×320) et la licence des polices.

---

## Interface

### 6. « Aucun réseau trouvé » ne propose pas de relancer le scan

`TigerTagSplashESP32.ino:2945-2953` : quand le scan Wi-Fi ne rapporte rien,
l'écran affiche un `msgHolder` de 230 px de haut, centré, contenant **un seul
label rouge** — « Aucun réseau trouvé » — et rien d'autre. Pas de bouton, pas de
relance. Le seul chemin est de ressortir et de rentrer.

**Ce n'est pas une préférence, c'est une incohérence :** le motif existe déjà
dans le produit. `I18N_WIFI_RETRY` est utilisé lignes 3604 et 6437, sur l'écran
d'échec de connexion et sur celui de mise à jour. Il n'a simplement pas été
appliqué ici.

**Conséquence :** un scan qui tombe à vide parce que la radio n'était pas encore
prête — ce qui arrive au premier démarrage — laisse l'utilisateur devant une
phrase rouge sans issue, sur l'écran le plus précoce du parcours. Il conclut que
l'appareil ne voit pas son réseau.

**Reporté :** c'est un changement visuel, donc maquette d'abord, conformément à la
règle du dépôt. Et il vaut d'être traité avec la question plus large de l'état
vide, pas seul.

*Note d'admission : la première version de cette entrée disait « aucun réseau
configuré, pas de compte : une phrase dans une carte », et confondait deux choses.
`I18N_NO_ACCOUNT` n'est pas un état vide, c'est une pastille d'état sur l'écran
principal (lignes 13791 et 13813), et elle est légitime. Vérifier avant d'écrire
a rétréci le constat et l'a rendu actionnable.*

### 7. « Compte Firebase » doit devenir « Compte »

`I18N_FB_ACCOUNT` affiche le nom du fournisseur devant l'utilisateur. Firebase est
un détail d'implémentation. Le TigerSpool dit « Compte », et c'est le bon mot.

**Conséquence :** deux appareils du même écosystème qui nomment la même chose
différemment. Alignement décidé le 2026-09-04, dans ce sens-là.

**Reporté :** neuf entrées à réécrire dans `i18n.h`, à faire avec la prochaine
passe sur la table.

---

## Outillage et exploitation

### 8. Deux endpoints simples à côté de la vue live

Le TigerSpool expose `/screen.bmp` et `/api/tap?x=&y=` : deux requêtes HTTP sans
état. Notre §LIVE fait plus — flux de bandes, temps réel, clics en retour — mais
il est plus lourd pour ce qu'un agent en fait, qui est de prendre une image et de
cliquer.

**Conséquence :** un agent qui veut vérifier un écran monte un protocole maison
là où deux `curl` suffiraient.

**Reporté :** ajout à côté de la vue live, pas à sa place. Attention au budget
mémoire — voir la ligne `liveEnsureBuffers` de la table Landmines.

### 9. `idf_component.yml` et son `.orig` ne sont ni suivis ni ignorés

Produits par le build dans `TigerTagSplashESP32/`, absents de l'historique et du
`.gitignore`.

**Conséquence :** ils apparaissent dans chaque `git status` et finiront commités
par un `git add -A`.

**Reporté :** décision de Benoît — les ignorer, ou comprendre pourquoi le build
les écrit là.
