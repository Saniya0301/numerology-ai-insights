const API_BASE = "http://localhost:8000";

const NUMBER_LABELS = {
  life_path_number: "Life Path",
  expression_number: "Expression",
  soul_urge_number: "Soul Urge",
  personality_number: "Personality",
  birthday_number: "Birthday",
  personal_year_number: "Personal Year",
};

const AREA_KEYS = [
  "Overview", "Personality", "Strengths", "Challenges", "Career",
  "Love", "Relationships", "Money", "This Year's Theme", "Growth",
  "Lucky Elements",
];

let currentProfileData = null;
let currentLifeAreas = null;
let chatHistory = [];

// ---------- Tab navigation ----------
document.querySelectorAll(".nav-link").forEach((btn) => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".nav-link").forEach((b) => b.classList.remove("active"));
    document.querySelectorAll(".tab-panel").forEach((p) => p.classList.remove("active"));
    btn.classList.add("active");
    document.getElementById(btn.dataset.tab).classList.add("active");
  });
});

// ---------- Profile form ----------
document.getElementById("profile-form").addEventListener("submit", async (e) => {
  e.preventDefault();

  const full_name = document.getElementById("full_name").value.trim();
  const day = parseInt(document.getElementById("day").value);
  const month = parseInt(document.getElementById("month").value);
  const year = parseInt(document.getElementById("year").value);

  document.getElementById("profile-results").classList.add("hidden");
  document.getElementById("profile-loading").classList.remove("hidden");

  try {
    const res = await fetch(`${API_BASE}/api/profile`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ full_name, day, month, year }),
    });
    if (!res.ok) throw new Error("Failed to calculate profile");
    const data = await res.json();

    currentProfileData = { full_name, day, month, year, ...data };
    renderProfileResults(currentProfileData);

    document.getElementById("profile-loading").classList.add("hidden");
    document.getElementById("profile-results").classList.remove("hidden");

    // Fire off the AI life areas generation next
    generateLifeAreas(currentProfileData);
  } catch (err) {
    document.getElementById("profile-loading").classList.add("hidden");
    alert("Something went wrong calculating your profile. Please try again.");
    console.error(err);
  }
});

function renderProfileResults(data) {
  // Number grid
  const grid = document.getElementById("number-grid");
  grid.innerHTML = "";
  Object.entries(NUMBER_LABELS).forEach(([key, label]) => {
    grid.innerHTML += `
      <div class="number-card">
        <div class="number">${data.profile[key]}</div>
        <div class="label">${label}</div>
      </div>`;
  });

  // Life Path breakdown
  const b = data.life_path_breakdown;
  document.getElementById("breakdown-content").innerHTML = `
    <p><strong>Your birth date:</strong> ${b.input}</p>
    <p><strong>Day →</strong> ${b.day_steps.join(" → ")}</p>
    <p><strong>Month →</strong> ${b.month_steps.join(" → ")}</p>
    <p><strong>Year →</strong> ${b.year_steps.join(" → ")}</p>
    <p><strong>Sum:</strong> ${b.sum_line}</p>
    ${b.final_steps.length > 1 ? `<p><strong>Final reduction:</strong> ${b.final_steps.join(" → ")}</p>` : ""}
    <p><strong>Life Path Number = ${b.result}</strong></p>
  `;

  // Pinnacles
  const pinLabels = ["1st Pinnacle", "2nd Pinnacle", "3rd Pinnacle", "4th Pinnacle"];
  const pinGrid = document.getElementById("pinnacle-grid");
  pinGrid.innerHTML = "";
  Object.values(data.pinnacles).forEach((p, i) => {
    pinGrid.innerHTML += `
      <div class="cycle-card">
        <div class="cycle-number">${p.number}</div>
        <div class="cycle-label">${pinLabels[i]}</div>
        <div class="cycle-range">Ages ${p.age_range}</div>
      </div>`;
  });

  // Challenges
  const chalLabels = ["1st Challenge", "2nd Challenge", "3rd Challenge", "4th Challenge"];
  const chalGrid = document.getElementById("challenge-grid");
  chalGrid.innerHTML = "";
  Object.values(data.challenges).forEach((c, i) => {
    chalGrid.innerHTML += `
      <div class="cycle-card">
        <div class="cycle-number">${c.number}</div>
        <div class="cycle-label">${chalLabels[i]}</div>
        <div class="cycle-range">Ages ${c.age_range}</div>
      </div>`;
  });

  // Karmic Lessons
  const karmicText = data.karmic_lessons.length
    ? `These numbers are missing from your name, suggesting traits that may need conscious development: <strong>${data.karmic_lessons.join(", ")}</strong>`
    : "All numbers 1–9 are present in your name — no missing Karmic Lessons.";
  document.getElementById("karmic-text").innerHTML = karmicText;
}

