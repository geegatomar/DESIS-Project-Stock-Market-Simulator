window.onload = function(){
    const signUpButton = document.getElementById('signUp');
    const signInButton = document.getElementById('signIn');
    const container = document.getElementById('container');

    signUpButton.addEventListener('click', handler1);
    signInButton.addEventListener('click', handler2);
}

function handler2(){
    container.classList.remove("right-panel-active");
}

function handler1(){
    container.classList.add("right-panel-active");
}