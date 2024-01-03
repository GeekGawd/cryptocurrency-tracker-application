import json
import websocket

def on_message(ws, message):
    data = json.loads(message)
    price = float(data['data']['a'])
    if price > THRESHOLD:
        print("Threshold reached, sending email")

def on_error(ws, error):
    print(error)

def on_close(ws):
    print("### closed ###")

def on_open(ws):
    payload = {
        "method": "SUBSCRIBE",
        "params": ["btcusdt@bookTicker"],
        "id": 1
    }
    ws.send(json.dumps(payload))

if __name__ == "__main__":
    THRESHOLD = 45216  # Set your price threshold here
    websocket.enableTrace(True)
    ws = websocket.WebSocketApp("wss://stream.binance.com/stream",
                                on_message=on_message,
                                on_error=on_error,
                                on_close=on_close)
    ws.on_open = on_open
    ws.run_forever()
