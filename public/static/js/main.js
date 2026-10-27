/* Wild Dandelions - three small jobs:
   1. open a piece bigger when you click its photo
   2. carry a piece's name down to the form when you ask about it
   3. send the form without reloading the page                        */

(function () {
  "use strict";

  /* ---------- 1. the lightbox ---------- */

  const lightbox = document.getElementById("lightbox");
  const lightboxImage = document.getElementById("lightbox-image");
  const lightboxCaption = document.getElementById("lightbox-caption");
  const lightboxPrice = document.getElementById("lightbox-price");
  const photos = Array.from(document.querySelectorAll(".piece__photo"));

  let openedFrom = null;

  function show(photo) {
    openedFrom = photo;
    lightboxImage.src = photo.dataset.image;
    lightboxImage.alt = photo.querySelector("img").alt;
    lightboxCaption.textContent = photo.dataset.piece;
    lightboxPrice.textContent = photo.dataset.price;
    lightbox.showModal();
  }

  photos.forEach((photo) => photo.addEventListener("click", () => show(photo)));

  document
    .getElementById("lightbox-close")
    .addEventListener("click", () => lightbox.close());

  // Clicking the backdrop closes it; clicking the picture does not.
  lightbox.addEventListener("click", (event) => {
    if (event.target === lightbox) lightbox.close();
  });

  // Put focus back where it was, so keyboard users don't lose their place.
  lightbox.addEventListener("close", () => {
    if (openedFrom) openedFrom.focus();
  });

  // Left and right walk through the pieces without closing.
  lightbox.addEventListener("keydown", (event) => {
    if (event.key !== "ArrowRight" && event.key !== "ArrowLeft") return;
    const step = event.key === "ArrowRight" ? 1 : -1;
    const next = (photos.indexOf(openedFrom) + step + photos.length) % photos.length;
    event.preventDefault();
    show(photos[next]);
  });

  /* ---------- 2. "email me about these" ---------- */

  const pieceField = document.getElementById("piece");
  const pieceNote = document.getElementById("about-piece");
  const pieceName = document.getElementById("about-piece-name");
  const messageField = document.getElementById("message");

  function askAbout(name) {
    pieceField.value = name;
    pieceName.textContent = name;
    pieceNote.dataset.shown = "true";
    document.getElementById("write").scrollIntoView({ behavior: "smooth" });
    // Land them on the first empty field rather than the top of the form.
    const nameField = document.getElementById("name");
    window.setTimeout(() => (nameField.value ? messageField : nameField).focus(), 450);
  }

  document.querySelectorAll("[data-ask-about]").forEach((button) => {
    button.addEventListener("click", () => askAbout(button.dataset.askAbout));
  });

  document.getElementById("clear-piece").addEventListener("click", () => {
    pieceField.value = "";
    pieceNote.dataset.shown = "false";
  });

  /* ---------- 3. sending the form ---------- */

  const form = document.getElementById("enquiry-form");
  const submit = document.getElementById("submit");
  const status = document.getElementById("status");

  function say(text, tone) {
    status.textContent = text;
    status.dataset.tone = tone;
  }

  form.addEventListener("submit", async (event) => {
    event.preventDefault();

    const payload = Object.fromEntries(new FormData(form).entries());

    submit.disabled = true;
    say("Sending...", "");

    try {
      const response = await fetch("/api/enquiry", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const result = await response.json();

      if (response.ok) {
        form.reset();
        pieceNote.dataset.shown = "false";
        say("Thank you, that reached Torie. She answers every message.", "ok");
      } else {
        say(result.error || "That didn't send. Try again in a moment.", "error");
      }
    } catch (networkProblem) {
      say(
        "That didn't send - check your connection, or email toriewhite9@gmail.com.",
        "error"
      );
    } finally {
      submit.disabled = false;
    }
  });
})();
