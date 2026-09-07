import sqlite3

conn = sqlite3.connect('database.db')
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS platos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    categoria TEXT NOT NULL,
    precio REAL NOT NULL,
    descripcion TEXT,
    es_plato_del_dia INTEGER DEFAULT 0,
    disponible INTEGER DEFAULT 1
)
''')

cursor.execute('''
INSERT INTO platos (nombre, categoria, precio, descripcion, es_plato_del_dia, disponible)
VALUES ('Milanesa con Papas Fritas', 'Minutas', 17500.0, 'Milanesa de ternera con papas crocantes', 1, 1)
''')

conn.commit()
conn.close()
print("¡Base de datos creada exitosamente adentro de la carpeta!")
