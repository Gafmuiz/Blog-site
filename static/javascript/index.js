document.addEventListener('DOMContentLoaded', function () {
    // correct selector — matches elements with class "alert"
    const flashes = document.querySelectorAll('.alert');

    flashes.forEach((flash) => {
        setTimeout(() => {
            flash.style.transition = "opacity 0.5s";  // ✅ use .style not .computedStyleMap
            flash.style.opacity = '0';

            setTimeout(() => flash.remove(), 500);
        }, 2000);
    });
});