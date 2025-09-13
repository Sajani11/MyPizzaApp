document.addEventListener("DOMContentLoaded", () => {
  // Check if we're on the "Add Pizza" page
  if (document.body.classList.contains("add-pizza-page")) {
    const form = document.getElementById("addPizzaForm");
    const imageInput = document.getElementById("image_url");
    const imagePreview = document.getElementById("imagePreview");

    // Check if all the elements exist before attaching event listeners
    if (form && imageInput && imagePreview) {
      // Handle URL input for the image
      imageInput.addEventListener("input", () => {
        const inputValue = imageInput.value; // Get the value from input
        const isUrl = inputValue.match(
          /^https?:\/\/.*\.(jpg|jpeg|png|gif|bmp)$/i
        );
        if (isUrl) {
          imagePreview.src = inputValue; // Set the image preview from the URL
          imagePreview.style.display = "block"; // Show the preview
        } else {
          imagePreview.style.display = "none"; // Hide the preview if the URL is invalid
        }
      });

      form.addEventListener("submit", (e) => {
        e.preventDefault(); // Prevents default form submission

        const name = form.querySelector('input[name="pizza_name"]');
        const price = form.querySelector('input[name="price"]');
        const description = form.querySelector('textarea[name="description"]');

        // Simple validation
        if (
          !name.value ||
          !price.value ||
          !description.value ||
          !imageInput.value
        ) {
          alert("Please fill out all fields.");
          return;
        }

        // If everything is valid, submit the form via AJAX
        const formData = new FormData(form);

        fetch("/add_pizza", {
          method: "POST",
          body: formData,
        })
          .then((response) => response.json())
          .then((data) => {
            if (data.success) {
              alert("Pizza added successfully!");
              form.reset(); // Reset the form after successful submission
              imagePreview.style.display = "none"; // Hide image preview after submission
              imageInput.value = ""; // Reset the image URL input
            } else {
              alert("Error adding pizza.");
            }
          })
          .catch((error) => {
            alert("Something went wrong. Please try again.");
            console.error(error);
          });
      });
    } else {
      console.error(
        "One or more elements (form, imageInput, imagePreview) are missing from the page."
      );
    }
  } else {
    // Handle other pages' functionality (e.g., search)
    const input = document.getElementById("searchInput");
    const pizzaItems = document.querySelectorAll(".pizza-item");
    const noResultMsg = document.getElementById("noResultMsg");

    if (input) {
      input.addEventListener("keyup", () => {
        const keyword = input.value.toLowerCase();
        let matchFound = false;

        pizzaItems.forEach((item) => {
          const name = item.getAttribute("data-name");
          if (name.includes(keyword)) {
            item.style.display = "block";
            gsap.to(item, {
              opacity: 1,
              y: 0,
              duration: 0.4,
              ease: "power2.out",
            });
            matchFound = true;
          } else {
            gsap.to(item, {
              opacity: 0,
              y: -20,
              duration: 0.3,
              ease: "power2.in",
              onComplete: () => {
                item.style.display = "none";
              },
            });
          }
        });

        noResultMsg.style.display = matchFound ? "none" : "block";
      });

      // Initial entrance animation
      gsap.from(".pizza-item", {
        opacity: 0,
        y: 50,
        duration: 0.6,
        ease: "back.out(1.7)",
        stagger: 0.1,
      });

      document.querySelectorAll(".pizza-img").forEach((img) => {
        img.addEventListener("mouseenter", () => {
          gsap.to(img, {
            boxShadow: "0 0 20px 5px rgba(255, 193, 7, 0.8)",
            scale: 1.05,
            duration: 0.3,
          });
        });

        img.addEventListener("mouseleave", () => {
          gsap.to(img, {
            boxShadow: "0 0 15px rgba(0, 0, 0, 0.2)",
            scale: 1,
            duration: 0.3,
          });
        });
      });
    }
  }
});

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
        resultDiv.innerText = "⚠️ Error: Reward not recognized.";
        spinBtn.disabled = false;
        return;
      }

      // Spin 5 full rotations + target angle
      const extraSpin = Math.floor(Math.random() * 30) - 15;
      currentAngle += 360 * 5 + angles[index] + extraSpin;

      wheel.style.transition = "transform 5s ease-out";
      wheel.style.transform = `rotate(${currentAngle}deg)`;

      function onTransitionEnd() {
        document.querySelectorAll(".segment-label").forEach((label) => {
          label.style.transform = `rotate(${-currentAngle}deg)`;
        });
        resultDiv.innerText = `🎉 You won: ${reward} 🎉`;

        // Redirect after 2 seconds
        setTimeout(() => {
          window.location.href = "{{ redirect_after_spin }}";
        }, 2000);

        wheel.removeEventListener("transitionend", onTransitionEnd);
      }

      wheel.addEventListener("transitionend", onTransitionEnd);
    })
    .catch(() => {
      resultDiv.innerText = "⚠️ Network error. Please try again.";
      spinBtn.disabled = false;
    });
});
