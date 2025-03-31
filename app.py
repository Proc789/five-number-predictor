from flask import Flask, request, render_template_string
import random

app = Flask(__name__)

history = []
training_mode = False
hit_count = 0
total_count = 0
stage = 1

TEMPLATE = '''
<!doctype html>
<title>5-Number Predictor</title>
<h2>5-Number Predictor</h2>
<form method=post>
  <label>前三名號碼 (每組輸入1個數字):</label><br>
  <input name=n1 required type=number min=1 max=10>
  <input name=n2 required type=number min=1 max=10>
  <input name=n3 required type=number min=1 max=10><br><br>
  <button type=submit>送出並預測</button>
</form>

<form method=post action="/toggle">
  <button type=submit>{{ '關閉訓練模式' if training else '啟用訓練模式' }}</button>
</form>

{% if prediction %}
  <h3>預測結果：{{ prediction }}</h3>
  <p>冠軍號碼：{{ first }}</p>
  <p>是否命中：{{ '命中' if hit else '未命中' }}</p>
  <p>命中率：{{ hit_count }}/{{ total_count }}</p>
  <p>目前階段：第{{ stage }}關</p>
{% endif %}
'''

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
    first = None
    hit = None
    if request.method == 'POST':
        try:
            n1 = int(request.form['n1'])
            n2 = int(request.form['n2'])
            n3 = int(request.form['n3'])
        except:
            return render_template_string(TEMPLATE, prediction="輸入錯誤", training=training_mode)

        new_data = [n1, n2, n3]
        history.append(new_data)

        if len(history) >= 3:
            prediction = generate_prediction()
            first = new_data[0]
            hit = first in prediction

            if training_mode:
                total_count += 1
                if hit:
                    hit_count += 1
                    stage = 1
                else:
                    stage += 1

    return render_template_string(TEMPLATE,
                                  prediction=prediction,
                                  first=first,
                                  hit=hit,
                                  training=training_mode,
                                  hit_count=hit_count,
                                  total_count=total_count,
                                  stage=stage)

@app.route('/toggle', methods=['POST'])
def toggle_training():
    global training_mode
    training_mode = not training_mode
    return index()

if __name__ == '__main__':
    app.run(debug=True)
