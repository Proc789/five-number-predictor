from flask import Flask, render_template_string, request
import random

app = Flask(__name__)
history = []
predictions = []
last_random = []
source_logs = []

TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
  <title>5碼分析器（動熱池版本）</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
</head>
<body style="max-width: 400px; margin: auto; padding-top: 40px; font-family: sans-serif; text-align: center;">
  <h2>5碼預測器（動熱池版本）</h2>
  <form method="POST">
    <input name="first" placeholder="冠軍" required style="width: 80%; padding: 8px;"><br><br>
    <input name="second" placeholder="亞軍" required style="width: 80%; padding: 8px;"><br><br>
    <input name="third" placeholder="季軍" required style="width: 80%; padding: 8px;"><br><br>
    <button type="submit" style="padding: 10px 20px;">提交</button>
  </form>
  {% if prediction %}
    <div style="margin-top: 20px;">
      <strong>預測號碼：</strong> {{ prediction }}
    </div>
  {% endif %}
  {% if result_log %}
    <div style="margin-top: 30px; text-align: left;">
      <strong>來源紀錄（冠軍號碼分類）：</strong>
      <ul>
        {% for row in result_log %}
          <li>{{ row }}</li>
        {% endfor %}
      </ul>
    </div>
  {% endif %}
  <script>
    document.querySelectorAll('input').forEach(inp => {
      inp.addEventListener('input', () => {
        if (inp.value === '0') inp.value = '10';
      });
    });
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

            if len(history) >= 3:
                recent = history[-3:]
                flat = [n for group in recent for n in group]

                # 熱號：上一期冠軍
                hot = recent[-1][0]

                # 動熱池：最近 3 期中出現兩次以上，排除熱號
                freq = {n: flat.count(n) for n in set(flat)}
                dynamic_pool = [n for n, c in freq.items() if c >= 2 and n != hot]

                # 其他號碼 = 1~10 扣掉熱號與動熱池
                others = [n for n in range(1, 11) if n not in [hot] + dynamic_pool]

                # 從每個池中選號
                selected = [hot]
                if dynamic_pool:
                    selected.append(random.choice(dynamic_pool))
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

                # 判斷來源
                champion = current[0]
                if champion == hot:
                    source = f"冠軍號碼 {champion} → 熱號"
                elif champion in dynamic_pool:
                    source = f"冠軍號碼 {champion} → 動熱池"
                else:
                    source = f"冠軍號碼 {champion} → 其他"
                source_logs.append(source)

        except:
            prediction = ["格式錯誤"]

    return render_template_string(TEMPLATE,
        prediction=prediction,
        result_log=source_logs[-10:])

if __name__ == "__main__":
    app.run(debug=True)
