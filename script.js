// ==========================================
// 1. SISTEMA DE RESERVAS POR WHATSAPP
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
// 2. CONFIGURACIÓN DE FECHA AL CARGAR LA WEB
// ==========================================
document.addEventListener("DOMContentLoaded", function() {
  const inputFecha = document.getElementById('fecha');
  if (inputFecha) {
    const hoy = new Date().toISOString().split('T')[0];
    inputFecha.value = hoy;
    inputFecha.min = hoy; // Evita seleccionar días del pasado
  }
});

function mostrarSeccion(idSeccion, botonClickeado) {
  console.log("Intentando mostrar la sección:", idSeccion); // Esto saldrá en la consola

  // Ocultar todas las secciones
  const secciones = document.querySelectorAll('.seccion-carta');
  secciones.forEach(seccion => {
    seccion.classList.remove('activa');
  });

  // Quitar 'active' de todos los botones
  const botones = document.querySelectorAll('.filter-btn');
  botones.forEach(boton => {
    boton.classList.remove('active');
  });

  // Mostrar la seleccionada
  const seccionAMostrar = document.getElementById(idSeccion);
  if (seccionAMostrar) {
    seccionAMostrar.classList.add('activa');
    console.log("¡Sección encontrada y activada con éxito!");
  } else {
    console.error("¡ERROR! No se encontró ninguna sección con el ID:", idSeccion);
  }

  // Activar el botón presionado
  if (botonClickeado) {
    botonClickeado.classList.add('active');
  }
}
// ==========================================
// 4. FUNCIÓN PARA EL MENÚ HAMBURGUESA MÓVIL
// ==========================================
function toggleMenu() {
    var navLinks = document.querySelector('.nav-links');
    // Al agregar o quitar esta clase, el CSS se encarga de mostrarlo y animarlo
    navLinks.classList.toggle('active'); 
}