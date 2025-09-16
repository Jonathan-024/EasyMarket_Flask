import os

# Chemin de base du projet (où se trouve config.py)
basedir = os.path.abspath(os.path.dirname(__file__))

# Créer le dossier instance automatiquement si inexistant
instance_path = os.path.join(basedir, 'instance')
if not os.path.exists(instance_path):
    os.makedirs(instance_path)

class Config:
    # Clé secrète pour Flask
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev_secret_change_me')

    # Base de données SQLite
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL',
        'sqlite:///' + os.path.join(instance_path, 'reservation.db')
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Uploads
    UPLOAD_FOLDER = os.path.join(basedir, 'static', 'uploads')
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

    # Orange RDC SMS
    ORANGE_CLIENT_ID = os.environ.get('ORANGE_CLIENT_ID')
    ORANGE_CLIENT_SECRET = os.environ.get('ORANGE_CLIENT_SECRET')
    ORANGE_SENDER = os.environ.get('ORANGE_SENDER')  # format +243XXXXXXXXX

    # OneSignal
    ONESIGNAL_APP_ID = os.environ.get('ONESIGNAL_APP_ID')
    ONESIGNAL_API_KEY = os.environ.get('ONESIGNAL_API_KEY')
