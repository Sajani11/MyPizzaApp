document.addEventListener("DOMContentLoaded", () => {
  // ---------------- Add Pizza Page Functionality ----------------
  const addPizzaForm = document.getElementById("addPizzaForm");
  const imageUrlInput = document.getElementById("image_url");
  const imageFileInput = document.getElementById("image_file");
  const imagePreview = document.getElementById("imagePreview");

  if (addPizzaForm) {
    const previewImage = (src) => {
      imagePreview.src = src;
      imagePreview.style.display = src ? "block" : "none";
    };

    // Image URL input
    if (imageUrlInput) {
      imageUrlInput.addEventListener("input", () => {
        const isValidUrl = imageUrlInput.value.match(
          /^https?:\/\/.*\.(jpg|jpeg|png|gif|bmp)$/i
        );
        previewImage(isValidUrl ? imageUrlInput.value : "");
      });
    }

    // Image file input
    if (imageFileInput) {
      imageFileInput.addEventListener("change", (e) => {
        const file = e.target.files[0];
        if (file) {
          const reader = new FileReader();
          reader.onload = (event) => previewImage(event.target.result);
          reader.readAsDataURL(file);
        } else {
          previewImage("");
        }
      });
    }

    addPizzaForm.addEventListener("submit", (e) => {
      e.preventDefault();
      const name = addPizzaForm
        .querySelector('input[name="pizza_name"]')
        .value.trim();
      const price = addPizzaForm
        .querySelector('input[name="price"]')
        .value.trim();
      const desc = addPizzaForm
        .querySelector('textarea[name="description"]')
        .value.trim();

      if (
        !name ||
        !price ||
        !desc ||
        (!imageUrlInput.value && !imageFileInput.value)
      ) {
        return alert("Please fill out all fields.");
      }

      fetch("/add_pizza", { method: "POST", body: new FormData(addPizzaForm) })
        .then((res) => res.json())
        .then((data) => {
          if (data.success) {
            alert("Pizza added successfully!");
            addPizzaForm.reset();
            previewImage("");
          } else {
            alert("Error adding pizza.");
          }
        })
        .catch(() => alert("Something went wrong. Please try again."));
    });
  }

  // ---------------- Search & Filter Pizzas ----------------
  const searchInput = document.getElementById("searchInput");
  const pizzaItems = document.querySelectorAll(".pizza-item");
  const noResultMsg = document.getElementById("noResultMsg");

  const filterPizzas = () => {
    const keyword = searchInput.value.toLowerCase();
    let found = false;
    pizzaItems.forEach((item) => {
      const name = item.dataset.name.toLowerCase();
      const category = item.dataset.category
        ? item.dataset.category.toLowerCase()
        : "";
      if (name.includes(keyword) || category.includes(keyword)) {
        item.style.display = "block";
        gsap.to(item, { opacity: 1, y: 0, duration: 0.4, ease: "power2.out" });
        found = true;
      } else {
        gsap.to(item, {
          opacity: 0,
          y: -20,
          duration: 0.3,
          ease: "power2.in",
          onComplete: () => (item.style.display = "none"),
        });
      }
    });
    if (noResultMsg) noResultMsg.style.display = found ? "none" : "block";
  };

  if (searchInput) searchInput.addEventListener("keyup", filterPizzas);

  // Initial GSAP animations
  gsap.from(".gsap-heading", { opacity: 0, y: -50, duration: 1 });
  gsap.from(".gsap-add", { opacity: 0, y: 50, duration: 1, delay: 0.3 });
  gsap.from(".pizza-item", {
    opacity: 0,
    scale: 0.8,
    duration: 0.6,
    stagger: 0.1,
    delay: 0.6,
  });

  // Pizza hover effects
  document.querySelectorAll(".pizza-img").forEach((img) => {
    img.addEventListener("mouseenter", () =>
      gsap.to(img, {
        scale: 1.05,
        boxShadow: "0 0 20px 5px rgba(255, 193, 7, 0.8)",
        duration: 0.3,
      })
    );
    img.addEventListener("mouseleave", () =>
      gsap.to(img, {
        scale: 1,
        boxShadow: "0 0 15px rgba(0, 0, 0, 0.2)",
        duration: 0.3,
      })
    );
  });

  // ---------------- Modals ----------------
  let selectedPizzaId = null;

  window.showOrderModal = (pizzaId) => {
    selectedPizzaId = pizzaId;
    const form = document.getElementById("addToCartForm");
    if (form) form.action = `/add-to-cart/${pizzaId}`;
    new bootstrap.Modal(document.getElementById("orderChoiceModal")).show();
  };

  document.getElementById("customizeBtn")?.addEventListener("click", () => {
    if (selectedPizzaId) window.location.href = `/customize/${selectedPizzaId}`;
  });

  window.showEditPizzaModal = (pizzaId, name, price, desc) => {
    document.getElementById("editPizzaId").value = pizzaId;
    document.getElementById("editPizzaName").value = name;
    document.getElementById("editPizzaPrice").value = price;
    document.getElementById("editPizzaDesc").value = desc;
    document.getElementById("editPizzaForm").action = `/edit-pizza/${pizzaId}`;
    new bootstrap.Modal(document.getElementById("editPizzaModal")).show();
  };

  window.showDeletePizzaModal = (pizzaId, name) => {
    document.getElementById("pizzaIdToDelete").value = pizzaId;
    document.getElementById("pizzaNameToDelete").innerText = name;
    document.getElementById(
      "deletePizzaForm"
    ).action = `/delete-pizza/${pizzaId}`;
    new bootstrap.Modal(document.getElementById("deletePizzaModal")).show();
  };

  // ---------------- Spin Wheel Functionality ----------------
  const rewards = [
    "Free Delivery",
    "10% Off",
    "Extra Cheese",
    "No Reward",
    "Buy 1 Get 1",
  ];
  const angles = [36, 108, 180, 252, 324];
  const wheel = document.getElementById("wheel");
  const spinBtn = document.getElementById("spin-btn");
  const resultDiv = document.getElementById("result");
  const redirectAfterSpin =
    typeof window.redirectAfterSpin !== "undefined"
      ? window.redirectAfterSpin
      : "/";

  if (wheel && spinBtn && resultDiv) {
    let currentAngle = 0;
    spinBtn.addEventListener("click", () => {
      spinBtn.disabled = true;
      fetch("/get-spin-reward")
        .then((res) => res.json())
        .then((data) => {
          if (data.error) {
            resultDiv.innerText = `⚠️ ${data.error}`;
            spinBtn.disabled = false;
            return;
          }
          const reward = data.reward;
          const index = rewards.indexOf(reward);
          if (index === -1) {
            resultDiv.innerText = "⚠️ Reward not recognized.";
            spinBtn.disabled = false;
            return;
          }

          const extraSpin = Math.floor(Math.random() * 30) - 15;
          currentAngle += 360 * 5 + angles[index] + extraSpin;
          wheel.style.transition = "transform 5s ease-out";
          wheel.style.transform = `rotate(${currentAngle}deg)`;

          function onTransitionEnd() {
            document
              .querySelectorAll(".segment-label")
              .forEach(
                (label) =>
                  (label.style.transform = `rotate(${-currentAngle}deg)`)
              );
            resultDiv.innerText = `🎉 You won: ${reward} 🎉`;
            setTimeout(() => (window.location.href = redirectAfterSpin), 2000);
            wheel.removeEventListener("transitionend", onTransitionEnd);
          }
          wheel.addEventListener("transitionend", onTransitionEnd);
        })
        .catch(() => {
          resultDiv.innerText = "⚠️ Network error. Please try again.";
          spinBtn.disabled = false;
        });
    });
  }
  // Toggle between URL and Upload input
  const sourceRadios = document.querySelectorAll('input[name="image_source"]');
  sourceRadios.forEach((radio) => {
    radio.addEventListener("change", (e) => {
      const urlDiv = document.getElementById("urlInputDiv");
      const uploadDiv = document.getElementById("uploadInputDiv");

      if (e.target.value === "url") {
        urlDiv.style.display = "block";
        uploadDiv.style.display = "none";
      } else if (e.target.value === "upload") {
        urlDiv.style.display = "none";
        uploadDiv.style.display = "block";
      }
    });
  });
});

