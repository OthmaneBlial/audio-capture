# ROADMAP — Voice Transcriber

> Audit du 8 septembre 2026. Plan d’exécution proposé, pas compte rendu de fonctionnalités livrées.
> L’audit initial n’a modifié que ce fichier ; les corrections incrémentales sont signalées dans les tâches et leurs commits.

## 1. Décision produit

**Faire de Voice Transcriber un petit atelier de dictée Linux fiable : parler, relire, corriger, puis copier ou exporter volontairement un brouillon.** Le public prioritaire est celui des utilisateurs Linux qui rédigent des prompts, tickets, courriels et notes et acceptent explicitement un fournisseur cloud. Le bénéfice doit se constater en quelques minutes sur un ordinateur ordinaire.

La direction « review-first » du README est cohérente avec les fonctions présentes. Elle reste une hypothèse d’adoption à vérifier : un éditeur de transcription et un habillage GTK ne constituent pas, à eux seuls, un avantage durable. La différence défendable sera la qualité du parcours complet, la maîtrise des erreurs et une frontière de données réellement appliquée.

Le dépôt possède déjà beaucoup de documentation et d’automatisation. Son principal manque est **l’écart entre ce qui est décrit, ce qui est testé isolément, ce que contient le téléchargement public et ce qui a été démontré sur un bureau Linux réel**. Ajouter des fonctionnalités avant de réduire cet écart augmenterait la dette de crédibilité.

Le nombre de stars ne constitue ni un test d’acceptation ni une promesse. Une installation simple, une première utilisation réussie, des preuves consultables et une maintenance visible rendent le projet plus recommandable ; leur effet sur les stars reste incertain.

## 2. Périmètre et méthode de l’audit

### Références examinées

- Branche locale `main`, HEAD d’audit `84323878f428ad5f4550bc24801f7f2f55e8fa9f` ; même SHA observé pour `main` via l’API GitHub. Arbre de travail propre avant l’audit.
- Code Python de capture, VAD, providers, contrôleur, configuration, historique, exports et interface ; tests ; scripts ; manifestes Flatpak ; workflows ; documentation ; site et assets.
- API GitHub en lecture seule : métadonnées, issues, PR, workflows, exécutions, release et reporting privé de vulnérabilités.
- Téléchargement du petit bundle public dans un dossier temporaire extérieur au dépôt ; comparaison SHA-256 et vérification d’attestation avec `gh attestation verify`.
- Tests et outils Python dans un environnement temporaire extérieur au dépôt, sans installation des dépendances natives de l’application. Reproductions déterministes avec faux transport et faux audio, sans appel de transcription externe.
- Inspection des PNG existants et du site public dans Chrome : desktop et largeur CSS effectivement mesurée à 375 px. Il s’agit du site, pas d’une exécution GTK.
- Comparaison limitée aux sources officielles des concurrents et à la documentation fournisseur. Les faits externes ci-dessous sont datés ; ils ne prouvent aucune capacité de ce dépôt.

### Résultats vérifiés aujourd’hui

| Contrôle | Résultat | Limite |
| --- | --- | --- |
| Suite standard, Python 3.14.6 | **69 tests passent**, aucun échec | Doubles de PyAudio, VAD, HTTP et processus ; ne valide pas le micro ni le fournisseur réel |
| Ruff `check --no-cache .` | Passe | Analyse statique, pas preuve fonctionnelle |
| `scripts/check_release.py v1.0.0` | Passe | Vérifie les chaînes de version et rubriques, pas l’identité du code avec le binaire publié |
| Bandit, périmètre et seuil `-ll` du workflow | Aucun résultat bloquant | Ne signifie pas absence de défaut de sécurité |
| `pip-audit --require-hashes --disable-pip -r packaging/requirements-audit.txt` | Aucune vulnérabilité connue signalée | Périmètre Python épinglé ; pas audit complet du runtime GNOME ni du système |
| Couverture avec la commande CI actuelle | **73 %**, lignes et branches combinées | Les modules non importés, notamment `main.py` et l’UI, disparaissent du dénominateur |
| Même suite avec `coverage run --branch --source=.` | **41 %**, mêmes exclusions `tests/*,scripts/*` | `main.py` et `ui/main_window.py` à 0 % dans cette suite ; le smoke GTK séparé n’est pas inclus |
| Release publique `v1.0.0` | Existe, publiée le 26 août 2026 | Correspond au commit `c2244664fda6cc1603fada2ee60632e00c403d39`, pas au HEAD audité |
| Bundle x86_64 téléchargé | 840 712 octets ; checksum correspondant ; commande de vérification d’attestation réussie | Pas réinstallé ici sur Linux ; cette taille exclut le runtime GNOME à télécharger |
| Rapport JSON de la release | **59 tests**, `manual_hardware.passed: false` | Les 69 tests actuels ne sont pas la preuve associée à ce bundle |
| Site public | Accueil, docs, privacy, CSS, JS et trois assets contrôlés : HTTP 200, contenu identique aux fichiers locaux | Pas audit exhaustif de tous les liens externes |
| Site à 375 px CSS | `scrollWidth === innerWidth` sur accueil et docs ; menu ouvert puis refermé par navigation ; aucun avertissement/erreur console collecté | Pas audit complet WCAG/lecteur d’écran ; rendu GTK non testé |

Checksum du bundle vérifié : `19f941a5767f7380eb8709bde3de3cbee78647ee263f343a7dca36b7c0baa43c`.

### État GitHub observé

