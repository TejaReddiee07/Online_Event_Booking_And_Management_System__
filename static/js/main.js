// Event Booking System - Dynamic Calculations
document.addEventListener('DOMContentLoaded', function() {
    
    // Booking form calculations (book_form.html)
    const fromDate = document.getElementById('from_date');
    const toDate = document.getElementById('to_date');
    const numPeople = document.getElementById('num_people');
    const totalHours = document.getElementById('total_hours');
    const totalPrice = document.getElementById('total_price');
    const hallPrice = {{ hall.price_per_hour if hall else 0 }}; // From backend

    function calculateTotals() {
        if (fromDate.value && toDate.value) {
            const from = new Date(fromDate.value + 'T00:00');
            const to = new Date(toDate.value + 'T23:59');
            const hours = (to - from) / (1000 * 60 * 60) + 1;
            totalHours.value = Math.max(1, Math.round(hours));
            
            const price = hallPrice * totalHours.value;
            totalPrice.value = Math.round(price * 100) / 100;
        }
    }

    if (fromDate && toDate) {
        fromDate.addEventListener('change', calculateTotals);
        toDate.addEventListener('change', calculateTotals);
        numPeople.addEventListener('input', calculateTotals);
    }

    // Table row hover (all tables)
    const rows = document.querySelectorAll('tbody tr');
    rows.forEach(row => {
        row.addEventListener('mouseenter', () => row.style.transform = 'scale(1.02)');
        row.addEventListener('mouseleave', () => row.style.transform = 'scale(1)');
    });

    // Modal auto-focus
    const modals = document.querySelectorAll('[data-bs-toggle="modal"]');
    modals.forEach(modal => {
        modal.addEventListener('click', function() {
            setTimeout(() => {
                const firstInput = document.querySelector('.modal .form-control');
                if (firstInput) firstInput.focus();
            }, 300);
        });
    });

    // Payment form simulation
    const paymentForm = document.getElementById('paymentForm');
    if (paymentForm) {
        paymentForm.addEventListener('submit', function(e) {
            e.preventDefault();
            alert('Payment successful! 🎉\nBooking requested - await admin approval.');
            window.location.href = '{{ url_for("organizer.bookings") }}';
        });
    }

    // Date pickers (today onwards)
    const dateInputs = document.querySelectorAll('input[type="date"]');
    dateInputs.forEach(input => {
        input.min = new Date().toISOString().split('T')[0];
    });

    console.log('EventHub JS loaded - calculations active');
});
