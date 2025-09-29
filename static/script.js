// Wait until the HTML document is fully loaded before running the script
document.addEventListener("DOMContentLoaded", function() {

    // Get the input element where the user types their answer
    const input = document.getElementById("answerInput");

    // Set a maximum allowed number of digits in the input
    const maxDigits = 16;

    // Get the correct answer from Flask and ensure it's treated as a string
    const correctAnswer = "{{ correct_answer|string }}";  

    // Add an event listener that runs every time the user types in the input
    input.addEventListener("input", function() {

        // If the user typed more digits than allowed, truncate the extra digits
        if (input.value.length > maxDigits) {
            input.value = input.value.slice(0, maxDigits);
        }

        // If the input matches the correct answer, submit the form automatically
        // Using == instead of === allows comparison between string and number
        // trim() removes any accidental whitespace from the input
        if (input.value.trim() == correctAnswer) {
            input.form.submit();
        }
    });
});
