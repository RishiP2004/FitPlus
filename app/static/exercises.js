// Live search + filter for the exercise library (PB-12, PB-13).
// Filters the already-loaded list in the browser, so results update instantly.
(function () {
  var form = document.getElementById("exercise-filters");
  if (!form) return;
  var q = form.querySelector("#q");
  var muscle = form.querySelector("#muscle");
  var equipment = form.querySelector("#equipment");
  var count = document.getElementById("result-count");
  var empty = document.getElementById("no-results");
  var groups = document.querySelectorAll(".muscle-group");

  function apply() {
    var term = q.value.trim().toLowerCase();
    var m = muscle.value;
    var e = equipment.value;
    var total = 0;
    groups.forEach(function (group) {
      var shown = 0;
      group.querySelectorAll(".exercise").forEach(function (item) {
        var ok = (!term || item.dataset.name.indexOf(term) !== -1) &&
                 (!m || item.dataset.muscle === m) &&
                 (!e || item.dataset.equipment === e);
        item.hidden = !ok;
        if (ok) shown++;
      });
      group.hidden = shown === 0;
      total += shown;
    });
    count.textContent = total + (total === 1 ? " exercise" : " exercises");
    empty.hidden = total !== 0;
    // Keep the URL shareable / bookmarkable.
    var params = new URLSearchParams();
    if (term) params.set("q", q.value.trim());
    if (m) params.set("muscle", m);
    if (e) params.set("equipment", e);
    var qs = params.toString();
    history.replaceState(null, "", location.pathname + (qs ? "?" + qs : ""));
  }

  q.addEventListener("input", apply);
  muscle.addEventListener("change", apply);
  equipment.addEventListener("change", apply);
  form.addEventListener("submit", function (ev) { ev.preventDefault(); apply(); });
  var actions = form.querySelector(".filter-actions button");
  if (actions) actions.hidden = true; // live filtering makes "Apply" unnecessary
})();
