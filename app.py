from flask import Flask, render_template_string, request
import random

app = Flask(__name__)
history = []
predictions = []
last_random = []
source_logs = []
debug_logs = []

TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
  <title>5碼分析器（動熱池 v4）</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
</head>
<body style="max-width: 400px; margin: auto; padding-top: 40px; font-family: sans-serif; text-align: center;">
  <h2>5碼預測器（動熱池 v4）</h2>
  <form method="POST">
    <input name="first" id="first" placeholder="冠軍" required style="width: 80%; padding: 8px;" oninput="moveToNext(this, 'second')"><br><br>
    <input name="second" id="second" placeholder="亞軍" required style="width: 80%; padding: 8px;" oninput="moveToNext(this, 'third')"><br><br>
    <input name="third" id="third" placeholder="季軍" required style="width: 80%; padding: 8px;"><br><br>
    <button type="submit" style="padding: 10px 20px;">提交</button>
  </form>

  {% if prediction %}
    <div style="margin-top: 20px;">
      <strong>預測號碼：</strong> {{ prediction }}
    </div>
  {% endif %}

  {% if history_data %}
    <div style="margin-top: 20px; text-align: left;">
      <strong>最近輸入紀錄：</strong>
      <ul>
        {% for row in history_data %}
          <li>第 {{ loop.index }} 期：{{ row }}</li>
        {% endfor %}
      </ul>
    </div>
  {% endif %}

  {% if result_log %}
    <div style="margin-top: 20px; text-align: left;">
      <strong>來源紀錄（冠軍號碼分類）：</strong>
      <ul>
        {% for row in result_log %}
          <li>第 {{ loop.index }} 期：{{ row }}</li>
        {% endfor %}
      </ul>
    </div>
  {% endif %}

  {% if debug_log %}
    <div style="margin-top: 20px; text-align: left; font-size: 13px; color: #555;">
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
      let val = parseInt(current.value);
      if (val === 0) current.value = 10;
      if (!isNaN(val) && val >= 1 && val <= 10) {
        setTimeout(() => {
          document.getElementById(nextId).focus();
        }, 150);
      }
    }
  </script>
</body>
</html>
"""

@app.route("/", methods=["GET", "POST"])
def index():
    global last_random
    prediction = None

    if request.method == "POST":
        try:
            first = int(request.form['first']) or 10
            second = int(request.form['second']) or 10
            third = int(request.form['third']) or 10
            current = [first, second, third]
            history.append(current)

            if len(history) >= 4:
                recent = history[-4:-1]  # 正確取最近三期（不包含當期）
                flat = [n for group in recent for n in group]

                hot = recent[-1][0]
                freq = {n: flat.count(n) for n in set(flat)}
                dynamic_pool = [n for n, c in freq.items() if c >= 2 and n != hot]
                others = [n for n in range(1, 11) if n not in [hot] + dynamic_pool]

                selected = [hot]
                dynamic_pick = random.choice(dynamic_pool) if dynamic_pool else None
                if dynamic_pick:
                    selected.append(dynamic_pick)
                if len(selected) < 5:
                    pool = [n for n in others if n not in selected]
                    random.shuffle(pool)
                    for n in pool:
                        if len(set(last_random) & set(selected + [n])) <= 2:
                            selected.append(n)
                        if len(selected) == 5:
                            break
                selected = sorted(selected)
                prediction = selected
                predictions.append(selected)
                last_random = selected

                champion = current[0]
                if champion == hot:
                    source = f"冠軍號碼 {champion} → 熱號"
                elif champion in dynamic_pool:
                    source = f"冠軍號碼 {champion} → 動熱池"
                else:
                    source = f"冠軍號碼 {champion} → 其他"
                source_logs.append(source)

                # 除錯紀錄加入
                debug_logs.append(
                    f"熱號={hot}｜動熱池={dynamic_pool}｜補碼={others}｜冠軍={champion}"
                )

        except:
            prediction = ["格式錯誤"]

    return render_template_string(TEMPLATE,
        prediction=prediction,
        history_data=history[-10:],
        result_log=source_logs[-10:],
        debug_log=debug_logs[-10:])

if __name__ == "__main__":
    app.run(debug=True)