document.addEventListener("DOMContentLoaded", () => {
  const imageUrlInput = document.getElementById("image_url");
  const imageFileInput = document.getElementById("image_file");
  const imagePreview = document.getElementById("imagePreview");
  const sourceRadios = document.querySelectorAll('input[name="image_source"]');

  const previewImage = (src) => {
    imagePreview.src = src || "";
    imagePreview.style.display = src ? "block" : "none";
  };

  // URL input
  imageUrlInput.addEventListener("input", () => {
    const isValidUrl = imageUrlInput.value.match(
      /^https?:\/\/.*\.(jpg|jpeg|png|gif|bmp)$/i
    );
    previewImage(isValidUrl ? imageUrlInput.value : "");
  });

  // File upload input
  imageFileInput.addEventListener("change", (e) => {
    const file = e.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (event) => previewImage(event.target.result);
      reader.readAsDataURL(file);
    } else {
      previewImage("");
    }
  });

  // Toggle input types
  sourceRadios.forEach((radio) => {
    radio.addEventListener("change", (e) => {
      const urlDiv = document.getElementById("urlInputDiv");
      const uploadDiv = document.getElementById("uploadInputDiv");
      previewImage(""); // clear previous preview when switching

      if (e.target.value === "url") {
        urlDiv.style.display = "block";
        uploadDiv.style.display = "none";
      } else {
        urlDiv.style.display = "none";
        uploadDiv.style.display = "block";
      }
    });
  });
});
