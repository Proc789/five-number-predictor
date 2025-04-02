from flask import Flask, render_template_string, request

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
  <title>6碼預測器（保守命中版）</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
</head>
<body style="max-width: 400px; margin: auto; padding-top: 50px; text-align: center; font-family: sans-serif;">
  <h2>6碼預測器（保守命中版）</h2>
  <form method="POST">
    <input type="number" name="first" placeholder="冠軍號碼" required style="width: 80%; padding: 8px;"><br><br>
    <input type="number" name="second" placeholder="亞軍號碼" required style="width: 80%; padding: 8px;"><br><br>
    <input type="number" name="third" placeholder="季軍號碼" required style="width: 80%; padding: 8px;"><br><br>
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
            current = [first, second, third]
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
    recent = history[-3:]
    flat = [n for group in recent for n in group]

    # 熱號：近3期冠軍出現最多的號碼
    champions = [group[0] for group in recent]
    freq = {n: champions.count(n) for n in set(champions)}
    hot = max(freq, key=freq.get)

    # 動態熱號：上期冠軍（固定納入）
    last_champion = history[-1][0]
    dynamic_hot = last_champion

    # 出現2次以上的熱門號（排除已選）
    flat_freq = {n: flat.count(n) for n in set(flat)}
    candidates = [n for n, count in flat_freq.items() if count >= 2 and n not in (hot, dynamic_hot)]

    # 依照出現頻率排序補足剩餘號碼
    others = [n for n in sorted(flat_freq, key=flat_freq.get, reverse=True)
              if n not in (hot, dynamic_hot) and n not in candidates]

    result = list({hot, dynamic_hot} | set(candidates))
    for n in others:
        if len(result) >= 6:
            break
        if n not in result:
            result.append(n)

    return sorted(result[:6])

if __name__ == "__main__":
    app.run(debug=True)
