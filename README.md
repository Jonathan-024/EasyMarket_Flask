# Réservation Boutique (MVP)

## Variables d'environnement (obligatoires en prod)
- SECRET_KEY=une_chaine_secrete
- ORANGE_CLIENT_ID=...
- ORANGE_CLIENT_SECRET=...
- ORANGE_SENDER=+243XXXXXXXXX
- ONESIGNAL_APP_ID=...
- ONESIGNAL_API_KEY=...

## Démarrage local
python -m venv venv
source venv/bin/activate  # (Windows: venv\Scripts\activate)
pip install -r requirements.txt
export FLASK_APP=app.py
flask run

## Build/Prod local
gunicorn app:app -b 0.0.0.0:8000