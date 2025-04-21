import os
import json
import random
from flask import Flask, render_template, request, redirect, session, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'change_this_secret_key'

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
MEMBRES_FILE = os.path.join(DATA_DIR, 'membres.json')
MISES_FILE = os.path.join(DATA_DIR, 'mises.json')
ADMIN_USER = 'xtremekiller'
ADMIN_PASS = generate_password_hash('MyNameIsMethos123')

# --- Helpers ---
def load_json(path, default):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return default

def save_json(path, data):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_membres():
    return load_json(MEMBRES_FILE, [])

def save_membres(membres):
    save_json(MEMBRES_FILE, membres)

def get_mises():
    return load_json(MISES_FILE, [])

def save_mises(mises):
    save_json(MISES_FILE, mises)

def get_user():
    if 'admin' in session and session['admin']:
        return {'nom': ADMIN_USER, 'isAdmin': True}
    if 'membre' in session:
        membres = get_membres()
        for m in membres:
            if m['nom'] == session['membre']:
                return {'nom': m['nom'], 'points': m['points'], 'isAdmin': False}
    return None

def is_admin():
    return 'admin' in session and session['admin']

# --- Routes ---
@app.route('/')
def index():
    membres = get_membres()
    mises = get_mises()
    for m in membres:
        m['mise'] = 0
        for mi in mises:
            if mi['nom'] == m['nom']:
                m['mise'] = mi['mise']
    return render_template('index.html', membres=membres, user=get_user())

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form.get('type') == 'admin':
            username = request.form['username']
            password = request.form['password']
            if username == ADMIN_USER and check_password_hash(ADMIN_PASS, password):
                session['admin'] = True
                return redirect(url_for('admin'))
            else:
                return render_template('login.html', error="Identifiants admin invalides", membres=get_membres(), last_draw=last_draw)
        else:
            membre_nom = request.form['membre_nom']
            membres = get_membres()
            if any(m['nom'] == membre_nom for m in membres):
                session['membre'] = membre_nom
                return redirect(url_for('membre'))
            else:
                return render_template('login.html', error="Membre inconnu", membres=membres, last_draw=last_draw)
    return render_template('login.html', error=None, membres=get_membres())

@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return redirect(url_for('index'))

