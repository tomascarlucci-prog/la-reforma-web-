import os
import sqlite3
import mimetypes  
from datetime import datetime, timezone, timedelta
from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.join(BASE_DIR, 'templates')
DB_PATH = os.path.join(BASE_DIR, 'database.db')

app = Flask(__name__, template_folder=TEMPLATE_DIR)

# Forzamos los tipos MIME para archivos multimedia
mimetypes.add_type('video/mp4', '.mp4')
mimetypes.add_type('video/webm', '.webm')

app.secret_key = 'reforma_secreta_key_2026'

# Zona horaria fija para Argentina (UTC-3)
ARG_TZA = timezone(timedelta(hours=-3))

def get_db_connection():
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    
    conn.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            rol TEXT DEFAULT 'admin'
        )
    ''')
    
    conn.execute('''
        CREATE TABLE IF NOT EXISTS platos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            categoria TEXT NOT NULL,
            precio REAL NOT NULL,
            descripcion TEXT,
            es_plato_del_dia BOOLEAN DEFAULT 0,
            disponible BOOLEAN DEFAULT 1
        )
    ''')

    conn.execute('''
        CREATE TABLE IF NOT EXISTS cuentas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numero_mesa TEXT NOT NULL,
            estado TEXT DEFAULT 'abierta',
            total REAL DEFAULT 0.0,
            hora_apertura TIMESTAMP,
            hora_cierre TIMESTAMP,
            medio_pago TEXT DEFAULT 'Efectivo'
        )
    ''')
    
    conn.execute('''
        CREATE TABLE IF NOT EXISTS detalle_cuenta (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cuenta_id INTEGER,
            nombre_plato TEXT NOT NULL,
            precio REAL NOT NULL,
            cantidad INTEGER DEFAULT 1,
            FOREIGN KEY (cuenta_id) REFERENCES cuentas (id)
        )
    ''')
    
    user_check = conn.execute('SELECT * FROM usuarios').fetchone()
    if not user_check:
        hashed_pw = generate_password_hash('reforma2026')
        conn.execute('INSERT INTO usuarios (usuario, password_hash, rol) VALUES (?, ?, ?)', ('admin', hashed_pw, 'admin'))
    
    conn.commit()
    conn.close()


@app.route('/')
def index():
    conn = get_db_connection()
    platos_del_dia = conn.execute('SELECT * FROM platos WHERE es_plato_del_dia = 1 AND disponible = 1').fetchall()
    todos_los_platos = conn.execute('SELECT * FROM platos WHERE disponible = 1').fetchall()
    conn.close()
    return render_template('index.html', platos_del_dia=platos_del_dia, platos=todos_los_platos)

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['usuario']
        password = request.form['password']
        
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM usuarios WHERE usuario = ?', (username,)).fetchone()
        conn.close()
        
        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['usuario'] = user['usuario']
            return redirect(url_for('admin'))
        else:
            error = 'Usuario o contraseña incorrectos'
            
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


@app.route('/admin')
def admin():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_db_connection()
    platos = conn.execute('SELECT * FROM platos').fetchall()
    conn.close()
    return render_template('admin.html', platos=platos)

@app.route('/admin/agregar', methods=['POST'])
def agregar_plato():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    nombre = request.form['nombre']
    descripcion = request.form['descripcion']
    categoria = request.form.get('categoria', 'Platos Principales')
    es_plato_del_dia = 1 if request.form.get('es_plato_del_dia') == '1' else 0
    
    # PROTECCIÓN: Si el usuario escribe mal el precio (ej. letras), se guarda como 0.0 para no romper el sistema
    try:
        precio_str = request.form['precio'].replace(',', '.')
        precio = float(precio_str)
    except ValueError:
        precio = 0.0
    
    conn = get_db_connection()
    conn.execute('INSERT INTO platos (nombre, descripcion, precio, categoria, disponible, es_plato_del_dia) VALUES (?, ?, ?, ?, 1, ?)',
                 (nombre, descripcion, precio, categoria, es_plato_del_dia))
    conn.commit()
    conn.close()
    return redirect(url_for('admin') + '#seccion-platos')

@app.route('/admin/toggle-disponible/<int:id>')
def toggle_disponible(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    conn = get_db_connection()
    plato = conn.execute('SELECT disponible FROM platos WHERE id = ?', (id,)).fetchone()
    nuevo_estado = 0 if plato['disponible'] == 1 else 1
    conn.execute('UPDATE platos SET disponible = ? WHERE id = ?', (nuevo_estado, id))
    conn.commit()
    conn.close()
    return redirect(url_for('admin') + '#seccion-platos')

@app.route('/admin/toggle-dia/<int:id>')
def toggle_dia(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    conn = get_db_connection()
    plato = conn.execute('SELECT es_plato_del_dia FROM platos WHERE id = ?', (id,)).fetchone()
    nuevo_estado = 0 if plato['es_plato_del_dia'] == 1 else 1
    conn.execute('UPDATE platos SET es_plato_del_dia = ? WHERE id = ?', (nuevo_estado, id))
    conn.commit()
    conn.close()
    return redirect(url_for('admin') + '#seccion-platos')

@app.route('/admin/editar/<int:id>', methods=['POST'])
def editar_plato(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    nombre = request.form['nombre']
    descripcion = request.form['descripcion']
    categoria = request.form.get('categoria', 'Platos Principales')
    
    # PROTECCIÓN: Evita caídas por errores de tipeo al editar
    try:
        precio_str = request.form['precio'].replace(',', '.')
        precio = float(precio_str)
    except ValueError:
        precio = 0.0
    
    conn = get_db_connection()
    conn.execute('''
        UPDATE platos
        SET nombre = ?, descripcion = ?, precio = ?, categoria = ?
        WHERE id = ?
    ''', (nombre, descripcion, precio, categoria, id))
    conn.commit()
    conn.close()
    return redirect(url_for('admin') + '#seccion-platos')


# ------------------ GESTIÓN DE MESAS Y CAJA DIARIA/HISTORIAL ------------------

@app.route('/admin/mesas')
def admin_mesas():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    
    mesas_abiertas = conn.execute('SELECT * FROM cuentas WHERE estado = "abierta"').fetchall()
    platos = conn.execute('SELECT * FROM platos WHERE disponible = 1').fetchall()
    
    hoy_str = datetime.now(ARG_TZA).strftime('%Y-%m-%d')
    fecha_seleccionada = request.args.get('fecha')
    
    if not fecha_seleccionada:
        fecha_seleccionada = hoy_str
        
    # CORRECCIÓN: Filtro LIKE para garantizar que la fecha coincida perfecto
    totales_pagos = conn.execute('''
        SELECT medio_pago, SUM(total) as subtotal
        FROM cuentas
        WHERE estado = "cerrada" AND hora_cierre LIKE ?
        GROUP BY medio_pago
    ''', (fecha_seleccionada + '%',)).fetchall()
    
    resumen_caja = {'Efectivo': 0.0, 'Mercado Pago': 0.0, 'Tarjeta': 0.0}
    
    for row in totales_pagos:
        mp_db = row['medio_pago']
        sub = float(row['subtotal']) if row['subtotal'] else 0.0
        
        if mp_db:
            mp_texto = mp_db.lower().strip()
            if 'mercado' in mp_texto or 'mp' in mp_texto:
                resumen_caja['Mercado Pago'] += sub
            elif 'tarjeta' in mp_texto:
                resumen_caja['Tarjeta'] += sub
            else:
                resumen_caja['Efectivo'] += sub
        else:
            resumen_caja['Efectivo'] += sub

    total_general = resumen_caja['Efectivo'] + resumen_caja['Mercado Pago'] + resumen_caja['Tarjeta']

    # CORRECCIÓN: Filtro LIKE para el historial del día
    historial_dia = conn.execute('''
        SELECT * FROM cuentas
        WHERE estado = "cerrada" AND hora_cierre LIKE ?
        ORDER BY hora_cierre DESC
    ''', (fecha_seleccionada + '%',)).fetchall()

    detalle_por_mesa = {}
    for mesa in mesas_abiertas:
        items = conn.execute('SELECT * FROM detalle_cuenta WHERE cuenta_id = ?', (mesa['id'],)).fetchall()
        detalle_por_mesa[mesa['id']] = items

    conn.close()
    
    return render_template('mesas.html',
                           mesas=mesas_abiertas,
                           platos=platos,
                           resumen_caja=resumen_caja,
                           total_general=total_general,
                           historial=historial_dia,
                           detalle_por_mesa=detalle_por_mesa,
                           fecha_seleccionada=fecha_seleccionada,
                           hoy_str=hoy_str)

@app.route('/admin/mesa/abrir', methods=['POST'])
def abrir_mesa():
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    numero_mesa = request.form['numero_mesa']
    hora_actual = datetime.now(ARG_TZA).strftime('%Y-%m-%d %H:%M:%S')
    
    conn = get_db_connection()
    conn.execute('INSERT INTO cuentas (numero_mesa, estado, hora_apertura) VALUES (?, "abierta", ?)', (numero_mesa, hora_actual))
    conn.commit()
    conn.close()
    
    return redirect(url_for('admin_mesas'))

@app.route('/admin/mesa/agregar-item/<int:cuenta_id>', methods=['POST'])
def agregar_item_mesa(cuenta_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    plato_id = request.form.get('plato_id')
    nombre_manual = request.form.get('nombre_manual')
    precio_manual_str = request.form.get('precio_manual')
    
    # PROTECCIÓN: Evita que manden letras y fuerza mínimo 1 cantidad
    try:
        cantidad = max(1, int(request.form.get('cantidad', 1)))
    except ValueError:
        cantidad = 1
    
    conn = get_db_connection()
    nombre = None
    precio = 0.0

    if plato_id and plato_id.strip() != "":
        plato = conn.execute('SELECT * FROM platos WHERE id = ?', (plato_id,)).fetchone()
        if plato:
            nombre = plato['nombre']
            precio = float(plato['precio'])
            
    elif nombre_manual and nombre_manual.strip() != "" and precio_manual_str:
        nombre = nombre_manual.strip()
        # PROTECCIÓN: Error de tipeo en precio manual
        try:
            precio = float(precio_manual_str.replace(',', '.'))
        except ValueError:
            precio = 0.0

    if nombre and precio > 0:
        conn.execute('INSERT INTO detalle_cuenta (cuenta_id, nombre_plato, precio, cantidad) VALUES (?, ?, ?, ?)',
                     (cuenta_id, nombre, precio, cantidad))
        
        subtotal = precio * cantidad
        conn.execute('UPDATE cuentas SET total = total + ? WHERE id = ?', (subtotal, cuenta_id))
        conn.commit()
        
    conn.close()
    return redirect(url_for('admin_mesas'))

@app.route('/admin/mesa/eliminar-item/<int:item_id>', methods=['POST'])
def eliminar_item_mesa(item_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    conn = get_db_connection()
    item = conn.execute('SELECT * FROM detalle_cuenta WHERE id = ?', (item_id,)).fetchone()
    
    if item:
        cuenta_id = item['cuenta_id']
        subtotal = round(float(item['precio']) * int(item['cantidad']), 2)
        
        conn.execute('DELETE FROM detalle_cuenta WHERE id = ?', (item_id,))
        conn.execute('UPDATE cuentas SET total = MAX(0, ROUND(total - ?, 2)) WHERE id = ?', (subtotal, cuenta_id))
        conn.commit()
        
    conn.close()
    return redirect(url_for('admin_mesas'))

@app.route('/admin/mesa/cerrar/<int:cuenta_id>', methods=['POST'])
def cerrar_mesa(cuenta_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    medio_pago = request.form.get('medio_pago', 'Efectivo')
    monto_final_str = request.form.get('monto_final', '').strip()
    hora_actual = datetime.now(ARG_TZA).strftime('%Y-%m-%d %H:%M:%S')
    
    conn = get_db_connection()
    
    if monto_final_str:
        # PROTECCIÓN: Si editan el total y ponen una letra, no revienta el sistema, solo ignora el cambio erróneo
        try:
            monto_final = float(monto_final_str.replace(',', '.'))
            conn.execute('UPDATE cuentas SET total = ? WHERE id = ?', (monto_final, cuenta_id))
        except ValueError:
            pass
    
    conn.execute('''
        UPDATE cuentas
        SET estado = "cerrada", medio_pago = ?, hora_cierre = ?
        WHERE id = ?
    ''', (medio_pago, hora_actual, cuenta_id))
    conn.commit()
    conn.close()
    
    return redirect(url_for('admin_mesas'))

if __name__ == '__main__':
    # CORRECCIÓN CRÍTICA: Ahora inicializa la BD antes de correr (evita el fallo en sistemas limpios)
    init_db()
    app.run(debug=True)