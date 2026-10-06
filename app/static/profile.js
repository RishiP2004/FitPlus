// Update the unit labels when the user switches kg/cm <-> lb/in (PB-08).
(function () {
  var labels = { metric: ["kg", "cm"], imperial: ["lb", "in"] };
  document.querySelectorAll('input[name="unit_system"]').forEach(function (radio) {
    radio.addEventListener("change", function () {
      var u = labels[radio.value];
      document.querySelector('[data-unit="weight"]').textContent = u[0];
      document.querySelector('[data-unit="height"]').textContent = u[1];
    });
  });
})();
