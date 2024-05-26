document.addEventListener("DOMContentLoaded", function() {
    // Функция для обновления общей суммы в корзине
    function updateTotalAmount() {
        const items = document.querySelectorAll('.order__item');
        let total = 0;
        items.forEach(item => {
            const price = parseFloat(item.querySelector('.order__product-price').innerText);
            const quantity = parseInt(item.querySelector('.count__amount').innerText);
            total += price * quantity;
        });
        document.querySelector('.order__total-amount').innerText = total.toFixed(2);
    }

    // Обработчик события для кнопок увеличения и уменьшения количества товара
    document.querySelectorAll('.count__wrapper').forEach(wrapper => {
        const minusButton = wrapper.querySelector('.count_minus');
        const plusButton = wrapper.querySelector('.count_plus');
        const amountText = wrapper.querySelector('.count__amount');

        minusButton.addEventListener('click', function() {
            let amount = parseInt(amountText.innerText);
            if (amount > 1) {
                amount--;
                amountText.innerText = amount;
                updateTotalAmount();
            }
        });

        plusButton.addEventListener('click', function() {
            let amount = parseInt(amountText.innerText);
            amount++;
            amountText.innerText = amount;
            updateTotalAmount();
        });
    });

    // Обработчик события для кнопки "Оформити замовлення"
    document.querySelector('.order__submit').addEventListener('click', function() {
        alert('Замовлення успішно оформлено!');
        // Здесь можно добавить отправку данных корзины на сервер и сохранение заказа в базе данных
        // После успешного оформления заказа, можно очистить корзину
        document.querySelectorAll('.order__item').forEach(item => {
            item.remove();
        });
        document.querySelector('.order__total-amount').innerText = '0.00';
        document.querySelector('.order__count').innerText = '0';
    });

    // Обработчик события для кнопки закрытия корзины
    document.querySelector('.order__close').addEventListener('click', function() {
        document.querySelector('.catalog__order').classList.remove('order_open');
    });
});