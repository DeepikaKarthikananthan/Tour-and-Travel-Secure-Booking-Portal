document.addEventListener("DOMContentLoaded", function () {
    // Dark / Light Theme Toggle Switch
    const themeBtn = document.getElementById("themeToggleBtn");
    const currentTheme = localStorage.getItem("wf_theme") || "light";

    if (currentTheme === "dark") {
        document.body.classList.add("dark-theme");
        if (themeBtn) themeBtn.innerHTML = `<i class="fa-solid fa-sun text-warning"></i>`;
    }

    if (themeBtn) {
        themeBtn.addEventListener("click", function () {
            document.body.classList.toggle("dark-theme");
            const isDark = document.body.classList.contains("dark-theme");
            localStorage.setItem("wf_theme", isDark ? "dark" : "light");
            themeBtn.innerHTML = isDark ? `<i class="fa-solid fa-sun text-warning"></i>` : `<i class="fa-solid fa-moon"></i>`;
        });
    }

    // Auto-dismiss flash alerts after a few seconds.
    document.querySelectorAll(".wf-alert").forEach(function (alertEl) {
        setTimeout(function () {
            const alert = bootstrap.Alert.getOrCreateInstance(alertEl);
            if (alert) alert.close();
        }, 6000);
    });

    // Dynamic Currency Switcher & Persistence Feature
    const currencyBtn = document.getElementById("currencyBtn");

    function applyCurrency(selectedCurrency) {
        if (!selectedCurrency) return;
        localStorage.setItem("selectedCurrency", selectedCurrency);
        if (currencyBtn) {
            currencyBtn.innerHTML = `<i class="fa-solid fa-coins me-1"></i> ${selectedCurrency}`;
        }
        window.applyCurrency = applyCurrency;
        
        fetch(`/api/currency/convert?currency=${selectedCurrency}&amount=100`)
            .then(res => res.json())
            .then(data => {
                if (data.status === "success") {
                    const rate = data.rate;
                    const symbol = data.symbol;
                    
                    // Select all price containers
                    document.querySelectorAll(".wf-tour-price, .currency-convert, [data-usd-price]").forEach(function (el) {
                        if (!el.dataset.usdPrice) {
                            const rawText = el.textContent.replace(/[^0-9.]/g, '');
                            if (rawText) el.dataset.usdPrice = rawText;
                        }
                        const basePrice = parseFloat(el.dataset.usdPrice || "0");
                        if (basePrice > 0) {
                            const converted = (basePrice * rate).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
                            // Preserve child elements like <small>
                            const small = el.querySelector("small");
                            if (small) {
                                el.innerHTML = `${symbol}${converted} ${small.outerHTML}`;
                            } else {
                                el.textContent = `${symbol}${converted}`;
                            }
                        }
                    });
                }
            })
            .catch(err => console.log("Currency conversion error:", err));
    }

    document.querySelectorAll(".currency-select").forEach(function (item) {
        item.addEventListener("click", function (e) {
            e.preventDefault();
            const selectedCurrency = this.dataset.currency;
            applyCurrency(selectedCurrency);
        });
    });

    // Auto-apply saved currency from localStorage across all pages
    const savedCurrency = localStorage.getItem("selectedCurrency");
    if (savedCurrency && savedCurrency !== "USD") {
        applyCurrency(savedCurrency);
    }

    // Booking form: live cost calculation with add-ons & insurance.
    const adultsInput = document.getElementById("adults");
    const childrenInput = document.getElementById("children");
    const summaryEl = document.getElementById("bookingSummary");
    const insuranceCheck = document.getElementById("insuranceCheck");
    const hotelSelect = document.querySelector("select[name='hotel_tier']");

    if (adultsInput && childrenInput && summaryEl) {
        const adultPrice = parseFloat(summaryEl.dataset.adultPrice || "0");
        const childPrice = parseFloat(summaryEl.dataset.childPrice || "0");

        function updateSummary() {
            const adults = Math.max(parseInt(adultsInput.value || "0", 10), 0);
            const children = Math.max(parseInt(childrenInput.value || "0", 10), 0);

            const adultCost = adults * adultPrice;
            const childCost = children * childPrice;
            const travelers = adults + children;

            let insuranceCost = 0;
            if (insuranceCheck && insuranceCheck.checked) {
                insuranceCost = travelers * 39.0;
            }

            let hotelCost = 0;
            if (hotelSelect) {
                if (hotelSelect.value === "Deluxe") hotelCost = 150.0;
                else if (hotelSelect.value === "5-Star Luxury") hotelCost = 300.0;
            }

            const total = adultCost + childCost + insuranceCost + hotelCost;

            if (document.getElementById("sumAdults")) document.getElementById("sumAdults").textContent = adults;
            if (document.getElementById("sumChildren")) document.getElementById("sumChildren").textContent = children;
            if (document.getElementById("sumAdultCost")) document.getElementById("sumAdultCost").textContent = "$" + adultCost.toFixed(2);
            if (document.getElementById("sumChildCost")) document.getElementById("sumChildCost").textContent = "$" + childCost.toFixed(2);
            if (document.getElementById("sumTotal")) document.getElementById("sumTotal").textContent = "$" + total.toFixed(2);
        }

        adultsInput.addEventListener("input", updateSummary);
        childrenInput.addEventListener("input", updateSummary);
        if (insuranceCheck) insuranceCheck.addEventListener("change", updateSummary);
        if (hotelSelect) hotelSelect.addEventListener("change", updateSummary);
        updateSummary();
    }

    // Star rating widgets on the feedback form.
    document.querySelectorAll(".wf-star-rating").forEach(function (widget) {
        const input = widget.querySelector("input[type=hidden]");
        const stars = widget.querySelectorAll(".wf-star");

        function setRating(value) {
            input.value = value;
            stars.forEach(function (star, idx) {
                star.classList.toggle("active", idx < value);
            });
        }

        stars.forEach(function (star, idx) {
            star.addEventListener("click", function () { setRating(idx + 1); });
        });
    });
});
