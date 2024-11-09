function showSection(sectionId, button) {
    // Hide all sections
    const sections = document.querySelectorAll('.section');
    sections.forEach(section => {
        section.style.display = 'none';
    });

    // Show the selected section
    document.getElementById(sectionId).style.display = 'block';

    // Remove active class from all buttons
    const buttons = document.querySelectorAll('.nav-button');
    buttons.forEach(btn => {
        btn.classList.remove('active');
    });

    // Add active class to the clicked button
    button.classList.add('active');
}