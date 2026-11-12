// Always use the deployed Render backend
const BACKEND_URL = "https://samvaadpay.onrender.com";

const chatForm = document.getElementById("chatForm");
const messageInput = document.getElementById("messageInput");
const chatMessages = document.getElementById("chatMessages");
const toast = document.getElementById("toast");
const sendBtn = chatForm.querySelector("button[type='submit']");

let toastTimer;

// Used only for the little color circle on product cards
const COLOR_MAP = {
  black: "#2b2b2b", white: "#f4f4f4", brown: "#8a5a3c", red: "#d64545",
  blue: "#3f6fd8", grey: "#9aa0a8", green: "#3f9b61", yellow: "#f2c94c",
  pink: "#ef8fb4", orange: "#ee8a3c", purple: "#8a5cd0", navy: "#1f2f5c"
};

// ---------- small helpers ----------

function showToast(message) {
  toast.textContent = message;
  toast.classList.add("show");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => toast.classList.remove("show"), 3500);
}

function scrollToBottom() {
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

function addMessage(text, sender = "user") {
  const row = document.createElement("div");
  row.className = `message ${sender}`;

  const bubble = document.createElement("div");
  bubble.className = "bubble";
  bubble.textContent = text; // textContent: never treated as HTML

  row.appendChild(bubble);
  chatMessages.appendChild(row);
  scrollToBottom();
  return row;
}

function addTyping() {
  const row = addMessage("...", "assistant");
  row.querySelector(".bubble").classList.add("typing");
  return row;
}

// ---------- product cards ----------

function buildProductCard(product) {
  const card = document.createElement("article");
  card.className = "product-card";

  const image = document.createElement("div");
  image.className = "product-image";
  const swatch = document.createElement("span");
  swatch.className = "swatch";
  swatch.style.background = COLOR_MAP[product.color] || "#cccccc";
  swatch.textContent = product.category === "shoes" ? "👟" : "👕";
  image.appendChild(swatch);

  const info = document.createElement("div");
  info.className = "product-info";

  const title = document.createElement("h3");
  title.textContent = product.name;

  const meta = document.createElement("p");
  meta.className = "product-meta";
  meta.textContent = `${product.category} · ${product.color} · size ${product.size}`;

  info.appendChild(title);
  info.appendChild(meta);

  if (product.stock <= 3) {
    const low = document.createElement("span");
    low.className = "stock-low";
    low.textContent = `Only ${product.stock} left`;
    info.appendChild(low);
  }

  const bottom = document.createElement("div");
  bottom.className = "product-bottom";

  const priceBox = document.createElement("div");
  const small = document.createElement("small");
  small.textContent = "Price";
  const price = document.createElement("h2");
  price.textContent = `$${Number(product.price).toFixed(2)}`;
  priceBox.appendChild(small);
  priceBox.appendChild(price);

  const buyBtn = document.createElement("button");
  buyBtn.type = "button";
  buyBtn.textContent = "Buy Now ↗";
  // Only the product id goes to the backend. Price comes from the DB there.
  buyBtn.addEventListener("click", () => buyProduct(product.id, buyBtn));

  bottom.appendChild(priceBox);
  bottom.appendChild(buyBtn);
  info.appendChild(bottom);

  card.appendChild(image);
  card.appendChild(info);
  return card;
}

function renderProducts(products) {
  if (!products || products.length === 0) return;

  const list = document.createElement("div");
  list.className = "product-list";
  products.forEach((p) => list.appendChild(buildProductCard(p)));

  chatMessages.appendChild(list);
  scrollToBottom();
}

// ---------- chat ----------

async function askBackend(message) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 60000);

  // Free Render servers sleep, so the first reply can be slow
  const slowTimer = setTimeout(
    () => showToast("Waking up the server, first reply can take ~30 seconds..."),
    5000
  );

  try {
    const response = await fetch(`${BACKEND_URL}/shop-chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message }),
      signal: controller.signal
    });

    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || "Something went wrong");
    }
    return data;
  } finally {
    clearTimeout(timeout);
    clearTimeout(slowTimer);
  }
}

chatForm.addEventListener("submit", async function (event) {
  event.preventDefault();

  const message = messageInput.value.trim();
  if (!message) {
    messageInput.focus();
    return;
  }

  addMessage(message, "user");
  messageInput.value = "";
  sendBtn.disabled = true;

  const typingRow = addTyping();

  try {
    const data = await askBackend(message);
    typingRow.remove();
    addMessage(data.reply, "assistant");
    renderProducts(data.products);
  } catch (error) {
    console.error("Chat error:", error);
    typingRow.remove();
    addMessage(
      "Sorry, I couldn't reach the shop right now. Please try again in a moment.",
      "assistant"
    );
  } finally {
    sendBtn.disabled = false;
    messageInput.focus();
  }
});

// Suggestion buttons: fill and send
document.querySelectorAll(".suggestion").forEach((button) => {
  button.addEventListener("click", () => {
    messageInput.value = button.dataset.message;
    chatForm.requestSubmit();
  });
});

// ---------- checkout ----------

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

    window.location.href = data.approve_link;
  } catch (error) {
    console.error("Checkout error:", error);
    showToast(error.message || "Unable to start payment");
    button.disabled = false;
    button.textContent = originalText;
  }
}

// ---------- coming back from PayPal ----------
// Works when the backend redirects to  <frontend>/?payment=success  or  ?payment=cancel
const payment = new URLSearchParams(window.location.search).get("payment");
if (payment === "success") {
  addMessage("Payment successful! 🎉 Thank you for shopping with SamvaadPay.", "assistant");
  showToast("Payment successful ✅");
  window.history.replaceState({}, "", window.location.pathname);
} else if (payment === "cancel") {
  addMessage("Payment was cancelled. You can pick an item and try again anytime.", "assistant");
  showToast("Payment cancelled");
  window.history.replaceState({}, "", window.location.pathname);
}