async function generateLifeAreas(data) {
  document.getElementById("life-areas-loading").classList.remove("hidden");
  document.getElementById("life-areas-section").classList.add("hidden");

  try {
    const res = await fetch(`${API_BASE}/api/life-areas`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        full_name: data.full_name, day: data.day, month: data.month, year: data.year,
      }),
    });
    if (!res.ok) throw new Error("Failed to generate life areas");
    const result = await res.json();
    currentLifeAreas = result.life_areas;

    renderLifeAreas(currentLifeAreas);

    document.getElementById("life-areas-loading").classList.add("hidden");
    document.getElementById("life-areas-section").classList.remove("hidden");
  } catch (err) {
    document.getElementById("life-areas-loading").classList.add("hidden");
    alert("Something went wrong generating your AI insights. Please try again.");
    console.error(err);
  }
}

function renderLifeAreas(areas) {
  const tabBtns = document.getElementById("area-tab-buttons");
  const content = document.getElementById("area-content");
  tabBtns.innerHTML = "";

  AREA_KEYS.forEach((key, i) => {
    const btn = document.createElement("button");
    btn.className = "area-tab-btn" + (i === 0 ? " active" : "");
    btn.textContent = key;
    btn.addEventListener("click", () => {
      document.querySelectorAll(".area-tab-btn").forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      content.textContent = areas[key] || "No content generated for this section.";
    });
    tabBtns.appendChild(btn);
  });

  content.textContent = areas[AREA_KEYS[0]] || "";
}

// ---------- PDF download ----------
document.getElementById("download-pdf-btn").addEventListener("click", async () => {
  if (!currentProfileData || !currentLifeAreas) return;

  try {
    const res = await fetch(`${API_BASE}/api/pdf-report`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        full_name: currentProfileData.full_name,
        profile: currentProfileData.profile,
        life_areas: currentLifeAreas,
        pinnacles: currentProfileData.pinnacles,
        challenges: currentProfileData.challenges,
        karmic_lessons: currentProfileData.karmic_lessons,
      }),
    });
    if (!res.ok) throw new Error("Failed to generate PDF");
    const blob = await res.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${currentProfileData.full_name.replace(/\s+/g, "_")}_numerology_report.pdf`;
    a.click();
    window.URL.revokeObjectURL(url);
  } catch (err) {
    alert("Something went wrong generating the PDF. Please try again.");
    console.error(err);
  }
});

// ---------- Chat ----------
document.getElementById("chat-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  if (!currentProfileData) return;

  const input = document.getElementById("chat-input");
  const question = input.value.trim();
  if (!question) return;

  appendChatMessage("user", question);
  chatHistory.push({ role: "user", content: question });
  input.value = "";

  const thinkingId = appendChatMessage("assistant", "Thinking...");

  try {
    const res = await fetch(`${API_BASE}/api/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        full_name: currentProfileData.full_name,
        profile: currentProfileData.profile,
        question,
        chat_history: chatHistory.slice(0, -1),
      }),
    });
    const data = await res.json();
    document.getElementById(thinkingId).textContent = data.answer;
    chatHistory.push({ role: "assistant", content: data.answer });
  } catch (err) {
    document.getElementById(thinkingId).textContent = "Sorry, something went wrong. Please try again.";
    console.error(err);
  }
});

