const socket = io();
let userName = "";

function login() {
  const name = document.getElementById("username").value.trim();
  const email = document.getElementById("email").value.trim();
  const password = document.getElementById("password").value.trim();

  if (!name || !email || !password) {
    alert("Please fill in all fields!");
    return;
  }

  userName = name;
  document.getElementById("userNameDisplay").textContent = name;
  document.getElementById("auth-section").classList.add("hidden");
  document.getElementById("contacts-section").classList.remove("hidden");
}

function addContact() {
  const contactList = document.getElementById("contact-list");
  const phoneInput = document.createElement("input");
  phoneInput.type = "tel";
  phoneInput.placeholder = "Contact phone";
  phoneInput.classList.add("contact-phone");
  contactList.appendChild(phoneInput);
}

function goToDashboard() {
  document.getElementById("contacts-section").classList.add("hidden");
  document.getElementById("dashboard-section").classList.remove("hidden");
}

function sendAlert() {
  if (!navigator.geolocation) {
    alert("Geolocation not supported in your browser.");
    return;
  }

  const phones = Array.from(document.getElementsByClassName("contact-phone"))
    .map(input => input.value.trim())
    .filter(p => p);

  if (phones.length === 0) {
    alert("Please enter at least one trusted contact.");
    return;
  }

  navigator.geolocation.getCurrentPosition(
    (position) => {
      const lat = position.coords.latitude;
      const lon = position.coords.longitude;

      document.getElementById("alert-status").textContent = "Alert sent! SMS and tracking started.";

      document.getElementById("dashboard-section").classList.add("hidden");
      document.getElementById("tracker-section").classList.remove("hidden");

      document.getElementById("location-display").textContent = `Latitude: ${lat.toFixed(4)}, Longitude: ${lon.toFixed(4)}`;

      fetch("/send_alert", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          username: userName,
          latitude: lat,
          longitude: lon,
          contacts: phones,
        }),
      });
    },
    (error) => {
      alert("Unable to get location.");
    }
  );
}

socket.on("location_update", (data) => {
  const msg = `${data.username} - Lat: ${data.lat}, Lon: ${data.lon}`;
  document.getElementById("location-display").textContent = msg;
});
