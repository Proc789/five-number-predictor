from flask import Flask, render_template_string, request, redirect
import random
from collections import Counter

app = Flask(__name__)
history = []
predictions = []
training_enabled = False
training_data = {
    "hot_hits": 0,
    "dynamic_hits": 0,
    "extra_hits": 0,
    "all_hits": 0,
    "total": 0,
    "stage": 1
}

TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
  <title>5碼預測器（穩定版）</title>
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
      熱號命中：{{ hot_hits }} / {{ total }}<br>
      動熱命中：{{ dynamic_hits }} / {{ total }}<br>
      補碼命中：{{ extra_hits }} / {{ total }}<br>
      總命中：{{ all_hits }} / {{ total }}<br>
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
    global training_enabled
    prediction = None
    last_prediction = predictions[-1] if predictions else None
    stage = training_data["stage"]

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

                if training_enabled:
                    champion = current[0]
                    training_data["total"] += 1

                    if champion in prediction:
                        training_data["all_hits"] += 1
                        training_data["stage"] = 1
                    else:
                        training_data["stage"] += 1

                    hot, dynamic, extra = categorize_prediction()
                    if champion in hot:
                        training_data["hot_hits"] += 1
                    elif champion in dynamic:
                        training_data["dynamic_hits"] += 1
                    elif champion in extra:
                        training_data["extra_hits"] += 1

        except:
            prediction = ['格式錯誤']

    return render_template_string(TEMPLATE,
        prediction=prediction,
        last_prediction=last_prediction,
        stage=stage,
        history_data=history[-10:],
        training=training_enabled,
        hot_hits=training_data["hot_hits"],
        dynamic_hits=training_data["dynamic_hits"],
        extra_hits=training_data["extra_hits"],
        all_hits=training_data["all_hits"],
        total=training_data["total"])

@app.route('/toggle')
def toggle():
    global training_enabled
    training_enabled = not training_enabled
    training_data.update({"hot_hits": 0, "dynamic_hits": 0, "extra_hits": 0, "all_hits": 0, "total": 0, "stage": 1})
    return redirect('/')

def make_prediction():
    hot, dynamic, extra = categorize_prediction()
    return sorted(hot + dynamic + extra)

def categorize_prediction():
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

    return hot, dynamic, extra

if __name__ == '__main__':
    app.run(debug=True)
