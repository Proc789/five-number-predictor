from flask import Flask, render_template_string, request
import random

app = Flask(__name__)
history = []
predictions = []
hits = 0
total = 0
stage = 1
training = False

TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
  <title>6碼預測器</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
</head>
<body style="max-width: 400px; margin: auto; padding-top: 50px; text-align: center; font-family: sans-serif;">
  <h2>6碼預測器</h2>
  <form method="POST">
    <input type="number" name="first" placeholder="第1名號碼" required style="width: 80%; padding: 8px;"><br><br>
    <input type="number" name="second" placeholder="第2名號碼" required style="width: 80%; padding: 8px;"><br><br>
    <input type="number" name="third" placeholder="第3名號碼" required style="width: 80%; padding: 8px;"><br><br>
    <input type="number" name="eighth" placeholder="第8名號碼" required style="width: 80%; padding: 8px;"><br><br>
    <input type="number" name="ninth" placeholder="第9名號碼" required style="width: 80%; padding: 8px;"><br><br>
    <input type="number" name="tenth" placeholder="第10名號碼" required style="width: 80%; padding: 8px;"><br><br>
    <button type="submit" style="padding: 10px 20px;">提交</button>
  </form>
  <br>
  <a href="/toggle"><button>{{ toggle_text }}</button></a>
  {% if training %}
    <div><strong>訓練中...</strong></div>
    <div>命中率：{{ stats }}</div>
    <div>目前階段：第 {{ stage }} 關</div>
  {% endif %}
  {% if last_champion %}
    <br><div><strong>上期冠軍號碼：</strong>{{ last_champion }}</div>
    <div><strong>是否命中：</strong>{{ hit }}</div>
    <div><strong>上期預測號碼：</strong>{{ last_prediction }}</div>
  {% endif %}
  {% if result %}
    <br><div><strong>下期預測號碼：</strong>{{ result }}</div>
  {% endif %}
  <br>
  <div style="text-align: left;">
    <strong>最近輸入紀錄：</strong>
    <ul>
      {% for row in history %}
        <li>{{ row }}</li>
      {% endfor %}
    </ul>
  </div>
</body>
</html>
"""

@app.route("/", methods=["GET", "POST"])
def index():
    global hits, total, stage, training
    result = None
    last_champion = None
    last_prediction = None
    hit = None

    if request.method == "POST":
        try:
            first = int(request.form.get("first"))
            second = int(request.form.get("second"))
            third = int(request.form.get("third"))
            eighth = int(request.form.get("eighth"))
            ninth = int(request.form.get("ninth"))
            tenth = int(request.form.get("tenth"))
            current = [first, second, third, eighth, ninth, tenth]
            history.append(current)

            if len(predictions) >= 1:
                last_prediction = predictions[-1]
                last_champion = current[0]
                if last_champion in last_prediction:
                    hit = "命中"
                    if training:
                        hits += 1
                        stage = 1
                else:
                    hit = "未命中"
                    if training:
                        stage += 1

                if training:
                    total += 1

            if len(history) >= 3:
                prediction = generate_prediction()
                predictions.append(prediction)
                result = prediction
            else:
                result = "請至少輸入三期資料後才可預測"

        except:
            result = "格式錯誤，請輸入 1~10 的整數"

    toggle_text = "關閉訓練模式" if training else "啟動訓練模式"
    return render_template_string(TEMPLATE, result=result, history=history[-5:],
                                  last_champion=last_champion, last_prediction=last_prediction,
                                  hit=hit, training=training, toggle_text=toggle_text,
                                  stats=f"{hits} / {total}" if training else None,
                                  stage=stage if training else None)

@app.route("/toggle")
def toggle():
    global training, hits, total, stage
    training = not training
    if training:
        hits = 0
        total = 0
        stage = 1
    return "<script>window.location.href='/'</script>"

def generate_prediction():
    # 取得最近一期輸入的 6 個號碼（第1,2,3,8,9,10名）
    last = history[-1]  # [first, second, third, eighth, ninth, tenth]

    champion = last[0]
    result = [champion]

    # 延伸選號來源（第2、3、8、9名）
    candidate_pool = [last[1], last[2], last[3], last[4]]

    # 第10名納入機率：30%
    if random.random() < 0.3:
        if last[5] != champion:
            candidate_pool.append(last[5])

    # 避免與冠軍重複
    candidate_pool = [n for n in candidate_pool if n != champion]

    # 從候選池中隨機選3碼
    extend_nums = random.sample(candidate_pool, min(3, len(candidate_pool)))
    result.extend(extend_nums)

    # 從1~10中排除已選號碼，再隨機補2碼
    remaining = [n for n in range(1, 11) if n not in result]
    final_random = random.sample(remaining, 2) if len(remaining) >= 2 else remaining
    result.extend(final_random)

    return sorted(result)

if __name__ == "__main__":
    app.run(debug=True)
