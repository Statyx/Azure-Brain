# Demo Runbook — Live DB-only + App refactor en pitch

> **Cible démo** : 20 min en live, prospect technique mixte (DBA + archi).
> **Posture** : tu maîtrises 100 % de ce que tu montres. Tout ce qui est risqué (refactor Java IA) est raconté, pas joué.
> **Stack démo** : Oracle XE 21c (VM) → Ora2Pg → PostgreSQL Flex 16 → ouverture VS Code.

---

## Préparation J-1 (30 min, à blanc)

### Pré-requis validés
- [ ] VM Oracle déployée, listener UP, schéma `HR` chargé (`employees`, `departments`, `jobs`)
- [ ] PG Flex 16 déployé, base `petclinic_demo` créée, Entra auth ON
- [ ] Ora2Pg installé sur la VM Oracle (ou poste démo) — `ora2pg --version` répond
- [ ] Extension VS Code `ms-ossdata.vscode-pgsql` installée
- [ ] Connexion PG enregistrée dans l'extension (avec ton user Entra)
- [ ] Tab terminal split : 1 onglet Oracle (SSH VM), 1 onglet local (PG counts)
- [ ] Script `ora2pg.conf` prêt dans `Database-Brain/agents/03-oracle-to-postgres/oracle-to-postgres-migration-agent/config/`
- [ ] Onglet browser ouvert sur Azure Portal → PG Flex (pour montrer la fiche resource)

### Répétition obligatoire
Fais le run complet **1 fois la veille** sur ta vraie démo. Chronomètre. Si > 25 min, coupe quelque chose.

---

## Déroulé live (15-20 min)

### 0. Intro contexte (1 min)
> "Je vais vous montrer la **migration de schéma + data** d'Oracle vers PostgreSQL Azure en live. Pour la partie modernisation du code applicatif Java qui parle à cette base, je vous en parle en fin de démo — c'est une autre étape, faite par d'autres outils."

### 1. Show the source — Oracle (2 min)
Terminal Oracle :
```bash
sqlplus hr/<password>@//localhost:1521/XEPDB1
SELECT COUNT(*) FROM employees;     -- ~107
SELECT COUNT(*) FROM departments;   --  27
SELECT COUNT(*) FROM jobs;          --  19
SELECT * FROM employees WHERE rownum <= 3;
EXIT;
```
**Message** : "Schéma HR classique, 3 tables, ~150 lignes. Suffisant pour la démo de principe — en prod on parle de milliers de tables, mais le pattern est le même."

### 2. Show the target — PostgreSQL vide (1 min)
Bascule sur VS Code → extension PostgreSQL → ton serveur Flex → base `petclinic_demo` → Object Explorer.
> "Base vide, prête à recevoir le schéma migré."

Optionnel : montre la fiche Azure Portal du PG Flex (HA, backup, Entra). 30 sec max.

### 3. Migration Ora2Pg (5 min — le cœur)

Terminal Oracle :
```bash
cd ~/ora2pg-demo
cat ora2pg.conf | grep -E "^(ORACLE_DSN|PG_DSN|TYPE|SCHEMA)"
```
> "La config tient en 6 lignes. Ora2Pg connaît les particularités Oracle (SEQUENCE.NEXTVAL, DUAL, ROWNUM…) et les traduit."

Lance la migration schéma :
```bash
ora2pg -c ora2pg.conf -t TABLE -o schema.sql
ora2pg -c ora2pg.conf -t COPY -o data.sql
```

Montre rapidement les fichiers (head -30) :
```bash
head -20 schema.sql
head -10 data.sql
```

Applique sur PG :
```bash
psql "host=<pg-flex>.postgres.database.azure.com user=<entra-user> dbname=petclinic_demo sslmode=require" -f schema.sql
psql "..." -f data.sql
```
> "Migration faite. Schéma + données dans PG en 30 secondes pour ce volume."

### 4. Validation row counts (2 min — le moment de vérité)

Terminal local PowerShell ou onglet PG :
```sql
SELECT 'employees' AS table, COUNT(*) FROM employees
UNION ALL SELECT 'departments', COUNT(*) FROM departments
UNION ALL SELECT 'jobs', COUNT(*) FROM jobs;
```
Compare visuellement avec les chiffres de l'étape 1.
> "Mêmes counts. Migration validée."

### 5. PG VS Code extension — wow effect (4 min)

Dans VS Code, sur ta connexion PG :
- Object Explorer → expand `petclinic_demo` → `schemas` → `hr` → `tables` → click droit sur `employees` → **Select Top 100**
- Montre la grille de résultats inline (familier pour SSMS / TOAD users)
- Click droit sur `employees` → **Generate CREATE script** → montre le SQL généré
- Ouvre un fichier `.sql` vierge → tape `SELECT ` → montre l'IntelliSense colonnes

