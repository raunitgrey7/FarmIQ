// 🌱 KisaanSaathi – Main JS File
console.log("✅ JS Loaded");

// 🌐 Translations Dictionary
const translations = {
  "title": { "en": "KisaanSaathi 🌾", "hi": "किसानसाथी 🌾" },
  "lang_toggle": { "en": "🇮🇳 View in Hindi", "hi": "🇬🇧 View in English" },
  "dark_toggle": { "en": "🌙 Dark Mode", "hi": "🌙 डार्क मोड" },
  "crop_tab": { "en": "🌾 Crop Prediction", "hi": "🌾 फसल सुझाव" },
  "disease_tab": { "en": "🩺 Disease Detection", "hi": "🩺 रोग पहचान" },
  "label_n": { "en": "Nitrogen", "hi": "नाइट्रोजन" },
  "label_p": { "en": "Phosphorus", "hi": "फास्फोरस" },
  "label_k": { "en": "Potassium", "hi": "पोटैशियम" },
  "label_temp": { "en": "Temperature", "hi": "तापमान" },
  "label_humidity": { "en": "Humidity", "hi": "आर्द्रता" },
  "label_ph": { "en": "Soil pH", "hi": "मिट्टी का pH" },
  "label_rain": { "en": "Rainfall", "hi": "वर्षा" },
  "submit_crop": { "en": "Suggest Crop", "hi": "फसल सुझाव दें" },
  "upload_label": { "en": "Upload plant image:", "hi": "पौधे की छवि अपलोड करें:" },
  "submit_disease": { "en": "Detect Disease", "hi": "रोग पहचानें" }
};

// 📍 Location Access Helper
function getUserLocation(callback) {
  if (navigator.geolocation) {
    navigator.geolocation.getCurrentPosition(
      (pos) => callback(pos.coords.latitude, pos.coords.longitude),
      (err) => {
        console.error("❌ Location error:", err.message);
        alert("Location access needed for weather info.");
      }
    );
  } else {
    alert("Geolocation not supported.");
  }
}

// 🌤️ Fetch Weather
async function fetchWeather(lat, lon) {
  const apiKey = "a1ebb70e1acc402d941200642250207";
  const url = `https://api.weatherapi.com/v1/current.json?key=${apiKey}&q=${lat},${lon}`;

  try {
    const res = await fetch(url);
    const data = await res.json();

    const weatherHtml = `
      <h3>📍 Location Weather</h3>
      <ul>
        <li><strong>Location:</strong> ${data.location.name}, ${data.location.region}</li>
        <li><strong>Temperature:</strong> ${data.current.temp_c} °C</li>
        <li><strong>Humidity:</strong> ${data.current.humidity}%</li>
        <li><strong>Condition:</strong> ${data.current.condition.text}</li>
        <li><strong>Wind:</strong> ${data.current.wind_kph} km/h</li>
      </ul>`;
    const weatherBox = document.getElementById("weatherResult");
    if (weatherBox) weatherBox.innerHTML = weatherHtml;
  } catch (err) {
    console.error("❌ Weather fetch error:", err);
    document.getElementById("weatherResult").innerHTML = `<p>Failed to fetch weather data.</p>`;
  }
}

