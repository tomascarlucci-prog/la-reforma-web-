import os
import mimetypes
from datetime import datetime, timezone, timedelta
from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash

import psycopg2
from psycopg2.extras import RealDictCursor

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.join(BASE_DIR, 'templates')

app = Flask(__name__, template_folder=TEMPLATE_DIR)

mimetypes.add_type('video/mp4', '.mp4')
mimetypes.add_type('video/webm', '.webm')

app.secret_key = 'reforma_secreta_key_2026'
# Zona horaria de Lomas del Mirador, Argentina (UTC-3)
ARG_TZA = timezone(timedelta(hours=-3))

def get_db_connection():
    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        raise ValueError("Falta configurar DATABASE_URL en el entorno")
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)
    conn = psycopg2.connect(db_url, cursor_factory=RealDictCursor)
    return conn

def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id SERIAL PRIMARY KEY,
            usuario TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            rol TEXT DEFAULT 'admin'
        )
    ''')
    
    cur.execute('''
        CREATE TABLE IF NOT EXISTS platos (
            id SERIAL PRIMARY KEY,
            nombre TEXT NOT NULL,
            categoria TEXT NOT NULL,
            precio REAL NOT NULL,
            descripcion TEXT,
            es_plato_del_dia INTEGER DEFAULT 0,
            disponible INTEGER DEFAULT 1
        )
    ''')

    cur.execute('''
        CREATE TABLE IF NOT EXISTS cuentas (
            id SERIAL PRIMARY KEY,
            numero_mesa TEXT NOT NULL,
            estado TEXT DEFAULT 'abierta',
            total REAL DEFAULT 0.0,
            hora_apertura TIMESTAMP,
            hora_cierre TIMESTAMP,
            medio_pago TEXT DEFAULT 'Efectivo'
        )
    ''')
    
    cur.execute('''
        CREATE TABLE IF NOT EXISTS detalle_cuenta (
            id SERIAL PRIMARY KEY,
            cuenta_id INTEGER,
            nombre_plato TEXT NOT NULL,
            precio REAL NOT NULL,
            cantidad INTEGER DEFAULT 1,
            FOREIGN KEY (cuenta_id) REFERENCES cuentas (id) ON DELETE CASCADE
        )
    ''')
    
    cur.execute('SELECT * FROM usuarios')
    user_check = cur.fetchone()
    if not user_check:
        hashed_pw = generate_password_hash('reforma2026')
        cur.execute('INSERT INTO usuarios (usuario, password_hash, rol) VALUES (%s, %s, %s)', ('admin', hashed_pw, 'admin'))
    
    conn.commit()
    cur.close()
    conn.close()

def limpiar_precio(precio_str):
    if not precio_str:
        return 0.0
    s = str(precio_str).replace('$', '').strip()
    if '.' in s and ',' in s:
        s = s.replace('.', '').replace(',', '.')
    elif ',' in s:
        s = s.replace(',', '.')
    elif '.' in s:
        partes = s.split('.')
        if len(partes[-1]) == 3:
            s = s.replace('.', '')
    try:
        return round(float(s), 2)
    except ValueError:
        return 0.0

try:
    init_db()
    print("Base de datos e inicialización verificadas con éxito.")
except Exception as e:
    print(f"Aviso al inicializar la base de datos: {e}")

@app.route('/')
def index():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM platos WHERE es_plato_del_dia = 1 AND disponible = 1')
    platos_del_dia = cur.fetchall()
    
    cur.execute('SELECT * FROM platos WHERE disponible = 1')
    todos_los_platos = cur.fetchall()
    
    cur.close()
    conn.close()
    return render_template('index.html', platos_del_dia=platos_del_dia, platos=todos_los_platos)

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['usuario']
        password = request.form['password']
        
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT * FROM usuarios WHERE usuario = %s', (username,))
        user = cur.fetchone()
        cur.close()
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
    cur = conn.cursor()
    cur.execute('SELECT * FROM platos')
    platos = cur.fetchall()
    cur.close()
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
    precio = limpiar_precio(request.form['precio'])
    
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('INSERT INTO platos (nombre, descripcion, precio, categoria, disponible, es_plato_del_dia) VALUES (%s, %s, %s, %s, 1, %s)',
                 (nombre, descripcion, precio, categoria, es_plato_del_dia))
    conn.commit()
    cur.close()
    conn.close()
    
    return redirect(url_for('admin') + '#seccion-platos')

@app.route('/admin/toggle-disponible/<int:id>')
def toggle_disponible(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT disponible FROM platos WHERE id = %s', (id,))
    plato = cur.fetchone()
    
    nuevo_estado = 0 if plato['disponible'] == 1 else 1
    cur.execute('UPDATE platos SET disponible = %s WHERE id = %s', (nuevo_estado, id))
    conn.commit()
    cur.close()
    conn.close()
    
    return redirect(url_for('admin') + '#seccion-platos')

@app.route('/admin/toggle-dia/<int:id>')
def toggle_dia(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT es_plato_del_dia FROM platos WHERE id = %s', (id,))
    plato = cur.fetchone()
    
    nuevo_estado = 0 if plato['es_plato_del_dia'] == 1 else 1
    cur.execute('UPDATE platos SET es_plato_del_dia = %s WHERE id = %s', (nuevo_estado, id))
    conn.commit()
    cur.close()
    conn.close()
    
    return redirect(url_for('admin') + '#seccion-platos')

@app.route('/admin/editar/<int:id>', methods=['POST'])
def editar_plato(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    nombre = request.form['nombre']
    descripcion = request.form['descripcion']
    categoria = request.form.get('categoria', 'Platos Principales')
    precio = limpiar_precio(request.form['precio'])
    
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''
        UPDATE platos
        SET nombre = %s, descripcion = %s, precio = %s, categoria = %s
        WHERE id = %s
    ''', (nombre, descripcion, precio, categoria, id))
    conn.commit()
    cur.close()
    conn.close()
    
    return redirect(url_for('admin') + '#seccion-platos')


