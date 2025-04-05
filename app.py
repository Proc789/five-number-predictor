from flask import Flask, render_template_string, request, redirect
import random
from collections import Counter

app = Flask(__name__)
history = []
predictions = []
current_stage = 1
training = False
hot_hits = 0
dynamic_hits = 0
extra_hits = 0
all_hits = 0
total_tests = 0

TEMPLATE = """
<!DOCTYPE html>
<html>
  <head>
    <title>5碼預測器</title>
    <meta name='viewport' content='width=device-width, initial-scale=1'>
  </head>
  <body style="max-width: 400px; margin: auto; padding-top: 30px; font-family: sans-serif; text-align: center;">
    <h2>5碼預測器</h2>
    <div style='margin-bottom: 10px;'>版本：熱號2＋動熱2＋補碼1（公版UI）</div>
    <form method='POST'>
      <input name='first' placeholder='冠軍' required style='width: 80%; padding: 8px;' oninput="moveToNext(this, 'second')" inputmode="numeric"><br><br>
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
        冠軍命中次數（任一區）：{{ all_hits }} / {{ total_tests }}<br>
        熱號命中次數：{{ hot_hits }} / {{ total_tests }}<br>
        動熱命中次數：{{ dynamic_hits }} / {{ total_tests }}<br>
        補碼命中次數：{{ extra_hits }} / {{ total_tests }}<br>
      </div>
    {% endif %}

    <div style='margin-top: 20px; text-align: left;'>
      <strong>最近輸入紀錄：</strong>
      <ul>
        {% for row in history %}
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
    global current_stage, hot_hits, dynamic_hits, extra_hits, all_hits, total_tests, training
    prediction = None
    last_prediction = predictions[-1] if predictions else None

    if request.method == 'POST':
        try:
            first = int(request.form['first'])
            second = int(request.form['second'])
            third = int(request.form['third'])
            current = [10 if x == 0 else x for x in [first, second, third]]
            history.append(current)

            if len(predictions) >= 1:
                champion = current[0]
                if champion in last_prediction:
                    all_hits += 1
                    if training:
                        current_stage = 1
                else:
                    if training:
                        current_stage += 1
                if training:
                    total_tests += 1

                if champion in hot:
                    hot_hits += 1
                elif champion in dynamic:
                    dynamic_hits += 1
                elif champion in extra:
                    extra_hits += 1

            if len(history) >= 3:
                try:
                    hot, dynamic, extra, prediction = generate_prediction()
                    predictions.append(prediction)
                except Exception as e:
                    prediction = [f'格式錯誤']
        except:
            prediction = ['格式錯誤']

    return render_template_string(TEMPLATE,
        prediction=prediction,
        last_prediction=last_prediction,
        stage=current_stage,
        history=history[-10:],
        training=training,
        hot_hits=hot_hits,
        dynamic_hits=dynamic_hits,
        extra_hits=extra_hits,
        all_hits=all_hits,
        total_tests=total_tests)

@app.route('/toggle')
def toggle():
    global training, current_stage, hot_hits, dynamic_hits, extra_hits, all_hits, total_tests
    training = not training
    current_stage = 1
    hot_hits = dynamic_hits = extra_hits = all_hits = total_tests = 0
    return redirect('/')

@app.route('/reset')
def reset():
    global history, predictions, current_stage
    history = []
    predictions = []
    current_stage = 1
    return redirect('/')

def generate_prediction():
    recent = history[-3:]
    flat = [n for g in recent for n in g]
    freq = Counter(flat)

    hot_pool = [n for n, _ in freq.most_common(3)]
    hot = random.sample(hot_pool, k=min(2, len(hot_pool)))

    flat_dynamic = [n for n in flat if n not in hot]
    freq_dyn = Counter(flat_dynamic)
    dynamic_pool = [n for n, _ in freq_dyn.most_common(3)]
    dynamic = random.sample(dynamic_pool, k=min(2, len(dynamic_pool)))

    used = set(hot + dynamic)
    pool = [n for n in range(1, 11) if n not in used]
    if len(pool) < 1:
        raise ValueError("補碼數量不足")
    extra = random.sample(pool, 1)

    result = sorted(hot + dynamic + extra)
    return hot, dynamic, extra, result

if __name__ == '__main__':
    app.run(debug=True)
