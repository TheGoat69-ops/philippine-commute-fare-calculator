
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
