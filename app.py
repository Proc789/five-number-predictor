from flask import Flask, render_template_string, request
import random
from collections import Counter

app = Flask(__name__)
history = []
predictions = []
source_logs = []
debug_logs = []

hot_hits = 0
dynamic_hits = 0
extra_hits = 0
all_hits = 0
total_tests = 0
current_stage = 1
started = False

TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
  <title>5碼預測器（公版UI + 開始統計機制）</title>
  <meta name='viewport' content='width=device-width, initial-scale=1'>
</head>
<body style='max-width: 400px; margin: auto; padding-top: 40px; font-family: sans-serif; text-align: center;'>
  <h2>5碼預測器（公版UI + 開始統計機制）</h2>
  <form method='POST'>
    <input name='first' id='first' placeholder='冠軍' required style='width: 80%; padding: 8px;' oninput="moveToNext(this, 'second')" inputmode="numeric"><br><br>
    <input name='second' id='second' placeholder='亞軍' required style='width: 80%; padding: 8px;' oninput="moveToNext(this, 'third')" inputmode="numeric"><br><br>
    <input name='third' id='third' placeholder='季軍' required style='width: 80%; padding: 8px;' inputmode="numeric"><br><br>
    <button type='submit' style='padding: 10px 20px;'>提交</button>
  </form>
  <br>
  <a href='/toggle'><button>{{ toggle_text }}</button></a>
  <a href='/start'><button>開始統計</button></a>

  {% if not started %}
    <div style='margin-top: 20px;'>請先輸入至少 5 組資料並點擊「開始統計」</div>
  {% endif %}

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

  <div style='margin-top: 20px; text-align: left;'>
    <strong>命中統計：</strong><br>
    冠軍命中次數（任一區）：{{ all_hits }} / {{ total_tests }}<br>
    熱號命中次數：{{ hot_hits }} / {{ total_tests }}<br>
    動熱命中次數：{{ dynamic_hits }} / {{ total_tests }}<br>
    補碼命中次數：{{ extra_hits }} / {{ total_tests }}<br>
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
    global hot_hits, dynamic_hits, extra_hits, all_hits, total_tests, current_stage, started
    prediction = None
    last_prediction = predictions[-1] if predictions else None

    if request.method == 'POST':
        try:
            first = int(request.form['first']) or 10
            second = int(request.form['second']) or 10
            third = int(request.form['third']) or 10
            current = [first, second, third]
            history.append(current)

            if not started or len(history) < 5:
                return render_template_string(TEMPLATE,
                    prediction=None,
                    last_prediction=None,
                    stage=current_stage,
                    started=started,
                    history_data=history[-10:],
                    result_log=source_logs[-10:],
                    debug_log=debug_logs[-10:],
                    hot_hits=hot_hits,
                    dynamic_hits=dynamic_hits,
                    extra_hits=extra_hits,
                    all_hits=all_hits,
                    total_tests=total_tests,
                    toggle_text="關閉訓練模式" if training else "啟動訓練模式")

            last_set = history[-2]
            hot = random.sample(last_set, k=2) if len(last_set) >= 2 else last_set

            recent = history[-3:]
            flat = [n for g in recent for n in g if n not in hot]
            freq = Counter(flat)
            dynamic_pool = [n for n, c in freq.items() if c == max(freq.values())] if freq else []
            dynamic_hot = [random.choice(dynamic_pool)] if dynamic_pool else []

            exclude = set(hot + dynamic_hot + dynamic_pool)
            cold = {n for n in range(1, 11)} - {n for g in history[-3:] for n in g}
            pool = [n for n in range(1, 11) if n not in exclude and n not in cold]
            random.shuffle(pool)
            extra = pool[:1]

            result = hot + dynamic_hot + extra
            if len(result) < 5:
                filler_pool = [n for n in range(1, 11) if n not in result]
                random.shuffle(filler_pool)
                result += filler_pool[:(5 - len(result))]

            prediction = sorted(result)
            predictions.append(prediction)

            champion = current[0]
            total_tests += 1

            if last_prediction and champion in last_prediction:
                all_hits += 1
                current_stage = 1
            else:
                current_stage += 1

            if champion in hot:
                hot_hits += 1
            elif champion in dynamic_hot:
                dynamic_hits += 1
            elif champion in extra:
                extra_hits += 1

        except:
            prediction = ["格式錯誤"]

    return render_template_string(TEMPLATE,
        prediction=prediction,
        last_prediction=last_prediction,
        stage=current_stage,
        started=started,
        history_data=history[-10:],
        result_log=source_logs[-10:],
        debug_log=debug_logs[-10:],
        hot_hits=hot_hits,
        dynamic_hits=dynamic_hits,
        extra_hits=extra_hits,
        all_hits=all_hits,
        total_tests=total_tests,
        toggle_text="關閉訓練模式" if training else "啟動訓練模式")

@app.route('/toggle')
def toggle():
    global training, hits, total, stage
    training = not training
    if training:
        hits = 0
        total = 0
        stage = 1
    return "<script>window.location.href='/'</script>"

@app.route('/start')
def start():
    global started
    started = True
    return "<script>window.location.href='/'</script>"

if __name__ == '__main__':
    app.run(debug=True)
