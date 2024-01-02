const alertPlaceholder = document.getElementById("alertPlaceholder");
alertPlaceholder.display = "hidden";
const appendAlert = (message, type) => {
  const wrapper = document.createElement("div");
  wrapper.innerHTML = [
    `<div class="alert alert-${type} alert-dismissible" role="alert">`,
    `   <div>${message}</div>`,
    '   <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>',
    "</div>",
  ].join("");
  alertPlaceholder.append(wrapper);
};

let msg = document.getElementById("alertMsg").getAttribute("data-value");
let type = document.getElementById("alertType").getAttribute("data-value");
if (msg && type) {
  appendAlert(msg, type);
  document.getElementById("alertMsg").setAttribute("data-value", "");
  document.getElementById("alertType").setAttribute("data-value", "");
} else {
  alertPlaceholder.innerHTML = "";
}
