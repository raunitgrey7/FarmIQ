function toggleChatbot() {
  const box = document.getElementById("chatbotContainer");
  const msgs = document.getElementById("chatMessages");

  box.style.display = box.style.display === "none" ? "flex" : "none";

  if (box.style.display === "flex") {
    msgs.innerHTML = `<div class='bot-msg'>👋 Namaste! I’m your KisaanSaathi. Select a question below.</div>`;
  }
}

function getAnswer() {
  const select = document.getElementById("questionSelect");
  const questionKey = select.value;
  const messages = document.getElementById("chatMessages");

  const answers = {
    crop_july_punjab: "🌾 In July in Punjab, you can grow Paddy (Rice). Monsoon helps its growth.",
    pest_tomato: "🪲 Spray neem oil weekly, remove affected leaves, and avoid overwatering.",
    fertilizer_wheat: "🌿 Use NPK in a 120:60:40 ratio. Apply urea in 3 split doses.",
    soil_moisture: "💧 Squeeze the soil—if it forms a loose ball, moisture is good. Or use a meter.",
    soil_ph: "🧪 Lime for acidic soil, sulfur for alkaline. Check with a soil test kit.",
    govt_schemes: "💰 Visit https://pmkisan.gov.in or your local Krishi Kendra for details.",
    rainfall_today: "☔ Use the KisaanSaathi Weather tab or IMD app for live rainfall updates.",
    crop_profitable: "📈 Tomato, Green Chilli, and Cotton can yield high profits depending on region.",
    natural_fertilizer: "🍀 Use compost, cow dung, vermicompost, and biofertilizers.",
    weather_forecast: "🌦️ Go to the Weather tab in KisaanSaathi for a 7-day forecast.",
    disease_identify: "🔍 Upload a leaf image in the Disease tab to identify problems.",
    save_water: "🚿 Use drip irrigation, mulch with dry leaves, and avoid daytime watering."
  };

  if (!questionKey || !answers[questionKey]) return;

  const userMsg = document.createElement("div");
  userMsg.className = "user-msg";
  userMsg.innerText = select.options[select.selectedIndex].text;

  const botMsg = document.createElement("div");
  botMsg.className = "bot-msg";
  botMsg.innerText = answers[questionKey];

  messages.appendChild(userMsg);
  messages.appendChild(botMsg);

  messages.scrollTop = messages.scrollHeight; // auto-scroll down
}
