from flask import Flask, render_template_string, request, redirect, session
import random
from collections import Counter

app = Flask(__name__)
app.secret_key = 'secret-key'

history = []
predictions = {}
sources = {}
hot_hits = 0
dynamic_hits = 0
extra_hits = 0
all_hits = 0
total_tests = 0
current_stage = 1
training_enabled = False
selected_mode = '5'

TEMPLATE = """
<!doctype html>
<html>
<head>
  <meta charset='utf-8'>
  <meta name='viewport' content='width=device-width, initial-scale=1'>
  <title>多碼預測器</title>
  <style>
    input { width: 30px; text-align: center; font-size: 20px; }
    td { padding: 4px; }
    .block { margin-bottom: 20px; }
  </style>
  <script>
    function autoTab(input, nextID) {
      if (input.value.length === 2) {
        var next = document.getElementById(nextID);
        if (next) next.focus();
      }
    }
  </script>
</head>
<body style='max-width: 460px; margin: auto; padding-top: 30px; font-family: sans-serif; text-align: center;'>
  <h2>預測器</h2>
  <form method="POST">
    <table style="margin:auto;">
      <tr>
        <td>第一名</td>
        <td><input name="n0" id="n0" maxlength="2" oninput="autoTab(this, 'n1')" required></td>
        <td>第二名</td>
        <td><input name="n1" id="n1" maxlength="2" oninput="autoTab(this, 'n2')" required></td>
        <td>第三名</td>
        <td><input name="n2" id="n2" maxlength="2" required></td>
      </tr>
    </table>
    <div class="block">
      <label><input type="checkbox" name="train" {% if training_enabled %}checked{% endif %}> 啟動訓練模式</label><br><br>
      <label>統計碼數版本：
        <select name="mode">
          {% for m in ['4','5','6','7'] %}
            <option value="{{m}}" {% if selected_mode == m %}selected{% endif %}>{{m}}碼</option>
          {% endfor %}
        </select>
      </label><br><br>
      <button type="submit">提交</button>
    </div>
  </form>

  {% if predictions %}
    <div class="block">
      <h3>預測結果</h3>
      {% for mode in ['4','5','6','7'] %}
        <div>{{mode}}碼預測：{{ predictions[mode]|join(', ') }}</div>
      {% endfor %}
    </div>
  {% endif %}

  {% if total_tests > 0 %}
    <div class="block">
      <h3>命中統計（以 {{selected_mode}}碼為主）</h3>
      <div>目前關卡：第 {{current_stage}} 關</div>
      <div>冠軍命中：{{all_hits}} / {{total_tests}}</div>
      <div>熱號命中：{{hot_hits}}，動熱命中：{{dynamic_hits}}，補碼命中：{{extra_hits}}</div>
    </div>
  {% endif %}
</body>
</html>
"""

def weighted_hot_numbers(recent_numbers, count):
    weights = {}
    for i, group in enumerate(reversed(recent_numbers)):
        for num in group:
            weights[num] = weights.get(num, 0) + (3 - i)
    return [num for num, _ in Counter(weights).most_common(count)]

def get_dynamic_hot(recent_numbers, hot_pool, count):
    flat = [n for group in recent_numbers for n in group if n not in hot_pool]
    return [num for num, _ in Counter(flat).most_common(count)]

@app.route("/", methods=["GET", "POST"])
def index():
    global history, predictions, sources, hot_hits, dynamic_hits, extra_hits
    global all_hits, total_tests, current_stage, training_enabled, selected_mode

    if request.method == "POST":
        try:
            nums = [int(request.form.get(f'n{i}', '')) for i in range(3)]
            nums = [10 if n == 0 else n for n in nums]
            history.append(nums)
        except:
            return redirect("/")

        training_enabled = 'train' in request.form
        selected_mode = request.form.get('mode', '5')

        if len(history) >= 5:
            recent = history[-3:]
            last_result = history[-1]

            predictions = {}
            sources = {}

            for mode in ['4','5','6','7']:
                m = int(mode)
                hot_pool = weighted_hot_numbers(recent, 2)
                dynamic_pool = get_dynamic_hot(recent, hot_pool, 2)
                combined = hot_pool + dynamic_pool
                extra_pool = [n for n in range(1, 11) if n not in combined]
                random.shuffle(extra_pool)

                result = combined[:]
                for n in extra_pool:
                    if len(result) >= m: break
                    if n not in result:
                        result.append(n)
                result = sorted(result[:m])

                predictions[mode] = result
                sources[mode] = {
                    "hot": hot_pool,
                    "dynamic": dynamic_pool,
                    "extra": [n for n in result if n not in hot_pool + dynamic_pool]
                }

            if training_enabled:
                target = predictions[selected_mode]
                if last_result[0] in target:
                    all_hits += 1
                    current_stage = 1
                else:
                    current_stage += 1
                total_tests += 1

                src = sources[selected_mode]
                if last_result[0] in src["hot"]:
                    hot_hits += 1
                elif last_result[0] in src["dynamic"]:
                    dynamic_hits += 1
                elif last_result[0] in src["extra"]:
                    extra_hits += 1

    return render_template_string(TEMPLATE,
        predictions=predictions if len(history) >= 5 else None,
        hot_hits=hot_hits,
        dynamic_hits=dynamic_hits,
        extra_hits=extra_hits,
        all_hits=all_hits,
        total_tests=total_tests,
        current_stage=current_stage,
        training_enabled=training_enabled,
        selected_mode=selected_mode
    )

if __name__ == "__main__":
    app.run(debug=True)
