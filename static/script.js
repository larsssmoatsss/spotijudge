document.addEventListener('DOMContentLoaded', function() {
    // Get the triangle indicator and the form
    const indicator = document.getElementById('next-indicator');
    const form = document.getElementById('next-form');
    
    // Add click event to the indicator
    if (indicator && form) {
        indicator.addEventListener('click', function() {
            form.submit();
        });
    }
});