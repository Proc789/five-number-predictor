from flask import Flask, render_template_string, request, redirect
import random
from collections import Counter

app = Flask(__name__)
history = []
predictions = []
hot_hits = 0
dynamic_hits = 0
extra_hits = 0
all_hits = 0
total_tests = 0
current_stage = 1
tracking_enabled = False

TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
  <title>5碼預測器（hotplus v2）</title>
  <meta name='viewport' content='width=device-width, initial-scale=1'>
</head>
<body style='max-width: 400px; margin: auto; padding-top: 40px; font-family: sans-serif; text-align: center;'>
  <h2>5碼預測器（熱2+動2+補1）</h2>
  <form method='POST'>
    <input name='first' id='first' placeholder='冠軍號碼' required style='width: 80%; padding: 8px;' oninput="moveToNext(this, 'second')" inputmode="numeric"><br><br>
    <input name='second' id='second' placeholder='亞軍號碼' required style='width: 80%; padding: 8px;' oninput="moveToNext(this, 'third')" inputmode="numeric"><br><br>
    <input name='third' id='third' placeholder='季軍號碼' required style='width: 80%; padding: 8px;' inputmode="numeric"><br><br>
    <button type='submit' style='padding: 10px 20px;'>提交</button>
  </form>
  <br>
  <a href='/start'><button>啟動統計模式</button></a>

  {% if prediction %}
    <div style='margin-top: 20px;'>
      <strong>本期預測號碼：</strong> {{ prediction }}（目前第 {{ stage }} 關）
    </div>
  {% endif %}
  {% if last_prediction %}
    <div><strong>上期預測號碼：</strong> {{ last_prediction }}</div>
  {% endif %}
  {% if last_champion is not none %}
    <div><strong>上期冠軍號碼：</strong> {{ last_champion }}</div>
    <div><strong>是否命中：</strong> {{ hit }}</div>
  {% endif %}
  {% if tracking %}
  <div style='margin-top: 20px; text-align: left;'>
    <strong>命中統計：</strong><br>
    冠軍命中次數（任一區）：{{ all_hits }} / {{ total }}<br>
    熱號命中次數：{{ hot_hits }} / {{ total }}<br>
    動熱命中次數：{{ dynamic_hits }} / {{ total }}<br>
    補碼命中次數：{{ extra_hits }} / {{ total }}<br>
  </div>
  {% endif %}
  <div style='margin-top: 20px; text-align: left;'>
    <strong>最近輸入紀錄：</strong>
    <ul>
      {% for row in history_data %}
        <li>{{ row }}</li>
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
    global hot_hits, dynamic_hits, extra_hits, all_hits, total_tests, current_stage, tracking_enabled
    prediction = None
    last_prediction = predictions[-1] if predictions else None
    last_champion = None
    hit = None

    if request.method == 'POST':
        try:
            current = [int(request.form[x]) or 10 for x in ('first', 'second', 'third')]
            history.append(current)

            if len(predictions) >= 1:
                last_prediction = predictions[-1]
                last_champion = current[0]
                if last_champion in last_prediction:
                    hit = "命中"
                    if tracking_enabled:
                        all_hits += 1
                        current_stage = 1
                else:
                    hit = "未命中"
                    if tracking_enabled:
                        current_stage += 1
                if tracking_enabled:
                    total_tests += 1

            if len(history) >= 5 or tracking_enabled:
                prediction = generate_prediction()
                predictions.append(prediction)

        except:
            prediction = ["格式錯誤"]

    return render_template_string(TEMPLATE,
        prediction=prediction,
        last_prediction=last_prediction,
        last_champion=last_champion,
        hit=hit,
        stage=current_stage,
        history_data=history[-10:],
        hot_hits=hot_hits,
        dynamic_hits=dynamic_hits,
        extra_hits=extra_hits,
        all_hits=all_hits,
        total=total_tests,
        tracking=tracking_enabled)

@app.route('/start')
def start_tracking():
    global tracking_enabled
    tracking_enabled = True
    return redirect('/')

def generate_prediction():
    recent = history[-3:]
    flat = [n for group in recent for n in group]

    # 熱號：從最近第2期選出最多的2碼
    hot_pool = history[-2] if len(history) >= 2 else []
    hot = random.sample(hot_pool, 2) if len(hot_pool) >= 2 else hot_pool

    # 動熱：從 recent 排除熱號後統計出現次數最多
    filtered = [n for n in flat if n not in hot]
    freq = Counter(filtered)
    dynamic_pool = [n for n, c in freq.items() if c == max(freq.values())] if freq else []
    dynamic_hot = random.sample(dynamic_pool, min(2, len(dynamic_pool)))

    # 補碼：排除熱號、動熱與動熱池與冷號
    exclude = set(hot + dynamic_hot + dynamic_pool)
    appeared = set(flat)
    cold = [n for n in range(1, 11) if n not in appeared]
    pool = [n for n in range(1, 11) if n not in exclude and n not in cold]
    extra = random.sample(pool, 1) if len(pool) >= 1 else []

    result = hot + dynamic_hot + extra
    # 強制補足 5 碼
    if len(result) < 5:
        filler = [n for n in range(1, 11) if n not in result]
        random.shuffle(filler)
        result += filler[:(5 - len(result))]

    return sorted(result)

if __name__ == '__main__':
    app.run(debug=True)
