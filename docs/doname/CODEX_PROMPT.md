# Mission Codex — refondre IsDomainOK en DoName

Tu interviens comme responsable de la conception et de l'implémentation de **DoName**, dans le dépôt `coconut971/isdomainok`. Le nom exact est DoName, D-O-N-A-M-E.

Lis d'abord `AGENTS.md` et `docs/doname/PROJECT.md`. Le second contient la mémoire du projet, les décisions explicites, un audit statique de départ et les références officielles. Ne le confonds pas avec une description de fonctionnalités déjà livrées. Inspecte toi-même le dépôt et vérifie ses constats.

## Le résultat attendu

Transforme cet ancien utilitaire en un véritable plugin de recherche de noms et de vérification de domaines, utilisable par ChatGPT, Codex, Claude et d'autres hôtes compatibles. Le produit doit être simple à installer, rapide à utiliser, précis dans ses réponses et léger à maintenir. L'ambition est de dépasser l'expérience d'un simple connecteur Namecheap, pas de reproduire sa boutique ni de prétendre posséder ses accès aux registres.

L'utilisateur doit pouvoir donner un brief naturel, obtenir une sélection courte de noms avec des domaines réellement vérifiés dans les limites des sources disponibles, puis affiner sa demande. Ne transforme pas le parcours en une suite de commandes techniques. L'IA hôte invente et juge les noms ; DoName vérifie, structure les preuves et aide à appliquer les contraintes. Aucun appel obligatoire à une autre IA.

La V1 est gratuite et **non transactionnelle**, mais elle doit déjà être connectée au marché réel. Elle doit viser au moins une source viable de disponibilité/prix en lecture seule afin que l'IA puisse connaître l'enregistrabilité actuelle, le prix d'enregistrement et, lorsque disponible, le renouvellement. Ne confonds pas « non commercial » avec « sans API de registrar ». En V1, DoName ne facture pas, ne touche pas de commission obligatoire, n'enregistre pas, ne transfère pas, ne réserve pas, ne modifie pas le DNS et n'exécute pas de checkout. Un lien sortant vers un registrar, marketplace ou courtier est acceptable s'il est clairement présenté comme externe.

Conçois une abstraction provider légère et réelle dès le départ. Étudie les API actuelles de registrars/registries/resellers pertinentes et sélectionne un premier provider V1 selon accès, couverture TLD, qualité des statuts, prix disponibles, limites, conditions et maintenabilité. Namecheap est une référence produit et peut être étudié comme provider potentiel, mais ne suppose ni partenariat ni accès privilégié. Le moteur ne doit pas être prisonnier de GoDaddy, Namecheap ou d'un fournisseur unique.

## Ton autonomie

Ne te contente pas d'exécuter une liste de fichiers ou de rédiger un nouveau plan. Analyse, tranche, implémente et vérifie. Tu peux profondément restructurer et supprimer l'obsolète. Réutilise les composants corrects plutôt que réécrire par principe. Le dépôt actuel et son historique sont conservés ; travaille sur une branche d'implémentation dédiée issue du cadrage DoName.

Choisis toi-même la structure, les noms exacts des outils, les bibliothèques et l'organisation des tests. Python est le point de départ existant, pas un dogme. Un changement de langage doit démontrer un bénéfice réel d'installation, de fiabilité ou de maintenance dans une courte décision d'architecture. Ne construis pas de microservices, de grosse interface, de base vectorielle ou de couche d'abstraction spéculative.

Pour les décisions réversibles, prends l'option la plus simple et explique-la brièvement. N'interromps pas le travail pour chaque préférence technique. Un blocage d'accès externe doit produire une limite exacte et un mode de repli honnête, pas une fausse intégration. Ne contourne aucune permission ni validation de l'hôte.

## Le socle à corriger en priorité

L'audit a relevé plusieurs problèmes de sens dans les données. Reproduis-les par des tests, puis corrige-les avant de développer la présentation :

- Un NXDOMAIN DNS ne signifie pas que le domaine est enregistrable.
- Un 404 RDAP ne signifie pas « disponible à l'achat ».
- Un refus de registrar ne signifie pas « déjà enregistré ».
- RDAP sans objet et registrar qui refuse ne constituent pas automatiquement une contradiction.
- Une réponse fournisseur incomplète ou mal typée n'est pas un résultat négatif valide.
- Timeout, quota, extension non couverte et erreur de réseau ne doivent jamais devenir une disponibilité confirmée.

Sépare observations DNS, état d'enregistrement et possibilité d'enregistrement auprès d'une source. Préserve la provenance, le moment du contrôle, la fraîcheur, la couverture et les raisons d'exclusion. Les sources peuvent être corrélées : pas de vote naïf présenté comme une probabilité scientifique. Ne promets pas une disponibilité universelle sans accès approprié aux services qui peuvent la confirmer.

