document.addEventListener("DOMContentLoaded", () => {
  const activitiesList = document.getElementById("activities-list");
  const activitySelect = document.getElementById("activity");
  const signupForm = document.getElementById("signup-form");
  const messageDiv = document.getElementById("message");

  // Function to fetch activities from API
  async function fetchActivities() {
    try {
      const response = await fetch("/activities");
      const activities = await response.json();

      // Clear loading message
      activitiesList.innerHTML = "";

      // Populate activities list
      Object.entries(activities).forEach(([name, details]) => {
        const activityCard = document.createElement("div");
        activityCard.className = "activity-card";

        const spotsLeft = details.max_participants - details.participants.length;

        const participantsList = details.participants
          .map(participant => `
            <li data-participant="${participant}" data-activity="${name}">
              <span>${participant}</span>
              <button class="delete-btn" aria-label="Remove ${participant}" title="Remove participant">✕</button>
            </li>
          `)
          .join("");

        activityCard.innerHTML = `
          <h4>${name}</h4>
          <p>${details.description}</p>
          <p><strong>Schedule:</strong> ${details.schedule}</p>
          <p><strong>Availability:</strong> ${spotsLeft} spots left</p>
          <div class="participants-section">
            <h5>Current Participants</h5>
            <ul class="participants-list">
              ${participantsList || "<li class='no-participants'>No participants yet</li>"}
            </ul>
          </div>
        `;

        activitiesList.appendChild(activityCard);

        // Add delete button event listeners
        const deleteButtons = activityCard.querySelectorAll(".delete-btn");
        deleteButtons.forEach(button => {
          button.addEventListener("click", async (event) => {
            event.preventDefault();
            
            const listItem = button.closest("li");
            const participant = listItem.getAttribute("data-participant");
            const activity = listItem.getAttribute("data-activity");

            try {
              const response = await fetch(
                `/activities/${encodeURIComponent(activity)}/unregister?email=${encodeURIComponent(participant)}`,
                {
                  method: "DELETE",
                }
              );

              if (response.ok) {
                // Remove the list item from the DOM
                listItem.style.opacity = "0.5";
                setTimeout(() => {
                  listItem.remove();
                  // If no more participants, show the "no participants" message
                  const list = button.closest(".participants-list");
                  if (list.children.length === 0) {
                    const noParticipantsItem = document.createElement("li");
                    noParticipantsItem.className = "no-participants";
                    noParticipantsItem.textContent = "No participants yet";
                    list.appendChild(noParticipantsItem);
                  }
                  // Refresh to update spot count
                  fetchActivities();
                }, 300);
              } else {
                const result = await response.json();
                alert(result.detail || "Failed to remove participant");
              }
            } catch (error) {
              console.error("Error removing participant:", error);
              alert("Failed to remove participant");
            }
          });
        });

        // Add option to select dropdown
        const option = document.createElement("option");
        option.value = name;
        option.textContent = name;
        activitySelect.appendChild(option);
      });
    } catch (error) {
      activitiesList.innerHTML = "<p>Failed to load activities. Please try again later.</p>";
      console.error("Error fetching activities:", error);
    }
  }

  // Handle form submission
  signupForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const email = document.getElementById("email").value;
    const activity = document.getElementById("activity").value;

    try {
      const response = await fetch(
        `/activities/${encodeURIComponent(activity)}/signup?email=${encodeURIComponent(email)}`,
        {
          method: "POST",
        }
      );

      const result = await response.json();

      if (response.ok) {
        messageDiv.textContent = result.message;
        messageDiv.className = "success";
        signupForm.reset();
        fetchActivities();
      } else {
        messageDiv.textContent = result.detail || "An error occurred";
        messageDiv.className = "error";
      }

      messageDiv.classList.remove("hidden");

      // Hide message after 5 seconds
      setTimeout(() => {
        messageDiv.classList.add("hidden");
      }, 5000);
    } catch (error) {
      messageDiv.textContent = "Failed to sign up. Please try again.";
      messageDiv.className = "error";
      messageDiv.classList.remove("hidden");
      console.error("Error signing up:", error);
    }
  });

  // Initialize app
  fetchActivities();
});
