""from flask import Flask, request, render_template_string
import random

app = Flask(__name__)

history = []
training_mode = False
hit_count = 0
total_count = 0
stage = 1

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>5 號碼預測器</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {
            font-family: Arial, sans-serif;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            min-height: 100vh;
            margin: 0;
            background-color: #fff;
        }
        h1 {
            font-size: 28px;
            font-weight: bold;
            margin-bottom: 24px;
        }
        form {
            display: flex;
            flex-direction: column;
            gap: 16px;
            width: 90%;
            max-width: 400px;
        }
        input[type="text"] {
            font-size: 18px;
            padding: 14px;
            border: 1px solid #ccc;
            border-radius: 6px;
        }
        button {
            font-size: 16px;
            padding: 12px;
            border: none;
            border-radius: 6px;
            background-color: #007bff;
            color: white;
            cursor: pointer;
        }
        button:hover {
            background-color: #0056b3;
        }
        .toggle {
            margin-top: 10px;
            background-color: #e0e0e0;
            color: #333;
        }
        .record {
            margin-top: 30px;
            font-size: 18px;
            text-align: left;
            width: 90%;
            max-width: 400px;
        }
    </style>
</head>
<body>
    <h1>5 號碼預測器</h1>
    <form method="post">
        <input type="text" name="first" placeholder="冠軍號碼">
        <input type="text" name="second" placeholder="亞軍號碼">
        <input type="text" name="third" placeholder="季軍號碼">
        <button type="submit">提交</button>
        <button type="submit" name="toggle_train" class="toggle">{{ '關閉訓練模式' if training else '啟動訓練模式' }}</button>
    </form>

    <div class="record">
        <p><strong>最近輸入紀錄：</strong><br>{{ history_display }}</p>
        {% if prediction %}
            <p><strong>預測結果：</strong> {{ prediction }}</p>
            <p><strong>命中判定：</strong> {{ hit_text }}</p>
            <p><strong>訓練狀態：</strong> {{ hit_count }} / {{ total_count }}，目前為第 {{ stage }} 關</p>
        {% endif %}
    </div>
</body>
</html>
"""

def get_hot_numbers():
    flat = [n for group in history[-3:] for n in group]
    freq = {n: flat.count(n) for n in set(flat)}
    max_freq = max(freq.values(), default=0)
    hot_candidates = [n for n in freq if freq[n] == max_freq]
    recent = list(reversed(history[-3:]))
    for group in recent:
        for n in group:
            if n in hot_candidates:
                return n
    return random.randint(1, 10)

def get_dynamic_hot():
    return history[-1][0] if history else random.randint(1, 10)

def get_cold():
    flat = [n for group in history[-6:] for n in group]
    freq = {n: flat.count(n) for n in range(1, 11)}
    min_freq = min(freq.values())
    cold_candidates = [n for n in freq if freq[n] == min_freq]
    return random.choice(cold_candidates)

def generate_prediction():
    hot = get_hot_numbers()
    dynamic_hot = get_dynamic_hot()
    if dynamic_hot == hot:
        pool = [n for n in range(1, 11) if n != hot]
        dynamic_hot = random.choice(pool)
    cold = get_cold()
    pool = [n for n in range(1, 11) if n not in {hot, dynamic_hot, cold}]

    for _ in range(10):
        rands = random.sample(pool, 2)
        combined = [hot, dynamic_hot, cold] + rands
        if len(set(combined)) == 5:
            return sorted(combined)
    return sorted([hot, dynamic_hot, cold] + random.sample(pool, 2))

@app.route('/', methods=['GET', 'POST'])
def index():
    global training_mode, hit_count, total_count, stage
    prediction = None
    hit_text = None
    if request.method == 'POST':
        if 'toggle_train' in request.form:
            training_mode = not training_mode
        else:
            try:
                n1 = int(request.form['first'])
                n2 = int(request.form['second'])
                n3 = int(request.form['third'])
                new_data = [n1, n2, n3]
                history.append(new_data)

                if len(history) >= 3:
                    prediction = generate_prediction()
                    champion = new_data[0]
                    hit = champion in prediction
                    hit_text = "命中" if hit else "未命中"

                    if training_mode:
                        total_count += 1
                        if hit:
                            hit_count += 1
                            stage = 1
                        else:
                            stage += 1
            except:
                hit_text = "輸入錯誤，請輸入 1-10 的整數"

    return render_template_string(HTML_TEMPLATE,
        prediction=prediction,
        hit_text=hit_text,
        training=training_mode,
        hit_count=hit_count,
        total_count=total_count,
        stage=stage,
        history_display='<br>'.join([str(h) for h in history])
    )

if __name__ == '__main__':
    app.run(debug=True)
