""from flask import Flask, request, render_template_string
import random

app = Flask(__name__)

history = []
training_mode = False
hit_count = 0
total_count = 0
stage = 1

html = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>5碼預測器</title>
  <style>
    body {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      min-height: 100vh;
      font-family: sans-serif;
    }
    input[type='text'] {
      font-size: 1.5rem;
      margin: 5px;
      padding: 10px;
      width: 60px;
      text-align: center;
    }
    button {
      padding: 10px 20px;
      font-size: 1.2rem;
    }
    .result {
      margin-top: 20px;
      font-size: 1.3rem;
    }
  </style>
</head>
<body>
  <h2>5碼預測器</h2>
  <form method="POST">
    <input type="text" name="n1" required>
    <input type="text" name="n2" required>
    <input type="text" name="n3" required>
    <button type="submit">提交</button>
  </form>
  <form method="POST">
    <input type="hidden" name="toggle_train" value="1">
    <button type="submit">{{ '關閉訓練模式' if training else '啟用訓練模式' }}</button>
  </form>
  {% if show_result %}
  <div class="result">
    <p>冠軍號碼：{{ result.champion }}</p>
    <p>預測號碼：{{ result.prediction }}</p>
    <p>是否命中：{{ result.hit }}</p>
    {% if result.training %}
    <p>訓練命中率：{{ result.hit_count }}/{{ result.total_count }}</p>
    <p>目前階段：第{{ result.stage }}關</p>
    {% endif %}
  </div>
  {% else %}
    <div class="result">
      <p>已輸入 {{ history_len }} 組，滿 3 組後開始預測。</p>
    </div>
  {% endif %}
</body>
</html>
"""

def generate_prediction():
    recent = history[-3:]
    pool = list(range(1, 11))
    freq = {}
    for group in recent:
        for n in group:
            freq[n] = freq.get(n, 0) + 1

    hot = max(freq, key=freq.get)
    dynamic_hot = recent[-1][0]
    if dynamic_hot == hot:
        sorted_freq = sorted(freq.items(), key=lambda x: (-x[1], -recent[::-1].index([g for g in recent if x[0] in g][0])))
        for n, _ in sorted_freq:
            if n != hot:
                dynamic_hot = n
                break

    cold_candidates = [n for n in pool if n not in freq]
    cold = random.choice(cold_candidates) if cold_candidates else random.choice(pool)

    avoid = {hot, dynamic_hot, cold}
    remaining = [n for n in pool if n not in avoid]
    rands = random.sample(remaining, 2)

    return sorted([hot, dynamic_hot, cold] + rands)

@app.route("/", methods=["GET", "POST"])
def index():
    global history, hit_count, total_count, stage, training_mode
    result = None
    show_result = False

    if request.method == "POST":
        if 'toggle_train' in request.form:
            training_mode = not training_mode
        else:
            try:
                nums = [int(request.form.get(f"n{i}")) for i in range(1, 4)]
                if len(nums) == 3:
                    history.append(nums)
            except:
                return render_template_string(html, result=None, training=training_mode, show_result=False, history_len=len(history))

    if len(history) >= 3:
        prediction = generate_prediction()
        last_input = history[-1]
        champion = last_input[0]
        hit = champion in prediction

        if training_mode:
            total_count += 1
            if hit:
                hit_count += 1
                stage = 1
            else:
                stage += 1

        result = {
            "champion": champion,
            "prediction": prediction,
            "hit": "命中" if hit else "未命中",
            "training": training_mode,
            "hit_count": hit_count,
            "total_count": total_count,
            "stage": stage
        }
        show_result = True

    return render_template_string(html, result=result, training=training_mode, show_result=show_result, history_len=len(history))

if __name__ == "__main__":
    app.run(debug=True)
