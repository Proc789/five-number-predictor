from flask import Flask, render_template_string, request
import random
from collections import Counter

app = Flask(__name__)
history = []
predictions = []
last_random = []
source_logs = []
debug_logs = []

# 命中統計計數器
hot_hits = 0
dynamic_hits = 0
extra_hits = 0
all_hits = 0
total_tests = 0

TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
  <title>5碼預測器（hotplus v2）</title>
  <meta name='viewport' content='width=device-width, initial-scale=1'>
</head>
<body style='max-width: 400px; margin: auto; padding-top: 40px; font-family: sans-serif; text-align: center;'>
  <h2>5碼預測器（hotplus v2）</h2>
  <form method='POST'>
    <input name='first' id='first' placeholder='冠軍' required style='width: 80%; padding: 8px;' oninput="moveToNext(this, 'second')"><br><br>
    <input name='second' id='second' placeholder='亞軍' required style='width: 80%; padding: 8px;' oninput="moveToNext(this, 'third')"><br><br>
    <input name='third' id='third' placeholder='季軍' required style='width: 80%; padding: 8px;'><br><br>
    <button type='submit' style='padding: 10px 20px;'>提交</button>
  </form>

  {% if prediction %}
    <div style='margin-top: 20px;'>
      <strong>預測號碼：</strong> {{ prediction }}
    </div>
  {% endif %}

  <div style='margin-top: 20px; text-align: left;'>
    <strong>命中統計：</strong><br>
    冠軍命中次數（任一區）：{{ all_hits }} / {{ total_tests }}<br>
    熱號命中次數：{{ hot_hits }} / {{ total_tests }}<br>
    動熱命中次數：{{ dynamic_hits }} / {{ total_tests }}<br>
    補碼命中次數：{{ extra_hits }} / {{ total_tests }}<br>
  </div>

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

  {% if result_log %}
    <div style='margin-top: 20px; text-align: left;'>
      <strong>來源紀錄（冠軍號碼分類）：</strong>
      <ul>
        {% for row in result_log %}
          <li>第 {{ loop.index }} 期：{{ row }}</li>
        {% endfor %}
      </ul>
    </div>
  {% endif %}

  {% if debug_log %}
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
        if (current.value === '0') {
          current.value = '10';
        }
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
    global last_random, hot_hits, dynamic_hits, extra_hits, all_hits, total_tests
    prediction = None

    if request.method == 'POST':
        try:
            first = int(request.form['first']) or 10
            second = int(request.form['second']) or 10
            third = int(request.form['third']) or 10
            current = [first, second, third]
            history.append(current)

            if len(history) >= 4:
                recent = history[-4:-1]  # 最近三期

                # 熱號：上一期的前三名中取 2 碼
                last_set = history[-2]
                hot = list(dict.fromkeys(last_set))[:2]

                # 動熱池：最近三期出現次數最多（排除熱號），取前 4
                flat = [n for group in recent for n in group if n not in hot]
                count = Counter(flat)
                dynamic_pool = [n for n, _ in count.most_common(4)]
                dynamic_hot = random.sample(dynamic_pool, k=min(2, len(dynamic_pool)))

                # 補碼：1~10 扣除熱號與動熱後隨機選 1
                used = set(hot + dynamic_hot)
                others = [n for n in range(1, 11) if n not in used]
                random.shuffle(others)
                extra = others[0:1] if others else []

                result = sorted(hot + dynamic_hot + extra)
                prediction = result
                predictions.append(result)
                last_random = result

                # 分析命中來源
                champion = current[0]
                total_tests += 1
                hit = False

                if champion in hot:
                    source = f"冠軍號碼 {champion} → 熱號"
                    label = "熱號命中"
                    hot_hits += 1
                    hit = True
                elif champion in dynamic_hot:
                    source = f"冠軍號碼 {champion} → 動熱"
                    label = "動熱命中"
                    dynamic_hits += 1
                    hit = True
                elif champion in extra:
                    source = f"冠軍號碼 {champion} → 補碼"
                    label = "補碼命中"
                    extra_hits += 1
                    hit = True
                else:
                    source = f"冠軍號碼 {champion} → 其他"
                    label = "未命中"

                if hit:
                    all_hits += 1

                source_logs.append(source)

                # 除錯紀錄
                debug_logs.append(
                    f"熱號 = {hot} ｜動熱池 = {dynamic_pool} ｜實際動熱 = {dynamic_hot} ｜補碼 = {extra} ｜冠軍 = {champion}（{label}）"
                )

        except:
            prediction = ["格式錯誤"]

    return render_template_string(TEMPLATE,
        prediction=prediction,
        history_data=history[-10:],
        result_log=source_logs[-10:],
        debug_log=debug_logs[-10:],
        hot_hits=hot_hits,
        dynamic_hits=dynamic_hits,
        extra_hits=extra_hits,
        all_hits=all_hits,
        total_tests=total_tests)

if __name__ == '__main__':
    app.run(debug=True)
