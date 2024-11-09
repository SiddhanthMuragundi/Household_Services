let selectedButton = null;

function selectUser(button) {
    const userType = button.getAttribute('data-user');
    const userRoleInput = document.getElementById('user-role');
    userRoleInput.value = userType;

    if (selectedButton) {
        selectedButton.style.backgroundColor = 'transparent'; // Reset previous selection
    }
    selectedButton = button;
    button.style.backgroundColor = 'lightgrey';  // Highlight selected button
}
