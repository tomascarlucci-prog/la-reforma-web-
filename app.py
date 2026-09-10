import os
import mimetypes
from datetime import datetime, timezone, timedelta
from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash

# Nuevas librerías para conectarnos a PostgreSQL (Supabase)
import psycopg2
from psycopg2.extras import RealDictCursor

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.join(BASE_DIR, 'templates')

app = Flask(__name__, template_folder=TEMPLATE_DIR)

# Forzamos los tipos MIME para archivos multimedia
mimetypes.add_type('video/mp4', '.mp4')
mimetypes.add_type('video/webm', '.webm')

app.secret_key = 'reforma_secreta_key_2026'

# Zona horaria fija para Argentina (UTC-3)
ARG_TZA = timezone(timedelta(hours=-3))

def get_db_connection():
    # Render va a leer la variable que configuraste en el panel
    db_url = os.environ.get('DATABASE_URL')
    
    if not db_url:
        raise ValueError("Falta configurar DATABASE_URL en el entorno (Si estás probando en tu PC, configúrala en tu terminal o usa un archivo .env)")
        
    # Corrección automática del prefijo para SQLAlchemy/psycopg2
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)
        
    # Nos conectamos a Supabase pidiéndole que devuelva los datos como diccionarios
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
            FOREIGN KEY (cuenta_id) REFERENCES cuentas (id)
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


# ------------------------------------------------------------------
# Inicialización automática al arrancar el servidor en Render (Gunicorn)
# ------------------------------------------------------------------
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
    
    # PROTECCIÓN: Si el usuario escribe mal el precio, se guarda como 0.0
    try:
        precio_str = request.form['precio'].replace(',', '.')
        precio = float(precio_str)
    except ValueError:
        precio = 0.0
    
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
    
    try:
        precio_str = request.form['precio'].replace(',', '.')
        precio = float(precio_str)
    except ValueError:
        precio = 0.0
    
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


# ------------------ GESTIÓN DE MESAS Y CAJA DIARIA/HISTORIAL ------------------

@app.route('/admin/mesas')
def admin_mesas():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("SELECT * FROM cuentas WHERE estado = 'abierta'")
    mesas_abiertas = cur.fetchall()
    
    cur.execute("SELECT * FROM platos WHERE disponible = 1")
    platos = cur.fetchall()
    
    hoy_str = datetime.now(ARG_TZA).strftime('%Y-%m-%d')
    fecha_seleccionada = request.args.get('fecha')
    if not fecha_seleccionada:
        fecha_seleccionada = hoy_str
        
    # CORRECCIÓN: CAST(hora_cierre AS TEXT) para que el LIKE funcione perfecto en Postgres
    cur.execute('''
        SELECT medio_pago, SUM(total) as subtotal
        FROM cuentas
        WHERE estado = 'cerrada' AND CAST(hora_cierre AS TEXT) LIKE %s
        GROUP BY medio_pago
    ''', (fecha_seleccionada + '%',))
    totales_pagos = cur.fetchall()
    
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

    cur.execute('''
        SELECT * FROM cuentas
        WHERE estado = 'cerrada' AND CAST(hora_cierre AS TEXT) LIKE %s
        ORDER BY hora_cierre DESC
    ''', (fecha_seleccionada + '%',))
    historial_dia = cur.fetchall()

    detalle_por_mesa = {}
    for mesa in mesas_abiertas:
        cur.execute('SELECT * FROM detalle_cuenta WHERE cuenta_id = %s', (mesa['id'],))
        items = cur.fetchall()
        detalle_por_mesa[mesa['id']] = items

    cur.close()
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
    cur = conn.cursor()
    cur.execute("INSERT INTO cuentas (numero_mesa, estado, hora_apertura) VALUES (%s, 'abierta', %s)", (numero_mesa, hora_actual))
    conn.commit()
    cur.close()
    conn.close()
    
    return redirect(url_for('admin_mesas'))

