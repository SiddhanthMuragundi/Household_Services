
    // Show the alert on page load (for demo purposes)
    window.onload = function() {
        const alertContainer = document.querySelector('.alert-container');
        alertContainer.classList.add('show');
    };

    // Close the alert when the close button is clicked
    const closeButton = document.querySelector('.close');
    closeButton.addEventListener('click', function() {
        const alertContainer = document.querySelector('.alert-container');
        alertContainer.classList.remove('show');
    });

