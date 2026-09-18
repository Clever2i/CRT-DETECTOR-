import os
import requests
from datetime import datetime, timezone

OANDA_TOKEN = os.environ["OANDA_TOKEN"]
OANDA_ACCOUNT_ID = os.environ["OANDA_ACCOUNT_ID"]
TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

OANDA_URL = "https://api-fxpractice.oanda.com/v3/instruments/XAU_USD/candles"


def get_candles():
    headers = {
        "Authorization": f"Bearer {OANDA_TOKEN}"
    }

    params = {
        "granularity": "H1",
        "count": 4,
        "price": "M"
    }

    response = requests.get(OANDA_URL, headers=headers, params=params, timeout=20)
    response.raise_for_status()

    return response.json()["candles"]


def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

    data = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message
    }

    response = requests.post(url, data=data, timeout=20)
    response.raise_for_status()


def is_down_crt(c1, c2):
    c1_open = float(c1["mid"]["o"])
    c1_high = float(c1["mid"]["h"])
    c1_low = float(c1["mid"]["l"])
    c1_close = float(c1["mid"]["c"])

    c2_open = float(c2["mid"]["o"])
    c2_high = float(c2["mid"]["h"])
    c2_low = float(c2["mid"]["l"])
    c2_close = float(c2["mid"]["c"])

    c1_body = abs(c1_close - c1_open)
    c1_upper_wick = c1_high - max(c1_open, c1_close)
    c1_lower_wick = min(c1_open, c1_close) - c1_low
    c1_range = c1_high - c1_low

    c2_body = abs(c2_close - c2_open)

    if c1_range == 0:
        return False

    c1_strong_bull = (
        c1_close > c1_open
        and c1_upper_wick + c1_lower_wick <= c1_body
    )

    c2_small = c2_body <= c1_range * 0.25

    return (
        c1_strong_bull
        and c2_high > c1_high
        and c2_low >= c1_low
        and c2_close < c1_high
        and c2_small
    )


def is_up_crt(c1, c2):
    c1_open = float(c1["mid"]["o"])
    c1_high = float(c1["mid"]["h"])
    c1_low = float(c1["mid"]["l"])
    c1_close = float(c1["mid"]["c"])

    c2_open = float(c2["mid"]["o"])
    c2_high = float(c2["mid"]["h"])
    c2_low = float(c2["mid"]["l"])
    c2_close = float(c2["mid"]["c"])

    c1_body = abs(c1_close - c1_open)
    c1_upper_wick = c1_high - max(c1_open, c1_close)
    c1_lower_wick = min(c1_open, c1_close) - c1_low
    c1_range = c1_high - c1_low

    c2_body = abs(c2_close - c2_open)

    if c1_range == 0:
        return False

    c1_strong_bear = (
        c1_close < c1_open
        and c1_upper_wick + c1_lower_wick <= c1_body
    )

    c2_small = c2_body <= c1_range * 0.25

    return (
        c1_strong_bear
        and c2_low < c1_low
        and c2_high <= c1_high
        and c2_close > c1_low
        and c2_small
    )


def main():
    candles = get_candles()

    # Last candle returned by OANDA may still be forming.
    # We use the most recent completed candle as Candle 2.
    completed = [c for c in candles if c["complete"]]

    if len(completed) < 2:
        print("Not enough completed candles.")
        return

    c1 = completed[-2]
    c2 = completed[-1]

    if is_down_crt(c1, c2):
        send_telegram(
            "🔴 DOWN CRT DETECTED\n\n"
            "XAUUSD — 1H\n"
            "Candle 2 swept Candle 1 HIGH and closed back below it.\n\n"
            "CHECK CANDLE 3."
        )
        print("DOWN CRT detected.")

    elif is_up_crt(c1, c2):
        send_telegram(
            "🟢 UP CRT DETECTED\n\n"
            "XAUUSD — 1H\n"
            "Candle 2 swept Candle 1 LOW and closed back above it.\n\n"
            "CHECK CANDLE 3."
        )
        print("UP CRT detected.")

    else:
        print("No CRT setup.")


if __name__ == "__main__":
    main()
