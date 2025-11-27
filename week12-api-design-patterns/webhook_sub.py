from flask import Flask, request

app = Flask(__name__)

@app.route("/webhook", methods=["POST"])
def webhook_receiver():
    payload = request.json
    print("Received webhook:", payload)
    # trigger notification, update dashboard,...
    return {"status": "ok"}, 200

if __name__ == "__main__":
    app.run(port=6000, debug=True)
