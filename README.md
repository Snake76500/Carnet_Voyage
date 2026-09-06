# 🌍 Carnet de Voyage (Esprit Polarsteps)

Un site web personnel de carnet de voyage interactif inspiré de **Polarsteps** : journal de bord chronologique par étapes, photos, vidéos YouTube et carte interactive synchronisée traçant l'itinéraire parcouru au fil des jours.

---

## ✨ Fonctionnalités Principales

- 🗺️ **Carte Interactive Synchronisée** : propulsée par **Leaflet.js** et **OpenStreetMap** (100% gratuit, sans aucune clé API payante).
  - Tracé animé du parcours (effet « chemin parcouru » avec animation pointillée).
  - Marqueurs numérotés cliquables pour chaque étape.
  - Synchronisation bidirectionnelle : survoler une étape dans le journal centre la carte ; cliquer sur un marqueur fait défiler la timeline jusqu'à l'étape.
- 📖 **Journal Quotidien (Day Entries)** :
  - Récit rédigé en Markdown riche (titres, listes, mise en valeur).
  - Date, nom du lieu et coordonnées GPS précises.
  - Sélecteur de position interactif sur mini-carte Leaflet avec géocodage inverse.
- 📸 **Médias par Étape** :
  - **Photos** : Liens directs ou liens partagés **Google Drive** (convertis automatiquement en aperçus haute résolution avec lien de secours).
  - **Vidéos** : Liens **YouTube** intégrés en iframe responsive.
  - Plusieurs médias par étape ordonnés avec légendes.
- 🔒 **Gestion Public / Privé & Partage** :
  - Option pour rendre un voyage public en lecture seule via un lien direct partageable.
- 📱 **Design Moderne & Responsive** :
  - Palette soignée et design épuré inspiré des meilleures applications de voyage.
  - Double panneau (Timeline à gauche, Carte sticky à droite sur grand écran).
  - Lightbox plein écran pour agrandir les photos.

---

## ⚠️ Points d'Attention Techniques Importants

### 1. Vidéos YouTube : « Non répertorié » (Unlisted)
> [!IMPORTANT]
> Une vidéo YouTube configurée en **Privé** n'est visible que par le compte Google propriétaire connecté — elle renverra une erreur d'accès si intégrée en `<iframe>` pour les visiteurs externes ou en navigation privée.
> **Pour un affichage fonctionnel :** Réglez impérativement vos vidéos YouTube en **« Non répertorié » (Unlisted)**. La vidéo reste invisible dans les moteurs de recherche YouTube mais s'affichera parfaitement dans votre carnet de voyage.

### 2. Photos Google Drive : Partage public du lien
> [!TIP]
> Pour que les photos hébergées sur Google Drive s'affichent directement en `<img>`, le fichier doit avoir son accès réglé sur **« Tous les utilisateurs disposant du lien »**. L'application convertit automatiquement l'URL Drive en lien de miniature haute résolution (`https://drive.google.com/thumbnail?id=FILE_ID&sz=w1200`). Un lien de secours « Voir sur Google Drive » est également proposé.

---

## 🚀 Démarrage Rapide

### Option A : Lancement Local (Développement avec SQLite ou PostgreSQL)

1. **Installer les dépendances Python :**
   ```bash
   pip install -r requirements.txt
   ```

2. **Lancer le serveur de développement :**
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

3. **Accéder à l'application :**
   - Application Web : [http://localhost:8000](http://localhost:8000)
   - Documentation interactive de l'API (Swagger UI) : [http://localhost:8000/docs](http://localhost:8000/docs)

*Note : Au premier lancement, des voyages de démonstration (Islande et Japon) avec coordonnées réelles et médias sont automatiquement créés pour vous permettre de tester immédiatement.*

4. **Comptes utilisateurs & Rôles :**
   - **Administrateur** : `admin` / `admin123` (Création, édition et suppression de voyages et étapes).
   - **Invité** : `invite` / `voyage123` (Consultation des voyages privés et publics en lecture seule).
   - **Visiteur anonyme** : Accès uniquement aux voyages configurés comme « Public ».
   - Page de connexion : [http://localhost:8000/login](http://localhost:8000/login)

---

### Option B : Déploiement avec Docker Compose (Production / PostgreSQL)

1. **Copier le fichier d'environnement (optionnel si réglages par défaut) :**
   ```bash
   cp .env.example .env
   ```

2. **Démarrer les conteneurs (FastAPI + PostgreSQL 16) :**
   ```bash
   docker-compose up -d --build
   ```

3. **Vérifier les logs :**
   ```bash
   docker-compose logs -f web
   ```

4. **Arrêter l'environnement :**
   ```bash
   docker-compose down
   ```

---

## 🗄️ Structure de la Base de Données & Migrations

- **Trip** : `id`, `title`, `slug`, `description`, `start_date`, `end_date`, `cover_image_url`, `is_public`, `created_at`
- **DayEntry** : `id`, `trip_id`, `date`, `title`, `body_markdown`, `location_name`, `latitude`, `longitude`, `order_index`, `created_at`
- **Media** : `id`, `day_entry_id`, `type` (`photo` | `video`), `url`, `caption`, `order_index`

### Exécuter les migrations Alembic :
```bash
python -m alembic upgrade head
```

---

## 📁 Architecture du Code

```
Site-Voyage/
├── app/
│   ├── core/
│   │   ├── config.py              # Configuration Pydantic Settings
│   │   └── database.py            # Session SQLAlchemy & Base declarative
│   ├── models/
│   │   └── trip.py                # Modèles Trip, DayEntry, Media
│   ├── schemas/
│   │   └── trip.py                # Schémas Pydantic (validation & API)
│   ├── services/
│   │   ├── media_helpers.py       # Parsers Google Drive & YouTube, Markdown renderer
│   │   └── seed_data.py           # Données de démo riches (Islande & Japon)
│   ├── routers/
│   │   ├── web.py                 # Vues HTML / Jinja2 (Accueil, Voyage, Formulaires)
│   │   └── api.py                 # API REST JSON & GeoJSON pour Leaflet
│   ├── static/
│   │   ├── css/style.css          # Design system complet (Polarsteps aesthetic)
│   │   └── js/
│   │       ├── map.js             # Leaflet, tracé animé et synchro timeline
│   │       └── entry_picker.js    # Mini-carte Leaflet pour sélection GPS
│   ├── templates/
│   │   ├── base.html              # Template racine
│   │   ├── index.html             # Page d'accueil (Grille des voyages)
│   │   ├── trip_detail.html       # Vue principale : Timeline + Carte synchronisée
│   │   ├── trip_form.html         # Création/Édition de voyage
│   │   └── entry_form.html        # Création/Édition d'étape avec carte GPS
│   └── main.py                    # Point d'entrée FastAPI
├── alembic/                       # Migrations SQLAlchemy
├── Dockerfile                     # Image Docker FastAPI
├── docker-compose.yml             # Orchestration FastAPI + PostgreSQL
├── requirements.txt               # Dépendances Python
└── README.md
```
