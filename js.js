document.addEventListener("DOMContentLoaded", function () {
    let navbarToggle = document.querySelector('#navbar-toggle');
    
    navbarToggle.addEventListener('click', function () {
        let navbarLinks = document.querySelector('.navbar-links');
        if (navbarToggle.checked) {
            navbarLinks.style.display = 'block';
        } else{
            navbarLinks.style.display = 'none';
        }
    });
});