**Si Copilot Chat dispo** :
- Cmd palette → `@pgsql` → "Show me the top 5 employees by salary"
- Montre le SQL généré + exécution

> "L'extension est gratuite, sortie en 2026, et remplace pgAdmin pour 80 % des usages quotidiens. Object Explorer + IntelliSense + Copilot intégré."

### 6. Pitch app modernization (3 min — narratif, zéro clic)

Reste sur VS Code, ouvre un dossier Java (peu importe le contenu) ou juste l'onglet Marketplace avec l'extension "GitHub Copilot App Modernization for Java" visible.

> "Maintenant, la base est migrée. Mais votre app Java qui parlait à Oracle utilise encore du SQL spécifique Oracle : `SYSDATE`, `ROWNUM`, `SEQUENCE.NEXTVAL`, `DUAL`. Il faut la refactorer.
>
> Microsoft a sorti en 2026 une **extension GitHub Copilot App Modernization for Java** qui fait ça automatiquement. Elle :
> 1. Lit les notes de migration générées par l'extension PostgreSQL que je viens de vous montrer (fichier `coding_notes.md`)
> 2. Refactore les requêtes JDBC / JPA Oracle → PostgreSQL
> 3. Bascule la connexion sur **Azure Managed Identity** (zéro mot de passe en config)
> 4. Génère les tests `Testcontainers` pour valider en local
>
> C'est l'autre moitié du puzzle. Sur un projet réel, on enchaîne les 2 dans le même sprint : migration DB d'abord, refactor code juste après. Si vous avez un cas Java concret, on peut faire un atelier dédié là-dessus."

### 7. Wrap-up (1 min)
> "Récap : Oracle → PG migré en 30 sec d'exécution, validé en row counts, exploré dans VS Code moderne. Pour aller plus loin sur le code applicatif, l'outillage 2026 est là. Questions ?"

---

## Fallback si quelque chose casse

| Si... | Alors... |
|---|---|
| Connexion Oracle KO | Tu as un dump SQL pré-fait → "On va simuler à partir d'un dump pour gagner du temps" |
| Ora2Pg plante | Tu as les `schema.sql` et `data.sql` pré-générés sous la main → tu les appliques directement |
| PG Flex injoignable (network) | Bascule sur Postgres local Docker (`docker run -p 5432:5432 postgres:16`) — même démo, même résultat |
| Extension PG bug | Skip étape 5, va direct au pitch — pas grave |

---

## Ce que tu ne dis JAMAIS en démo

- "Je ne suis pas à l'aise sur Java" → dis "Je préfère vous montrer l'expert tooling de Microsoft sur ce sujet en atelier dédié"
- "Je n'ai pas testé en prod" → dis "Sur des volumes plus importants, on ajoute du tuning Ora2Pg : parallélisme, batching, exclusion de tables"
- "Je sais pas" → "Bonne question, je reviens vers vous demain avec la réponse précise"

---

## Après la démo — questions probables

| Question prospect | Réponse courte |
|---|---|
| "Et les triggers / packages PL/SQL ?" | "Ora2Pg les traduit en PL/pgSQL, taux de réussite ~70-80 %. Le reste = revue manuelle." |
| "Combien de temps sur une vraie migration ?" | "Variable : 2 semaines pour une centaine de tables simples, plusieurs mois si beaucoup de PL/SQL. L'audit Ora2Pg donne une estimation initiale." |
| "Downtime ?" | "Zéro downtime possible avec Oracle GoldenGate ou Azure DMS en mode online. Ora2Pg seul = downtime court (la fenêtre de bascule)." |
| "Coût licence ?" | "Ora2Pg = open source gratuit. PG Flex = pay-as-you-go Azure. Vs licence Oracle EE = ROI immédiat." |
| "Et la sécurité ?" | "Entra ID auth + Managed Identity côté app = zéro credential en clair. C'est ce que l'extension App Modernization configure automatiquement." |

---

## Checklist J-J (1h avant)

- [ ] VM Oracle UP (`az vm start` si éteinte)
- [ ] Listener Oracle répond (`tnsping`)
- [ ] PG Flex joignable (`psql` test connexion)
- [ ] Base PG vide (DROP/CREATE si reste de répétition)
- [ ] VS Code ouvert avec connexion PG active
- [ ] Terminaux pré-positionnés dans les bons dossiers
- [ ] Police terminal en taille démo (16pt min)
- [ ] Mode présentation activé (notifs OFF)
- [ ] Backup `schema.sql` + `data.sql` sur le bureau au cas où
