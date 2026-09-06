import os
from datetime import date
from sqlalchemy.orm import Session
from app.models.trip import Trip, DayEntry, Media
from app.models.user import User
from app.core.security import hash_password

def seed_users(db: Session):
    """Seed initial admin and guest accounts if not present."""
    admin_username = os.getenv("ADMIN_USERNAME", "admin")
    admin_password = os.getenv("ADMIN_PASSWORD", "admin123")
    guest_username = os.getenv("GUEST_USERNAME", "invite")
    guest_password = os.getenv("GUEST_PASSWORD", "voyage123")

    admin = db.query(User).filter(User.username == admin_username).first()
    if not admin:
        admin = User(
            username=admin_username,
            hashed_password=hash_password(admin_password),
            role="admin",
            is_active=True
        )
        db.add(admin)

    guest = db.query(User).filter(User.username == guest_username).first()
    if not guest:
        guest = User(
            username=guest_username,
            hashed_password=hash_password(guest_password),
            role="guest",
            is_active=True
        )
        db.add(guest)

    db.commit()

def create_demo_data(db: Session):
    # Ensure default users exist
    seed_users(db)

    # Check if demo trip already exists
    existing = db.query(Trip).filter(Trip.slug == "roadtrip-islande-route-1").first()
    if existing:
        return existing


    # 1. Iceland Roadtrip
    trip = Trip(
        title="Road Trip en Islande : L'Anneau d'Or & Route 1",
        slug="roadtrip-islande-route-1",
        description="Une aventure inoubliable de 10 jours à travers les paysages volcaniques, les cascades majestueuses et les lagons glaciaires d'Islande.",
        start_date=date(2025, 6, 12),
        end_date=date(2025, 6, 22),
        cover_image_url="https://images.unsplash.com/photo-1504893524553-b855bce32c67?auto=format&fit=crop&w=1600&q=80",
        is_public=True
    )
    db.add(trip)
    db.flush()

    # Step 1: Reykjavik & Blue Lagoon
    step1 = DayEntry(
        trip_id=trip.id,
        date=date(2025, 6, 12),
        title="Arrivée à Reykjavík & Détente au Lagon Bleu",
        location_name="Reykjavík, Islande",
        latitude=64.1466,
        longitude=-21.9426,
        order_index=1,
        body_markdown="""### Premier contact avec la terre de feu et de glace

Atterrissage à l'aéroport de Keflavík sous un ciel d'été lumineux (le soleil de minuit commence déjà !). Après avoir récupéré notre 4x4 équipé pour l'aventure, premier arrêt incontournable : les eaux chaudes et laiteuses du Blue Lagoon. 

En soirée, balade colorée dans les rues de **Reykjavík**, montée au sommet de l'église *Hallgrímskirkja* pour admirer la vue panoramique sur les toits colorés et l'océan Atlantique.

**Points forts de la journée :**
- Bain à 38°C sous une brise fraîche islandaise
- Dégustation d'un délicieux *Kjötsúpa* (soupe d'agneau traditionnelle)
- Préparation de l'itinéraire pour le Cercle d'Or le lendemain.
"""
    )
    db.add(step1)
    db.flush()

    db.add_all([
        Media(
            day_entry_id=step1.id,
            type="photo",
            url="https://images.unsplash.com/photo-1529963183134-61a90db47eaf?auto=format&fit=crop&w=1200&q=80",
            caption="L'église Hallgrímskirkja dominant la capitale Reykjavík",
            order_index=1
        ),
        Media(
            day_entry_id=step1.id,
            type="video",
            url="https://www.youtube.com/watch?v=dQw4w9WgXcQ", # Demo video link
            caption="Ambiance au coucher de soleil à Reykjavík",
            order_index=2
        )
    ])

    # Step 2: Gullfoss & Geysir (Golden Circle)
    step2 = DayEntry(
        trip_id=trip.id,
        date=date(2025, 6, 14),
        title="Le Cercle d'Or : Geysers rugissants & Chute de Gullfoss",
        location_name="Geysir & Gullfoss",
        latitude=64.3138,
        longitude=-20.3024,
        order_index=2,
        body_markdown="""### Les forces brutes de la nature

Départ matinal pour le célèbre **Cercle d'Or**. Première halte à *Þingvellir*, où la faille entre les plaques tectoniques nord-américaine et eurasienne est béante.

Ensuite, direction la zone géothermique de **Geysir**. Le geyser *Strokkur* entre en éruption toutes les 6 à 10 minutes avec une précision chirurgicale, projetant une colonne d'eau bouillante à plus de 20 mètres !

Quelques kilomètres plus loin, le grondement assourdissant de la chute de **Gullfoss** (la Chute Dorée) nous laisse sans voix. La puissance du débit glaciaire est saisissante.
"""
    )
    db.add(step2)
    db.flush()

    db.add(
        Media(
            day_entry_id=step2.id,
            type="photo",
            url="https://images.unsplash.com/photo-1517411032315-54ef2cb783bb?auto=format&fit=crop&w=1200&q=80",
            caption="L'incroyable puissance des chutes de Gullfoss",
            order_index=1
        )
    )

    # Step 3: Seljalandsfoss & Skógafoss
    step3 = DayEntry(
        trip_id=trip.id,
        date=date(2025, 6, 16),
        title="La Côte Sud : Cascades légendaires et Plage de sable noir",
        location_name="Vík í Mýrdal & Skógafoss",
        latitude=63.5321,
        longitude=-19.5112,
        order_index=3,
        body_markdown="""### Entre falaises verdoyantes et sable noir volcanique

Nous prenons la Route 1 vers le sud. Premier arrêt : **Seljalandsfoss**, où l'on peut littéralement marcher *derrière* le rideau d'eau (penser au k-way étanche !). 

Puis, **Skógafoss**, un mur d'eau parfait de 60 mètres où un double arc-en-ciel apparaît avec la brume. 

Nous terminons la journée sur la mystique plage de sable noir de **Reynisfjara** à Vík, face aux pitons rocheux des trolls légendaires défiant les vagues tumultueuses de l'Atlantique Nord.
"""
    )
    db.add(step3)
    db.flush()

    db.add_all([
        Media(
            day_entry_id=step3.id,
            type="photo",
            url="https://images.unsplash.com/photo-1476610182048-b716b8518aae?auto=format&fit=crop&w=1200&q=80",
            caption="Reynisfjara et ses orgues basaltiques",
            order_index=1
        ),
        Media(
            day_entry_id=step3.id,
            type="photo",
            url="https://images.unsplash.com/photo-1509316975850-ff9c5deb0cd9?auto=format&fit=crop&w=1200&q=80",
            caption="La chute de Skógafoss vue de face",
            order_index=2
        )
    ])

    # Step 4: Jökulsárlón Glacier Lagoon
    step4 = DayEntry(
        trip_id=trip.id,
        date=date(2025, 6, 19),
        title="Jökulsárlón & Diamond Beach : Au cœur des glaces",
        location_name="Jökulsárlón, Vatnajökull",
        latitude=64.0484,
        longitude=-16.1795,
        order_index=4,
        body_markdown="""### Le clou du spectacle : les icebergs étincelants

Une journée magique au bord du lagon glaciaire de **Jökulsárlón**, au pied du colossal glacier Vatnajökull. Des blocs de glace millénaires bleutés se détachent lentement et dérivent vers l'océan.

De l'autre côté du pont, sur **Diamond Beach**, les morceaux de glace polis par les vagues reposent sur le sable noir comme de véritables diamants géants sculptés par la mer. Nous avons même aperçu des phoques curieux nageant entre les icebergs !
"""
    )
    db.add(step4)
    db.flush()

    db.add(
        Media(
            day_entry_id=step4.id,
            type="photo",
            url="https://images.unsplash.com/photo-1518709268805-4e9042af9f23?auto=format&fit=crop&w=1200&q=80",
            caption="Icebergs flottant sur le lagon de Jökulsárlón",
            order_index=1
        )
    )

    # 2. Second trip: Japan
    trip2 = Trip(
        title="Japon : Des Néons de Tokyo aux Temples de Kyoto",
        slug="japon-tokyo-kyoto-2024",
        description="Une traversée en Shinkansen entre modernité futuriste, sanctuaires shintoïstes secrets et gastronomie raffinée.",
        start_date=date(2024, 10, 5),
        end_date=date(2024, 10, 20),
        cover_image_url="https://images.unsplash.com/photo-1493976040374-85c8e12f0c0e?auto=format&fit=crop&w=1600&q=80",
        is_public=True
    )
    db.add(trip2)
    db.flush()

    step_jp1 = DayEntry(
        trip_id=trip2.id,
        date=date(2024, 10, 6),
        title="Tokyo : Shinjuku, Shibuya & Temple Senso-ji",
        location_name="Tokyo, Japon",
        latitude=35.6762,
        longitude=139.6503,
        order_index=1,
        body_markdown="Arrivée dans la mégapole tokyoïte. Émerveillement immédiat au carrefour de Shibuya et immersion paisible à Asakusa."
    )
    step_jp2 = DayEntry(
        trip_id=trip2.id,
        date=date(2024, 10, 12),
        title="Kyoto : Les 10 000 Torii de Fushimi Inari",
        location_name="Kyoto, Japon",
        latitude=34.9671,
        longitude=135.7727,
        order_index=2,
        body_markdown="Montée matinale à travers les tunnels de torii vermillon de Fushimi Inari, suivie d'une visite du Pavillon d'Or Kinkaku-ji."
    )
    db.add_all([step_jp1, step_jp2])

    db.commit()
    db.refresh(trip)
    return trip
