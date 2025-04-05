from flask import Flask, render_template_string, request, redirect
import random
from collections import Counter

app = Flask(__name__)
history = []
predictions = []
source_logs = []
debug_logs = []

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
  <title>5碼預測器</title>
  <meta name='viewport' content='width=device-width, initial-scale=1'>
</head>
<body style='max-width: 400px; margin: auto; padding-top: 40px; font-family: sans-serif; text-align: center;'>
  <h2>5碼預測器<br>版本：熱2 + 動2 + 補1（排除冷號）</h2>
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

  {% if training %}
    <div style='margin-top: 20px; text-align: left; font-size: 13px; color: #555;'>
      <strong>除錯紀錄（每期來源分析）：</strong>
      <ul>
        {% for row in debug_log %}
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
    global training_enabled, hot_hits, dynamic_hits, extra_hits
    global all_hits, total_tests, current_stage
    prediction = None
    last_prediction = predictions[-1] if predictions else None

    if request.method == 'POST':
        try:
            first = int(request.form['first']) or 10
            second = int(request.form['second']) or 10
            third = int(request.form['third']) or 10
            current = [first, second, third]
            history.append(current)

            if (len(history) >= 5) or training_enabled:
                prediction = make_prediction()
                predictions.append(prediction)

                if len(predictions) >= 2:
                    champion = current[0]
                    last_pred = predictions[-2]
                    if champion in last_pred:
                        all_hits += 1
                        current_stage = 1
                    else:
                        current_stage += 1

                    if training_enabled:
                        total_tests += 1
                        if champion in last_pred:
                            if champion in last_pred[:2]:
                                hot_hits += 1
                            elif champion in last_pred[2:4]:
                                dynamic_hits += 1
                            elif champion in last_pred[4:]:
                                extra_hits += 1

        except:
            prediction = ['格式錯誤']

    return render_template_string(TEMPLATE,
        prediction=prediction,
        last_prediction=last_prediction,
        stage=current_stage,
        history_data=history[-10:],
        debug_log=debug_logs[-10:],
        training=training_enabled,
        hot_hits=hot_hits,
        dynamic_hits=dynamic_hits,
        extra_hits=extra_hits,
        all_hits=all_hits,
        total_tests=total_tests)

@app.route('/toggle')
def toggle():
    global training_enabled, hot_hits, dynamic_hits, extra_hits
    global all_hits, total_tests, current_stage
    training_enabled = not training_enabled
    hot_hits = dynamic_hits = extra_hits = all_hits = total_tests = 0
    current_stage = 1
    return redirect('/')

def make_prediction():
    recent = history[-3:]
    flat = [n for g in recent for n in g]
    freq = Counter(flat)
    hot_pool = [n for n, _ in freq.most_common(3)]
    hot = random.sample(hot_pool, k=min(2, len(hot_pool)))

    flat_dyn = [n for n in flat if n not in hot]
    freq_dyn = Counter(flat_dyn)
    if freq_dyn:
        max_freq = max(freq_dyn.values())
        dynamic_pool = [n for n, c in freq_dyn.items() if c == max_freq]
    else:
        dynamic_pool = []
    dynamic_hot = random.sample(dynamic_pool, k=min(2, len(dynamic_pool)))

    cold = {n for n in range(1, 11)} - set(flat)
    exclude = set(hot + dynamic_hot + dynamic_pool + list(cold))
    pool = [n for n in range(1, 11) if n not in exclude]
    random.shuffle(pool)
    extra = pool[:1] if pool else []

    result = hot + dynamic_hot + extra
    if len(result) < 5:
        filler = [n for n in range(1, 11) if n not in result]
        random.shuffle(filler)
        result += filler[:5 - len(result)]

    debug_logs.append(
        f"熱號 = {hot} ｜動熱 = {dynamic_hot} ｜補碼 = {extra} ｜總組合 = {sorted(result)}"
    )
    return sorted(result)

if __name__ == '__main__':
    app.run(debug=True)
