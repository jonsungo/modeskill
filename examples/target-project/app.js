const openButton = document.querySelector("#open-dialog");
const closeButton = document.querySelector("#close-dialog");
const overlay = document.querySelector("#dialog-overlay");
const dialog = document.querySelector("#review-dialog");
let returnFocus = null;

function openModal() {
  returnFocus = document.activeElement;
  overlay.hidden = false;
  dialog.focus();
}

function closeModal() {
  overlay.hidden = true;
  if (returnFocus) returnFocus.focus();
}

openButton.addEventListener("click", openModal);
closeButton.addEventListener("click", closeModal);
overlay.addEventListener("click", (event) => {
  if (event.target === overlay) closeModal();
});
document.addEventListener("keydown", (event) => {
  if (event.key === "Escape" && !overlay.hidden) closeModal();
});
