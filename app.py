from flask import Flask, render_template_string, request, redirect
import random
from collections import Counter

app = Flask(__name__)
history = []
predictions = []
hit_stats = {"hot": 0, "dynamic": 0, "extra": 0, "total": 0, "all": 0}
current_stage = 1
training_mode = False

TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
  <title>5碼預測器</title>
  <meta name='viewport' content='width=device-width, initial-scale=1'>
</head>
<body style='max-width: 400px; margin: auto; padding-top: 30px; font-family: sans-serif; text-align: center;'>
  <h2>5碼預測器</h2>
  <div>版本：熱號2＋動熱2＋補碼1（公版UI）</div>
  <form method='POST'>
    <input name='first' id='first' placeholder='冠軍' required style='width: 80%; padding: 8px;' oninput="moveToNext(this, 'second')" inputmode="numeric"><br><br>
    <input name='second' id='second' placeholder='亞軍' required style='width: 80%; padding: 8px;' oninput="moveToNext(this, 'third')" inputmode="numeric"><br><br>
    <input name='third' id='third' placeholder='季軍' required style='width: 80%; padding: 8px;' inputmode="numeric"><br><br>
    <button type='submit' style='padding: 10px 20px;'>提交</button>
  </form>
  <br>
  <a href='/toggle'><button>{{ '關閉統計模式' if training else '啟動統計模式' }}</button></a>
  <a href='/reset'><button>清除資料</button></a>

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
      冠軍命中次數（任一區）：{{ hit_stats.all }} / {{ hit_stats.total }}<br>
      熱號命中次數：{{ hit_stats.hot }} / {{ hit_stats.total }}<br>
      動熱命中次數：{{ hit_stats.dynamic }} / {{ hit_stats.total }}<br>
      補碼命中次數：{{ hit_stats.extra }} / {{ hit_stats.total }}<br>
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
    global current_stage
    prediction = None
    last_prediction = predictions[-1] if predictions else None

    if request.method == 'POST':
        try:
            first = int(request.form['first']) or 10
            second = int(request.form['second']) or 10
            third = int(request.form['third']) or 10
            current = [first, second, third]
            history.append(current)

            if len(history) >= 3:
                prediction = generate_prediction()
                predictions.append(prediction)

                if training_mode:
                    champion = current[0]
                    hit_stats['total'] += 1
                    if champion in last_prediction:
                        hit_stats['all'] += 1
                        current_stage = 1
                    else:
                        current_stage += 1
                    if champion in prediction[:2]:
                        hit_stats['hot'] += 1
                    elif champion in prediction[2:4]:
                        hit_stats['dynamic'] += 1
                    elif champion in prediction[4:]:
                        hit_stats['extra'] += 1
            else:
                prediction = ['請輸入至少三期']

        except:
            prediction = ['格式錯誤']

    return render_template_string(TEMPLATE,
        prediction=prediction,
        last_prediction=last_prediction,
        stage=current_stage,
        history_data=history[-10:],
        hit_stats=hit_stats,
        training=training_mode)

@app.route('/toggle')
def toggle():
    global training_mode, hit_stats, current_stage
    training_mode = not training_mode
    hit_stats = {"hot": 0, "dynamic": 0, "extra": 0, "total": 0, "all": 0}
    current_stage = 1
    return redirect('/')

@app.route('/reset')
def reset():
    global history, predictions, hit_stats, current_stage
    history = []
    predictions = []
    hit_stats = {"hot": 0, "dynamic": 0, "extra": 0, "total": 0, "all": 0}
    current_stage = 1
    return redirect('/')

def generate_prediction():
    recent = history[-3:]
    flat = [n for g in recent for n in g]
    freq = Counter(flat)

    hot_pool = [n for n, _ in freq.most_common()]
    hot = hot_pool[:2] if len(hot_pool) >= 2 else hot_pool

    dynamic_pool = [n for n in freq if n not in hot]
    dynamic_sorted = sorted(dynamic_pool, key=lambda x: (-freq[x], -flat[::-1].index(x)))
    dynamic = dynamic_sorted[:2] if len(dynamic_sorted) >= 2 else dynamic_sorted

    used = set(hot + dynamic)
    pool = [n for n in range(1, 11) if n not in used]
    random.shuffle(pool)
    extra = pool[:1] if len(pool) >= 1 else []

    result = hot + dynamic + extra
    filler_pool = [n for n in range(1, 11) if n not in result]
    random.shuffle(filler_pool)
    result += filler_pool[:(5 - len(result))]

    return sorted(result)

if __name__ == '__main__':
    app.run(debug=True)
