from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class Vendeur(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    telephone = db.Column(db.String(20), nullable=False)
    mot_de_passe_hash = db.Column(db.String(200), nullable=False)
    boutique = db.Column(db.String(150), nullable=False)

    def set_password(self, password):
        self.mot_de_passe_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.mot_de_passe_hash, password)

class Reservation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    client_nom = db.Column(db.String(100), nullable=False)
    client_telephone = db.Column(db.String(20), nullable=False)
    produits = db.Column(db.Text, nullable=True)                 # "Huile | 1L; Riz | 2kg"
    image_liste = db.Column(db.String(255), nullable=True)       # chemin vers l'image
    vendeur_id = db.Column(db.Integer, db.ForeignKey('vendeur.id'), nullable=False)
    heure_retrait = db.Column(db.Time, nullable=False)
    date_reservation = db.Column(db.DateTime, default=datetime.utcnow)
    retire = db.Column(db.Boolean, default=False)
    code_retrait = db.Column(db.String(10), nullable=False)

    vendeur = db.relationship('Vendeur', backref='reservations')