from flask import Flask, render_template_string, request, redirect
import random
from collections import Counter

app = Flask(__name__)
history = []
predictions = []
training_enabled = False
stage = 1
training_stage = 1
hits = 0
total = 0

TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
  <title>5碼預測器</title>
  <meta name='viewport' content='width=device-width, initial-scale=1'>
</head>
<body style='max-width: 400px; margin: auto; padding-top: 40px; font-family: sans-serif; text-align: center;'>
  <h2>5碼預測器</h2>
  <div style="margin-bottom: 8px;">版本：hotplus-v2-新版邏輯</div>
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
    {% if last_prediction %}
    <div style='margin-top: 10px;'>
      <strong>上期預測號碼：</strong> {{ last_prediction }}
    </div>
    {% endif %}
  {% endif %}

  {% if training %}
    <div style='margin-top: 20px; text-align: left;'>
      <strong>命中統計：</strong><br>
      冠軍命中次數（任一區）：{{ hits }} / {{ total }}
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
    global training_enabled, stage, training_stage, hits, total
    prediction = None
    last_prediction = predictions[-1] if predictions else None

    if request.method == 'POST':
        try:
            first = int(request.form['first']) or 10
            second = int(request.form['second']) or 10
            third = int(request.form['third']) or 10
            current = [first, second, third]
            history.append(current)

            if len(history) >= 5 or training_enabled:
                prediction = make_prediction()
                predictions.append(prediction)

                # 判定命中與關卡計算
                if len(predictions) >= 2:
                    champion = current[0]
                    prev = predictions[-2]
                    if champion in prev:
                        if training_enabled:
                            training_stage = 1
                            hits += 1
                        stage = 1
                    else:
                        if training_enabled:
                            training_stage += 1
                        stage += 1
                    if training_enabled:
                        total += 1
        except:
            prediction = ['格式錯誤']

    return render_template_string(TEMPLATE,
        prediction=prediction,
        last_prediction=last_prediction,
        stage=training_stage if training_enabled else stage,
        history_data=history[-10:],
        training=training_enabled,
        hits=hits,
        total=total)

@app.route('/toggle')
def toggle():
    global training_enabled, training_stage, hits, total
    training_enabled = not training_enabled
    training_stage = 1
    hits = 0
    total = 0
    return redirect('/')

def make_prediction():
    recent = history[-3:]
    flat = [n for group in recent for n in group]
    freq = Counter(flat)

    hot = [n for n, _ in freq.most_common(3)][:2]
    dynamic_pool = [n for n in freq if n not in hot]
    dynamic_sorted = sorted(dynamic_pool, key=lambda x: (-freq[x], -flat[::-1].index(x)))
    dynamic = dynamic_sorted[:2]

    cold = {n for n in range(1, 11)} - set(flat)
    exclude = set(hot + dynamic + dynamic_sorted)
    pool = [n for n in range(1, 11) if n not in exclude and n not in cold]
    random.shuffle(pool)
    extra = pool[:1]

    result = hot + dynamic + extra
    if len(result) < 5:
        filler_pool = [n for n in range(1, 11) if n not in result]
        random.shuffle(filler_pool)
        result += filler_pool[:(5 - len(result))]

    return sorted(result)

if __name__ == '__main__':
    app.run(debug=True)
