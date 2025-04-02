from flask import Flask, request, jsonify

app = Flask(__name__)
records = []
hit_count = 0
total_count = 0
streak = 1
training_mode = True
last_prediction = []
last_hit = False
last_champion = None

def predict_next(records, last_champion):
    recent = records[-3:]  # 取近3期
    champions = [r[0] for r in recent]  # 冠軍號碼列表

    # 熱號：近3期冠軍出現次數最多
    freq = {}
    for n in champions:
        freq[n] = freq.get(n, 0) + 1
    hot = max(freq, key=freq.get)

    # 動態熱號：上一期冠軍
    dynamic_hot = last_champion

    # 穩定熱門號（近3期前3名出現2次以上）
    flat = [n for r in recent for n in r]
    flat_freq = {}
    for n in flat:
        flat_freq[n] = flat_freq.get(n, 0) + 1

    candidates = [int(n) for n, c in flat_freq.items() if c >= 2 and int(n) not in [int(hot), int(dynamic_hot)]]
    result = list({int(hot), int(dynamic_hot)} | set(candidates[:3]))
    result = sorted(result)[:5]
    return result

@app.route("/predict", methods=["POST"])
def predict():
    global records, hit_count, total_count, streak
    global last_prediction, last_hit, last_champion

    data = request.get_json()
    first, second, third = data.get("first"), data.get("second"), data.get("third")
    if not all(n in range(1, 11) for n in [first, second, third]):
        return jsonify({"error": "號碼需為 1–10 之間"}), 400

    new_entry = [first, second, third]
    records.append(new_entry)
    if len(records) > 10:
        records.pop(0)

    last_champion = first

    if first in last_prediction:
        last_hit = True
        if training_mode:
            hit_count += 1
            streak = 1
    else:
        last_hit = False
        if training_mode:
            streak += 1

    total_count += 1
    last_prediction = predict_next(records, last_champion)

    return jsonify({
        "prediction": last_prediction,
        "hit": last_hit,
        "lastChampion": last_champion,
        "hitCount": hit_count,
        "totalCount": total_count,
        "streak": streak
    })

@app.route("/toggle-training", methods=["POST"])
def toggle_training():
    global training_mode
    training_mode = not training_mode
    return jsonify({"training": training_mode})

@app.route("/reset", methods=["POST"])
def reset():
    global records, hit_count, total_count, streak, last_prediction, last_hit, last_champion
    records = []
    hit_count = 0
    total_count = 0
    streak = 1
    last_prediction = []
    last_hit = False
    last_champion = None
    return jsonify({"message": "重置完成"})

if __name__ == "__main__":
    app.run(debug=True)
