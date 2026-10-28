from math import isfinite
from threading import Lock

from flask import Flask, jsonify, render_template_string, request

app = Flask(__name__)

# Initial coin inventory of the hardware machine
INITIAL_BALANCE = 10000.00

class CashMachine:
    def __init__(self, initial_balance=INITIAL_BALANCE):
        self.balance = round(initial_balance, 2)
        self.lock = Lock()

    def get_balance(self):
        with self.lock:
            return self.balance

    def exchange_bill(self, amount):
        if not isfinite(amount) or amount <= 0:
            return False, "Enter a valid amount greater than zero."

        with self.lock:
            if amount > self.balance:
                return False, "Insufficient coins in the machine."

            # Deduct only the value of coins dispensed.
            self.balance = round(self.balance - amount, 2)
            return True, "Coin exchange recorded successfully."


machine = CashMachine()

prices = {
    "JEEPNEY": {
        "base_fare": 13.00,
        "included_km": 10,
        "extra_per_km": 3.00
    },
    "TRICYCLE": {
        "base_fare": 10.00,
        "included_km": 10,
        "extra_per_km": 2.00
    },
    "BUS": {
        "base_fare": 15.00,
        "included_km": 5,
        "extra_per_km": 3.00
    },
    "E-BUS": {
        "base_fare": 17.00,
        "included_km": 4,
        "extra_per_km": 3.00
    },
    "UV EXPRESS": {
        "base_fare": 35.00,
        "included_km": 5,
        "extra_per_km": 5.00
    },
}

PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport"
          content="width=device-width, initial-scale=1">

    <title>Philippine Commute Fare Calculator</title>

    <style>
        body {
            font-family: Arial, sans-serif;
            background: #f2f5f9;
            margin: 0;
            padding: 25px;
            color: #202938;
        }

        .container {
            max-width: 650px;
            margin: auto;
        }

        .card {
            background: white;
            padding: 25px;
            margin-bottom: 20px;
            border-radius: 14px;
            box-shadow: 0 3px 12px #00000012;
        }

        h1, h2 {
            margin-top: 0;
        }

        .balance {
            font-size: 38px;
            font-weight: bold;
            color: #16834a;
            margin: 15px 0;
        }

        .subtitle {
            color: #687386;
            font-size: 14px;
        }

        label {
            display: block;
            margin-top: 15px;
            margin-bottom: 7px;
        }

        input, select, button {
            width: 100%;
            box-sizing: border-box;
            padding: 12px;
            font-size: 16px;
            border-radius: 8px;
            border: 1px solid #ccd3dd;
        }

        input[type="checkbox"] {
            width: auto;
        }

        button {
            background: #1769e0;
            color: white;
            border: none;
            margin-top: 18px;
            cursor: pointer;
            font-weight: bold;
        }

        button:hover {
            background: #0f50b5;
        }

        .result {
            background: #edf8f0;
            padding: 15px;
            border-radius: 8px;
            margin-top: 20px;
        }

        .error {
            background: #fff0f0;
            color: #b42318;
            padding: 12px;
            border-radius: 8px;
            margin-top: 15px;
        }

        .balance-row {
            display: flex;
            justify-content: space-between;
            gap: 10px;
            margin-top: 15px;
        }

        .balance-row span {
            color: #687386;
        }

        .demo-box {
            margin-top: 20px;
            padding: 15px;
            background: #f4f7ff;
            border: 1px solid #d9e3ff;
            border-radius: 10px;
        }

        .message {
            margin-top: 12px;
            padding: 12px;
            border-radius: 8px;
            display: none;
        }

        .message.success {
            display: block;
            background: #edf8f0;
            color: #176b3a;
        }

        .message.failure {
            display: block;
            background: #fff0f0;
            color: #b42318;
        }
    </style>
</head>

<body>
<div class="container">

    <div class="card">
        <h1>Philippine Commute Fare Calculator</h1>
        <p class="subtitle">
            Calculate your estimated commute fare.
        </p>

        <form method="POST" action="/">
            <label for="vehicle">Vehicle type:</label>
            <select id="vehicle" name="vehicle" required>
                {% for name in vehicles %}
                <option value="{{ name }}"
                    {% if name == selected_vehicle %}selected{% endif %}>
                    {{ name }}
                </option>
                {% endfor %}
            </select>

            <label for="distance">Commute distance (km):</label>
            <input id="distance" name="distance" type="number"
                   min="0" step="any"
                   value="{{ distance_text }}" required>

            <label>
                <input type="checkbox" name="discount" value="yes"
                       {% if discounted %}checked{% endif %}>
                Apply 20% discount
            </label>

            <button type="submit">Calculate Fare</button>
        </form>

        {% if fare is not none %}
        <div class="result">
            <h2>Estimated Fare: ₱{{ "%.2f"|format(fare) }}</h2>
        </div>
        {% endif %}

        {% if error %}
        <div class="error">{{ error }}</div>
        {% endif %}
    </div>

    <div class="card">
        <h2>Hardware Coin Balance</h2>
        <p class="subtitle">
            Remaining value of coins inside the machine
        </p>

        <div class="balance" id="balance">
            ₱{{ "%.2f"|format(balance) }}
        </div>

        <div class="balance-row">
            <span>Initial coin balance</span>
            <strong>₱{{ "%.2f"|format(initial_balance) }}</strong>
        </div>

        <div class="balance-row">
            <span>Current coin balance</span>
            <strong id="balance-small">
                ₱{{ "%.2f"|format(balance) }}
            </strong>
        </div>

        <p class="subtitle">
            This balance decreases after a successful exchange transaction.
            The control below is a software demo and does not dispense real coins.
        </p>

        <div class="demo-box">
            <h3>Test Coin Exchange (Demo)</h3>
            <p class="subtitle">Use this while the physical hardware is not connected.</p>
            <form id="exchange-form">
                <label for="exchange-amount">Amount to exchange (₱):</label>
                <input id="exchange-amount" name="amount" type="number"
                       min="0.01" step="0.01" value="50.00" required>
                <button id="exchange-button" type="submit">Test Exchange</button>
            </form>
            <div id="exchange-message" class="message" role="status" aria-live="polite"></div>
        </div>
    </div>