function appendChatMessage(role, text) {
  const container = document.getElementById("chat-messages");
  const id = "msg-" + Date.now() + Math.random().toString(36).slice(2);
  const div = document.createElement("div");
  div.className = `chat-message ${role}`;
  div.id = id;
  div.textContent = text;
  container.appendChild(div);
  container.scrollTop = container.scrollHeight;
  return id;
}

// ---------- Compatibility ----------
document.getElementById("compatibility-form").addEventListener("submit", async (e) => {
  e.preventDefault();

  const payload = {
    name_a: document.getElementById("name_a").value.trim(),
    day_a: parseInt(document.getElementById("day_a").value),
    month_a: parseInt(document.getElementById("month_a").value),
    year_a: parseInt(document.getElementById("year_a").value),
    name_b: document.getElementById("name_b").value.trim(),
    day_b: parseInt(document.getElementById("day_b").value),
    month_b: parseInt(document.getElementById("month_b").value),
    year_b: parseInt(document.getElementById("year_b").value),
  };

  document.getElementById("compat-results").classList.add("hidden");
  document.getElementById("compat-loading").classList.remove("hidden");

  try {
    const res = await fetch(`${API_BASE}/api/compatibility`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!res.ok) throw new Error("Failed to calculate compatibility");
    const data = await res.json();

    document.getElementById("compat-overall-score").textContent = `${data.compatibility.overall_score}%`;
    document.getElementById("compat-score-grid").innerHTML = `
      <div class="number-card"><div class="number">${data.compatibility.life_path_score}%</div><div class="label">Life Path</div></div>
      <div class="number-card"><div class="number">${data.compatibility.expression_score}%</div><div class="label">Expression</div></div>
      <div class="number-card"><div class="number">${data.compatibility.soul_urge_score}%</div><div class="label">Soul Urge</div></div>
    `;
    document.getElementById("compat-explanation").textContent = data.explanation;

    document.getElementById("compat-loading").classList.add("hidden");
    document.getElementById("compat-results").classList.remove("hidden");
  } catch (err) {
    document.getElementById("compat-loading").classList.add("hidden");
    alert("Something went wrong. Please try again.");
    console.error(err);
  }
});

// ---------- Shop ----------
const PRODUCTS = {
  "🟤 Rudraksha": [
    { name: "5 Mukhi Rudraksha Bead", price: "₹499", description: "The most common and widely worn rudraksha, associated with calm and focus." },
    { name: "Rudraksha Mala (108 Beads)", price: "₹1,899", description: "A traditional strand used for japa meditation and daily wear." },
    { name: "1 Mukhi Rudraksha Pendant", price: "₹3,499", description: "A rare single-faced bead, set as a pendant for daily wear." },
  ],
  "💎 Crystals": [
    { name: "Amethyst Cluster", price: "₹899", description: "A natural raw cluster, often placed for calm, reflective spaces." },
    { name: "Rose Quartz Tumbled Set", price: "₹599", description: "A set of 5 polished stones, popular for personal or gifting use." },
    { name: "Clear Quartz Point", price: "₹749", description: "A single terminated point, commonly used in personal crystal practice." },
  ],
  "🔺 Yantras": [
    { name: "Sri Yantra (Copper)", price: "₹1,299", description: "A hand-finished copper Sri Yantra for home or altar placement." },
    { name: "Numerology Yantra Card", price: "₹349", description: "A compact printed yantra paired with your personal number, easy to carry." },
  ],
};

function renderShop() {
  const container = document.getElementById("shop-content");
  container.innerHTML = "";
  Object.entries(PRODUCTS).forEach(([category, items]) => {
    let html = `<h3 class="shop-category-title">${category}</h3><div class="product-grid">`;
    items.forEach((p) => {
      html += `
        <div class="product-card">
          <div class="product-image-placeholder">Product Photo<br/>Coming Soon</div>
          <div class="product-info">
            <h4>${p.name}</h4>
            <div class="product-price">${p.price}</div>
            <div class="product-description">${p.description}</div>
            <button class="btn-enquire" data-product="${p.name}">Enquire</button>
          </div>
        </div>`;
    });
    html += `</div>`;
    container.innerHTML += html;
  });

  document.querySelectorAll(".btn-enquire").forEach((btn) => {
    btn.addEventListener("click", () => openEnquiryModal(btn.dataset.product));
  });
}

