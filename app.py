# app.py - Minimal Flask URL shortener using SQLite
from flask import Flask, request, jsonify, redirect, render_template
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from urllib.parse import urlparse
import string, random
from datetime import datetime
import os

app = Flask(__name__, template_folder='templates', static_folder='static')

# Use SQLite database in project folder
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///urls.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# DB model: store code <-> original_url
class URLMap(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(16), unique=True, nullable=False, index=True)
    original_url = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    access_count = db.Column(db.Integer, default=0)

# helper: ensure scheme exists (http://)
def normalize_url(url: str) -> str:
    if not url:
        return None
    url = url.strip()
    parsed = urlparse(url)
    if not parsed.scheme:
        url = 'http://' + url
    return url

def generate_code(length=6):
    alphabet = string.ascii_letters + string.digits
    return ''.join(random.choices(alphabet, k=length))

# create DB tables automatically (for development)
@app.before_first_request
def create_tables():
    db.create_all()

# Basic frontend (optional)
@app.route('/')
def index():
    return render_template('index.html')

# API to shorten a URL (POST JSON { "url": "..." })
@app.route('/api/shorten', methods=['POST'])
def shorten():
    data = request.get_json(silent=True) or request.form
    original = (data.get('url') if data else None)
    original = normalize_url(original)
    if not original:
        return jsonify({'error': 'Invalid or missing URL'}), 400

    # try to insert a unique random code (retry on collision)
    for _ in range(8):
        code = generate_code(6)
        mapping = URLMap(code=code, original_url=original)
        db.session.add(mapping)
        try:
            db.session.commit()
            short_url = request.host_url.rstrip('/') + '/' + code
            return jsonify({'code': code, 'short_url': short_url, 'original_url': original})
        except IntegrityError:
            db.session.rollback()
    return jsonify({'error': 'Could not generate unique code'}), 500

# Redirect route - when a user visits /<code> they go to original_url
@app.route('/<code>')
def redirect_code(code):
    mapping = URLMap.query.filter_by(code=code).first_or_404()
    mapping.access_count += 1
    db.session.commit()
    return redirect(mapping.original_url, code=302)

# Small info endpoint
@app.route('/api/info/<code>')
def info(code):
    m = URLMap.query.filter_by(code=code).first_or_404()
    return {
        'code': m.code,
        'original_url': m.original_url,
        'created_at': m.created_at.isoformat(),
        'access_count': m.access_count
    }

if __name__ == '__main__':
    # debug=True for automatic reload during development
    app.run(host='127.0.0.1', port=5000, debug=True)
