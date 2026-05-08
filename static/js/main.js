// static/js/main.js

document.addEventListener('DOMContentLoaded', function () {

    // Inicializar tooltips de Bootstrap
    document.querySelectorAll('[data-bs-toggle="tooltip"]')
        .forEach(el => new bootstrap.Tooltip(el));

    // Auto-cerrar alertas flash después de 5 segundos
    // (complementa la animación CSS del styles.css)
    setTimeout(function () {
        document.querySelectorAll('.alert').forEach(function (alert) {
            const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
            bsAlert.close();
        });
    }, 5000);

    // Confirmación antes de eliminar
    // Uso en el template: <a href="..." onclick="return confirmar()">Eliminar</a>
    window.confirmar = function (mensaje) {
        return confirm(mensaje || '¿Estás seguro?');
    };

    // Resaltar fila al hacer clic (navegación intuitiva)
    // Uso en el template: <tr class="fila-link" data-href="{% url '...' %}">
    document.querySelectorAll('.fila-link').forEach(function (fila) {
        fila.addEventListener('click', function () {
            window.location = this.dataset.href;
        });
    });

});