// DOM Ready
document.addEventListener("DOMContentLoaded", () => {
  let currentLang = localStorage.getItem("lang") || "en";

  // 🌐 Language Toggle
  const langToggle = document.getElementById("language-toggle");
  function setLanguage(lang) {
    currentLang = lang;
    localStorage.setItem("lang", lang);

    const elements = document.querySelectorAll("[data-key]");
    elements.forEach(el => {
      const key = el.getAttribute("data-key");
      if (!translations[key]) return;

      if (el.childNodes.length > 1 && el.childNodes[0].nodeType === 3) {
        el.childNodes[0].textContent = translations[key][lang] + " ";
      } else {
        el.innerText = translations[key][lang];
      }
    });

    const langFeedback = document.createElement("div");
    langFeedback.innerText = lang === "hi" ? "भाषा: हिंदी" : "Language: English";
    langFeedback.className = "lang-toast";
    document.body.appendChild(langFeedback);
    setTimeout(() => langFeedback.remove(), 2000);
  }

  if (langToggle) {
    langToggle.checked = currentLang === "hi";
    setLanguage(currentLang);
    langToggle.addEventListener("change", (e) => {
      const lang = e.target.checked ? "hi" : "en";
      setLanguage(lang);
    });
  }

  // 📍 Get Weather on load
  getUserLocation(fetchWeather);

 // 🌾 Crop Prediction – Updated with Enhancements
const cropForm = document.getElementById("cropForm");
const resultBox = document.getElementById("result");

if (cropForm) {
  // Restore previous result from localStorage
  const savedResult = localStorage.getItem("crop_result_html");
  if (savedResult && resultBox) {
    resultBox.innerHTML = savedResult;
  }

  cropForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const form = e.target;
    const data = {
      nitrogen: parseFloat(form.nitrogen.value),
      phosphorus: parseFloat(form.phosphorus.value),
      potassium: parseFloat(form.potassium.value),
      temperature: parseFloat(form.temperature.value),
      humidity: parseFloat(form.humidity.value),
      ph: parseFloat(form.ph.value),
      rainfall: parseFloat(form.rainfall.value)
    };

    resultBox.innerHTML = "<p>⏳ Predicting best crop...</p>";

    try {
      const res = await fetch("http://localhost:8000/predict-json", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data)
      });

      const result = await res.json();
      let tipsHtml = "";

      if (result.tips && Object.keys(result.tips).length > 0) {
        tipsHtml = `
          <ul>
            <li><strong>Sowing Season:</strong> ${result.tips.sowing_season}</li>
            <li><strong>Watering:</strong> ${result.tips.watering}</li>
            <li><strong>Fertilizer:</strong> ${result.tips.fertilizer}</li>
            <li><strong>Organic Pest Control:</strong> ${result.tips.pest_control}</li>
            <li><strong>Harvest Time:</strong> ${result.tips.harvest}</li>
          </ul>`;
      } else {
        tipsHtml = "<p>No tips available for this crop yet.</p>";
      }

      // 🎨 Build chart and final HTML
      const html = `
        <h3>🌱 <strong>Recommended Crop:</strong> ${result.recommended_crop}</h3>
        <div style="max-width: 300px; margin: 10px auto;">
          <canvas id="npkChart"></canvas>
        </div>
        <h4>📋 <strong>Care Guide:</strong></h4>${tipsHtml}`;

      resultBox.innerHTML = html;
      localStorage.setItem("crop_result_html", html); // 🔒 Save result

      // 📊 Render Chart
      renderNPKChart(data.nitrogen, data.phosphorus, data.potassium);

      form.reset();
    } catch (err) {
      console.error("❌ Prediction Error:", err);
      resultBox.innerHTML = `<p>Error occurred while predicting crop.</p>`;
    }
  });
}

// 📊 Chart Renderer
function renderNPKChart(n, p, k) {
  const ctx = document.getElementById("npkChart");
  if (!ctx) return;

  new Chart(ctx, {
    type: "pie",
    data: {
      labels: ["Nitrogen", "Phosphorus", "Potassium"],
      datasets: [{
        data: [n, p, k],
        backgroundColor: ["#81c784", "#64b5f6", "#ffd54f"]
      }]
    },
    options: {
      responsive: true,
      plugins: {
        legend: { position: "bottom" }
      }
    }
  });
}


  // 🩺 Disease Detection
  const diseaseForm = document.getElementById("diseaseForm");
  if (diseaseForm) {
    diseaseForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const file = diseaseForm.querySelector("input[type='file']").files[0];
      if (!file) return alert("Please upload an image.");

      const formData = new FormData(diseaseForm);
      document.getElementById("diseaseResult").innerHTML = "<p>🔍 Detecting disease...</p>";

      try {
        const res = await fetch("http://localhost:8000/predict-disease", {
          method: "POST",
          body: formData
        });
        const result = await res.json();
        const output = result.predicted_disease
          ? `<h3>🩺 Disease Detected:</h3><p>${result.predicted_disease}</p>`
          : `<p>Error: ${result.error || "Unknown issue"}</p>`;
        document.getElementById("diseaseResult").innerHTML = output;
        diseaseForm.reset();
      } catch (err) {
        console.error("❌ Disease Detection Error:", err);
        document.getElementById("diseaseResult").innerHTML = `<p>Error: ${err.message}</p>`;
      }
    });
  }

  // 🌙 Dark Mode Toggle
  const darkToggle = document.getElementById("darkToggle");
  if (darkToggle) {
    const savedMode = localStorage.getItem("mode");
    if (savedMode === "dark") {
      document.body.classList.add("dark-mode");
      darkToggle.checked = true;
    }

    darkToggle.addEventListener("change", () => {
      document.body.classList.toggle("dark-mode", darkToggle.checked);
      localStorage.setItem("mode", darkToggle.checked ? "dark" : "light");
    });
  }

  // 🔄 Tab Switching
  const tabButtons = document.querySelectorAll(".tab-button");
  const tabContents = document.querySelectorAll(".tab-content");
  tabButtons.forEach((button, index) => {
    button.addEventListener("click", () => {
      tabButtons.forEach((btn) => btn.classList.remove("active"));
      button.classList.add("active");
      tabContents.forEach((content) => content.classList.remove("active"));
      tabContents[index].classList.add("active");
    });
  });

  // 🍔 Hamburger Menu Toggle
  const burger = document.getElementById("burger");
  const navLinks = document.getElementById("navLinks");

  if (burger && navLinks) {
    burger.addEventListener("click", () => {
      navLinks.classList.toggle("active");
    });
  }
});

// ✅ Toast Message Function
function showToast(message) {
  const toast = document.createElement("div");
  toast.className = "lang-toast";
  toast.innerText = message;
  document.body.appendChild(toast);
  setTimeout(() => toast.remove(), 2000);
}

// 🌱 Welcome Toast
showToast("Welcome to KisaanSaathi 🌿");


