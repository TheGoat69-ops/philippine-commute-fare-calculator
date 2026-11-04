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


# Demo-only top-up endpoint. It does not verify or accept real payments.
@app.route("/api/demo-topup", methods=["POST"])
def demo_topup():
    data = request.get_json(silent=True) or {}
    allowed_amounts = {50.0, 100.0, 200.0}
    try:
        amount = float(data.get("amount", 0))
    except (ValueError, TypeError):
        amount = 0

    if amount not in allowed_amounts:
        return jsonify({
            "success": False,
            "message": "Choose a valid demo top-up: ₱50, ₱100, or ₱200."
        }), 400

    with machine.lock:
        machine.balance = round(machine.balance + amount, 2)
        new_balance = machine.balance

    return jsonify({
        "success": True,
        "message": f"Demo top-up of ₱{amount:.2f} added. No real payment was made.",
        "remaining_coin_balance": new_balance
    })


# Demo-only refund/reset endpoint. Restores the virtual coin balance to ₱10,000.
# This does not return real cash or control physical hardware.
@app.route("/api/refund-reset", methods=["POST"])
def refund_reset():
    with machine.lock:
        machine.balance = INITIAL_BALANCE
        new_balance = machine.balance

    return jsonify({
        "success": True,
        "message": f"Demo coin balance restored to ₱{new_balance:,.2f}. No real cash was refunded.",
        "remaining_coin_balance": new_balance
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

    service_fee = 3.00
    dispensed_amount = round(amount - service_fee, 2)

    if dispensed_amount <= 0:
        return jsonify({
            "success": False,
            "message": "Transaction amount must be greater than the ₱3.00 service fee.",
            "remaining_coin_balance": machine.get_balance()
        }), 400

    success, message = machine.exchange_bill(dispensed_amount)

    if not success:
        return jsonify({
            "success": False,
            "message": message,
            "remaining_coin_balance": machine.get_balance()
        }), 400

    return jsonify({
        "success": True,
        "message": "Exchange completed. ₱3.00 service fee deducted.",
        "transaction_amount": amount,
        "service_fee": service_fee,
        "dispensed_amount": dispensed_amount,
        "remaining_coin_balance": machine.get_balance()
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
