from flask import Flask, render_template_string, request
import requests

app = Flask(__name__)

TEMPLATE = """
<!DOCTYPE html>
<html>
  <head>
    <title>擷取開獎資料測試</title>
    <meta name='viewport' content='width=device-width, initial-scale=1'>
  </head>
  <body style="max-width: 400px; margin: auto; padding-top: 50px; text-align: center; font-family: sans-serif;">
    <h2>擷取開獎資料測試</h2>
    <form action="/fetch" method="post">
      <button type="submit" style="padding: 10px 20px;">擷取開獎資料</button>
    </form>
    {% if result %}
      <div style="margin-top: 20px; text-align: left;">
        <h4>擷取結果：</h4>
        <pre>{{ result }}</pre>
      </div>
    {% endif %}
  </body>
</html>
"""

@app.route("/", methods=["GET"])
def home():
    return render_template_string(TEMPLATE)

@app.route("/fetch", methods=["POST"])
def fetch():
    url = "https://ar1.ar198.com/lobby/520201"
    try:
        res = requests.get(url, timeout=10)
        data = res.json()
        numbers = data["data"]["list"][0]["last"]["n"]  # 1到10名
        return render_template_string(TEMPLATE, result=f"目前開獎號碼（第一名到第十名）：\n{numbers}")
    except Exception as e:
        return render_template_string(TEMPLATE, result=f"擷取失敗：{e}")

if __name__ == "__main__":
    app.run(debug=True)