# RUTAS DE GESTIÓN DE MESAS Y CAJA

@app.route('/admin/mesas')
def admin_mesas():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("SELECT * FROM cuentas WHERE estado = 'abierta'")
    mesas_abiertas = cur.fetchall()
    
    # Procesar hora de apertura para la vista
    for mesa in mesas_abiertas:
        if isinstance(mesa['hora_apertura'], datetime):
            mesa['hora_apertura_str'] = mesa['hora_apertura'].strftime('%H:%M')
        elif mesa['hora_apertura']:
            mesa['hora_apertura_str'] = str(mesa['hora_apertura'])[11:16]
        else:
            mesa['hora_apertura_str'] = "--:--"
    
    detalle_por_mesa = {}
    for mesa in mesas_abiertas:
        cur.execute("SELECT * FROM detalle_cuenta WHERE cuenta_id = %s", (mesa['id'],))
        detalle_por_mesa[mesa['id']] = cur.fetchall()
        
    cur.execute("SELECT * FROM platos WHERE disponible = 1")
    platos = cur.fetchall()
    
    hoy_str = datetime.now(ARG_TZA).strftime('%Y-%m-%d')
    fecha_seleccionada = request.args.get('fecha')
    if not fecha_seleccionada:
        fecha_seleccionada = hoy_str
        
    # Extraer historial del día seleccionado (Filtrando directo como texto date para evitar bugs en Postgres)
    cur.execute('''
        SELECT medio_pago, SUM(total) as subtotal
        FROM cuentas
        WHERE estado = 'cerrada' AND DATE(hora_cierre) = %s
        GROUP BY medio_pago
    ''', (fecha_seleccionada,))
    totales_pagos = cur.fetchall()
    
    resumen_caja = {'Efectivo': 0.0, 'Mercado Pago': 0.0, 'Tarjeta': 0.0}
    total_general = 0.0
    
    for row in totales_pagos:
        mp_db = row['medio_pago']
        sub = float(row['subtotal']) if row['subtotal'] else 0.0
        total_general += sub
        
        if mp_db:
            mp_texto = mp_db.lower().strip()
            if 'mercado' in mp_texto or 'mp' in mp_texto:
                resumen_caja['Mercado Pago'] += sub
            elif 'tarjeta' in mp_texto:
                resumen_caja['Tarjeta'] += sub
            else:
                resumen_caja['Efectivo'] += sub
                
    cur.execute('''
        SELECT * FROM cuentas
        WHERE estado = 'cerrada' AND DATE(hora_cierre) = %s
        ORDER BY hora_cierre DESC
    ''', (fecha_seleccionada,))
    historial = cur.fetchall()
    
    for hc in historial:
        if isinstance(hc['hora_apertura'], datetime):
            hc['hora_apertura_str'] = hc['hora_apertura'].strftime('%H:%M')
        else:
            hc['hora_apertura_str'] = str(hc['hora_apertura'])[11:16] if hc['hora_apertura'] else "--:--"
            
        if isinstance(hc['hora_cierre'], datetime):
            hc['hora_cierre_str'] = hc['hora_cierre'].strftime('%H:%M')
        else:
            hc['hora_cierre_str'] = str(hc['hora_cierre'])[11:16] if hc['hora_cierre'] else "--:--"

    cur.close()
    conn.close()
    
    return render_template(
        'mesas.html',
        mesas=mesas_abiertas,
        detalle_por_mesa=detalle_por_mesa,
        platos=platos,
        resumen_caja=resumen_caja,
        total_general=total_general,
        historial=historial,
        hoy_str=hoy_str,
        fecha_seleccionada=fecha_seleccionada
    )