function openEnquiryModal(productName) {
  document.getElementById("enquiry-product-name").textContent = `Enquire about: ${productName}`;
  document.getElementById("enquiry-form").classList.remove("hidden");
  document.getElementById("enquiry-success").classList.add("hidden");
  document.getElementById("enquiry-modal").classList.remove("hidden");
  document.getElementById("enquiry-modal").dataset.product = productName;
  document.getElementById("enquiry-modal").dataset.type = "shop";
}

document.getElementById("modal-close-btn").addEventListener("click", () => {
  document.getElementById("enquiry-modal").classList.add("hidden");
});

document.getElementById("enquiry-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const modal = document.getElementById("enquiry-modal");
  const itemName = modal.dataset.product;
  const type = modal.dataset.type || "shop";
  const name = document.getElementById("enquiry_name").value.trim();
  const contact = document.getElementById("enquiry_contact").value.trim();
  const message = document.getElementById("enquiry_message").value.trim();

  const ENDPOINT_MAP = {
    shop: { url: "/api/shop-enquiry", itemKey: "product" },
    course: { url: "/api/course-enquiry", itemKey: "course" },
    ebook: { url: "/api/ebook-enquiry", itemKey: "ebook" },
  };
  const { url, itemKey } = ENDPOINT_MAP[type];
  const payload = { [itemKey]: itemName, name, contact, message };

  try {
    const res = await fetch(`${API_BASE}${url}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!res.ok) throw new Error("Failed to submit enquiry");

    document.getElementById("enquiry-form").classList.add("hidden");
    document.getElementById("enquiry-success").classList.remove("hidden");
  } catch (err) {
    alert("Something went wrong submitting your enquiry. Please try again.");
    console.error(err);
  }
});

renderShop();

// ---------- Booking ----------
const SERVICES = [
  { name: "Numerology Consultation", duration: "30 min", price: "₹799" },
  { name: "Relationship Reading", duration: "45 min", price: "₹1,199" },
  { name: "Career Reading", duration: "45 min", price: "₹1,199" },
  { name: "Complete Occult Reading", duration: "60 min", price: "₹1,999" },
];

let selectedService = null;

function renderServices() {
  const grid = document.getElementById("service-grid");
  grid.innerHTML = "";
  SERVICES.forEach((s) => {
    const card = document.createElement("div");
    card.className = "service-card";
    card.innerHTML = `
      <h4>${s.name}</h4>
      <div class="service-duration">${s.duration}</div>
      <div class="service-price">${s.price}</div>
    `;
    card.addEventListener("click", () => selectService(s, card));
    grid.appendChild(card);
  });
}

function selectService(service, cardEl) {
  selectedService = service;
  document.querySelectorAll(".service-card").forEach((c) => c.classList.remove("selected"));
  cardEl.classList.add("selected");

  document.getElementById("booking-selected-service").textContent =
    `${service.name} — ${service.duration} — ${service.price}`;
  document.getElementById("booking-form").classList.remove("hidden");
  document.getElementById("booking-success").classList.add("hidden");
}

document.getElementById("booking-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  if (!selectedService) return;

  const payload = {
    service: selectedService.name,
    duration: selectedService.duration,
    price: selectedService.price,
    preferred_date: document.getElementById("preferred_date").value,
    preferred_time: document.getElementById("preferred_time").value,
    name: document.getElementById("booking_name").value.trim(),
    contact: document.getElementById("booking_contact").value.trim(),
    notes: document.getElementById("booking_notes").value.trim(),
  };

  try {
    const res = await fetch(`${API_BASE}/api/booking`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!res.ok) throw new Error("Failed to submit booking");

    document.getElementById("booking-form").classList.add("hidden");
    document.getElementById("booking-success").classList.remove("hidden");
    document.getElementById("booking-form").reset();
    selectedService = null;
    document.querySelectorAll(".service-card").forEach((c) => c.classList.remove("selected"));
  } catch (err) {
    alert("Something went wrong submitting your booking. Please try again.");
    console.error(err);
  }
});

renderServices();

// ---------- Courses ----------
const COURSES = [
  { name: "Numerology Foundations", level: "Beginner", lessons: "12 Lessons", duration: "4 Hours", price: "₹999" },
  { name: "Advanced Numerology", level: "Advanced", lessons: "20 Lessons", duration: "10 Hours", price: "₹2,499" },
  { name: "Tarot Reading Mastery", level: "Beginner → Intermediate", lessons: "24 Lessons", duration: "8 Hours", price: "₹1,999" },
  { name: "Vedic Astrology Fundamentals", level: "Intermediate", lessons: "30 Lessons", duration: "12 Hours", price: "₹2,999" },
];

function renderCourses() {
  const container = document.getElementById("courses-content");
  let html = `<div class="course-grid">`;
  COURSES.forEach((c) => {
    html += `
      <div class="course-card">
        <span class="course-level">${c.level}</span>
        <h4>${c.name}</h4>
        <div class="course-meta">${c.lessons} · ${c.duration}</div>
        <div class="course-price">${c.price}</div>
        <button class="btn-enquire" data-course="${c.name}">Enroll Now</button>
      </div>`;
  });
  html += `</div>`;
  container.innerHTML = html;

  container.querySelectorAll(".btn-enquire").forEach((btn) => {
    btn.addEventListener("click", () => {
      const modal = document.getElementById("enquiry-modal");
      document.getElementById("enquiry-product-name").textContent = `Enroll in: ${btn.dataset.course}`;
      document.getElementById("enquiry-form").classList.remove("hidden");
      document.getElementById("enquiry-success").classList.add("hidden");
      modal.classList.remove("hidden");
      modal.dataset.product = btn.dataset.course;
      modal.dataset.type = "course";
    });
  });
}

// ---------- Library / Ebooks ----------
const EBOOKS = {
  "🔢 Numerology": [
    { name: "Numerology for Beginners", price: "₹299", description: "The fundamentals of numerology, explained simply." },
    { name: "Understanding Your Moolank", price: "₹249", description: "A deep dive into your root number and what it reveals." },
    { name: "The Complete Guide to Numerology", price: "₹399", description: "Life Path, Destiny, Soul Urge, and practical examples." },
  ],
  "🔮 Tarot": [
    { name: "Tarot for Beginners", price: "₹349", description: "Start reading tarot with confidence, card by card." },
    { name: "Major Arcana Guide", price: "₹299", description: "A focused guide to the 22 Major Arcana cards." },
  ],
  "🌙 Astrology": [
    { name: "Vedic Astrology Basics", price: "₹399", description: "An introduction to houses, planets, and charts." },
    { name: "Nakshatra Guide", price: "₹349", description: "Understanding the 27 lunar mansions." },
  ],
};

function renderLibrary() {
  const container = document.getElementById("library-content");
  container.innerHTML = "";
  Object.entries(EBOOKS).forEach(([category, items]) => {
    let html = `<h3 class="shop-category-title">${category}</h3><div class="ebook-grid">`;
    items.forEach((b) => {
      html += `
        <div class="ebook-card">
          <h4>${b.name}</h4>
          <div class="ebook-price">${b.price}</div>
          <div class="ebook-description">${b.description}</div>
          <button class="btn-enquire" data-ebook="${b.name}">Get This Ebook</button>
        </div>`;
    });
    html += `</div>`;
    container.innerHTML += html;
  });

  container.querySelectorAll(".btn-enquire").forEach((btn) => {
    btn.addEventListener("click", () => {
      const modal = document.getElementById("enquiry-modal");
      document.getElementById("enquiry-product-name").textContent = `Get: ${btn.dataset.ebook}`;
      document.getElementById("enquiry-form").classList.remove("hidden");
      document.getElementById("enquiry-success").classList.add("hidden");
      modal.classList.remove("hidden");
      modal.dataset.product = btn.dataset.ebook;
      modal.dataset.type = "ebook";
    });
  });
}

renderCourses();
renderLibrary();