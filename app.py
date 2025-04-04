from flask import Flask, render_template_string, request
import random
from collections import Counter

app = Flask(__name__)
history = []
predictions = []
hits = 0
total = 0
stage = 1
training = False

@app.route("/", methods=["GET", "POST"])
def home():
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
            first = 10 if first == 0 else first
            second = 10 if second == 0 else second
            third = 10 if third == 0 else third

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
    last = history[-1]
    hot = random.sample(last, k=2)

    flat = [n for group in recent for n in group if n not in hot]
    freq = Counter(flat)
    if freq:
        max_freq = max(freq.values())
        dynamic_pool = [n for n, c in freq.items() if c == max_freq]
        dynamic_hot = [random.choice(dynamic_pool)]
    else:
        dynamic_hot = []

    exclude_from_extra = set(hot + dynamic_hot + dynamic_pool)
    pool = [n for n in range(1, 11) if n not in exclude_from_extra]
    random.shuffle(pool)
    extra = pool[: max(0, 5 - len(hot + dynamic_hot))]

    return sorted(hot + dynamic_hot + extra)

TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
  <title>5碼預測器（熱2+動1+補足）</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
</head>
<body style="max-width: 400px; margin: auto; padding-top: 50px; font-family: sans-serif; text-align: center;">
  <h2>5碼預測器（熱2+動1+補足）</h2>
  <form method="POST">
    <input type="number" name="first" id="first" placeholder="冠軍號碼" required inputmode="numeric" style="width: 80%; padding: 8px;" oninput="handleInput(this, 'second')"><br><br>
    <input type="number" name="second" id="second" placeholder="亞軍號碼" required inputmode="numeric" style="width: 80%; padding: 8px;" oninput="handleInput(this, 'third')"><br><br>
    <input type="number" name="third" id="third" placeholder="季軍號碼" required inputmode="numeric" style="width: 80%; padding: 8px;"><br><br>
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

  <script>
    function handleInput(current, nextId) {
      let val = parseInt(current.value);
      if (val === 0) {
        current.value = 10;
      }
      if (current.value.length >= 1 && val >= 1 && val <= 10) {
        setTimeout(() => {
          document.getElementById(nextId).focus();
        }, 50);
      }
    }
  </script>
</body>
</html>
"""

if __name__ == "__main__":
    app.run(debug=True)
