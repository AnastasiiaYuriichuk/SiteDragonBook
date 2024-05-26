// static/js/main.js
document.addEventListener('DOMContentLoaded', function() {
    const signinBtn = document.querySelector('.signin-btn');
    const signupBtn = document.querySelector('.signup-btn');
    const formBox = document.querySelector('.form-box');

    signinBtn.addEventListener('click', () => {
        formBox.classList.remove('active');
    });

    signupBtn.addEventListener('click', () => {
        formBox.classList.add('active');
    });
});
