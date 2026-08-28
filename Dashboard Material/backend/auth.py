from flask import Blueprint, request, session, redirect, url_for, render_template
from backend.database import get_db

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/', methods=['GET'])
def login():
    if 'user_id' in session:
        return redirect(url_for('main.dashboard'))
    return render_template('login.html', error=request.args.get('error'))

@auth_bp.route('/login_auth', methods=['POST'])
def login_auth():
    username = request.form['username']
    password = request.form['password']
    db = get_db()
    user = db.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password)).fetchone()
    if user:
        session['user_id'] = user['id']
        session['username'] = user['username']
        session['role'] = user['role']
        session['region'] = user['region']
        return redirect(url_for('main.dashboard'))
    return redirect(url_for('auth.login', error="Username atau Password salah"))

@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))