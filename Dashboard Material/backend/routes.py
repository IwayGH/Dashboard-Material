from functools import wraps
from flask import Blueprint, request, session, redirect, url_for, render_template, flash, Response
from backend.database import get_db
import sqlite3
import csv
from io import StringIO

main_bp = Blueprint('main', __name__)

# Decorators
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))
        if session.get('role') not in ['Superuser', 'Jakarta']:
            flash("Akses ditolak. Hanya Jakarta/Superuser yang bisa mengakses halaman ini.", "error")
            return redirect(url_for('main.dashboard'))
        return f(*args, **kwargs)
    return decorated_function

@main_bp.route('/dashboard')
@login_required
def dashboard():
    db = get_db()
    role = session['role']
    region = session['region']
    
    if role in ['Superuser', 'Jakarta']:
        stats = db.execute("SELECT SUM(spare) as spare, SUM(used) as used, SUM(faulty) as faulty, SUM(licensed) as licensed FROM materials").fetchone()
        reg_stats = db.execute("SELECT region, SUM(stock) as total FROM regional_stocks GROUP BY region").fetchall()
        
        # Ambil statistik repair untuk Jakarta/Superuser
        repair_stats = db.execute("""
            SELECT 
                SUM(CASE WHEN repair_status = 'Initialize' THEN 1 ELSE 0 END) as initialize,
                SUM(CASE WHEN repair_status = 'On Progress' THEN 1 ELSE 0 END) as on_progress,
                SUM(CASE WHEN repair_status = 'Done' THEN 1 ELSE 0 END) as done,
                SUM(CASE WHEN repair_status = 'Failed' THEN 1 ELSE 0 END) as failed
            FROM repairs
        """).fetchone()
    else:
        stats = db.execute("SELECT SUM(stock) as spare, 0 as used, 0 as faulty, 0 as licensed FROM regional_stocks WHERE region=?", (region,)).fetchone()
        reg_stats = []
        repair_stats = None

    return render_template('dashboard.html', stats=stats, reg_stats=reg_stats, repair_stats=repair_stats, username=session['username'], role=role, region=region)

@main_bp.route('/regional_detail/<region>')
@login_required
def regional_detail(region):
    db = get_db()
    if session['role'] not in ['Superuser', 'Jakarta'] and session['region'] != region:
        flash("Akses ditolak.", "error")
        return redirect(url_for('main.dashboard'))
        
    # Hanya ambil material yang stock-nya lebih dari 0
    mats = db.execute('''
        SELECT m.*, rs.stock as regional_stock 
        FROM materials m 
        JOIN regional_stocks rs ON m.id = rs.material_id 
        WHERE rs.region=? AND rs.stock > 0
    ''', (region,)).fetchall()
    
    return render_template('regional_detail.html', mats=mats, region=region)

@main_bp.route('/export_region/<region>')
@login_required
def export_region(region):
    db = get_db()
    if session['role'] not in ['Superuser', 'Jakarta'] and session['region'] != region:
        flash("Akses ditolak.", "error")
        return redirect(url_for('main.dashboard'))
        
    mats = db.execute('''
        SELECT m.code, m.name, m.type, m.vendor, m.material_baru, m.after_repair, m.faulty, m.licensed, rs.stock as regional_stock, m.remark
        FROM materials m 
        JOIN regional_stocks rs ON m.id = rs.material_id 
        WHERE rs.region=? AND rs.stock > 0
    ''', (region,)).fetchall()
    
    # Membuat file CSV di memory
    si = StringIO()
    cw = csv.writer(si)
    
    # Header CSV
    cw.writerow(['Code', 'Name', 'Type', 'Vendor', 'Material Baru', 'After Repair', 'Faulty', 'License', 'Stock', 'Remark'])
    
    # Data CSV
    for m in mats:
        cw.writerow([m['code'], m['name'], m['type'], m['vendor'], m['material_baru'], m['after_repair'], m['faulty'], m['licensed'], m['regional_stock'], m['remark']])
        
    output = si.getvalue()
    
    # Response untuk download file
    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-disposition": f"attachment; filename=detail_stock_{region}.csv"}
    )

@main_bp.route('/materials')
@login_required
def materials():
    db = get_db()
    role = session['role']
    region = session['region']
    
    if role in ['Superuser', 'Jakarta']:
        mats = db.execute("SELECT * FROM materials").fetchall()
    else:
        mats = db.execute('''
            SELECT m.*, rs.stock as regional_stock 
            FROM materials m 
            JOIN regional_stocks rs ON m.id = rs.material_id 
            WHERE rs.region=?
        ''', (region,)).fetchall()

    return render_template('materials.html', mats=mats, role=role, region=region)