Un mode sans clé doit rester utile et expliquer ce qu'il peut établir : éliminer des noms enregistrés, signaler une absence de résultat, préparer une shortlist à confirmer. **Mais le parcours V1 principal doit également prévoir une vraie vérification provider lorsque celle-ci est configurée/disponible.** Ne cache pas les limites du mode sans clé pour imiter une réponse de registrar. Ne dégrade pas non plus toutes les réponses en « inconnu » lorsqu'une preuve de registration valide existe. Les éventuels prix inconnus ne valent ni zéro ni conformité à un budget. Représente séparément prix d'enregistrement et prix de renouvellement lorsque la source les fournit, avec devise, provider et instant de vérification.

## Le parcours de recherche de noms

Conçois quelques opérations cohérentes : diagnostic des capacités, contrôle d'un ensemble de domaines exacts, filtrage de candidats sur plusieurs extensions. Évite les doublons et les dizaines d'outils de bas niveau. Un résultat doit permettre à l'IA de répondre sans relancer une requête pour chaque détail.

Gère au minimum noms exacts, noms de base, doublons, casse, entrées vides ou invalides, IDNA/Unicode et suffixes à plusieurs niveaux. Distingue suffixe public et niveau enregistrable ; ne suppose pas que toute chaîne contenant un point est un domaine valide à enregistrer. Définis une politique claire pour les sous-domaines, les adresses IP, les URL, les ports et les caractères trompeurs. Rejette les entrées dangereuses avant toute requête.

Respecte les contraintes du brief. Si `.com` ET `.fr` sont demandés, groupe les résultats par candidat et applique ce ET. Ne présente pas une seule extension favorable comme la réussite du candidat complet. Si la condition est « au moins une de ces extensions », distingue-la explicitement. Conserve des explications courtes pour les exclusions et les cas non vérifiés.

Le skill doit aider l'IA à produire une première sélection, consulter DoName par lots bornés, améliorer les candidats dans une boucle limitée et expliquer ses recommandations. Sépare qualité créative subjective, conformité mesurable et état des domaines. Aucune « note de marque » présentée comme une vérité objective. Aucune prétendue vérification juridique ou de marque déposée. Les exemples de documentation sont synthétiques et explicitement non vérifiés en direct.

## Un plugin, pas seulement un script

Utilise un SDK MCP officiellement pris en charge. Vérifie sa version et ses API actuelles ; ne conserve pas une dépendance simplement parce que le README l'annonce. Prévois un moteur commun, un transport local stdio et un transport HTTP auto-hébergeable/servable pour les hôtes distants. Les sorties stdout du transport stdio ne doivent pas être polluées par des logs.

**Prévois une expérience UI compacte dans le chat lorsque l'hôte supporte MCP Apps / UI resources.** L'objectif est proche de l'ergonomie observée avec les plugins de domaines : cartes ou liste compacte avec nom, extension, disponibilité, prix d'enregistrement, renouvellement si connu, provider, fraîcheur et actions utiles. Les filtres peuvent notamment couvrir « disponibles uniquement », TLD obligatoire, budget et comparaison. Ne crée pas un gros dashboard. Le même résultat doit rester pleinement exploitable en données structurées/texte dans Codex, Claude ou tout hôte sans UI riche.

Prépare les skills et le packaging réellement compatibles avec les hôtes visés en consultant leurs documentations officielles actuelles. Ne suppose pas qu'un seul manifeste fonctionne partout. ChatGPT web, ChatGPT desktop, Codex CLI/IDE, Claude Code et les connecteurs distants doivent être distingués dans la matrice de compatibilité.

La documentation OpenAI distingue actuellement connexion locale, MCP distant, tunnel privé de développement et publication publique. Teste ce qui est effectivement accessible ; ne présente ni une configuration copiée ni un tunnel de développement comme un plugin publié. Aucun serveur DoName central ne doit devenir obligatoire pour les usages locaux. En revanche, conçois proprement le chemin d'un **DoName remote MCP exploitable par un plugin ChatGPT public**, où les credentials provider peuvent être conservés côté serveur plutôt que demandés à chaque utilisateur. Ce chemin distant reste séparé de l'exécution locale/self-hosted et aucun déploiement public ne doit être effectué silencieusement dans cette mission.

Chaque outil doit avoir une description exploitable, des schémas d'entrée/sortie, des limites et des annotations de sécurité exactes. Une opération de lecture externe n'est pas une opération sans échanges externes. Retourne des données compactes et un résumé lisible, avec assez d'éléments pour justifier le résultat. Conserve une CLI de diagnostic sans en faire le produit principal.

## Confidentialité et sécurité