- Dépôt public, licence MIT détectée, description, homepage et topics renseignés : ces éléments ne sont pas à créer de zéro.
- 0 star, 1 fork, 7 issues ouvertes et 2 PR ouvertes à l’instant de lecture. Ces compteurs ne mesurent pas les utilisateurs actifs.
- Une contribution externe a réellement été intégrée : [PR #11, fixture provider](https://github.com/OthmaneBlial/audio-capture/pull/11), fusionnée le 27 août. Les deux PR ouvertes sont des mises à jour Dependabot (#12 et #13), pas des fonctionnalités utilisateur.
- Workflow général `CI` : **`disabled_manually`**. Cette pause est aussi documentée dans `docs/SUPPORT.md` ; elle doit être préservée tant que la décision de maintenance n’est pas changée explicitement.
- Workflows Flatpak, Release, benchmark et CodeQL actifs. CodeQL a réussi sur le HEAD audité ; dernier succès Flatpak observé sur `8e30dfe`, un ancêtre du HEAD. Une réussite CodeQL ne remplace pas la CI fonctionnelle.
- Reporting privé de vulnérabilités GitHub : **désactivé** (`enabled: false`) lors de l’audit, alors que `SECURITY.md` propose cette voie « when available » et un repli vers l’adresse du profil, non vérifiée ici.
- Six assets de release existent : bundle, checksum, SBOM, rapport de tests et deux bundles d’attestation. Leur existence est vérifiée ; le rapport matériel reste négatif.

Sources : [dépôt](https://github.com/OthmaneBlial/audio-capture), [release v1.0.0](https://github.com/OthmaneBlial/audio-capture/releases/tag/v1.0.0), [rapport de release](https://github.com/OthmaneBlial/audio-capture/releases/download/v1.0.0/voice-transcriber-1.0.0-test-report.json), [Actions](https://github.com/OthmaneBlial/audio-capture/actions), [site](https://othmaneblial.github.io/audio-capture/).

### Ce qui reste non vérifié

Aucun lancement GTK natif, microphone physique, traitement Groq réel, traduction réelle, permission desktop, export par portail ou cycle Flatpak sur machine propre n’a été exécuté pendant cet audit macOS. Le benchmark local historique n’a pas été rejoué. Aucune session avec un utilisateur n’a été conduite. L’absence de preuve dans le dépôt ne prouve pas que personne n’a jamais utilisé le logiciel, mais interdit d’en déduire une compatibilité acquise.

## 3. Inventaire critique

### Produit et fonctions

**Présent dans le code :** sélection du micro, capture PCM 16 kHz mono, VAD WebRTC, jauge RMS, file de capture bornée, deux workers Groq et quatre requêtes admises, texte éditable, undo/redo, états de segments, copie, exports texte/Markdown/note horodatée, historique local opt-in, langue, option de traduction, préférences visuelles et commandes de diagnostic. Une note horodatée n’est pas un export SRT/VTT synchronisé.

**Présent mais limité :** appui maintenu à la souris dans la fenêtre, raccourcis lorsque l’application a le focus, ancien tray X11 hors Flatpak, adaptateur `whisper.cpp` expérimental nécessitant exécutable et modèle fournis par l’utilisateur. Le mode local est désactivé dans Flatpak et n’est pas un moteur hors ligne distribué.

**Manquant pour l’usage quotidien crédible :** une barrière de consentement centrale, un vrai test micro sans cloud, l’ordre garanti des segments, l’isolation entre sessions, des états finaux fiables, un arrêt/abandon compréhensible, une compatibilité matérielle prouvée et une voie de mise à jour accessible. Les raccourcis globaux et l’inférence locale distribuée sont des pistes distinctes, pas des capacités existantes.

### Défauts et risques identifiés

Niveaux de preuve : **reproduit** = exécution déterministe sans périphérique ; **statique** = chemin de code identifié ; **externe** = contradiction avec une source officielle ; **à valider** = impact réel dépendant du bureau ou du package.

| ID | Priorité | Constat, preuve et impact | Localisation |
| --- | --- | --- | --- |
| F01 | P0 | **Reproduit au contrôleur :** `onboarding_complete=False` avec une clé factice plausible autorise `_start_listening()`. « Explore first » sort du dialogue ; Settings peut enregistrer une clé sans `validate_cloud_setup`. Le consentement est une validation d’écran, pas une condition d’envoi centrale. Aucun audio réel envoyé pendant la reproduction. | `main.py`, `ui/main_window.py`, `config.py`, `onboarding.py` |
| F02 | P0 | **Corrigé localement après l’audit :** `whisper-large-v3-turbo` est conservé pour la transcription et `whisper-large-v3` est sélectionné pour `/translations`, conformément à la matrice Groq. Les tests inspectent maintenant le modèle et la tâche ; l’essai réel de traduction reste ouvert. | `transcription/groq_service.py`, `groq_transport.py`, `tests/test_transcription.py` |
| F03 | P0 | **Reproduit :** deux requêtes A puis B dont A est retardée livrent `SECOND, FIRST`. Le callback ne transporte pas l’identité du segment et l’UI ajoute chaque texte à l’arrivée. Un brouillon peut changer de sens. | `groq_service.py`, `provider.py`, `main.py`, `ui/main_window.py` |
| F04 | P0 | **Statique :** aucun identifiant de génération ne protège Clear, changement de provider ou redémarrage contre un résultat tardif. Stop vide la file audio avant traitement complet ; la fermeture détruit l’UI avant la fin des résultats. Pertes, mélange ou retour de texte à reproduire en intégration. | `main.py`, `audio/capture.py`, `ui/main_window.py` |
| F05 | P0 | **Statique, primitives reproduites :** Clear dit « permanently cleared » et « cannot be recovered », mais appelle `_replace_transcript(..., remember=True)` ; Undo récupère l’ancien texte. Le message de confidentialité est faux. | `ui/main_window.py`, `transcript.py` |
| F06 | P0 | **Statique + conventions officielles :** `ConfigManager` ignore `XDG_CONFIG_HOME`, contrairement à l’historique qui utilise `XDG_DATA_HOME`. Risque de mauvaise persistance/isolation dans Flatpak ; l’échec exact du bundle est à tester. | `config.py`, `history.py`, `packaging/smoke_test_flatpak.sh` |
| F07 | P1 | **Reproduit :** un échec de sauvegarde laisse une préférence changée en mémoire sans fichier enregistré. La création du dossier peut aussi lever un `OSError` hors de la conversion en `ConfigError`. L’UI ne maîtrise pas toutes ces erreurs. | `config.py`, `ui/main_window.py` |
| F08 | P1 | **Reproduit :** 10 000 états ajoutés au tracker, 4 affichés, 10 000 conservés. La visibilité est bornée, le stockage ne l’est pas. Undo limite le nombre de snapshots mais pas leur poids ; l’historique limite les jours mais pas le volume. | `transcript.py`, `history.py` |
| F09 | P1 | **Reproduit avec faux classifieur :** 300 ms de parole suivies de silence ne produisent aucun segment. Le seuil d’amorçage exige 19 trames vocales sur 20, soit environ 570 ms, malgré `min_speech_ms=300`. Les mots courts sont fragiles ; les segments incluent du pré/post-silence, donc « silence jamais envoyé » est trop absolu. | `audio/vad.py`, `main.py`, README et site |
| F10 | P1 | **Statique :** la jauge ne reçoit du son que via la capture démarrée après validation du provider. Le parcours « vérifier le signal sans clé avant la session » promis n’a pas de mode dédié. | `main.py`, `audio/capture.py`, `ui/main_window.py`, README |
| F11 | P1 | **Statique :** push-to-talk connecté à `button-press/release-event` ; Ctrl+Enter déclenche `clicked`, donc un toggle. Aucune gestion explicite de perte de focus pendant l’appui. Compatibilité clavier et arrêt sûr à tester. | `ui/main_window.py`, `platform_capabilities.py` |
| F12 | P1 | **Mesuré :** tests verts et couverture 73 % cachent contrôleur/UI non exécutés par la suite. Le test de non-persistance audio inspecte un dossier temporaire qui n’est pas relié aux écritures potentielles du service. | `.github/workflows/ci.yml`, `tests/test_privacy.py`, `tests/gtk_accessibility_smoke.py` |
| F13 | P1 | **Statique :** filtres du workflow Flatpak omettent `exports.py`, `history.py`, `transcript.py`, `platform_capabilities.py` et `tests/**`. Le workflow release ne dépend pas de la CI générale et ne lance pas tous ses audits. | `.github/workflows/flatpak.yml`, `release.yml`, `ci.yml` |
| F14 | P1 | **Statique :** smoke affiche un succès incluant retrait même si le cleanup échoue (`|| true`), et peut sauter GTK sans bloquer. Le générateur de rapport affirme le succès Flatpak sans recevoir un résultat machine de ce contrôle. Le script ne doit pas être lancé sur le profil quotidien d’un utilisateur : son cleanup supprime les données de l’app. | `packaging/smoke_test_flatpak.sh`, `scripts/run_release_tests.py` |
| F15 | P1 | **Vérifié :** README/site actuels, version interne toujours 1.0.0, mais bundle et rapport au commit antérieur ; les faits fournisseur ajoutés le 1er septembre ne sont pas dans `onboarding.py` au tag v1.0.0. | `main.py`, `pyproject.toml`, `README.md`, `site/*`, tag/release |
| F16 | P1 | **Statique :** le README propose `requirements-dev.txt` pour développer sans matériel, mais celui-ci inclut les dépendances natives complètes. Le guide dédié utilise seulement Ruff ; les chemins d’entrée se contredisent. `CONTRIBUTING.md` pointe aussi vers une ancienne ancre README. | `requirements-dev.txt`, `README.md`, `CONTRIBUTING.md`, `docs/contributing/*` |
| F17 | P1 | **Visuel + source :** le GIF est composé de rendus Chrome de `site/product-tour.html`. Il ne montre pas une transcription réelle ; son écran final omet Undo, Redo, History et les états de segments présents dans GTK. | `scripts/render_demo_assets.sh`, `site/product-tour.html`, `site/assets/*` |

Pour F02 : [matrice officielle Groq des modèles et tâches](https://console.groq.com/docs/speech-to-text). Pour F06 : [conventions XDG de Flatpak](https://docs.flatpak.org/en/latest/conventions.html#xdg-base-directories). Ces vérifications documentaires ne remplacent pas les tests de bout en bout prévus ci-dessous.

### Architecture, sécurité et maintenance

Les modules de capture, configuration et providers sont séparés ; le transport HTTP est petit, les erreurs fournisseur normalisées, les fichiers de configuration/historique écrits atomiquement avec permissions restrictives. Ce sont des acquis à conserver.

`ui/main_window.py` compte **1 447 lignes** et mélange styles, composition, consentement, contrôles, stockage, historique et cycle de vie. La priorité est d’extraire l’état de session testable et les dialogues, pas de migrer tout GTK ou de réécrire dans un autre langage. Les `Any` du contrôleur et l’absence d’identité dans le callback de texte rendent les contrats asynchrones difficiles à vérifier.

Points complémentaires à traiter : réponse HTTP lue sans limite explicite, course possible entre admission et fermeture de l’executor, sauvegarde d’historique corrompu qui peut repartir d’une liste vide, export avec troncature directe et suivi de liens symboliques, persistance du choix de micro par index susceptible de changer. Ce sont des chemins à tester et durcir ; l’audit ne prétend pas avoir démontré une exploitation distante.

La clé sauvegardée est du texte local protégé par permissions, pas du chiffrement. Le projet n’a pas de télémétrie applicative identifiée dans les chemins examinés. La documentation doit préserver les limites liées au presse-papiers, au fournisseur, au runtime et aux sauvegardes.

### UX, visuels et présentation

L’identité vert sombre/crème, la typographie et la hiérarchie générale sont reconnaissables. Le site est déjà publié, responsive sur les deux pages contrôlées, avec navigation mobile fonctionnelle et liens de confidentialité visibles. Une refonte cosmétique totale n’est donc pas prioritaire.

À 1600 × 740 px CSS, le titre occupe l’essentiel de la hauteur et les boutons du hero sont sous le premier écran. L’image `social-preview.png` est une capture de hero coupée avant les appels à l’action ; ce n’est pas une composition sociale optimisée. Le site répète plusieurs fois la même promesse avant l’installation. Les captures synthétiques sont honnêtement signalées, mais ne peuvent pas convertir un lecteur sceptique en lui prouvant que le produit marche.

Les risques d’UI native à lever sont concrets : écran de configuration dense, multiples actions sur une petite largeur minimale, texte de 11–12 px, contraste à mesurer, focus/Orca non validés, autoscroll en fin de transcription qui peut gêner une correction. L’interface réelle doit être inspectée à taille minimale, à fort agrandissement et pendant une erreur longue ; les PNG marketing n’en donnent aucune preuve.

### Installation, distribution et contributions

Le bundle Flatpak existe et sa provenance est vérifiable. Il dépend néanmoins d’un runtime externe et n’ajoute pas de canal de mise à jour pour l’application. Le téléchargement manuel, les commandes, la création d’une clé fournisseur et l’absence de preuve sur machine vierge cumulent la friction.

La documentation Flatpak expose déjà l’exception d’affiliation entre l’App ID `audio_capture` et le dépôt `audio-capture`. Une exception locale de lint n’est pas une acceptation Flathub. Aucun téléchargement Windows/macOS/ARM n’est à promettre.

Les guides, licence, code de conduite, templates, labels et issues existent. Le déficit communautaire porte sur les retours réels, le suivi et la maintenance de cette file : le guide des premières issues cite encore la fixture déjà intégrée. Le protocole d’étude demande cinq personnes, l’ancien roadmap dix sessions ; une seule définition opérationnelle est nécessaire.

## 4. Positionnement concurrentiel

Comparaison relue le 8 septembre 2026, sur les descriptions officielles ; aucune évaluation comparative des performances n’a été menée.

| Projet | Proposition documentée | Conséquence pour ce projet |
| --- | --- | --- |
| [Speech Note](https://github.com/mkiol/dsnote) | Atelier graphique local de transcription, lecture et traduction, choix de modèles, distribution Flathub | L’édition de notes et le hors ligne sont déjà occupés. Gagner par un parcours plus étroit et plus facile, sans prétendre inventer la relecture |
| [nerd-dictation](https://github.com/ideasman42/nerd-dictation) | Dictée Vosk hors ligne, commandes begin/end/cancel, intégrations et hooks configurables | Ne pas rivaliser sur la seule « simplicité du code » ; offrir une expérience graphique compréhensible sans scripts personnels |
| [Vocalinux](https://github.com/VocaHQ/vocalinux) | Dictée locale, plusieurs moteurs, réglages graphiques, modèles et formats de distribution ; contraintes d’injection expliquées | Les moteurs locaux, raccourcis et paquets ne sont pas des différenciateurs nouveaux. Ne pas annoncer une supériorité non mesurée |
| [Voxtype](https://github.com/peteonrails/voxtype) | Dictée push-to-talk orientée intégration aux bureaux Wayland | Une personne voulant taper directement dans n’importe quelle application choisira potentiellement un autre outil ; préciser le parcours de relecture volontaire |

**Positionnement retenu pour la version cible :** « Une dictée Linux légère pour transformer une idée en brouillon relu, avec un transfert cloud explicite et des erreurs compréhensibles. » Le qualificatif « légère » doit être accompagné de mesures distinguant taille du bundle, runtime installé, mémoire et absence de modèle local.

**Hors périmètre de cette version :** transcription de réunions, diarisation, import de médias, résumé IA, synchronisation, multiplication des providers, saisie automatique dans l’application active, ports macOS/Windows/mobile, ARM et traduction complète de l’interface. Leur absence doit être indiquée, pas camouflée. Ils ne sont pas des prérequis à un excellent outil ciblé.

**Pistes P2 à réévaluer après des retours :** runtime local distribué avec choix/licence/checksum/taille du modèle, téléchargement repris et annulable, suppression et test réseau coupé ; raccourcis globaux via portail avec binding retourné par le bureau et repli explicite ; lexique personnel/ponctuation et traduction française de l’aide avec relecteur. Leur étude se conclut en phase 0 par une décision écrite. Aucune ne devient une promesse de la version cible ni une phase cachée après la vidéo.

## 5. Organisation et règles d’acceptation

- **P0** : confidentialité, intégrité du texte et blocages de persistance ; à corriger avant distribution renforcée.
- **P1** : parcours complet, preuves, installation, qualité et maintenance ; requis pour la version cible.
- **P2** : extensions explicitement exclues de cette version, réexaminées sur demande constatée.
- Chaque tâche ci-dessous commence **à faire**, même lorsqu’elle consolide un mécanisme existant. Les observations de l’audit ne valent pas réalisation de la tâche.
- Un résultat doit être relié à un commit, une version, un environnement, une commande ou un scénario, un résultat et une preuve nettoyée des données privées. « Non exécuté », « ignoré », « échec » et « réussi » restent distincts.
- Aucun test matériel n’est remplacé par un mock ; aucune preuve d’un ancien tag n’est recyclée pour un nouveau binaire.
- Les défauts de confidentialité seront traités sans publier de détails d’exploitation en issue ouverte avant correction. Ce roadmap local n’autorise aucune publication ni communication externe.
- La CI générale reste désactivée pendant cette analyse. Le plan prévoit une décision explicite : réactivation choisie par le mainteneur, ou contrôles équivalents exécutables et rapportés sans prétendre qu’ils tournent sur chaque PR.
- Une release corrective P0 peut être publiée avant la fin du programme lorsque ses propres contrôles sont satisfaits. **La vidéo finale attend toutes les phases 0 à 7**, y compris la validation du binaire final téléchargé.

### Charge indicative

| Phase | Charge de réalisation indicative |
| --- | --- |
| 0 — Contrat produit et preuves | 1–2 jours |
| 1 — Corrections de confiance | 6–10 jours |
| 2 — Architecture et vérification | 4–7 jours |
| 3 — Première utilisation et UX | 4–7 jours |
| 4 — Linux réel et qualité de transcription | 3–6 jours de travail, hors recrutement |
| 5 — Distribution et chaîne de release | 4–8 jours, hors revue Flathub |
| 6 — Documentation, présentation et contribution | 3–5 jours |
| 7 — Publication et recette finale | 2–4 jours |
| 8 — Vidéo réelle finale | 2–4 jours |

Ordre de grandeur : **29–53 jours de travail**, non engagement calendaire. Les retours utilisateurs, accès aux machines Linux et décisions de distribution peuvent allonger le calendrier. Les contrôles de phase 2 doivent accompagner les corrections de phase 1 ; l’ordre des portes de validation reste obligatoire.

## Phase 0 — Fixer le contrat publiable

### 0.1 — Définir la version cible et ses non-objectifs · P1

- **Objectif :** une promesse assez précise pour être implémentée et démontrée intégralement.
- **Changements :** fixer les scénarios prompt/ticket/note, x86_64 Linux et Groq ; distinguer transcription et traduction ; consigner la décision de reporter le local distribué et les raccourcis globaux, sauf nouvelle décision explicite de périmètre. Prévoir une version corrective puis une version mineure selon les changements réels, sans date commerciale imposée.
- **Fichiers/parties :** `README.md`, `docs/SUPPORT.md`, `docs/PROVIDERS.md`, `docs/VERSION-POLICY.md`, ce roadmap ; futur `docs/PRODUCT-SCOPE.md`.
- **Acceptation :** chaque affirmation publique correspond à un scénario et à un statut ; aucune fonction expérimentale présentée comme livrée dans le Flatpak.
- **Tests/validations :** revue croisée README, UI, CLI, manifestes, tag et release ; tableau des capacités de la version cible.
- **Dépendances/risques :** mainteneur pour le périmètre ; éviter de transformer une petite app en suite universelle. Toute extension choisie impose ses tests avant la phase vidéo.

### 0.2 — Créer un registre de preuves et un protocole utilisateur unique · P1

- **Objectif :** éliminer les cases cochées sans preuve et les objectifs contradictoires.
- **Changements :** centraliser statut, SHA, paquet, machine, date et résultat ; relier les anciennes preuves au seul tag concerné. Retenir cinq participants Linux indépendants pour la première étude, couvrant les profils du protocole existant ; séparer leurs sessions des essais mainteneur. Définir qui peut accepter chaque porte.
- **Fichiers/parties :** `docs/COMPATIBILITY.md`, `docs/packaging/RELEASE-CHECKLIST.md`, `research/usability/PROTOCOL.md`, futur `docs/RELEASE-EVIDENCE.md`.
- **Acceptation :** les cinq sessions sont un objectif, pas un résultat acquis ; aucun « passé » sans preuve ; voies matérielles ouvertes explicitement nommées.
- **Tests/validations :** contrôler les liens et la concordance entre rapport machine et texte public ; relire les champs pour exclure clés, noms privés et enregistrements personnels.
- **Dépendances/risques :** accès à deux configurations Linux et recrutement. Aucun participant fictif, aucun seuil ajusté après coup pour déclarer un succès.

## Phase 1 — Corriger les défauts qui cassent la confiance

### 1.1 — Appliquer le consentement au point d’envoi · P0 · F01

- **Objectif :** aucune transmission cloud sans accord correspondant au fournisseur actif.
- **Changements :** état de consentement versionné et distinct de l’onboarding ; garde dans le contrôleur et à la soumission ; mêmes règles après Explore first, clé d’environnement, Settings, migration et changement de provider ; action de retrait arrêtant la capture et les travaux encore annulables. **Fait localement :** la configuration expose `cloud_boundary_confirmed`, l’onboarding et Settings l’exigent pour Groq, et `_start_listening()` bloque une capture cloud non confirmée ; les tests contrôleur/configuration couvrent le garde-fou.
- **Fichiers/parties :** `config.py`, `onboarding.py`, `main.py`, `transcription/provider.py`, services, `ui/main_window.py`, `tests/test_onboarding.py`, nouveaux tests contrôleur.
- **Acceptation :** aucun appel du faux transport quand le consentement manque ou est retiré ; l’UI demande l’accord avant toute soumission ; le diagnostic par défaut reste sans réseau. Un appel déjà envoyé ne peut pas être « désenvoyé » : l’UI l’explique.
- **Tests/validations :** tests locaux de matrice clé d’environnement/consentement et démarrage contrôleur ; restent à valider la première ouverture/Explore first, le retrait pendant une session, l’annulation des travaux en vol et l’assertion réseau bout en bout sur le paquet Linux.
- **Dépendances/risques :** 0.1 ; migration des configurations existantes, erreur de classement entre configuration valide et consentement valide.

### 1.2 — Corriger le contrat modèle, langue et traduction · P0 · F02

- **Objectif :** chaque option offerte correspond à une requête fournisseur supportée.
- **Changements :** sélectionner un modèle compatible pour la traduction, conserver celui adapté à la transcription ; lier les capabilities au chemin effectif ; afficher l’impact de coût lorsque les modèles diffèrent ; normaliser les refus de modèle/tâche sans exposer le corps d’erreur. **Fait localement :** le service utilise maintenant `whisper-large-v3-turbo` pour la transcription et `whisper-large-v3` pour la traduction, et les tests inspectent le modèle choisi.
- **Fichiers/parties :** `groq_service.py`, `groq_transport.py`, `provider.py`, `onboarding.py`, `ui/main_window.py`, `docs/PROVIDERS.md`, tests provider/transport.
- **Acceptation :** les tests inspectent endpoint, modèle, langue et tâche ; aucune traduction n’est envoyée au modèle turbo incompatible. L’essai réel français → anglais reste ouvert sur le paquet cible avant de conserver la promesse publique.
- **Tests/validations :** tests de contrat transcription/translation et réponses erronées passent ; la documentation officielle Groq a été relue pendant l’implémentation. L’essai réseau explicite avec phrase sans données sensibles et clé du testeur reste à faire.
- **Dépendances/risques :** 1.1 ; coût et disponibilité du fournisseur. Sans accès réel, garder le contrôle manuel ouvert, ou retirer explicitement l’option de la version cible.

### 1.3 — Garantir ordre, identité et isolation des sessions · P0 · F03–F04

- **Objectif :** restituer les mots dans l’ordre parlé sans réinjecter un texte abandonné.
- **Changements :** identifiants de session et de segment dans les résultats ; ordonnancement borné ; définition des états terminé/échoué/annulé/vide ; invalidation des résultats tardifs à l’abandon ou au remplacement du provider. Une erreur de A doit libérer B sans attente infinie. **Fait localement :** un tampon partagé libère les résultats asynchrones dans l’ordre de soumission tout en conservant des workers parallèles ; les callbacks de résultat portent `request_id`, et le contrôleur ignore ceux qui ne sont plus actifs. L’annulation/abandon complet et la génération persistante de session restent ouverts.
- **Fichiers/parties :** `transcript.py`, `provider.py`, deux services, `main.py`, `ui/main_window.py`, fixture provider et tests d’intégration.
- **Acceptation :** A lent/B rapide donne A puis B ; échec de A visible et B exploitable ; aucun résultat d’une génération abandonnée ne modifie le nouveau brouillon, l’historique ou le presse-papiers.
- **Tests/validations :** test déterministe A lent/B rapide et test contrôleur de retour inactif ; restent à ajouter annulation, Clear avec travail en attente, changement de langue/provider, redémarrage rapide, erreur/texte vide et horloge/ordonnanceur contrôlés.
- **Dépendances/risques :** 1.1 ; ne pas ajouter une file de réordonnancement illimitée ni écraser les corrections manuelles lors d’un résultat tardif.

### 1.4 — Rendre arrêt, abandon et effacement exacts · P0 · F04–F05

- **Objectif :** un clic de fin de session a un effet compréhensible et vérifiable.
- **Changements :** Stop ferme le micro, traite les trames déjà admises et attend les résultats utiles avec état « traitement restant » ; Cancel invalide et supprime le travail annulable sans flush cloud. Ajouter une fermeture coordonnée avant destruction des widgets. Distinguer effacement réversible et abandon définitif ; pour ce dernier purger Undo/Redo et les résultats en attente. **Fait localement :** le bouton Clear n’enregistre plus de snapshot Undo et purge les piles Undo/Redo ; le contrat est couvert par un test pur.
- **Fichiers/parties :** `main.py`, `audio/capture.py`, `transcript.py`, `ui/main_window.py`, docs confidentialité et tests.
- **Acceptation :** dernière phrase préservée après Stop ; pas d’envoi supplémentaire provoqué par Cancel ; pas de callback GTK sur fenêtre détruite ; aucun Undo après un effacement annoncé définitif ; historique et exports décrits séparément.
- **Tests/validations :** stop avec backlog audio, fermeture pendant HTTP lent, SIGTERM, Clear puis Undo, retour tardif après Clear, copie automatique ; mesurer délais de fermeture et tester un blocage du lecteur audio.
- **Dépendances/risques :** 1.3 ; les workers HTTP actifs ont une limite d’annulation réelle. Ne pas promettre un effacement sécurisé de la RAM Python, du presse-papiers externe ou des sauvegardes.

### 1.5 — Fiabiliser configuration et stockage explicite · P0/P1 · F06–F07

- **Objectif :** des réglages et textes conservés exactement comme l’interface l’annonce.
- **Changements :** respecter `XDG_CONFIG_HOME` avec repli et migration prudente ; préparer un nouvel état puis ne le valider en mémoire qu’après sauvegarde ; normaliser tous les échecs d’I/O. **Fait localement :** le chemin par défaut respecte maintenant `XDG_CONFIG_HOME`, les erreurs d’écriture de configuration sont converties en `ConfigError`, et une mise à jour échouée restaure l’état mémoire. Préserver un historique corrompu ou futur au lieu de l’écraser silencieusement ; protéger les exports contre troncature partielle et liens inattendus en respectant le portail.
- **Fichiers/parties :** `config.py`, `history.py`, `exports.py`, `ui/main_window.py`, tests configuration/historique/exports/privacy ; docs de migration.
- **Acceptation :** relance du vrai Flatpak retrouve les préférences dans son espace XDG ; refus d’écriture laisse mémoire et disque cohérents ; fichier préexistant intact si export échoue ; erreur d’historique expliquée et récupérable.
- **Tests/validations :** XDG personnalisé, dossier absent/non inscriptible, disque plein simulé, JSON invalide, schéma futur, migration, symlink, export via portail et nettoyage de données après désinstallation.
- **Dépendances/risques :** 1.1 et 1.4 ; compatibilité avec les fichiers existants et les droits accordés par le portail. Ne pas déplacer ni supprimer les données utilisateur sans procédure documentée.

## Phase 2 — Rendre la robustesse mesurable et maintenable

### 2.1 — Extraire les contrats de session et alléger l’UI · P1

- **Objectif :** rendre les scénarios critiques testables sans GTK et les modifications localisées.
- **Changements :** extraire contrôleur de session/ordonnanceur, dialogues de setup, préférences et historique ; isoler le CSS ; typer les dépendances par protocols. Garder GTK 3 et les modules audio existants, avec refactoring progressif après les tests de régression P0.
- **Fichiers/parties :** `main.py`, `ui/main_window.py`, `transcription/provider.py`, nouveaux modules ciblés sous `ui/` et de session ; `docs/ARCHITECTURE.md`.
- **Acceptation :** contrôleur instanciable sans importer GTK/PyAudio ; aucun accès widget depuis un worker ; les callbacks portent session/segment ; mêmes raccourcis, formats et paramètres publics.
- **Tests/validations :** tests de contrat et d’intégration de phase 1, smoke GTK, comparaison visuelle avant/après sur Linux, vérification des imports CLI.
- **Dépendances/risques :** tests P0 ; éviter une réécriture globale et un framework d’abstraction plus complexe que le produit.

### 2.2 — Borner toutes les ressources et rendre les pertes visibles · P1 · F08

- **Objectif :** une longue session et un réseau dégradé ne dégradent pas progressivement l’app.
- **Changements :** éviction réelle des états finalisés, conservation séparée des seuls états en cours ; budget de snapshots en octets et regroupement des éditions ; limites documentées de l’historique et des réponses HTTP ; gestion atomique admission/fermeture de l’executor ; indication des pertes de trames et de saturation avec action de reprise. **Fait localement :** `SegmentTracker` évince maintenant les états et identifiants hors de la fenêtre visible, avec compteur borné et test à 10 000 requêtes ; les budgets audio, historique, HTTP et executor restent à traiter.
- **Fichiers/parties :** `transcript.py`, `history.py`, `audio/capture.py`, services/transport, contrôleur et tests de stress.
- **Acceptation :** 10 000 segments ne créent pas 10 000 états conservés ; limites mesurées et constantes indépendamment de la durée ; saturation visible, pas de retry illimité ni de nouvelle copie d’audio persistée.
- **Tests/validations :** stress déterministe, réponse surdimensionnée, fermeture concurrente, 429, panne prolongée, session réelle de 30 minutes ; vérifier mémoire et nombre de threads après retour au repos.
- **Dépendances/risques :** 1.3, 2.1 ; un budget peut refuser du travail : l’utilisateur doit savoir quelle partie n’a pas été transcrite et devoir la redire si l’audio a été supprimé.

### 2.3 — Corriger la stratégie de tests et la couverture · P1 · F12

- **Objectif :** les résultats verts doivent couvrir les comportements qui comptent.
- **Changements :** source de couverture explicite incluant les modules non importés ; rapport séparant cœur, contrôleur et UI ; nouveaux tests de session et vraies assertions d’I/O pour la non-persistance ; smoke GTK avec interactions et états, pas seulement existence des contrôles. Conserver la fixture externe utile.
- **Fichiers/parties :** `pyproject.toml`, `.github/workflows/ci.yml`, `tests/*`, `tests/gtk_accessibility_smoke.py`, `scripts/run_release_tests.py`.
- **Acceptation :** tous les F01–F12 ont une régression pertinente ; aucune exclusion silencieuse du contrôleur ; viser au moins 80 % lignes+branches du cœur/contrôleur après extraction, publier la couverture globale sans prétendre que ce chiffre valide GTK. Les skips sont visibles.
- **Tests/validations :** montrer qu’un test échoue avec l’ancien comportement puis passe avec la correction ; tests d’écritures interceptées plus observation sandbox ; suite hermétique sans accès micro/réseau ; jobs Linux natifs distincts.
- **Dépendances/risques :** 2.1 ; ne pas remplir le score avec des tests d’accesseurs ou de chaînes de documentation. Adapter un seuil seulement avec justification écrite et sans masquer le périmètre.

### 2.4 — Fermer les trous d’automatisation et de sécurité · P1 · F13–F14

- **Objectif :** vérifier le code effectivement livré même si la CI générale reste en pause.
- **Changements :** commande unique de validation locale ; alignement des contrôles release et CI ; filtres Flatpak couvrant tous les modules runtime, tests et outils de release ; pinning des actions/images critiques par révision/digest avec mise à jour contrôlée ; examen des PR Dependabot. Formaliser le choix mainteneur sur la pause et le canal privé de signalement.
- **Fichiers/parties :** `.github/workflows/*.yml`, `.github/dependabot.yml`, scripts de vérification, `SECURITY.md`, paramètres GitHub ultérieurement selon décision explicite.
- **Acceptation :** un changement de `history.py` ou d’un test pertinent déclenche le bon contrôle lorsque le workflow est actif ; une release ne peut pas publier après audit/test échoué ; le canal de sécurité indiqué existe. En cas de pause conservée, rapport exact attaché à chaque candidat et aucune promesse de CI par PR.
- **Tests/validations :** cas de filtres, exécution sur branche de test/candidat, échec volontaire d’un contrôle bloquant, permissions minimales des jobs ; vérification en lecture seule des paramètres après toute action future autorisée.
- **Dépendances/risques :** décision mainteneur pour réactiver un workflow ou le reporting privé ; compatibilité des majors Actions ; aucune activation automatique au prétexte de ce document.

## Phase 3 — Réussir la première utilisation et la relecture

### 3.1 — Ajouter le test micro local et un onboarding court · P1 · F10

- **Objectif :** identifier son micro et comprendre la frontière cloud avant de payer ou dicter.
- **Changements :** mode explicite « Tester le microphone » qui alimente uniquement la jauge, sans VAD soumis au provider, timeout et arrêt visibles ; parcours choisir micro → comprendre fournisseur → configurer → phrase réelle → copie ; Settings et premier lancement utilisent les mêmes composants et règles.
- **Fichiers/parties :** `audio/capture.py`, contrôleur, dialogues `ui/`, `onboarding.py`, diagnostics et guides.
- **Acceptation :** sans clé ni consentement cloud, le test affiche le vrai signal et aucun transport n’est appelé ; fermeture/libération du micro garanties ; phrase test réelle uniquement après consentement ; erreurs clé/réseau/micro comportent une action concrète.
- **Tests/validations :** faux provider piégé si appelé en mode test ; ouverture/fermeture répétée ; mesure physique sur deux sources ; parcours clavier complet et relance sans clé.
- **Dépendances/risques :** phases 1–2 ; le test micro lui-même implique un accès audio local qui doit être visible et initié par l’utilisateur.

### 3.2 — Stabiliser sélection audio et push-to-talk · P1 · F09–F11

- **Objectif :** aucune ambiguïté sur quand on écoute et quel périphérique est utilisé.
- **Changements :** séparer amorçage et fin de parole ; calibrer les mots courts et la coupure à 20 s ; conserver suffisamment de contexte sans promettre zéro silence dans les segments. Résoudre le micro sauvegardé avec identité vérifiée plutôt qu’un index seul ; gérer changement/retrait. Ajouter press/release clavier et perte de focus, ou renommer honnêtement le mode souris si le clavier n’est pas supporté. **Fait localement :** le seuil d’amorçage VAD utilise maintenant la durée minimale configurée, et une séquence de 300 ms de parole produit un segment dans le test déterministe ; la mesure sur micros réels et le reste du mode push-to-talk restent ouverts.
- **Fichiers/parties :** `audio/vad.py`, `capture.py`, `config.py`, contrôleur, `ui/`, tests audio/VAD, `docs/DAILY-DICTATION.md`.
- **Acceptation :** une phrase courte au seuil documenté passe ; silence seul ne déclenche pas d’upload ; mots aux limites préservés ; aucun mauvais micro choisi silencieusement ; relâchement, perte de focus et fermeture arrêtent le mode maintenu.
- **Tests/validations :** corpus déterministe trame par trame, mots courts/bruit/longue parole ; micro USB retiré/rebranché ; Ctrl+Enter répétitif, Tab/Alt+Tab pendant l’appui et événements de relâchement perdus.
- **Dépendances/risques :** 2.1, 3.1 ; compromis latence/qualité/coût par requête ; pas de promesse de raccourci global.

### 3.3 — Polir l’atelier et ses états, avec accessibilité réelle · P1

- **Objectif :** privilégier la relecture et la copie au lieu d’obliger à surveiller l’application.
- **Changements :** hiérarchie claire entre capture, traitement restant et brouillon prêt ; copie/export sensibles au contenu et à l’état ; autoscroll uniquement quand l’utilisateur suit déjà la fin ; préserver curseur/sélection pendant les arrivées. Réorganiser Settings en groupes courts ; améliorer messages longs, focus, contrastes et tailles de texte ; confirmation à la fermeture d’un brouillon non conservé.
- **Fichiers/parties :** `ui/`, styles extraits, `transcript.py`, `tests/gtk_accessibility_smoke.py`, `docs/contributing/UI-GUIDE.md`.
- **Acceptation :** boutons essentiels accessibles à 560 × 520 et à la taille minimale annoncée, échelle 100/150/200 %, texte 12–32 ; aucune action perdue hors écran ; parcours entièrement clavier ; lecture Orca des états importants sans spam ; aucune correction écrasée par une arrivée.
- **Tests/validations :** captures GTK réelles de setup/repos/écoute/attente/erreur/historique ; contraste mesuré ; clavier, Orca, texte long, français et écriture RTL ; redimensionnement et absence de warnings GTK pertinents.
- **Dépendances/risques :** 1.3–1.5, 2.1 ; préférences keep-on-top/opacité variables selon le compositeur : rendre l’indisponibilité explicite après essais.

## Phase 4 — Prouver le produit sur Linux et avec des utilisateurs

### 4.1 — Passer la matrice matérielle minimale · P1

- **Objectif :** remplacer les compatibilités attendues par des rapports reproductibles.
- **Changements :** tester Ubuntu GNOME/Wayland/PipeWire et Debian/X11/PulseAudio, versions exactes ; x86_64 ; micro intégré et USB ; clé de testeur ; launcher, consentement, signal, dictée, traduction, stop/cancel, correction, copie, export, historique et suppression. Tester les restrictions sandbox et la révocation réelle disponible sur le bureau sans inventer un prompt par capture.
- **Fichiers/parties :** `docs/COMPATIBILITY.md`, `docs/SUPPORT.md`, checklist package, futurs rapports anonymisés reliés aux issues #3, #4, #5 et #7.
- **Acceptation :** deux rapports complets sur un candidat identifié ; aucune ligne « supported » déduite uniquement d’un manifeste ; incidents P0/P1 du parcours corrigés et rejoués ; les autres bureaux restent non vérifiés.
- **Tests/validations :** micro débranché, suspend/reprise, clé refusée, réseau coupé, saturation déterministe ; véritable export par portail puis relecture du fichier ; historique off/on et relance ; installation propre séparée du profil quotidien.
- **Dépendances/risques :** phases 1–3, candidat Flatpak disponible ; accès à du Linux physique. Une VM peut compléter l’installation, mais pas être décrite comme preuve de tous les micros physiques.

### 4.2 — Mesurer le temps jusqu’au texte utile et les ressources · P1

- **Objectif :** remplacer « rapide/léger » par des chiffres contextualisés.
- **Changements :** benchmark du provider distribué et du parcours VAD → texte visible ; corpus autorisé anglais/français incluant phrases courtes et pauses ; mesurer latence médiane/p95, taux d’erreur, pertes de mots/segments, temps de démarrage, mémoire et téléchargements runtime. Conserver le reçu tiny.en historique avec son périmètre explicite.
- **Fichiers/parties :** `benchmarks/`, `benchmarks/results/`, docs provider/support, futur résumé de performance.
- **Acceptation :** matériel, connexion, modèle, version, taille d’échantillon, licences et méthode publiés ; distinguer temps réseau et délai de segmentation ; aucune comparaison « plus rapide que X » sans protocole commun. Définir les budgets avant la recette, puis publier aussi les résultats défavorables.
- **Tests/validations :** calculs WER/percentiles existants, corpus déterministe, au moins 30 phrases par langue pour le premier relevé ; session 30 minutes ; absence de croissance mémoire non bornée hors taille du texte ; mesures répétées avec dispersion.
- **Dépendances/risques :** 3.2 et 4.1 ; API payante et variabilité réseau ; le benchmark local CI sur 25 extraits ne mesure ni Groq ni l’usage quotidien.

### 4.3 — Conduire cinq sessions de première utilisation · P1

- **Objectif :** vérifier qu’une personne découvre et utilise le produit sans coaching.
- **Changements :** appliquer le protocole unifié ; mesurer séparément installation/runtime/création de compte fournisseur et temps « application prête → première copie » ; consigner les incompréhensions et corriger les obstacles ; inclure au moins une personne peu technique.
- **Fichiers/parties :** `research/usability/PROTOCOL.md`, futur `FINDINGS.md`, guides d’installation et issues de correction.
- **Acceptation :** cinq vraies sessions consenties ; au moins quatre réussites autonomes ; après prérequis disponibles, première copie en moins de cinq minutes pour ces réussites ; cinq personnes capables d’expliquer où va l’audio avant transmission. Les échecs restent dans le rapport et les blocages sont corrigés puis revérifiés.
- **Tests/validations :** dictée d’une phrase neutre, correction/Undo/copie/export, choix historique et effacement ; observation manuelle anonymisée, sans analytics ni collecte de clé/audio personnel.
- **Dépendances/risques :** 4.1 ; recrutement, quotas fournisseur, temps de téléchargement. Cinq personnes révèlent des problèmes, ne constituent pas une preuve statistique de marché.

## Phase 5 — Distribuer et mettre à jour un vrai paquet

### 5.1 — Fiabiliser le package et ses preuves d’installation · P1 · F14

- **Objectif :** vérifier le paquet livré, ses données et sa suppression de manière exacte.
- **Changements :** smoke sur compte/VM jetable ; tests de sauvegarde/relecture Settings et historique dans le sandbox ; GTK requis pour le job de release ; résultat JSON par étape ; désinstallation réellement vérifiée avant succès ; version attendue fournie au script ; aucun cleanup destructif du profil courant.
- **Fichiers/parties :** manifestes `packaging/*`, `io.github.othmaneblial.audio_capture.yml`, `smoke_test_flatpak.sh`, `run_release_tests.py`, checklist et workflows.
- **Acceptation :** saut GTK et échec uninstall ne produisent plus un rapport « passed » ; données de test supprimées ; permissions comparées à une liste autorisée complète, pas à un seul motif `home|host` ; configuration XDG persistante ; export choisi sans accès large au home.
- **Tests/validations :** build propre, sources récupérées puis rebuild sans téléchargement, lints, install/CLI/GTK/settings/export/uninstall ; injecter un échec à chaque étape pour vérifier le rapport et le code retour.
- **Dépendances/risques :** 1.5, 2.4, 4.1 ; runtime GNOME et comportement portail. Un rebuild sans téléchargement ne prouve pas une identité binaire bit à bit.

### 5.2 — Fournir un canal de mise à jour maintenable · P1

- **Objectif :** installation et mises à jour accessibles sans cloner le dépôt.
- **Changements :** privilégier une soumission Flathub avec métadonnées, vraies captures et revue d’affiliation de l’App ID ; conserver le bundle GitHub vérifiable. Si la revue externe bloque, choisir explicitement un dépôt Flatpak signé maintenu, avec `.flatpakref`, politique de mise à jour et clés gérées hors Git. Ne pas changer d’App ID sans migration planifiée.
- **Fichiers/parties :** manifestes, desktop/MetaInfo, `docs/packaging/DECISION.md`, `FLATPAK.md`, workflow de distribution et paramètres du canal futur.
- **Acceptation :** un canal réellement publié permet installation puis mise à niveau entre deux versions et suppression ; le lien primaire ne bascule vers Flathub qu’après page publique vérifiée. Une PR de soumission seule ne satisfait pas la porte ; si aucun canal n’est disponible, la diffusion renforcée et la vidéo finale attendent.
- **Tests/validations :** machine propre, vérification signature/identité, update avec historique/préférences, retrait de données, ancien bundle vers nouvelle distribution ; revue des permissions et de la procédure de récupération.
- **Dépendances/risques :** 5.1, affiliation/acceptation externe ; maintenance d’un dépôt signé et protection des clés. Ne pas créer plusieurs formats pour embellir la liste des badges.

### 5.3 — Produire un candidat reproductible avec provenance complète · P1

- **Objectif :** associer version, source, contrôles et contenu livré.
- **Changements :** source unique pour la version, changelog réel, notes et tests générés depuis les résultats ; distinguer candidat et stable ; checksums de tous les artefacts ; validation de schéma SBOM et vérification de son inventaire avec le paquet ; enregistrer révision du runtime et outils de build, attestations et licences des composants.
- **Fichiers/parties :** `pyproject.toml`, `main.py`, `scripts/check_release.py`, `generate_sbom.py`, `render_release_notes.py`, `run_release_tests.py`, `release.yml`, `CHANGELOG.md`, MetaInfo.
- **Acceptation :** tag, source, package et rapport désignent exactement la même version ; aucun succès prérempli ; une commande permet de vérifier checksum et provenance ; archive source/roue installables si proposées, sans les présenter comme binaires desktop autonomes.
- **Tests/validations :** dry-run sans publication, version incohérente bloquée, schéma SBOM, comparaison des dépendances, vérification d’attestation téléchargée ; tests et audits de 2.4 sur le SHA candidat.
- **Dépendances/risques :** 5.1 et 2.4 ; reproductibilité réseau/runtime et portée du SBOM. Ne pas réécrire silencieusement les assets ou le tag v1.0.0 existants.

## Phase 6 — Présentation GitHub, documentation et contribution

### 6.1 — Aligner README et guides sur le paquet candidat · P1 · F15–F16

- **Objectif :** comprendre le bénéfice et atteindre la première copie avec un chemin unique.
- **Changements :** haut de README court : cas d’usage, capture réelle, installation recommandée, prérequis cloud et limites ; différencier stable et développement. Corriger les promesses de jauge, silence, effacement et traduction. Unifier les guides sans clé ; séparer les dépendances de tests purs des dépendances GTK complètes ; réparer les ancres et exemples d’installation source avec clone/cd.
- **Fichiers/parties :** `README.md`, `requirements-dev.txt`, éventuel fichier de tests purs, `CONTRIBUTING.md`, `docs/CLI.md`, `FAQ.md`, `SUPPORT.md`, `PROVIDERS.md`, guides contributeurs, `site/docs.html`.
- **Acceptation :** commandes copiées sur environnement vierge fonctionnent ; tests purs installables sans GTK/PortAudio/clé ; chaque fonction annoncée appartient au candidat ; le lecteur voit architecture, cloud et mode d’update avant installation.
- **Tests/validations :** vérification des commandes dans VM/venv jetables ; contrôle liens locaux/ancres et URLs de téléchargement ; confrontation aux sessions de phase 4 ; exemples vérifiés sur le paquet.
- **Dépendances/risques :** phases 3–5 ; maintenance de la documentation HTML/Markdown dupliquée. Garder une source canonique ou un contrôle de divergence.

### 6.2 — Montrer l’application réelle et raccourcir le site · P1 · F17

- **Objectif :** une première impression visuelle agréable qui prouve les fonctions importantes.
- **Changements :** captures statiques issues du vrai GTK candidat : setup, écoute, relecture, erreur récupérable ; légendes et version ; remplacer progressivement les rendus HTML en tant que preuve. Compacter hero et répétitions ; concevoir une vraie image de partage ; conserver la direction visuelle existante. Préparer l’emplacement vidéo sans créer de film avant la phase 8.
- **Fichiers/parties :** `site/index.html`, `styles.css`, `docs.html`, `product-tour.html`, `site/assets/`, `README.md`, MetaInfo et script d’assets.
- **Acceptation :** bénéfice, plateforme, cloud et lien d’installation visibles au premier écran desktop de référence ; captures cohérentes avec le candidat, texte neutre réellement produit ; illustrations restantes explicitement étiquetées ; aucune capture synthétique présentée comme preuve d’exécution.
- **Tests/validations :** desktop 1280/1440 px et mobile 375/768 px, `scrollWidth === innerWidth`, menu/clavier/copie des commandes, console, images/alt, contrastes, préférence de mouvement réduit ; vérification visuelle du social preview aux petites tailles.
- **Dépendances/risques :** 3.3, 4.1 et 5.3 ; secrets et noms privés hors champ ; les captures statiques ne satisfont pas la phase vidéo finale.

### 6.3 — Transformer la documentation communautaire en boucle de maintenance · P1

- **Objectif :** aider un contributeur à produire une amélioration utile et reconnue.
- **Changements :** actualiser les issues #3–#10 et le guide des premières tâches ; créditer la PR #11 ; préparer trois tâches petites avec reproduction, fichiers, critère et interlocuteur ; préciser support et réponse sécurité effective ; revue Dependabot régulière ; plan de partage ciblé avec exemples du produit et règles des communautés.
- **Fichiers/parties :** `.github/ISSUE_TEMPLATE/*`, labels et PR template, `CONTRIBUTING.md`, `SECURITY.md`, `docs/GOOD-FIRST-ISSUES.md`, `docs/FEEDBACK.md`, `research/p5-launch-posts.md`, billets existants et métadonnées GitHub.
- **Acceptation :** aucune tâche déjà terminée présentée comme ouverte ; un contributeur peut lancer les tests en moins de dix minutes hors téléchargement ; description/homepage/topics cohérents ; social preview réellement vérifié dans les paramètres s’il est téléversé. Les brouillons de lancement restent des brouillons jusqu’à autorisation d’envoi.
- **Tests/validations :** parcours contributeur depuis clone propre, contrôle templates/liens, audit des versions dans les articles ; suivi manuel hebdomadaire des installations rapportées, problèmes résolus, retours et contributions récurrentes, sans télémétrie applicative.
- **Dépendances/risques :** 2.4, 6.1 ; disponibilité du mainteneur. La diffusion publique et les messages à des tiers demandent une autorisation explicite au moment de l’exécution future ; aucun spam ni échange de stars.

## Phase 7 — Publier et valider la version finale

### 7.1 — Geler le code puis publier les artefacts exacts · P1

- **Objectif :** faire correspondre la promesse finale au téléchargement proposé.
- **Changements :** revue finale du périmètre et des risques, version/changelog/tag définitifs, exécution de tous les contrôles, publication des binaires et preuves, synchronisation du canal d’update, README/site et release notes. Conserver les preuves du candidat mais refaire celles que le code final invalide.
- **Fichiers/parties :** surfaces de version, workflows et scripts de release, GitHub Releases, canal Flatpak, `README.md`, site, `docs/RELEASE-EVIDENCE.md`.
- **Acceptation :** phases 0–6 validées, zéro P0/P1 bloquant sur le parcours ; assets publics accessibles et associés au SHA final ; documentation stable exacte ; état CI déclaré honnêtement ; aucun badge « latest » pointant vers un produit différent des captures.
- **Tests/validations :** suite complète, audits, build offline, lints, smoke et porte humaine signée ; contrôle des jobs sur SHA final, checksum et provenance après téléchargement depuis la release.
- **Dépendances/risques :** phases 0–6 ; autorisation future de publication, services externes et caches. Une release corrective déjà publiée n’est pas automatiquement la version finale à filmer.

### 7.2 — Faire une recette du téléchargement public sur machine propre · P1

- **Objectif :** prouver le même parcours qu’un nouvel utilisateur après publication.
- **Changements :** télécharger depuis le lien du README, installer, lancer par l’icône, configurer, dicter, relire, copier vers un éditeur neutre, exporter, relancer et vérifier mise à jour/suppression. Recontrôler le site servi, les fichiers et les liens externes essentiels.
- **Fichiers/parties :** registre de preuves, checklist release, support/compatibilité, paquets et pages publiques.
- **Acceptation :** rapport daté du vrai paquet téléchargé ; mêmes SHA/digest/version que 7.1 ; fonctionnement complet et données conformes aux préférences ; aucun élément crucial simplement « supposé identique au build local ». Le produit à filmer est ce produit-là.
- **Tests/validations :** recette physique des deux configurations minimales, erreurs critiques, provenance, lancement sans clone, désinstallation sur profil jetable ; page/asset HTTP et contrôle visuel après publication.
- **Dépendances/risques :** 7.1 ; toute correction du code impose un nouveau paquet et la reprise des validations affectées avant la vidéo. Une panne externe laisse la porte ouverte, elle n’autorise pas à substituer une maquette.

## Phase 8 — Créer la vraie vidéo de démonstration du produit terminé

> **Dernière phase, obligatoire.** Aucune capture destinée au film, aucun montage de la vidéo finale avant l’implémentation et la validation de toutes les phases 0 à 7. Les captures statiques de QA précédentes ne sont pas un commencement de cette production vidéo. Si une porte manque, cette phase reste bloquée.
>
> Utiliser obligatoirement la skill **`ffmpeg-video-editor`**, relue au début de l’exécution. Référence disponible lors de cet audit : `/Users/othmane/.codex/skills/ffmpeg-video-editor/SKILL.md`. Lire aussi ses presets et références utiles ; ne pas supposer que le chemin local sera identique sur une autre machine.

### 8.1 — Préparer le tournage à partir des preuves finales · P1

- **Objectif :** démontrer le problème résolu et le produit téléchargeable sans mise en scène trompeuse.
- **Changements :** rédiger un conducteur de 90–120 s ; choisir une configuration Linux validée et le paquet de 7.2 ; préparer un bureau propre et des phrases de démonstration sans données personnelles ; installer/configurer la clé hors champ. Le récit couvre problème → installation/démarrage → choix et test du micro → frontière cloud → dictée → attente réelle → relecture/correction/Undo → copie collée dans un éditeur neutre → export relu.
- **Fichiers/parties :** futurs `docs/demo/SHOTLIST.md`, `docs/demo/RECORDING.md` ; rushes privés/temporaires hors Git ; manifeste du paquet utilisé.
- **Acceptation :** chaque scène correspond à une fonction livrée et validée ; tag, commit, architecture, bureau et digest consignés ; aucun compte, clé, notification, chemin personnel ou texte privé visible ; aucune phrase de rapidité ou de confidentialité au-delà de la preuve.
- **Tests/validations :** contrôler toutes les portes 0–7 avant de filmer ; répétition réelle non enregistrée du scénario et contrôle du cadrage ; autorisation des voix/musiques/visuels éventuels.
- **Dépendances/risques :** 7.2 et matériel de capture Linux ; indisponibilité de Groq. Les délais d’installation coupés doivent être signalés, sans suggérer une installation instantanée.

### 8.2 — Capturer une véritable utilisation et monter avec FFmpeg · P1

- **Objectif :** un film lisible et rythmé qui reste une preuve d’utilisation.
- **Changements :** enregistrer le vrai bureau et le micro avec un outil compatible avec la session Linux ; conserver une prise continue du cœur dicter → recevoir → corriger → copier ; sonder les rushes avec `ffprobe` avant montage. Appliquer la skill pour coupes, titres sobres, recadrages utiles et mixage ; garder des temps de lecture suffisants et le son de la phrase dictée, ou une explication fidèle si le son n’est pas retenu.
- **Fichiers/parties :** rushes hors dépôt ; futurs script reproductible de montage, fichiers de titres/sous-titres sous `scripts/` ou `docs/demo/` ; fichier final en zone de livraison.
- **Acceptation :** aucun rendu de `site/product-tour.html`, transcript injecté, remplacement d’écran ou succès inventé ; ce qui est copié est bien le résultat visible puis corrigé ; temps réel conservé pour la preuve de latence, accélérations/coupes de délais explicitement signalées ; montage sans zoom décoratif qui masque le contexte.
- **Tests/validations :** contrôle des rushes et timecodes ; comparaison du texte entendu, reçu, édité et collé ; inspection des transitions et de la lisibilité à taille README ; normalisation audio deux passes si nécessaire, absence d’écrêtage et musique facultative discrète.
- **Dépendances/risques :** 8.1 ; capture et encodage peuvent ralentir l’app. Mesurer cette influence et ne pas utiliser le film comme benchmark non contrôlé ; une panne découverte renvoie à la phase concernée puis à 7.2 avant de reprendre.

### 8.3 — Exporter, vérifier intégralement et intégrer les médias · P1

- **Objectif :** une démonstration partageable qui se lit vraiment sur les surfaces prévues.
- **Changements :** master de bonne qualité conservé hors Git ; export principal MP4 H.264, `yuv420p`, 1920 × 1080, 30 fps, `faststart`, AAC si piste audio. Cible 90–120 s et ≤ 25 Mo, à ajuster sur lisibilité mesurée ; option 1280 × 720 si utile au poids. Préparer une version courte de 20–35 s si le cadrage permet de comprendre dictée/relecture/copie, en 16:9 ou 9:16 adapté sans couper l’interface essentielle.
- **Fichiers/parties :** futurs `demo.mp4`, `demo-short.mp4` si pertinent, poster réel, sous-titres WebVTT/SRT, transcription accessible, rapport de validation ; `README.md`, `site/index.html`, `site/assets/` et assets de release/hosting selon canal retenu.
- **Acceptation :** rapport `ffprobe` indiquant durée, résolution, fps, codecs, format pixel, pistes et poids réels ; décodage complet sans erreur ; lecture humaine du début à la fin pour chaque export ; pas d’écran noir, gel, texte illisible, désynchronisation ni secret. La version courte est contrôlée séparément. La version principale reste accessible même si aucune courte n’est pertinente.
- **Tests/validations :** exécuter les contrôles ci-dessous, écouter et regarder intégralement, puis lire le fichier effectivement téléversé sur GitHub et sur le site desktop/mobile. Tester chargement, contrôle lecture/pause, sous-titres, poster et repli accessible ; conserver SHA-256 de chaque livraison et provenance des rushes.
- **Dépendances/risques :** 8.2 ; limites d’upload et rendu GitHub à vérifier à ce moment. Ne pas supposer qu’une balise HTML `<video>` dans le README donne un lecteur. Utiliser une pièce jointe GitHub vérifiée si elle rend un lecteur ; sinon poster cliquable vers la vidéo hébergée/asset de release, et `<video controls>` sur le site. Un GIF éventuel n’est qu’un extrait secondaire sans audio, jamais le substitut de la vidéo demandée.

Commandes minimales de validation à adapter aux exports réellement produits :

```bash
ffprobe -v error -show_streams -show_format -of json demo.mp4
ffmpeg -v error -xerror -i demo.mp4 -map 0:v:0 -map '0:a?' -f null -
```

Ces commandes vérifient structure et décodage ; elles ne remplacent pas la lecture humaine intégrale. Le rapport final doit donner le fichier, la durée, la résolution, les codecs, le poids, le résultat de lecture et l’URL réellement vérifiée. La mise en ligne de ces seuls médias complète cette dernière phase ; aucun chantier produit supplémentaire n’est placé après elle.
