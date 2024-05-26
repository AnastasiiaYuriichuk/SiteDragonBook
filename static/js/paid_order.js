document.querySelectorAll('.order-cart__pay-btn').forEach(button => {
    button.addEventListener('click', function() {
        const orderCart = this.closest('.profile__order-cart');
        const orderId = orderCart.getAttribute('data-order-id');
        const statusElement = orderCart.querySelector('.order-status');
        const statusInput = orderCart.querySelector('.order-status-value');

        fetch('/pay_order', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': '{{ csrf_token() }}'  // Assuming you're using CSRF protection
            },
            body: JSON.stringify({ order_id: orderId })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Update the button and status text
                this.classList.add('paid');
                this.setAttribute('disabled', 'disabled');
                this.querySelector('span').textContent = "Оплачено";
                statusElement.textContent = "Оплачено";
                statusInput.value = 2;
            } else {
                console.error('Error:', data.message);
            }
        })
        .catch(error => {
            console.error('Error:', error);
        });
    });
});

