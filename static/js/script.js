document.getElementById('reservation-form').addEventListener('submit', function(event) {
    event.preventDefault();

    const name = document.getElementById('name').value;
    const people = document.getElementById('people').value;
    const phone = document.getElementById('phone').value;
    const agreement = document.getElementById('agreement').checked;

    if (!agreement) {
        alert('주의사항에 동의해주세요.');
        return;
    }

    fetch('/reserve', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ name, people: parseInt(people), phone }),
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            document.getElementById('message').textContent = '예약이 완료되었습니다!';
            document.getElementById('message').style.color = 'green';
        } else {
            document.getElementById('message').textContent = data.message;
        }
    })
    .catch(error => {
        console.error('Error:', error);
    });
});
