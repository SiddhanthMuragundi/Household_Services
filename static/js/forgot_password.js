let selectedButton = null;

// Function to handle user selection
function selectUser(button) {
    const selectedUser = button.getAttribute('data-user');
    const userRoleInput = document.getElementById('user-role');
    userRoleInput.value = selectedUser;

    // Show the "Secret Key" field if the admin is selected
    if (selectedUser === 'admin') {
        document.getElementById('secret-key-container').style.display = 'block';
    } else {
        document.getElementById('secret-key-container').style.display = 'none';
    }

    // Change the background color of the selected button
    if (selectedButton) {
        selectedButton.style.backgroundColor = 'transparent'; // Reset previous selection
    }
    selectedButton = button;
    button.style.backgroundColor = 'lightgrey'; // Highlight selected button
}
