document.addEventListener('DOMContentLoaded', function() {
    // get the triangle indicator and the form
    const indicator = document.getElementById('next-indicator');
    const form = document.getElementById('next-form');
    
    // add click event indicator thing
    if (indicator && form) {
        indicator.addEventListener('click', function() {
            form.submit();
        });
    }
});