Le code est public ; les briefs, domaines candidats, historiques et clés ne le sont pas. Aucun domaine recherché, prompt réel ou jeton dans Git, fixtures, issues, captures, artefacts CI ou rapports de test publics. Aucune télémétrie ni conservation de recherches par défaut. Documente les sorties réseau et les destinataires ; la confidentialité n'efface pas la visibilité de l'IA hôte ou du service interrogé.

N'envoie aux fournisseurs que les domaines strictement nécessaires, jamais le brief. Ne fais pas de crawling arbitraire des pages des domaines proposés. L'aftermarket/broker en V1 doit venir de sources explicites et bornées si tu l'implémentes, pas d'un fetch libre du site cible. Pas d'URL arbitraire fournie par le modèle pour choisir un endpoint. Valide les destinations autorisées, redirections et réponses ; protège les accès internes et les métadonnées d'infrastructure. Les tests de sécurité utilisent des doubles locaux/mocks, pas des cibles tierces.

Pour HTTP : limite l'exposition par défaut, documente le modèle d'authentification applicable, protège contre les abus et isole les données entre utilisateurs. Vérifie aussi les logs du proxy, de l'hébergement et des exceptions. Ne prétends pas à une confidentialité de production sans avoir examiné ce déploiement. Les identifiants ne doivent jamais passer dans les prompts ou résultats des outils.

Garde les caches courts et bornés ; sépare les métadonnées publiques de référence des recherches privées. Respecte les quotas et `Retry-After`, définis des délais globaux, limite le nombre de candidats, la concurrence et la taille des réponses. Un batch doit pouvoir rendre un résultat partiel compréhensible plutôt que bloquer indéfiniment. Ne multiplie pas les services interrogés seulement pour gonfler un score de confiance.

## Exécution attendue

Commence par un état initial concis : architecture existante, problèmes confirmés, tests réellement exécutables et ce que tu gardes ou remplaces. Puis avance par tranches fonctionnelles avec des commits cohérents. Ne t'arrête pas à l'audit : livre un parcours réel allant d'une requête MCP à des preuves structurées et à une sélection exploitable.

Réconcilie README, package, commandes, anciennes déclarations d'outils et documentation. La marque devient DoName. Vérifie les noms de packages avant de proposer une commande d'installation publique. Préserve MIT et les attributions. Distingue DoName V1 de l'ancienne numérotation IsDomainOK 2.1.0. Ne publie pas de package, ne renomme pas le dépôt distant, ne déploie pas de service et ne fusionne pas dans main au titre de cette seule mission.

Tiens la mémoire du projet à jour : décisions retenues, fonctionnalités réellement livrées, limites et prochaines étapes, sans données privées. Ne crée pas dix documents qui se contredisent. Conserve une référence claire au cadrage et à la migration.

## Critères de fin

La livraison n'est pas terminée parce que le README est joli. Elle doit démontrer :

1. Des tests de non-régression pour les erreurs de disponibilité et de validation mentionnées ci-dessus, y compris extension non couverte, données incomplètes, quotas, délais et cas contradictoires.
2. Un mode sans clé utile, borné et transparent, **plus une architecture provider et au moins un chemin d'intégration live viable pour disponibilité/prix**, avec tests contractuels/mocks et test réel seulement si des credentials/environnements autorisés sont disponibles.
3. Un parcours de noms multi-extensions correctement groupé, avec exclusions expliquées, résultats non vérifiés identifiables et contraintes ET/OU testées.
4. Un véritable échange MCP initialize/list_tools/call_tool et des contrats cohérents entre transports, pas seulement un import Python ou des appels directs aux fonctions.
5. Des contrôles sur les entrées, sorties réseau, fuites de logs et isolation ; aucune visite automatique des domaines proposés.
6. Une installation depuis un checkout propre ou un artefact construit, avec contrôle du contenu distribué, notamment des skills/configurations nécessaires.
7. Une matrice honnête : implémenté, testé automatiquement, essayé dans l'hôte, publication requise. Une fixture ou un test mocké n'est pas un test de fournisseur réel.
8. Des mesures reproductibles sur un corpus synthétique : latence du moteur, appels externes simulés, taille des résultats, limites de batch. Les objectifs choisis ne doivent pas être présentés comme des résultats déjà acquis. Sépare latence locale, temps réseau et délai du modèle.
9. Une UI chat compacte lorsque la plateforme ciblée la supporte, avec fallback structuré/texte complet ; ne considère pas la V1 terminée si l'intégration « plugin » n'est qu'un serveur JSON sans parcours utilisateur démontrable.

À la fin, donne les changements réels, les choix importants et leurs raisons, les commandes de test et leurs résultats exacts, les plateformes effectivement testées, les limites restantes, la branche/les commits et le chemin le plus court pour essayer DoName. Ouvre une PR de revue si l'accès le permet, sans fusion automatique. S'il reste un blocage, livre ce qui fonctionne et identifie précisément ce qui manque, sans inventer une réussite et sans reléguer silencieusement la V1 à un squelette.
