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
stage = 1

TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
  <title>5碼預測器</title>
  <meta name='viewport' content='width=device-width, initial-scale=1'>
</head>
<body style='max-width: 400px; margin: auto; padding-top: 40px; font-family: sans-serif; text-align: center;'>
  <h2>5碼預測器</h2>
  <div style="margin-bottom: 10px;">版本：hotplus-v2-新版邏輯</div>

  <form method='POST'>
    <input name='first' id='first' placeholder='冠軍' required style='width: 80%; padding: 8px;' oninput="moveToNext(this, 'second')" inputmode="numeric"><br><br>
    <input name='second' id='second' placeholder='亞軍' required style='width: 80%; padding: 8px;' oninput="moveToNext(this, 'third')" inputmode="numeric"><br><br>
    <input name='third' id='third' placeholder='季軍' required style='width: 80%; padding: 8px;' inputmode="numeric"><br><br>
    <button type='submit' style='padding: 10px 20px;'>提交</button>
  </form>

  <br><a href='/toggle'><button>{{ '關閉統計模式' if training else '啟動統計模式' }}</button></a>

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

  {% if history_data %}
    <div style='margin-top: 20px; text-align: left;'>
      <strong>最近輸入紀錄：</strong>
      <ul>
        {% for row in history_data %}
          <li>第 {{ loop.index }} 期：{{ row }}</li>
        {% endfor %}
      </ul>
    </div>
  {% endif %}

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
    global training_enabled, hot_hits, dynamic_hits, extra_hits, all_hits, total_tests, stage
    prediction = None
    last_prediction = predictions[-1] if predictions else None

    if request.method == 'POST':
        try:
            first = int(request.form['first']) or 10
            second = int(request.form['second']) or 10
            third = int(request.form['third']) or 10
            current = [first, second, third]
            history.append(current)

            # 關數統計（從第6筆開始對照上期預測）
            if len(history) >= 6 or training_enabled:
                if predictions:
                    champion = current[0]
                    if champion in predictions[-1]:
                        all_hits += 1
                        stage = 1
                    else:
                        stage += 1

                    # 命中類型
                    last_set = predictions[-1]
                    if champion in hot_zone: hot_hits += 1
                    elif champion in dynamic_zone: dynamic_hits += 1
                    elif champion in extra_zone: extra_hits += 1
                total_tests += 1

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
    global training_enabled, hot_hits, dynamic_hits, extra_hits, all_hits, total_tests, stage
    training_enabled = not training_enabled
    hot_hits = dynamic_hits = extra_hits = all_hits = total_tests = 0
    stage = 1
    return redirect('/')

def make_prediction():
    global hot_zone, dynamic_zone, extra_zone
    recent = history[-3:]
    flat = [n for g in recent for n in g]
    freq = Counter(flat)

    # 熱號
    hot = [n for n, _ in freq.most_common(3)][:2]

    # 動熱
    dynamic_pool = [n for n in freq if n not in hot]
    dynamic_sorted = sorted(dynamic_pool, key=lambda x: (-freq[x], -flat[::-1].index(x)))
    dynamic = dynamic_sorted[:2]

    # 補碼排除
    exclude = set(hot + dynamic + dynamic_sorted)
    cold = {n for n in range(1, 11)} - set(flat)
    pool = [n for n in range(1, 11) if n not in exclude and n not in cold]
    random.shuffle(pool)
    extra = pool[:1]

    hot_zone = hot
    dynamic_zone = dynamic
    extra_zone = extra

    result = hot + dynamic + extra
    return sorted(result)

if __name__ == '__main__':
    app.run(debug=True)
