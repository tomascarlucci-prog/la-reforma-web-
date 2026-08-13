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
/* ========================================= */
/* FUNCIÓN PARA MOSTRAR LAS SECCIONES DE LA CARTA */
/* ========================================= */
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

/* ========================================= */
/* FUNCIÓN PARA EL MENÚ HAMBURGUESA MÓVIL */
/* ========================================= */
function toggleMenu() {
  const menu = document.querySelector('.nav-links');
  if (menu.style.display === 'flex') {
    menu.style.display = 'none';
  } else {
    menu.style.display = 'flex';
  }
}