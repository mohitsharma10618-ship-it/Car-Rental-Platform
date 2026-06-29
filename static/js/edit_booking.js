document.addEventListener("DOMContentLoaded", function () {

    const startInput = document.getElementById("start_time");
    const endInput = document.getElementById("end_time");

    const duration = document.getElementById("duration");
    const price = document.getElementById("price");

    const rentPerHour = parseFloat(
        document.getElementById("rent_per_hour").value
    );

    function calculatePrice() {

        if (!startInput.value || !endInput.value)
            return;

        const start = new Date(startInput.value);
        const end = new Date(endInput.value);

        const hours =
            (end - start) / (1000 * 60 * 60);

        if (hours <= 0) {

            duration.innerHTML = "--";
            price.innerHTML = "--";

            return;

        }

        duration.innerHTML =
            hours.toFixed(1) + " Hours";

        price.innerHTML =
            (hours * rentPerHour).toFixed(2);

    }

    calculatePrice();

    startInput.addEventListener(
        "change",
        calculatePrice
    );

    endInput.addEventListener(
        "change",
        calculatePrice
    );

});