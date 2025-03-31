from flask import Flask, request, render_template_string
import random

app = Flask(__name__)

# 預設歷史資料與訓練統計
history = []
training_mode = False
hit_count = 0
total_count = 0
current_stage = 1

# HTML 介面（五碼輸入）
HTML_TEMPLATE = """
<!doctype html>
<title>5碼預測器</title>
<h2>輸入前三名號碼</h2>
<form method=post>
  冠軍：<input name=num1 size=1>
  亞軍：<input name=num2 size=1>
  季軍：<input name=num3 size=1>
  <input type=submit value=送出>
</form>
<form method=post>
  <input type=hidden name=toggle_training value=1>
  <button type=submit>{{ '關閉訓練模式' if training else '啟動訓練模式' }}</button>
</form>
{% if prediction %}
  <p><strong>預測號碼：</strong> {{ prediction }}</p>
  <p><strong>冠軍號碼：</strong> {{ champion }}</p>
  <p><strong>是否命中：</strong> {{ '命中' if hit else '未命中' }}</p>
  <p><strong>階段：</strong> 第 {{ stage }} 關</p>
  <p><strong>訓練統計：</strong> {{ hit_count }} / {{ total_count }}</p>
{% endif %}
"""

# 預測邏輯（5碼版本）
def generate_prediction():
    recent = history[-3:]
    flat = [n for group in recent for n in group]
    freq = {n: flat.count(n) for n in set(flat)}

    max_freq = max(freq.values()) if freq else 0
    hot_candidates = [n for n in freq if freq[n] == max_freq]
    hot = hot_candidates[-1] if hot_candidates else random.randint(1, 10)

    last_champion = history[-1][0] if history else hot
    dynamic_hot = last_champion if last_champion != hot else (hot_candidates[-2] if len(hot_candidates) > 1 else random.randint(1, 10))

    all_numbers = [n for n in range(1, 11)]
    count_map = {n: flat.count(n) for n in all_numbers}
    min_freq = min(count_map.values()) if count_map else 0
    cold_candidates = [n for n in count_map if count_map[n] == min_freq]
    cold = random.choice(cold_candidates)
    pool = [n for n in all_numbers if n not in [hot, dynamic_hot, cold]]

    prev_random = history[-1][-2:] if len(history) >= 1 else []

    for _ in range(10):
        rands = random.sample(pool, 2)
        if len(set(rands) & set(prev_random)) <= 1:
            return sorted([hot, dynamic_hot, cold] + rands)

    return sorted([hot, dynamic_hot, cold] + random.sample(pool, 2))

@app.route("/", methods=["GET", "POST"])
def index():
    global history, training_mode, hit_count, total_count, current_stage

    prediction = None
    champion = None
    hit = False

    if request.method == "POST":
        if "toggle_training" in request.form:
            training_mode = not training_mode
        else:
            try:
                nums = [int(request.form[f"num{i}"]) for i in range(1, 4)]
                if len(nums) == 3:
                    history.append(nums)
                    prediction = generate_prediction()
                    champion = nums[0]
                    hit = champion in prediction

                    if training_mode:
                        total_count += 1
                        if hit:
                            hit_count += 1
                            current_stage = 1
                        else:
                            current_stage += 1
            except:
                pass

    return render_template_string(HTML_TEMPLATE,
        prediction=prediction,
        champion=champion,
        hit=hit,
        stage=current_stage,
        hit_count=hit_count,
        total_count=total_count,
        training=training_mode
    )

if __name__ == "__main__":
    app.run(debug=True)