@app.route('/admin/mesa/abrir', methods=['POST'])
def abrir_mesa():
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    numero_mesa = request.form['numero_mesa']
    # Enviar texto exacto de la hora local a Postgres para evitar desfasajes en Render
    hora_actual_str = datetime.now(ARG_TZA).strftime('%Y-%m-%d %H:%M:%S')
    
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''
        INSERT INTO cuentas (numero_mesa, estado, total, hora_apertura)
        VALUES (%s, 'abierta', 0.0, %s)
    ''', (numero_mesa, hora_actual_str))
    conn.commit()
    cur.close()
    conn.close()
    
    return redirect(url_for('admin_mesas'))

@app.route('/admin/mesa/agregar-item/<int:mesa_id>', methods=['POST'])
def agregar_item_mesa(mesa_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    plato_id = request.form.get('plato_id')
    nombre_manual = request.form.get('nombre_manual')
    precio_manual = request.form.get('precio_manual')
    cantidad = int(request.form.get('cantidad', 1))
    
    nombre_plato = ""
    precio_plato = 0.0
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    if plato_id:
        cur.execute("SELECT * FROM platos WHERE id = %s", (plato_id,))
        plato = cur.fetchone()
        if plato:
            nombre_plato = plato['nombre']
            precio_plato = float(plato['precio'])
    elif nombre_manual and precio_manual:
        nombre_plato = nombre_manual
        precio_plato = limpiar_precio(precio_manual)
        
    if nombre_plato and precio_plato > 0:
        cur.execute('''
            INSERT INTO detalle_cuenta (cuenta_id, nombre_plato, precio, cantidad)
            VALUES (%s, %s, %s, %s)
        ''', (mesa_id, nombre_plato, precio_plato, cantidad))
        
        cur.execute('''
            SELECT SUM(precio * cantidad) as total FROM detalle_cuenta WHERE cuenta_id = %s
        ''', (mesa_id,))
        res = cur.fetchone()
        nuevo_total = float(res['total']) if res and res['total'] else 0.0
        
        cur.execute('''
            UPDATE cuentas SET total = %s WHERE id = %s
        ''', (nuevo_total, mesa_id))
        
        conn.commit()
        
    cur.close()
    conn.close()
    
    return redirect(url_for('admin_mesas'))

@app.route('/admin/mesa/eliminar-item/<int:item_id>', methods=['POST'])
def eliminar_item_mesa(item_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("SELECT cuenta_id FROM detalle_cuenta WHERE id = %s", (item_id,))
    item = cur.fetchone()
    
    if item:
        cuenta_id = item['cuenta_id']
        cur.execute("DELETE FROM detalle_cuenta WHERE id = %s", (item_id,))
        
        cur.execute("SELECT SUM(precio * cantidad) as total FROM detalle_cuenta WHERE cuenta_id = %s", (cuenta_id,))
        res = cur.fetchone()
        nuevo_total = float(res['total']) if res and res['total'] else 0.0
        
        cur.execute("UPDATE cuentas SET total = %s WHERE id = %s", (nuevo_total, cuenta_id))
        conn.commit()
        
    cur.close()
    conn.close()
    
    return redirect(url_for('admin_mesas'))

@app.route('/admin/mesa/cerrar/<int:mesa_id>', methods=['POST'])
def cerrar_mesa(mesa_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    monto_final = limpiar_precio(request.form.get('monto_final'))
    medio_pago = request.form.get('medio_pago', 'Efectivo')
    
    # Enviar texto exacto de la hora local
    hora_cierre_str = datetime.now(ARG_TZA).strftime('%Y-%m-%d %H:%M:%S')
    
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''
        UPDATE cuentas
        SET estado = 'cerrada', total = %s, medio_pago = %s, hora_cierre = %s
        WHERE id = %s
    ''', (monto_final, medio_pago, hora_cierre_str, mesa_id))
    
    conn.commit()
    cur.close()
    conn.close()
    
    return redirect(url_for('admin_mesas'))

@app.route('/admin/mesa/eliminar-historial/<int:mesa_id>', methods=['POST'])
def eliminar_historial_mesa(mesa_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    conn = get_db_connection()
    cur = conn.cursor()
    # Primero se elimina el detalle por las relaciones
    cur.execute("DELETE FROM detalle_cuenta WHERE cuenta_id = %s", (mesa_id,))
    # Luego se elimina la cuenta en sí
    cur.execute("DELETE FROM cuentas WHERE id = %s", (mesa_id,))
    conn.commit()
    cur.close()
    conn.close()
    
    return redirect(url_for('admin_mesas'))

@app.route('/imprimir-ticket/<int:mesa_id>')
def imprimir_ticket(mesa_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM cuentas WHERE id = %s", (mesa_id,))
    mesa = cur.fetchone()
    
    cur.execute("SELECT * FROM detalle_cuenta WHERE cuenta_id = %s", (mesa_id,))
    detalle = cur.fetchall()
    
    cur.close()
    conn.close()
    
    if not mesa:
        return "Mesa no encontrada", 404
        
    return render_template('ticket.html', mesa=mesa, detalle=detalle)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)