</div>

<script>
function formatPeso(value) {
    return "₱" + Number(value).toLocaleString("en-PH", {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    });
}

async function updateBalance() {
    try {
        const response = await fetch("/api/balance");
        if (!response.ok) return;

        const data = await response.json();

        const formatted = formatPeso(data.remaining_coin_balance);
        document.getElementById("balance").textContent = formatted;
        document.getElementById("balance-small").textContent = formatted;
    } catch (error) {
        console.log("Unable to update coin balance.");
    }
}

document.getElementById("exchange-form").addEventListener("submit", async function(event) {
    event.preventDefault();

    const amountInput = document.getElementById("exchange-amount");
    const button = document.getElementById("exchange-button");
    const message = document.getElementById("exchange-message");
    const amount = Number(amountInput.value);

    message.className = "message";
    message.textContent = "";

    if (!Number.isFinite(amount) || amount <= 0 || Math.round(amount * 100) !== amount * 100) {
        message.className = "message failure";
        message.textContent = "Enter a valid amount greater than zero, with up to 2 decimal places.";
        return;
    }

    button.disabled = true;
    button.textContent = "Processing...";

    try {
        const response = await fetch("/api/exchange", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ amount: amount })
        });
        const data = await response.json();

        if (!response.ok || !data.success) {
            message.className = "message failure";
            message.textContent = data.message || "Exchange failed.";
            if (data.remaining_coin_balance !== undefined) {
                document.getElementById("balance").textContent = formatPeso(data.remaining_coin_balance);
                document.getElementById("balance-small").textContent = formatPeso(data.remaining_coin_balance);
            }
            return;
        }

        document.getElementById("balance").textContent = formatPeso(data.remaining_coin_balance);
        document.getElementById("balance-small").textContent = formatPeso(data.remaining_coin_balance);
        message.className = "message success";
        message.textContent = data.message + " New balance: " + formatPeso(data.remaining_coin_balance);
        amountInput.value = "";
    } catch (error) {
        message.className = "message failure";
        message.textContent = "Could not contact the server. Please try again.";
    } finally {
        button.disabled = false;
        button.textContent = "Test Exchange";
    }
});

// Refresh the displayed balance every 2 seconds.
setInterval(updateBalance, 2000);
updateBalance();
</script>

</body>
</html>
"""


@app.route("/", methods=["GET", "POST"])
def home():
    selected_vehicle = "JEEPNEY"
    distance_text = ""
    discounted = False
    fare = None
    error = None

    if request.method == "POST":
        selected_vehicle = request.form.get(
            "vehicle", ""
        ).strip().upper()

        distance_text = request.form.get(
            "distance", ""
        ).strip()

        discounted = request.form.get("discount") == "yes"

        if selected_vehicle not in prices:
            error = "Please select a valid vehicle type."
        else:
            try:
                distance = float(distance_text)

                if not isfinite(distance) or distance < 0:
                    raise ValueError

                details = prices[selected_vehicle]

                extra_km = max(
                    0, distance - details["included_km"]
                )

                fare = (
                    details["base_fare"]
                    + extra_km * details["extra_per_km"]
                )

                if discounted:
                    fare *= 0.80

            except ValueError:
                error = "Enter a valid distance of zero or more kilometers."

    return render_template_string(
        PAGE,
        vehicles=prices.keys(),
        selected_vehicle=selected_vehicle,
        distance_text=distance_text,
        discounted=discounted,
        fare=fare,
        error=error,
        balance=machine.get_balance(),
        initial_balance=INITIAL_BALANCE,
    )


# Website reads the latest coin balance from the machine's balance object.
@app.route("/api/balance", methods=["GET"])
def get_balance():
    return jsonify({
        "initial_coin_balance": INITIAL_BALANCE,
        "remaining_coin_balance": machine.get_balance()
    })


# Hardware sends a request here after successfully dispensing coins.
@app.route("/api/exchange", methods=["POST"])
def record_exchange():
    data = request.get_json(silent=True) or {}

    try:
        amount = float(data.get("amount", 0))

        if not isfinite(amount) or amount <= 0:
            raise ValueError

        # Accept amounts with up to two decimal places.
        if round(amount, 2) != amount:
            raise ValueError

    except (ValueError, TypeError):
        return jsonify({
            "success": False,
            "message": "Invalid exchange amount."
        }), 400

    success, message = machine.exchange_bill(amount)

    if not success:
        return jsonify({
            "success": False,
            "message": message,
            "remaining_coin_balance": machine.get_balance()
        }), 400

    return jsonify({
        "success": True,
        "message": message,
        "remaining_coin_balance": machine.get_balance()
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)

