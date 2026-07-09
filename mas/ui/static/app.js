async function sendMessage() {
    const input = document.getElementById("input");
    const chat = document.getElementById("chat");

    const userText = input.value;

    if (!userText) return;

    chat.innerHTML += `<p><b>You:</b> ${userText}</p>`;

    const response = await fetch("/chat", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ message: userText })
    });

    const data = await response.json();

    chat.innerHTML += `<p><b>Bot:</b> ${data.response}</p>`;

    input.value = "";
}