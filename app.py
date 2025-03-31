""from flask import Flask, request, render_template_string
import random

app = Flask(__name__)

# 資料初始化
history = []
hit_count = 0
total_count = 0
current_stage = 1
training_mode = False

HTML_TEMPLATE = """
<!doctype html>
<title>5碼預測器</title>
<style>
  body { font-family: sans-serif; padding: 20px; max-width: 500px; margin: auto; }
  input { width: 60px; padding: 5px; margin: 5px; text-align: center; }
  button { padding: 10px 20px; margin-top: 10px; }
  .result { margin-top: 20px; padding: 10px; background: #f5f5f5; border-radius: 8px; }
</style>
<h2>輸入前三名號碼</h2>
<form method="post">
  <input name="num1" type="number" required>
  <input name="num2" type="number" required>
  <input name="num3" type="number" required>
  <button type="submit">送出</button>
</form>
<form method="post">
  <input type="hidden" name="toggle_training" value="1">
  <button type="submit">{{ '關閉訓練模式' if training else '啟動訓練模式' }}</button>
</form>

{% if len(history) >= 3 %}
<div class="result">
  <p><strong>預測號碼：</strong> {{ prediction }}</p>
  <p><strong>冠軍號碼：</strong> {{ champion }}</p>
  <p><strong>是否命中：</strong> {{ '命中' if hit else '未命中' }}</p>
  <p><strong>階段：</strong> 第 {{ stage }} 關</p>
  <p><strong>命中統計：</strong> {{ hit_count }} / {{ total_count }}</p>
</div>
{% else %}
<div class="result">
  <p>已輸入 {{ len(history) }} 組，需滿 3 組後開始預測。</p>
</div>
{% endif %}
"""

def generate_prediction():
    recent = history[-3:]
    flat = [n for group in recent for n in group]
    freq = {n: flat.count(n) for n in set(flat)}
    max_freq = max(freq.values()) if freq else 0
    hot_candidates = [n for n in freq if freq[n] == max_freq]
    hot = hot_candidates[-1] if hot_candidates else random.randint(1, 10)

    last_champion = history[-1][0] if history else hot
    dynamic_hot = last_champion if last_champion != hot else (hot_candidates[-2] if len(hot_candidates) > 1 else random.randint(1, 10))

    all_numbers = list(range(1, 11))
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
    global history, hit_count, total_count, current_stage, training_mode

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
                    if len(history) >= 3:
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
        history=history,
        training=training_mode
    )

if __name__ == "__main__":
    app.run(debug=True)
