from flask import Flask, request, render_template_string
import random

app = Flask(__name__)

# 資料初始化
history = []
hit_count = 0
total_count = 0
current_stage = 1

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
  <button type="submit">預測</button>
</form>

{% if prediction %}
<div class="result">
  <p><strong>預測號碼：</strong> {{ prediction }}</p>
  <p><strong>冠軍號碼：</strong> {{ champion }}</p>
  <p><strong>是否命中：</strong> {{ '命中' if hit else '未命中' }}</p>
  <p><strong>階段：</strong> 第 {{ stage }} 關</p>
  <p><strong>命中統計：</strong> {{ hit_count }} / {{ total_count }}</p>
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
    global history, hit_count, total_count, current_stage

    prediction = None
    champion = None
    hit = False

    if request.method == "POST":
        try:
            nums = [int(request.form[f"num{i}"]) for i in range(1, 4)]
            if len(nums) == 3:
                history.append(nums)
                prediction = generate_prediction()
                champion = nums[0]
                hit = champion in prediction
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
        total_count=total_count
    )

if __name__ == "__main__":
    app.run(debug=True)
