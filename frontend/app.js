
const chatForm = document.getElementById("chatForm");
const messageInput = document.getElementById("messageInput");
const chatMessages = document.getElementById("chatMessages");
const checkoutBtn = document.getElementById("checkoutBtn");
const toast = document.getElementById("toast");

let toastTimer;

// Show a small notification
function showToast(message) {
  toast.textContent = message;
  toast.classList.add("show");

  clearTimeout(toastTimer);

  toastTimer = setTimeout(() => {
    toast.classList.remove("show");
  }, 3500);
}

// Add a chat message to the screen
function addMessage(text, sender = "user") {
  const row = document.createElement("div");
  row.className = `message ${sender}`;

  const bubble = document.createElement("div");
  bubble.className = "bubble";

  // textContent prevents input from being treated as HTML
  bubble.textContent = text;

  row.appendChild(bubble);
  chatMessages.appendChild(row);

  chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Temporary mock AI response
function getDemoReply(message) {
  const text = message.toLowerCase();

  if (text.includes("color") || text.includes("colour")) {
    return "This demo item is shown in natural canvas color. Live variants will be checked using seller inventory.";
  }

  if (text.includes("price") || text.includes("cost")) {
    return "The illustrative demo price is ₹799. Actual prices will come from the seller catalog.";
  }

  if (
    text.includes("checkout") ||
    text.includes("payment") ||
    text.includes("pay")
  ) {
    return "Checkout is not connected yet. In the integrated version, the backend will provide a trusted payment link.";
  }

  if (text.includes("stock") || text.includes("available")) {
    return "This is sample information. The live application will check current inventory.";
  }

  return "Thanks for your message! I'm a demo assistant right now. Soon I'll help you explore products, check stock and checkout.";
}

// Handle chat form submission
chatForm.addEventListener("submit", function (event) {
  event.preventDefault();

  const message = messageInput.value.trim();

  if (!message) {
    messageInput.focus();
    return;
  }

  addMessage(message, "user");

  messageInput.value = "";
  messageInput.focus();

  // Mock reply, not a real AI API call
  setTimeout(() => {
    addMessage(getDemoReply(message), "assistant");
  }, 350);
});

// Suggestion buttons
document.querySelectorAll(".suggestion").forEach((button) => {
  button.addEventListener("click", () => {
    messageInput.value = button.dataset.message;
    messageInput.focus();
  });
});

// Demo checkout action
checkoutBtn.addEventListener("click", () => {
  showToast(
    "Demo only: checkout is not connected. No payment was started."
  );
});

/*
BACKEND INTEGRATION - LATER

First ask your backend teammate to confirm the API contract.

Example only:

const response = await fetch("YOUR_BACKEND_URL/chat", {
  method: "POST",
  headers: {
    "Content-Type": "application/json"
  },
  body: JSON.stringify({
    message: message
  })
});

Do not assume the endpoint or response format is final.
Keep API keys and payment credentials on the backend.
Verify payment status on the server.
*/
