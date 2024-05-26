function updateOrderStatus(orderId) {
    var statusId = document.getElementById('status_' + orderId).value;

    fetch('/admin/update_order_status', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            order_id: orderId,
            status_id: statusId
        }),
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('Статус заказа успешно обновлен.');
            location.reload(); // Обновление страницы после успешного обновления статуса
        } else {
            alert('Произошла ошибка при обновлении статуса заказа.');
        }
    })
    .catch((error) => {
        console.error('Ошибка:', error);
    });
}