@app.route('/admin/mesa/agregar-item/<int:cuenta_id>', methods=['POST'])
def agregar_item_mesa(cuenta_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    plato_id = request.form.get('plato_id')
    nombre_manual = request.form.get('nombre_manual')
    precio_manual_str = request.form.get('precio_manual')
    
    try:
        cantidad = max(1, int(request.form.get('cantidad', 1)))
    except ValueError:
        cantidad = 1
    
    conn = get_db_connection()
    cur = conn.cursor()
    nombre = None
    precio = 0.0

    if plato_id and plato_id.strip() != "":
        cur.execute('SELECT * FROM platos WHERE id = %s', (plato_id,))
        plato = cur.fetchone()
        if plato:
            nombre = plato['nombre']
            precio = float(plato['precio'])
            
    elif nombre_manual and nombre_manual.strip() != "" and precio_manual_str:
        nombre = nombre_manual.strip()
        try:
            precio = float(precio_manual_str.replace(',', '.'))
        except ValueError:
            precio = 0.0

    if nombre and precio > 0:
        cur.execute('INSERT INTO detalle_cuenta (cuenta_id, nombre_plato, precio, cantidad) VALUES (%s, %s, %s, %s)',
                     (cuenta_id, nombre, precio, cantidad))
        
        subtotal = precio * cantidad
        cur.execute('UPDATE cuentas SET total = total + %s WHERE id = %s', (subtotal, cuenta_id))
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
    cur.execute('SELECT * FROM detalle_cuenta WHERE id = %s', (item_id,))
    item = cur.fetchone()
    
    if item:
        cuenta_id = item['cuenta_id']
        subtotal = round(float(item['precio']) * int(item['cantidad']), 2)
        
        cur.execute('DELETE FROM detalle_cuenta WHERE id = %s', (item_id,))
        
        # Leemos el total actual y lo recalculamos seguro en Python
        cur.execute('SELECT total FROM cuentas WHERE id = %s', (cuenta_id,))
        cuenta = cur.fetchone()
        if cuenta:
            nuevo_total = max(0.0, round(float(cuenta['total']) - subtotal, 2))
            cur.execute('UPDATE cuentas SET total = %s WHERE id = %s', (nuevo_total, cuenta_id))
            
        conn.commit()
        
    cur.close()
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
    cur = conn.cursor()
    
    if monto_final_str:
        try:
            monto_final = float(monto_final_str.replace(',', '.'))
            cur.execute('UPDATE cuentas SET total = %s WHERE id = %s', (monto_final, cuenta_id))
        except ValueError:
            pass
    
    cur.execute('''
        UPDATE cuentas
        SET estado = 'cerrada', medio_pago = %s, hora_cierre = %s
        WHERE id = %s
    ''', (medio_pago, hora_actual, cuenta_id))
    
    conn.commit()
    cur.close()
    conn.close()
    
    return redirect(url_for('admin_mesas'))


# ------------------ SISTEMA DE TICKETS (TÉRMICA SAM4S) ------------------

@app.route('/imprimir-ticket/<int:mesa_id>')
def imprimir_ticket(mesa_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute('SELECT * FROM cuentas WHERE id = %s', (mesa_id,))
    cuenta = cur.fetchone()
    
    if not cuenta:
        cur.close()
        conn.close()
        return redirect(url_for('admin_mesas'))
        
    cur.execute('SELECT * FROM detalle_cuenta WHERE cuenta_id = %s', (mesa_id,))
    items_db = cur.fetchall()
    
    cur.close()
    conn.close()
    
    datos_mesa = {
        "numero": cuenta['numero_mesa'],
        "total": cuenta['total'],
        "items": []
    }
    
    for item in items_db:
        datos_mesa["items"].append({
            "cantidad": item['cantidad'],
            "detalle": item['nombre_plato'],
            "precio": round(item['precio'] * item['cantidad'], 2)
        })
        
    return render_template('ticket.html', mesa=datos_mesa)


if __name__ == '__main__':
    # Inicializa la BD antes de correr
    init_db()
    app.run(debug=True)