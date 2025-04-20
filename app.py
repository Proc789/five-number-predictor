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
  <title>多碼數預測器</title>
  <style>
    input { width: 30px; text-align: center; font-size: 20px; }
    td { padding: 4px; }
    .block { margin-bottom: 20px; }
  </style>
  <script>
    function autoTab(input, nextFieldID) {
      if (input.value.length === 2) {
        document.getElementById(nextFieldID).focus();
      }
    }
  </script>
</head>
<body style='max-width: 480px; margin: auto; padding-top: 30px; font-family: sans-serif; text-align: center;'>
  <h2>預測器</h2>
  <div class="block">
    <form method='POST'>
      <table style="margin:auto;">
        {% for i in range(5) %}
          <tr>
            <td>第 {{i+1}} 期：</td>
            {% for j in range(3) %}
              <td><input name="n{{i}}_{{j}}" id="n{{i}}_{{j}}" maxlength="2"
                oninput="autoTab(this, 'n{{i}}_{{j+1}}')" value="{{session.get('n'+str(i)+'_'+str(j), '')}}"></td>
            {% endfor %}
          </tr>
        {% endfor %}
      </table>
      <div class="block">
        <label><input type="checkbox" name="train" {% if training_enabled %}checked{% endif %}> 啟動訓練模式</label><br><br>
        <label>選擇統計模式：
          <select name="mode">
            {% for m in ['4','5','6','7'] %}
              <option value="{{m}}" {% if selected_mode == m %}selected{% endif %}>{{m}}碼</option>
            {% endfor %}
          </select>
        </label><br><br>
        <button type="submit">預測</button>
      </div>
    </form>
  </div>

  {% if predictions %}
    <div class="block">
      <h3>預測結果：</h3>
      {% for mode in ['4','5','6','7'] %}
        <div>預測（{{mode}}碼）：{{ predictions[mode]|join(', ') }}</div>
      {% endfor %}
    </div>
  {% endif %}

  {% if total_tests > 0 %}
    <div class="block">
      <h3>統計結果（以 {{selected_mode}}碼為主）：</h3>
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
    for i, round_data in enumerate(reversed(recent_numbers)):
        for num in round_data:
            weights[num] = weights.get(num, 0) + (3 - i)
    return [num for num, _ in Counter(weights).most_common(count)]

def get_dynamic_hot(recent_numbers, hot_pool, count):
    flat = [n for group in recent_numbers for n in group if n not in hot_pool]
    return [num for num, _ in Counter(flat).most_common(count)]

@app.route("/", methods=["GET", "POST"])
def index():
    global history, predictions, sources, hot_hits, dynamic_hits, extra_hits, all_hits, total_tests, current_stage, training_enabled, selected_mode

    if request.method == "POST":
        # 儲存輸入資料
        for i in range(5):
            for j in range(3):
                session[f'n{i}_{j}'] = request.form.get(f'n{i}_{j}', '')
        training_enabled = 'train' in request.form
        selected_mode = request.form.get('mode', '5')

        # 收集資料
        history = []
        for i in range(5):
            try:
                nums = [int(request.form.get(f'n{i}_{j}', '')) for j in range(3)]
                nums = [10 if n == 0 else n for n in nums]
                history.append(nums)
            except:
                return redirect("/")

        last_result = history[-1]
        recent = history[-3:] if len(history) >= 3 else history

        predictions = {}
        sources = {}

        for mode in ['4', '5', '6', '7']:
            m = int(mode)
            hot_pool = weighted_hot_numbers(recent, 2)
            dynamic_pool = get_dynamic_hot(recent, hot_pool, 2)
            combined = hot_pool + dynamic_pool
            extra_pool = [n for n in range(1, 11) if n not in combined]
            random.shuffle(extra_pool)

            count_needed = m - len(combined)
            final = (hot_pool + dynamic_pool + extra_pool[:count_needed])[:m]
            final = sorted(list(set(final)))  # 去重後補足
            while len(final) < m:
                left = [n for n in range(1, 11) if n not in final]
                final.append(random.choice(left))
                final = sorted(final)

            predictions[mode] = final
            sources[mode] = {
                "hot": hot_pool,
                "dynamic": dynamic_pool,
                "extra": [n for n in final if n not in hot_pool + dynamic_pool]
            }

        if training_enabled:
            selected_prediction = predictions[selected_mode]
            if last_result[0] in selected_prediction:
                all_hits += 1
                current_stage = 1
            else:
                current_stage += 1
            total_tests += 1

            # 命中區域記錄
            src = sources[selected_mode]
            if last_result[0] in src["hot"]:
                hot_hits += 1
            elif last_result[0] in src["dynamic"]:
                dynamic_hits += 1
            elif last_result[0] in src["extra"]:
                extra_hits += 1

    return render_template_string(TEMPLATE,
        predictions=predictions,
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
