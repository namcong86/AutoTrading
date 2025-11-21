from flask import Flask, jsonify
import json
import os

app = Flask(__name__)
# Use relative path to work on both Windows (C:\AutoTrading\...) and Linux (/var/AppDev/...)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
HISTORY_FILE = os.path.join(BASE_DIR, "history.json")

@app.route('/history', methods=['GET'])
def get_history():
    if not os.path.exists(HISTORY_FILE):
        return jsonify([])
    
    try:
        with open(HISTORY_FILE, 'r') as f:
            data = json.load(f)
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
