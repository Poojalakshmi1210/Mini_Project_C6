$(document).ready(function() {
    $('#send_btn').click(sendMessage);
    
    $('#user_input').keypress(function(e) {
        if (e.which == 13) {  // Enter key pressed
            sendMessage();
        }
    });

    $('#toggle_mode').click(function() {
        $('body').toggleClass('dark-mode');
        const mode = $('body').hasClass('dark-mode') ? 'Light Mode' : 'Dark Mode';
        $('#toggle_mode').text(`Switch to ${mode}`);
    });
});

function sendMessage() {
    const user_input = $('#user_input').val();
    if (user_input.trim() === "") return;

    $('#responses').append('<p><strong>You:</strong> ' + user_input + '</p>');
    $.post('/chat', { user_input: user_input }, function(data) {
        $('#responses').append('<p><strong>Chatbot:</strong> ' + data.response + '</p>');
        $('#user_input').val('');
        $('#chatbox').scrollTop($('#chatbox')[0].scrollHeight);  // Auto-scroll to the bottom
    });
}
// Handle form submission
        document.getElementById('quizForm').onsubmit = function(event) {
            event.preventDefault();
            const formData = new FormData(this);
            // Collect user answers from the quiz
            const userAnswers = Array.from(formData.values()).map(answer => answer.trim());
            // Send answers to the chat endpoint
            fetch('/chat', {
                method: 'POST',
                body: new URLSearchParams({ 'user_input': 'submit answers', 'answers': userAnswers }),
            })
            .then(response => response.json())
            .then(data => {
                // Display results
                // You will need to append results to your HTML
                console.log(data.response);
            });
        };