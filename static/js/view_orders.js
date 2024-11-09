function showTab(tabName) {
    const tabs = document.querySelectorAll('.tab-content');
    const buttons = document.querySelectorAll('.tab-button');

    tabs.forEach(tab => {
        tab.classList.remove('active');
    });

    buttons.forEach(button => {
        button.classList.remove('active');
    });

    document.getElementById(tabName).classList.add('active');
    event.currentTarget.classList.add('active');
}




    function toggleFlag(event) {
        const checkbox = event.currentTarget.querySelector('input[type="checkbox"]');
        const orderId = event.currentTarget.dataset.orderId;

        // Toggle the checked state
        checkbox.checked = !checkbox.checked; 
        
        // Change the icon color based on the checked state
        const flagIcon = event.currentTarget.querySelector('i');
        flagIcon.style.color = checkbox.checked ? 'red' : 'gray'; 

        // AJAX call to update the flag status in the database
        fetch(`/update_flag/${orderId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ flag: checkbox.checked })
        });
    }

