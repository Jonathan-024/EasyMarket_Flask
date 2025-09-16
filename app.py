import os, random, string, base64, requests
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.utils import secure_filename
from models import db, Vendeur, Reservation
from config import Config

def create_app():
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(Config)

    # ✅ Création automatique du dossier instance/
    os.makedirs(app.instance_path, exist_ok=True)

    # ✅ Création automatique du dossier uploads/
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # Initialisation DB
    db.init_app(app)
    with app.app_context():
        db.create_all()

    # --- Fonctions utilitaires ---
    def allowed_file(filename):
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

    def generer_code_retrait():
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

    # --- API Orange RDC ---
    def get_orange_token():
        auth = base64.b64encode(f"{app.config['ORANGE_CLIENT_ID']}:{app.config['ORANGE_CLIENT_SECRET']}".encode()).decode()
        headers = {"Authorization": f"Basic {auth}", "Content-Type": "application/x-www-form-urlencoded"}
        data = {"grant_type": "client_credentials"}
        r = requests.post("https://api.orange.com/oauth/v3/token", headers=headers, data=data, timeout=15)
        r.raise_for_status()
        return r.json().get("access_token")

    def envoyer_sms_orange(numero, message):
        try:
            token = get_orange_token()
            headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
            payload = {
                "outboundSMSMessageRequest": {
                    "address": f"tel:{numero}",
                    "senderAddress": f"tel:{app.config['ORANGE_SENDER']}",
                    "outboundSMSTextMessage": {"message": message}
                }
            }
            url = f"https://api.orange.com/smsmessaging/v1/outbound/tel%3A{app.config['ORANGE_SENDER']}/requests"
            r = requests.post(url, headers=headers, json=payload, timeout=20)
            return r.status_code, r.text
        except Exception as e:
            return 500, str(e)

    # --- Notifications push OneSignal ---
    def envoyer_notification_vendeur(vendeur_id, titre, message, target_url=None):
        try:
            url = "https://onesignal.com/api/v1/notifications"
            headers = {
                "Content-Type": "application/json; charset=utf-8",
                "Authorization": f"Basic {app.config['ONESIGNAL_API_KEY']}"
            }
            payload = {
                "app_id": app.config['ONESIGNAL_APP_ID'],
                "filters": [{"field": "tag", "key": "vendeur_id", "relation": "=", "value": str(vendeur_id)}],
                "headings": {"en": titre},
                "contents": {"en": message},
                "url": target_url or request.host_url.rstrip('/') + url_for('dashboard')
            }
            requests.post(url, headers=headers, json=payload, timeout=15)
        except Exception:
            pass

    # --- Routes principales ---
    @app.route('/')
    def index():
        vendeurs = Vendeur.query.all()
        return render_template('index.html', vendeurs=vendeurs)

    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if request.method == 'POST':
            nom = request.form['nom']
            email = request.form['email']
            telephone = request.form['telephone']
            boutique = request.form['boutique']
            password = request.form['password']

            if Vendeur.query.filter_by(email=email).first():
                flash("Email déjà utilisé.", "danger")
                return redirect(url_for('register'))

            v = Vendeur(nom=nom, email=email, telephone=telephone, boutique=boutique)
            v.set_password(password)
            db.session.add(v)
            db.session.commit()
            flash("Compte vendeur créé. Connectez-vous.", "success")
            return redirect(url_for('login'))
        return render_template('register.html')

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            email = request.form['email']
            password = request.form['password']
            v = Vendeur.query.filter_by(email=email).first()
            if v and v.check_password(password):
                session['vendeur_id'] = v.id
                flash("Connexion réussie.", "success")
                return redirect(url_for('dashboard'))
            flash("Identifiants invalides.", "danger")
        return render_template('login.html')

    @app.route('/logout')
    def logout():
        session.pop('vendeur_id', None)
        flash("Déconnecté.", "info")
        return redirect(url_for('index'))

    @app.route('/reserver', methods=['GET', 'POST'])
    def reserver():
        vendeurs = Vendeur.query.all()
        if request.method == 'POST':
            nom = request.form['nom'].strip()
            telephone = request.form['telephone'].strip().replace(' ', '')
            vendeur_id = int(request.form['vendeur_id'])
            heure_retrait = request.form['heure_retrait']

            produits_list = []
            noms = request.form.getlist('produit_nom')
            qtes = request.form.getlist('produit_qte')
            for n, q in zip(noms, qtes):
                if n.strip() and q.strip():
                    produits_list.append(f"{n.strip()} | {q.strip()}")
            produits_str = "; ".join(produits_list) if produits_list else None

            image_path = None
            file = request.files.get('image_liste')
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(save_path)
                image_path = save_path

            code = generer_code_retrait()

            reservation = Reservation(
                client_nom=nom,
                client_telephone=telephone,
                produits=produits_str,
                image_liste=image_path,
                vendeur_id=vendeur_id,
                heure_retrait=datetime.strptime(heure_retrait, "%H:%M").time(),
                code_retrait=code
            )
            db.session.add(reservation)
            db.session.commit()

            vendeur = Vendeur.query.get(vendeur_id)

            sms_client = f"Bonjour {nom}, votre code de retrait est {code}. Boutique: {vendeur.boutique}, Heure: {heure_retrait}"
            sms_vendeur = f"Reservation: Code {code}, Client {nom} ({telephone}), Heure {heure_retrait}"
            envoyer_sms_orange(telephone, sms_client)
            envoyer_sms_orange(vendeur.telephone, sms_vendeur)

            envoyer_notification_vendeur(vendeur_id, "Nouvelle réservation", f"{nom} pour {heure_retrait}")

            flash("Réservation enregistrée. Code envoyé par SMS.", "success")
            return redirect(url_for('index'))

        return render_template('reservation.html', vendeurs=vendeurs)

    @app.route('/dashboard')
    def dashboard():
        if 'vendeur_id' not in session:
            return redirect(url_for('login'))
        vendeur = Vendeur.query.get(session['vendeur_id'])
        reservations = Reservation.query.filter_by(vendeur_id=vendeur.id).order_by(Reservation.date_reservation.desc()).all()
        return render_template('dashboard.html', vendeur=vendeur, reservations=reservations,
                               onesignal_app_id=app.config['ONESIGNAL_APP_ID'])

    @app.route('/valider_retrait', methods=['POST'])
    def valider_retrait():
        if 'vendeur_id' not in session:
            return redirect(url_for('login'))
        code_saisi = request.form['code_retrait'].strip().upper()
        r = Reservation.query.filter_by(code_retrait=code_saisi, vendeur_id=session['vendeur_id']).first()
        if r and not r.retire:
            r.retire = True
            db.session.commit()
            flash("Retrait validé ✅", "success")
        else:
            flash("Code invalide ou déjà utilisé ❌", "danger")
        return redirect(url_for('dashboard'))

    return app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True)