const BACKEND_URL = "https://samvaadpay.onrender.com";

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
    return "The illustrative demo price is $45.00. Actual prices will come from the seller catalog.";
  }

  if (
    text.includes("checkout") ||
    text.includes("payment") ||
    text.includes("pay")
  ) {
    return "Click Pay Now on the product card. The backend will create a secure PayPal payment link for you.";
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

// Checkout: send ONLY the product id. Backend reads the price from the DB.
async function buyProduct(productId, button) {
  const originalText = button.textContent;

  try {
    button.disabled = true;
    button.textContent = "Please wait...";
    showToast("Connecting to checkout...");

    const response = await fetch(`${BACKEND_URL}/api/checkout`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ product_id: productId })
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.detail || "Checkout failed");
    }

    if (!data.approve_link) {
      throw new Error("PayPal link not received");
    }

    // Redirect to PayPal
    window.location.href = data.approve_link;
  } catch (error) {
    console.error("Checkout error:", error);
    showToast(error.message || "Unable to start payment");

    button.disabled = false;
    button.textContent = originalText;
  }
}

checkoutBtn.addEventListener("click", () => {
  buyProduct(Number(checkoutBtn.dataset.productId), checkoutBtn);
});

/*
FOR NAMRATHA (when /chat returns products dynamically):

When you render a product card from the /chat response, create the Buy
button and call:

  buyBtn.addEventListener("click", () => buyProduct(product.id, buyBtn));

where product.id is the DB products.id sent by the backend.
Never send price from the frontend.
*/
