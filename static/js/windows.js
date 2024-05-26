//Открывает/закрывает корзину
const orderWrapTitle = document.querySelector('.order__wrap-title');

orderWrapTitle.addEventListener('click', () => {
  const order = document.querySelector('.catalog__order');
  order.classList.toggle('order_open');
});

//Открывает модальное окно с деталями при нажатии на название в карточке книги 
//и закрывает при нажатии на крестик
const buttons = document.querySelectorAll('.product__detail');
const modal = document.querySelector('.modal_product');
const closeButtonDetails = document.querySelector('.modal__close');

buttons.forEach(button => {
  button.addEventListener('click', () => {
    modal.classList.add('modal_open');
  });
});

closeButtonDetails.addEventListener('click', () => {
  modal.classList.remove('modal_open');
});

//В оформлении заказа при выборе "Самовывоз" скрывает поля для почты 
//(применяет класс modal-delivery__fieldset_hide)
// Select the radio buttons
const pickupRadio = document.querySelector('input[name="format"][value="pickup"]');
const deliveryRadio = document.querySelector('input[name="format"][value="delivery"]');

// Select the fieldset
const fieldset = document.querySelector('.modal-delivery__change-hidden');

// Add an event listener to the radio buttons
pickupRadio.addEventListener('change', () => {
  if (pickupRadio.checked) {
    // Add the hide class to the fieldset
    fieldset.classList.add('modal-delivery__fieldset_hide');
  }
});

deliveryRadio.addEventListener('change', () => {
  if (deliveryRadio.checked) {
    // Remove the hide class from the fieldset
    fieldset.classList.remove('modal-delivery__fieldset_hide');
  }
});







