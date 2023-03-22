const myButtons = document.querySelectorAll('button');
myButtons.forEach((myButton) => {
  myButton.addEventListener('click', () => {
    // Remove the active class from all buttons
    myButtons.forEach((button) => {
      button.classList.remove('active');
    });
    // Add the active class to the clicked button
    myButton.classList.add('active');
  });
});


const form = document.querySelector('#my-form');
form.addEventListener('submit', event => {
    event.preventDefault();
    const selected_value = event.submitter.value;
    fetch('/process', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded'
        },
        body: `selected_value=${selected_value}`
    })
    .then(response => response.json())
    .then(data => {
        // Update page content based on response data
        for (const key in data) {
            const element = document.querySelector(`#${key}`);
            if (element) {
                element.textContent = data[key];
            }
        }
    });
});