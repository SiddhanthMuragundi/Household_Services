function showForm(type) {
    const customerForm = document.getElementById('customer-form');
    const serviceForm = document.getElementById('service-prof-form');

    if (type === 'customer') { 
        // Show customer form, hide service form
        customerForm.classList.remove('hidden');
        serviceForm.classList.add('hidden');
    } else if (type === 'service') {
        // Show service form, hide customer form
        customerForm.classList.add('hidden');
        serviceForm.classList.remove('hidden');
    }
}
