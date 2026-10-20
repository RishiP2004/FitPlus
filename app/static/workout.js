// Workout page: live elapsed timer (PB-19) and a notes character counter (PB-25).
(function () {
  var el = document.getElementById("elapsed");
  if (el) {
    var started = new Date(el.dataset.started);
    var tick = function () {
      var s = Math.max(0, Math.floor((Date.now() - started.getTime()) / 1000));
      var h = Math.floor(s / 3600), m = Math.floor((s % 3600) / 60), sec = s % 60;
      el.textContent = (h ? h + ":" + String(m).padStart(2, "0") : m) + ":" + String(sec).padStart(2, "0") + " elapsed";
    };
    tick();
    setInterval(tick, 1000);
  }
  var notes = document.getElementById("notes-text");
  var count = document.getElementById("notes-count");
  if (notes && count) {
    var max = parseInt(notes.getAttribute("maxlength"), 10);
    var update = function () { count.textContent = notes.value.length + " / " + max; };
    notes.addEventListener("input", update);
    update();
  }
  // Keep the reps/weight a user is typing if the page reloads before they press "Add set".
  try {
    document.querySelectorAll("form.add-set").forEach(function (form) {
      var key = "fitplus:" + form.getAttribute("action");
      var saved = JSON.parse(sessionStorage.getItem(key) || "null");
      if (saved) {
        form.reps.value = saved.reps; form.weight.value = saved.weight;
      }
      form.addEventListener("input", function () {
        sessionStorage.setItem(key, JSON.stringify({ reps: form.reps.value, weight: form.weight.value }));
      });
      form.addEventListener("submit", function () { sessionStorage.removeItem(key); });
    });
  } catch (e) { /* storage unavailable: nothing to restore */ }
})();
