from flask import Flask, render_template_string, request, redirect
import random
from collections import Counter

app = Flask(__name__)
history = []
predictions = []
training_enabled = False

hot_hits = 0
dynamic_hits = 0
extra_hits = 0
all_hits = 0
total_tests = 0
current_stage = 1

TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
  <title>5碼預測器（熱2+動2+補1）</title>
  <meta name='viewport' content='width=device-width, initial-scale=1'>
</head>
<body style='max-width: 400px; margin: auto; padding-top: 40px; font-family: sans-serif; text-align: center;'>
  <h2>5碼預測器（熱2+動2+補1）</h2>
  <form method='POST'>
    <input name='first' id='first' placeholder='冠軍' required style='width: 80%; padding: 8px;' oninput="moveToNext(this, 'second')" inputmode="numeric"><br><br>
    <input name='second' id='second' placeholder='亞軍' required style='width: 80%; padding: 8px;' oninput="moveToNext(this, 'third')" inputmode="numeric"><br><br>
    <input name='third' id='third' placeholder='季軍' required style='width: 80%; padding: 8px;' inputmode="numeric"><br><br>
    <button type='submit' style='padding: 10px 20px;'>提交</button>
  </form>
  <br>
  <a href='/toggle'><button>{{ '關閉統計模式' if training else '啟動統計模式' }}</button></a>

  {% if prediction %}
    <div style='margin-top: 20px;'>
      <strong>本期預測號碼：</strong> {{ prediction }}（目前第 {{ stage }} 關）
    </div>
  {% endif %}
  {% if last_prediction %}
    <div style='margin-top: 10px;'>
      <strong>上期預測號碼：</strong> {{ last_prediction }}
    </div>
  {% endif %}

  {% if training %}
  <div style='margin-top: 20px; text-align: left;'>
    <strong>命中統計：</strong><br>
    冠軍命中次數（任一區）：{{ all_hits }} / {{ total_tests }}<br>
    熱號命中次數：{{ hot_hits }} / {{ total_tests }}<br>
    動熱命中次數：{{ dynamic_hits }} / {{ total_tests }}<br>
    補碼命中次數：{{ extra_hits }} / {{ total_tests }}<br>
  </div>
  {% endif %}

  <div style='margin-top: 20px; text-align: left;'>
    <strong>最近輸入紀錄：</strong>
    <ul>
      {% for row in history_data %}
        <li>第 {{ loop.index }} 期：{{ row }}</li>
      {% endfor %}
    </ul>
  </div>

  <script>
    function moveToNext(current, nextId) {
      setTimeout(() => {
        if (current.value === '0') current.value = '10';
        let val = parseInt(current.value);
        if (!isNaN(val) && val >= 1 && val <= 10) {
          document.getElementById(nextId).focus();
        }
      }, 100);
    }
  </script>
</body>
</html>
"""

@app.route('/', methods=['GET', 'POST'])
def index():
    global training_enabled, hot_hits, dynamic_hits, extra_hits, all_hits, total_tests, current_stage

    prediction = None
    last_prediction = predictions[-1] if predictions else None
    stage = current_stage

    if request.method == 'POST':
        try:
            first = int(request.form['first']) or 10
            second = int(request.form['second']) or 10
            third = int(request.form['third']) or 10
            current = [first, second, third]
            history.append(current)

            # 更新關數（不論訓練模式與否）
            if last_prediction and len(predictions) > 0:
                if current[0] in last_prediction:
                    current_stage = 1
                else:
                    current_stage += 1
                stage = current_stage

            # 統計模式下進行命中統計
            if training_enabled and last_prediction:
                total_tests += 1
                if current[0] in last_prediction:
                    all_hits += 1
                if current[0] in hot:
                    hot_hits += 1
                elif current[0] in dynamic:
                    dynamic_hits += 1
                elif current[0] in extra:
                    extra_hits += 1

            # 開始預測（需輸入至少 5 組 或 開啟訓練模式）
            if len(history) >= 5 or training_enabled:
                prediction = make_prediction()
                predictions.append(prediction)
        except:
            prediction = ['格式錯誤']

    return render_template_string(TEMPLATE,
        prediction=prediction,
        last_prediction=last_prediction,
        stage=stage,
        history_data=history[-10:],
        training=training_enabled,
        hot_hits=hot_hits,
        dynamic_hits=dynamic_hits,
        extra_hits=extra_hits,
        all_hits=all_hits,
        total_tests=total_tests)

@app.route('/toggle')
def toggle():
    global training_enabled, hot_hits, dynamic_hits, extra_hits, all_hits, total_tests, current_stage
    training_enabled = not training_enabled
    hot_hits = dynamic_hits = extra_hits = all_hits = total_tests = 0
    current_stage = 1
    return redirect('/')

def make_prediction():
    global hot, dynamic, extra
    recent = history[-3:]
    flat = [n for g in recent for n in g]
    freq = Counter(flat)

    # 熱號：取出現次數最多的前3碼，選2
    hot_pool = [n for n, _ in freq.most_common(3)]
    hot = random.sample(hot_pool, k=min(2, len(hot_pool)))

    # 動態熱號：排除熱號後統計頻率，選最多的前3中隨機選2
    flat_dyn = [n for n in flat if n not in hot]
    dyn_freq = Counter(flat_dyn)
    dyn_pool = [n for n, _ in dyn_freq.most_common(3)]
    dynamic = random.sample(dyn_pool, k=min(2, len(dyn_pool)))

    # 補碼：排除熱號、動熱與整個動熱池，再排除冷號（3期未出現）
    exclude = set(hot + dynamic + dyn_pool)
    recent_nums = set(flat)
    cold = {n for n in range(1, 11)} - recent_nums
    pool = [n for n in range(1, 11) if n not in exclude and n not in cold]
    random.shuffle(pool)
    extra = pool[:1]

    result = hot + dynamic + extra
    # 強制補足到5碼
    if len(result) < 5:
        filler_pool = [n for n in range(1, 11) if n not in result]
        random.shuffle(filler_pool)
        result += filler_pool[:(5 - len(result))]

    return sorted(result)

if __name__ == '__main__':
    app.run(debug=True)