@main_bp.route('/edit_stock/<int:mat_id>', methods=['GET', 'POST'])
@login_required
def edit_stock(mat_id):
    db = get_db()
    role = session['role']
    region = session['region']
    
    if role in ['Superuser', 'Jakarta']:
        return redirect(url_for('main.materials'))

    if request.method == 'POST':
        new_stock = request.form['stock']
        db.execute("UPDATE regional_stocks SET stock=? WHERE material_id=? AND region=?", (new_stock, mat_id, region))
        db.commit()
        flash("Stock updated successfully", "success")
        return redirect(url_for('main.materials'))

    mat = db.execute("SELECT * FROM materials WHERE id=?", (mat_id,)).fetchone()
    rstock = db.execute("SELECT stock FROM regional_stocks WHERE material_id=? AND region=?", (mat_id, region)).fetchone()
    
    return render_template('edit_stock.html', mat=mat, rstock=rstock, region=region)

# --- REPAIR FEATURES ---
@main_bp.route('/repair_logs/<int:mat_id>')
@login_required
def repair_logs(mat_id):
    db = get_db()
    mat = db.execute("SELECT * FROM materials WHERE id=?", (mat_id,)).fetchone()
    logs = db.execute("SELECT * FROM repairs WHERE material_id=? ORDER BY id DESC", (mat_id,)).fetchall()
    return render_template('repair_logs.html', mat=mat, logs=logs)

