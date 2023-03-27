const myButtons = document.querySelectorAll('.select');
const form = document.querySelector('#my-form');

myButtons.forEach((myButton) => {
  myButton.addEventListener('click', () => {
    myButtons.forEach((button) => {
      button.classList.remove('active');
    });
    myButton.classList.add('active');
  });
});

function copyToClipboard(textarea_id, span_id) {
  var textarea = document.getElementById(textarea_id);
  var text = textarea.value;
  navigator.clipboard.writeText(text)
    .then(() => {
      document.getElementById(span_id).textContent = "Copied!";
      setTimeout(function() {
        document.getElementById(span_id).innerHTML = '<i class="fa-solid fa-copy"></i>';
      }, 3000);
    })
    .catch(err => {
      console.error('Failed to copy text: ', err);
    });
}

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
        for (const key in data) {
            const element = document.querySelector(`#${key}`);
            if (element) {
                element.textContent = data[key];
            }
        }
    });
});