def get_draw_history():
    draw_history_file = os.path.join(DATA_DIR, 'draw_history.json')
    try:
        with open(draw_history_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return []

@app.route('/membre', methods=['GET'])
def membre():
    user = get_user()
    if not user or user.get('isAdmin'):
        return redirect(url_for('login'))
    mises = get_mises()
    mise = 0
    for mi in mises:
        if mi['nom'] == user['nom']:
            mise = mi['mise']
    # Derniers tirages
    draw_history = get_draw_history()
    last_draw = draw_history[-1] if draw_history else None
    recent_draws = draw_history[-4:] if draw_history else []
    return render_template('membre.html', user={**user, 'mise': mise}, message=None, error=None, last_draw=last_draw, recent_draws=recent_draws)

@app.route('/miser', methods=['POST'])
def miser():
    user = get_user()
    if not user or user.get('isAdmin'):
        return redirect(url_for('login'))
    try:
        mise = int(request.form['mise'])
        if mise < 0 or mise > user['points']:
            raise ValueError
    except Exception:
        return render_template('membre.html', user=user, message=None, error="Mise invalide.")
    mises = get_mises()
    found = False
    for mi in mises:
        if mi['nom'] == user['nom']:
            mi['mise'] = mise
            found = True
    if not found:
        mises.append({'nom': user['nom'], 'mise': mise})
    save_mises(mises)
    return render_template('membre.html', user={**user, 'mise': mise}, message="Mise enregistrée !", error=None)

@app.route('/admin', methods=['GET'])
def admin():
    if not is_admin():
        return redirect(url_for('login'))
    membres = get_membres()
    mises = get_mises()
    total_mise = sum(mi['mise'] for mi in mises)
    for m in membres:
        m['mise'] = 0
        for mi in mises:
            if mi['nom'] == m['nom']:
                m['mise'] = mi['mise']
        m['chance'] = round(100 * m['mise'] / total_mise, 1) if total_mise > 0 else 0.0
    draw_history = get_draw_history()
    return render_template('admin.html', membres=membres, user=get_user(), draw_history=draw_history)

@app.route('/ajouter_membre', methods=['POST'])
def ajouter_membre():
    if not is_admin():
        return redirect(url_for('login'))
    nom = request.form['nom']
    points = int(request.form['points'])
    membres = get_membres()
    if any(m['nom'] == nom for m in membres):
        flash('Nom déjà utilisé', 'error')
        return redirect(url_for('admin'))
    membres.append({'nom': nom, 'points': points})
    save_membres(membres)
    return redirect(url_for('admin'))

@app.route('/supprimer_membre', methods=['POST'])
def supprimer_membre():
    if not is_admin():
        return redirect(url_for('login'))
    nom = request.form['nom']
    membres = [m for m in get_membres() if m['nom'] != nom]
    save_membres(membres)
    mises = [mi for mi in get_mises() if mi['nom'] != nom]
    save_mises(mises)
    return redirect(url_for('admin'))

@app.route('/import_json', methods=['POST'])
def import_json():
    if not is_admin():
        return redirect(url_for('login'))
    file = request.files['jsonfile']
    if not file:
        flash('Aucun fichier', 'error')
        return redirect(url_for('admin'))
    try:
        data = json.load(file)
        membres = []
        for entry in data:
            nom = entry.get('nom') or entry.get('name')
            points = entry.get('points')
            if not nom or nom is None or str(nom).strip() == '':
                continue
            membres.append({'nom': nom, 'points': points})
        if not membres:
            flash('Aucun membre valide trouvé dans le JSON', 'error')
        else:
            save_membres(membres)
            flash('Import/MAJ réussi', 'success')
    except Exception as e:
        flash('Erreur import JSON', 'error')
    return redirect(url_for('admin'))

@app.route('/import_json_paste', methods=['POST'])
def import_json_paste():
    if not is_admin():
        return redirect(url_for('login'))
    jsontext = request.form.get('jsontext', '').strip()
    if not jsontext:
        flash('Aucun texte JSON fourni', 'error')
        return redirect(url_for('admin'))
    try:
        data = json.loads(jsontext)
        membres = get_membres()
        noms_existants = {m['nom']: m for m in membres if m.get('nom') and m['nom'] is not None and str(m['nom']).strip() != ''}
        for entry in data:
            nom = entry.get('nom') or entry.get('name')
            points = entry.get('points')
            if not nom or nom is None or str(nom).strip() == '':
                continue
            if nom in noms_existants:
                noms_existants[nom]['points'] = points
            else:
                membres.append({'nom': nom, 'points': points})
        membres = [m for m in membres if m.get('nom') and m['nom'] is not None and str(m['nom']).strip() != '']
        save_membres(membres)
        flash('Membres/points mis à jour (copier-coller)', 'success')
    except Exception as e:
        flash('Erreur import JSON (copier-coller)', 'error')
    return redirect(url_for('admin'))

@app.route('/reset_tirage', methods=['POST'])
def reset_tirage():
    if not is_admin():
        return redirect(url_for('login'))
    save_mises([])
    # Efface le dernier gagnant
    try:
        with open(os.path.join(DATA_DIR, 'last_draw.json'), 'w', encoding='utf-8') as f:
            json.dump({}, f)
    except Exception:
        pass
    flash('Tirage/mises réinitialisés', 'success')
    return redirect(url_for('admin'))

@app.route('/tirage', methods=['POST'])
def tirage():
    if not is_admin():
        return redirect(url_for('login'))
    mises = get_mises()
    membres = get_membres()
    total_mise = sum(mi['mise'] for mi in mises)
    if total_mise == 0:
        flash('Aucune mise', 'error')
        return redirect(url_for('admin'))
    population = []
    for mi in mises:
        population.extend([mi['nom']] * mi['mise'])
    winner = random.choice(population)
    gagnant = None
    mise_gagnant = 0
    for m in membres:
        if m['nom'] == winner:
            gagnant = m
            break
    for mi in mises:
        if mi['nom'] == winner:
            mise_gagnant = mi['mise']
    percent = round(100 * mise_gagnant / total_mise, 1) if total_mise > 0 else 0.0
    if gagnant:
        gagnant['points'] -= mise_gagnant  # On retire la mise du gagnant de ses points
        save_membres(membres)
    save_mises([])
    # Ajoute ce tirage à l'historique
    draw_history_file = os.path.join(DATA_DIR, 'draw_history.json')
    try:
        if os.path.exists(draw_history_file):
            with open(draw_history_file, 'r', encoding='utf-8') as f:
                draw_history = json.load(f)
        else:
            draw_history = []
    except Exception:
        draw_history = []
    draw = {'winner': winner, 'points': total_mise, 'percent': percent, 'mise': mise_gagnant}
    draw_history.append(draw)
    with open(draw_history_file, 'w', encoding='utf-8') as f:
        json.dump(draw_history, f, ensure_ascii=False, indent=2)
    # Envoie le résultat sur Discord
    msg = f"🎲 **TIRAGE** 🎲\nGagnant : **{winner}**\nMise : {mise_gagnant} pts\nChance : {percent}%"
    send_discord_webhook(msg)
    flash(f"Tirage effectué ! Gagnant : {winner}", "success")
    return redirect(url_for('admin'))

@app.route('/reset_mises', methods=['POST'])
def reset_mises():
    if not is_admin():
        return redirect(url_for('login'))
    save_mises([])
    # Efface le dernier gagnant
    try:
        with open(os.path.join(DATA_DIR, 'last_draw.json'), 'w', encoding='utf-8') as f:
            json.dump({}, f)
    except Exception:
        pass
    flash('Mises réinitialisées', 'success')
    return redirect(url_for('admin'))

@app.route('/modifier_points', methods=['POST'])
def modifier_points():
    if not is_admin():
        return redirect(url_for('login'))
    nom = request.form['nom']
    try:
        points = int(request.form['points'])
        if points < 0:
            raise ValueError
    except Exception:
        flash('Valeur de points invalide', 'error')
        return redirect(url_for('admin'))
    membres = get_membres()
    for m in membres:
        if m['nom'] == nom:
            m['points'] = points
    save_membres(membres)
    flash(f'Points de {nom} mis à jour', 'success')
    return redirect(url_for('admin'))

from flask import jsonify, send_file, make_response

@app.route('/envoyer_points_discord', methods=['POST'])
def envoyer_points_discord():
    if not is_admin():
        return redirect(url_for('login'))
    membres = get_membres()
    if not membres:
        flash("Aucun membre à envoyer.", "error")
        return redirect(url_for('admin'))
    # On trie par points décroissants
    membres_sorted = sorted(membres, key=lambda m: m['points'], reverse=True)
    total_points = sum(m['points'] for m in membres_sorted)
    msg_header = f"🏦 Banque de Points\nTotal: {total_points:,} pts\n\n"
    msg = msg_header
    first = True
    for i, m in enumerate(membres_sorted, 1):
        if i == 1:
            line = f"🏅1. {m['nom']} — {m['points']:,} pts\n"
        elif i == 2:
            line = f"🏅2. {m['nom']} — {m['points']:,} pts\n"
        elif i == 3:
            line = f"🏅3. {m['nom']} — {m['points']:,} pts\n"
        else:
            line = f"⭐{m['nom']} — {m['points']:,} pts\n"
        if len(msg) + len(line) > 1900:
            send_discord_webhook(msg)
            msg = line if not first else ''
            first = False
        else:
            msg += line
    if msg.strip() != (msg_header.strip() if first else ''):
        send_discord_webhook(msg)
    flash("Liste envoyée sur Discord !", "success")
    return redirect(url_for('admin'))
import requests

@app.route('/reset_tirages', methods=['POST'])
def reset_tirages():
    draw_history_file = os.path.join(DATA_DIR, 'draw_history.json')
    try:
        with open(draw_history_file, 'w', encoding='utf-8') as f:
            json.dump([], f)
        flash('Historique des tirages réinitialisé.', 'success')
    except Exception as e:
        flash(f'Erreur lors de la réinitialisation : {e}', 'danger')
    return redirect(url_for('admin'))

@app.route('/export_tirages_json', methods=['GET'])
def export_tirages_json():
    draw_history_file = os.path.join(DATA_DIR, 'draw_history.json')
    try:
        with open(draw_history_file, 'r', encoding='utf-8') as f:
            draw_history = json.load(f)
    except Exception:
        draw_history = []
    export = []
    for idx, tirage in enumerate(draw_history):
        if tirage.get('annule'):
            continue  # On ignore les tirages annulés
        export.append({
            "tirage": idx + 1,
            "gagnant": tirage.get('winner', ''),
            "points_retires": tirage.get('mise', 0)
        })
    response = make_response(json.dumps(export, ensure_ascii=False, indent=2))
    response.headers['Content-Type'] = 'application/json'
    response.headers['Content-Disposition'] = 'attachment; filename=historique_tirages_points_retires.json'
    return response

# === CONFIGURATION DISCORD WEBHOOK ===
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1363704476753723574/WDWoX1wGGbONI5a-4t6SWcxWTT5o34CmC_7yTWIfkMVuJ2-pZ7UOXj0gMbMwplUzrh1v"

def send_discord_webhook(message):
    if not DISCORD_WEBHOOK_URL or 'TON_WEBHOOK_ICI' in DISCORD_WEBHOOK_URL:
        return  # Webhook non configuré
    try:
        requests.post(DISCORD_WEBHOOK_URL, json={"content": message})
    except Exception as e:
        print(f"Erreur envoi Discord: {e}")

@app.route('/annuler_tirage/<int:draw_id>', methods=['POST'])
def annuler_tirage(draw_id):
    if not is_admin():
        return redirect(url_for('login'))
    # Charger l'historique
    draw_history_file = os.path.join(DATA_DIR, 'draw_history.json')
    try:
        with open(draw_history_file, 'r', encoding='utf-8') as f:
            draw_history = json.load(f)
    except Exception:
        draw_history = []
    if draw_id < 0 or draw_id >= len(draw_history):
        flash('Tirage introuvable', 'error')
        return redirect(url_for('admin'))
    tirage = draw_history[draw_id]
    if tirage.get('annule'):
        flash('Tirage déjà annulé', 'error')
        return redirect(url_for('admin'))
    # Rendre la mise au gagnant
    membres = get_membres()
    for m in membres:
        if m['nom'] == tirage['winner']:
            m['points'] += tirage['mise']
    save_membres(membres)
    tirage['annule'] = True
    with open(draw_history_file, 'w', encoding='utf-8') as f:
        json.dump(draw_history, f, ensure_ascii=False, indent=2)
    flash(f'Tirage annulé, {tirage["winner"]} a récupéré sa mise.', 'success')
    return redirect(url_for('admin'))

@app.route('/tirage_status')
def tirage_status():
    mises = get_mises()
    total = sum(mi['mise'] for mi in mises)
    result = []
    for mi in mises:
        percent = round(100 * mi['mise'] / total, 1) if total > 0 else 0.0
        result.append({'nom': mi['nom'], 'mise': mi['mise'], 'chance': percent})
    return jsonify({'participants': result, 'total': total})

if __name__ == '__main__':
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(MEMBRES_FILE):
        save_membres([])
    if not os.path.exists(MISES_FILE):
        save_mises([])
    app.run(debug=True)
import os

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))  # Render donne PORT, sinon 5000 en local
    app.run(host='0.0.0.0', port=port)