@main_bp.route('/add_repair/<int:mat_id>', methods=['GET', 'POST'])
@admin_required
def add_repair(mat_id):
    db = get_db()
    mat = db.execute("SELECT * FROM materials WHERE id=?", (mat_id,)).fetchone()
    if request.method == 'POST':
        db.execute('''INSERT INTO repairs (
            material_id, 
            delivery_date, delivery_dn, delivery_serial, delivery_status,
            inbound_date, inbound_dn, inbound_serial, inbound_status,
            outbound_date, outbound_dn, outbound_serial, outbound_status,
            repair_status, repair_date, repair_dn, repair_serial
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', (
            mat_id, 
            request.form['delivery_date'], request.form['delivery_dn'], request.form['delivery_serial'], request.form['delivery_status'],
            request.form['inbound_date'], request.form['inbound_dn'], request.form['inbound_serial'], request.form['inbound_status'],
            request.form['outbound_date'], request.form['outbound_dn'], request.form['outbound_serial'], request.form['outbound_status'],
            request.form['repair_status'], request.form['repair_date'], request.form['repair_dn'], request.form['repair_serial']
        ))
        db.commit()
        flash("Repair log added.", "success")
        return redirect(url_for('main.repair_logs', mat_id=mat_id))
    return render_template('repair_form.html', mat=mat, log=None)

@main_bp.route('/edit_repair/<int:repair_id>', methods=['GET', 'POST'])
@admin_required
def edit_repair(repair_id):
    db = get_db()
    log = db.execute("SELECT * FROM repairs WHERE id=?", (repair_id,)).fetchone()
    mat_id = log['material_id']
    mat = db.execute("SELECT * FROM materials WHERE id=?", (mat_id,)).fetchone()
    
    if request.method == 'POST':
        db.execute('''UPDATE repairs SET 
            delivery_date=?, delivery_dn=?, delivery_serial=?, delivery_status=?,
            inbound_date=?, inbound_dn=?, inbound_serial=?, inbound_status=?,
            outbound_date=?, outbound_dn=?, outbound_serial=?, outbound_status=?,
            repair_status=?, repair_date=?, repair_dn=?, repair_serial=?
            WHERE id=?''', (
            request.form['delivery_date'], request.form['delivery_dn'], request.form['delivery_serial'], request.form['delivery_status'],
            request.form['inbound_date'], request.form['inbound_dn'], request.form['inbound_serial'], request.form['inbound_status'],
            request.form['outbound_date'], request.form['outbound_dn'], request.form['outbound_serial'], request.form['outbound_status'],
            request.form['repair_status'], request.form['repair_date'], request.form['repair_dn'], request.form['repair_serial'],
            repair_id
        ))
        db.commit()
        flash("Repair log updated.", "success")
        return redirect(url_for('main.repair_logs', mat_id=mat_id))
    return render_template('repair_form.html', mat=mat, log=log)

# --- REQUEST FEATURES ---
@main_bp.route('/request_material', methods=['GET', 'POST'])
@login_required
def request_material():
    db = get_db()
    role = session['role']
    region = session['region']
    
    if role in ['Superuser', 'Jakarta']:
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        mat_id = request.form['material_id']
        qty = request.form['quantity']
        db.execute("INSERT INTO requests (material_id, region, quantity, status, requested_by) VALUES (?, ?, ?, 'Pending', ?)",
                   (mat_id, region, qty, session['username']))
        db.commit()
        flash("Request submitted to Jakarta for approval.", "success")
        return redirect(url_for('main.dashboard'))

    mats = db.execute("SELECT * FROM materials").fetchall()
    return render_template('request_material.html', mats=mats, region=region)

@main_bp.route('/approvals')
@admin_required
def approvals():
    db = get_db()
    reqs = db.execute('''
        SELECT r.*, m.code, m.name 
        FROM requests r 
        JOIN materials m ON r.material_id = m.id 
        WHERE r.status = 'Pending'
    ''').fetchall()
    return render_template('approvals.html', reqs=reqs)

@main_bp.route('/approve/<int:req_id>')
@admin_required
def approve(req_id):
    db = get_db()
    req = db.execute("SELECT * FROM requests WHERE id=?", (req_id,)).fetchone()
    if req and req['status'] == 'Pending':
        db.execute("UPDATE materials SET spare = spare - ? WHERE id=?", (req['quantity'], req['material_id']))
        db.execute("UPDATE regional_stocks SET stock = stock + ? WHERE material_id=? AND region=?", (req['quantity'], req['material_id'], req['region']))
        db.execute("UPDATE requests SET status='Approved' WHERE id=?", (req_id,))
        db.commit()
        flash("Request Approved & Stock Updated.", "success")
    return redirect(url_for('main.approvals'))

@main_bp.route('/reject/<int:req_id>')
@admin_required
def reject(req_id):
    db = get_db()
    db.execute("UPDATE requests SET status='Rejected' WHERE id=?", (req_id,))
    db.commit()
    flash("Request Rejected.", "error")
    return redirect(url_for('main.approvals'))

# --- ACCOUNT MANAGEMENT ---
@main_bp.route('/accounts', methods=['GET', 'POST'])
@admin_required
def accounts():
    db = get_db()
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']
        region = request.form['region']
        try:
            db.execute("INSERT INTO users (username, password, role, region) VALUES (?, ?, ?, ?)",
                       (username, password, role, region))
            db.commit()
            flash("Account added successfully.", "success")
        except sqlite3.IntegrityError:
            flash("Username already exists.", "error")
        return redirect(url_for('main.accounts'))

    users = db.execute("SELECT * FROM users").fetchall()
    regions = ['Jakarta', 'Kalimantan', 'Maluku', 'Natuna', 'NTT', 'Sumatera', 'Sulawesi']
    return render_template('accounts.html', users=users, regions=regions)

@main_bp.route('/edit_account/<int:user_id>', methods=['GET', 'POST'])
@admin_required
def edit_account(user_id):
    db = get_db()
    user = db.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']
        region = request.form['region']
        
        try:
            db.execute("UPDATE users SET username=?, password=?, role=?, region=? WHERE id=?",
                       (username, password, role, region, user_id))
            db.commit()
            flash("Account updated successfully.", "success")
        except sqlite3.IntegrityError:
            flash("Username already exists.", "error")
        return redirect(url_for('main.accounts'))
        
    regions = ['Jakarta', 'Kalimantan', 'Maluku', 'Natuna', 'NTT', 'Sumatera', 'Sulawesi']
    return render_template('edit_account.html', user=user, regions=regions)

# --- MATERIAL EDIT (GLOBAL NUMBERS) ---
@main_bp.route('/edit_material/<int:mat_id>', methods=['GET', 'POST'])
@admin_required
def edit_material(mat_id):
    db = get_db()
    mat = db.execute("SELECT * FROM materials WHERE id=?", (mat_id,)).fetchone()
    
    if request.method == 'POST':
        spare = request.form['spare']
        used = request.form['used']
        faulty = request.form['faulty']
        licensed = request.form['licensed']
        
        db.execute("UPDATE materials SET spare=?, used=?, faulty=?, licensed=? WHERE id=?", 
                   (spare, used, faulty, licensed, mat_id))
        db.commit()
        flash("Material numbers updated successfully.", "success")
        return redirect(url_for('main.materials'))
        
    return render_template('edit_material.html', mat=mat)

# --- REPAIR STATUS LIST ---
@main_bp.route('/repair_status')
@login_required
def repair_status():
    db = get_db()
    # Ambil material yang punya log repair, sekaligus ambil status repair terakhirnya
    mats = db.execute('''
        SELECT m.*, (
            SELECT r.repair_status 
            FROM repairs r 
            WHERE r.material_id = m.id 
            ORDER BY r.id DESC LIMIT 1
        ) as latest_status
        FROM materials m 
        WHERE EXISTS (SELECT 1 FROM repairs r WHERE r.material_id = m.id)
        ORDER BY m.code
    ''').fetchall()
    return render_template('repair_status.html', mats=mats)