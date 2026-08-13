// ==========================================
// 1. FILTRADO DEL MENÚ POR CATEGORÍA
// ==========================================
function filtrarMenu(categoria, event) {
  const tarjetas = document.querySelectorAll('.dish-card');
  const botones = document.querySelectorAll('.filter-btn');

  botones.forEach(btn => btn.classList.remove('active'));
  if (event) {
    event.target.classList.add('active');
  }

  tarjetas.forEach(tarjeta => {
    if (categoria === 'todos' || tarjeta.dataset.categoria === categoria) {
      tarjeta.style.display = 'flex';
    } else {
      tarjeta.style.display = 'none';
    }
  });
}

// ==========================================
// 2. SISTEMA DE RESERVAS POR WHATSAPP
// ==========================================
function enviarWhatsApp(e) {
  e.preventDefault();
  
  const nombre = document.getElementById('nombre').value;
  const personas = document.getElementById('personas').value;
  const fecha = document.getElementById('fecha').value;
  const hora = document.getElementById('hora').value;

  const telefono = "5491154510569"; 
  
  const mensaje = `Hola *La Reforma*! 🍝 Queríamos solicitar una reserva para comer allá:%0A%0A` +
                  `👤 *Nombre:* ${nombre}%0A` +
                  `👥 *Mesa para:* ${personas}%0A` +
                  `📅 *Fecha:* ${fecha}%0A` +
                  `⏰ *Horario:* ${hora} hs%0A%0A` +
                  `¿Tienen disponibilidad? ¡Muchas gracias!`;

  const url = `https://wa.me/${telefono}?text=${mensaje}`;
  window.open(url, '_blank');
}

// ==========================================
// 3. CONFIGURACIÓN DE FECHA AL CARGAR LA WEB
// ==========================================
document.addEventListener("DOMContentLoaded", function() {
  const inputFecha = document.getElementById('fecha');
  if (inputFecha) {
    const hoy = new Date().toISOString().split('T')[0];
    inputFecha.value = hoy;
    inputFecha.min = hoy;
  }
});
/* Contenedor de botones con scroll horizontal prolijo para celulares */
.menu-filters {
  display: flex;
  gap: 10px;
  overflow-x: auto;
  padding: 15px 20px;
  background-color: #1a1a1a;
  white-space: nowrap;
  scrollbar-width: thin;
  scrollbar-color: #ff4d4d #2a2a2a;
}

/* Estilo de los botones del menú */
.filter-btn {
  background-color: #2a2a2a;
  color: #ffffff;
  border: 1px solid #444;
  padding: 10px 18px;
  border-radius: 20px;
  cursor: pointer;
  font-size: 0.95rem;
  transition: all 0.3s ease;
  flex-shrink: 0;
}

.filter-btn:hover {
  background-color: #ff4d4d;
  border-color: #ff4d4d;
}

/* Botón activo (seleccionado) */
.filter-btn.active {
  background-color: #ff4d4d;
  color: white;
  border-color: #ff4d4d;
  font-weight: bold;
  box-shadow: 0 0 10px rgba(255, 77, 77, 0.4);
}

<script>
  function mostrarSeccion(idSeccion, botonClickeado) {
    // 1. Ocultar todas las secciones de la carta
    const secciones = document.querySelectorAll('.seccion-carta');
    secciones.forEach(seccion => {
      seccion.classList.remove('activa');
    });

    // 2. Quitar la clase 'active' de todos los botones
    const botones = document.querySelectorAll('.filter-btn');
    botones.forEach(boton => {
      boton.classList.remove('active');
    });

    // 3. Mostrar únicamente la sección seleccionada
    const seccionAMostrar = document.getElementById(idSeccion);
    if (seccionAMostrar) {
      seccionAMostrar.classList.add('activa');
    }

    // 4. Activar el botón que se presionó
    botonClickeado.classList.add('active');
  }
</script>