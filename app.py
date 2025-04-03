# （略過 TEMPLATE 與 /toggle，與之前版本一致）
# 關鍵修復在 index()

@app.route("/", methods=["GET", "POST"])
def index():
    global hits, total, stage, training, last_random, hit_source_counter
    result = None
    last_champion = None
    last_prediction = None
    hit = None
    prediction_parts = None

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

            # 先做預測
            if len(history) >= 3:
                prediction, last_random, prediction_parts = generate_prediction(last_random)
                predictions.append(prediction)
                result = prediction
            else:
                result = "請至少輸入三期資料後才可預測"
                return render_template_string(
                    TEMPLATE, result=result, history=history[-5:], last_champion=None,
                    last_prediction=None, hit=None, training=training,
                    toggle_text="關閉訓練模式" if training else "啟動訓練模式",
                    stats=f"{hits} / {total}" if training else None,
                    stage=stage if training else None,
                    hit_sources=hit_source_counter if training else {}
                )

            # 命中判定與統計（需要至少兩組預測才判斷）
            if len(predictions) >= 2:
                last_prediction = predictions[-2]
                last_champion = current[0]

                if last_champion in last_prediction:
                    hit = "命中"
                    if training:
                        hits += 1
                        stage = 1

                        if prediction_parts:
                            hot, dynamic_hot, pick, rand_fill = prediction_parts
                            if last_champion == hot:
                                hit_source_counter["熱號"] += 1
                            elif last_champion == dynamic_hot:
                                hit_source_counter["動熱"] += 1
                            elif pick and last_champion in pick:
                                hit_source_counter["候選碼"] += 1
                            elif last_champion in rand_fill:
                                hit_source_counter["補碼"] += 1
                else:
                    hit = "未命中"
                    if training:
                        stage += 1

                if training:
                    total += 1

        except:
            result = "格式錯誤，請輸入 1~10 的整數"

    toggle_text = "關閉訓練模式" if training else "啟動訓練模式"
    return render_template_string(TEMPLATE, result=result, history=history[-5:],
                                  last_champion=last_champion, last_prediction=last_prediction,
                                  hit=hit, training=training, toggle_text=toggle_text,
                                  stats=f"{hits} / {total}" if training else None,
                                  stage=stage if training else None,
                                  hit_sources=hit_source_counter if training else {})
