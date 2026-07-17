from flask import Flask, render_template, session, redirect, url_for
from flask import request, jsonify
from datetime import datetime, timedelta
import os
import psycopg2
DATABASE_URL = os.getenv("DATABASE_URL")
def get_db_connection():
    return psycopg2.connect(DATABASE_URL)
    
app = Flask(__name__)
app.secret_key = "present-web-secret-key"

from openai import OpenAI
client = OpenAI()

def is_english(text):
    return sum(1 for c in text if ord(c) < 128) / max(len(text), 1) > 0.6
def load_prompt(filename):
    try:
        with open(filename, encoding="utf-8") as f:
            text = f.read().strip()
            if text:
                return text
            else:
                return ""
    except:
        return ""
def select_prompt(user_input, mode):    
    if mode == "aiemon":
        return load_prompt("aiuemon.txt")

    elif mode == "concierge":
        return load_prompt("concierge.txt")

    else:
        if is_english(user_input):
            return load_prompt("gift_en.txt")
        else:
            return load_prompt("gift_ja.txt")
def load_story_spec():
    return load_prompt("story_spec.txt")

def load_runtime_initial():
    return load_prompt("runtime_initial.txt")

def load_runtime_interview():
    return load_prompt("runtime_interview.txt")

def load_runtime_ready():
    return load_prompt("runtime_ready.txt")

def load_history(mode):
    if mode == "aiemon":
        return session.get("aiuemon_history", [])
    return []
def load_story_state():
    return session.get("story_state", "INITIAL")
    
def save_story_state(state):
    session["story_state"] = state

def build_messages(
    prompt,
    story_spec,
    runtime_initial,
    runtime_interview,
    runtime_ready,
    history,
    user_input,
    state
):
    messages = [
        {"role":"system","content":prompt}
    ]

    if state == "INITIAL":
        messages.append({
            "role":"system",
            "content":runtime_initial
        })

    if state == "INTERVIEW":
        messages.append({
            "role":"system",
            "content":runtime_interview
        })

    if state == "READY":
        messages.append({
            "role":"system",
            "content":runtime_ready
        })

    if state == "INITIAL":
        messages.append({
            "role": "system",
            "content": story_spec
        })

    for item in history:
        messages.append(item)

    messages.append({
        "role": "user",
        "content": user_input
    })

    return messages

def call_openai(messages):
    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=messages
    )

    increment_count()

    return response.choices[0].message.content

def save_history(mode, history, user_input, reply):
    if mode == "aiemon":
        history.append({
            "role": "user",
            "content": user_input
        })

        history.append({
            "role": "assistant",
            "content": reply
        })

        session["aiuemon_history"] = history[-30:]

def generate_response(user_input, mode, history):
# 今日の言葉を読み込み
    with open("words.txt", encoding="utf-8") as f:
        text = f.read()
# モードに応じたプロンプト選択
    state = load_story_state()

    if state == "INITIAL":
        save_story_state("INTERVIEW")

    prompt = select_prompt(user_input, mode)
    story_spec = load_story_spec()
    runtime_initial = load_runtime_initial()
    runtime_interview = load_runtime_interview()
    runtime_ready = load_runtime_ready()

# 会話履歴の準備
    history = load_history(mode)
    messages = build_messages(
        prompt,
        story_spec,
        runtime_initial,
        runtime_interview,
        runtime_ready,
        history,
        user_input,
        state
    )
# OpenAIへ問い合わせ 
    reply = call_openai(messages)

    if reply.startswith("<STATE:READY>"):
        save_story_state("READY")
        print("story_state changed to READY")
        reply = reply.replace("<STATE:READY>", "", 1).strip()

    elif reply.startswith("<STATE:INTERVIEW>"):
        save_story_state("INTERVIEW")
        print("story_state changed to INTERVIEW")
        reply = reply.replace("<STATE:INTERVIEW>", "", 1).strip()

# 履歴保存
    save_history(mode, history, user_input, reply)
# 応答を返す    
    return reply
    
    
def get_db_count():
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute("SELECT COUNT(*) FROM entries")
        result = cur.fetchone()
        return result[0] if result else 0

    except Exception as e:
        print("get_db_count error:", e)
        return 0

    finally:
        cur.close()
        conn.close()

def increment_count():
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute(
            "INSERT INTO entries (app_name, user_key, input_text, output_text) VALUES (%s, %s, %s, %s)",
            ("present_web", "happy_count", "count", "count")
        )
        conn.commit()

    except Exception as e:
        print("increment_count error:", e)

    finally:
        cur.close()
        conn.close()

@app.route("/")
def index():
    mode = session.get("mode", "gift")
    date_text = (datetime.utcnow() + timedelta(hours=9)).strftime("%Y年%m月%d日")
    
    with open("enjoy.txt", encoding="utf-8") as f:
        enjoy_words = [line.strip() for line in f if line.strip()]
    with open("words.txt", encoding="utf-8") as f:
        words = [line.strip() for line in f if line.strip()]

    if words:
        index = (datetime.utcnow() + timedelta(hours=9)).day % len(words)
        today_word = words[index]
    else:
        today_word = "（言葉がありません）"

    return render_template(
        "index.html",
        mode=mode,
        count=get_db_count(),
        date_text=date_text,
        tone="",
        user_text="こんにちは",
        reply="",
        today_word=today_word,
        enjoy_words=enjoy_words
    )

@app.route("/toggle_mode", methods=["POST"])
def toggle_mode():
    current = session.get("mode", "gift")

    if current == "gift":
        session["mode"] = "aiemon"
    elif current == "aiemon":
        session["mode"] = "concierge"
    else:
        session["mode"] = "gift"

    return "OK"

@app.route("/send", methods=["POST"])
def send():
    data = request.get_json()
    user_text = data.get("user_text", "")
    mode = session.get("mode", "gift")
    history = session.get("history", [])

    # words.txt 読み込み
    with open("words.txt", encoding="utf-8") as f:
        words = [line.strip() for line in f if line.strip()]

    # 空入力 → 今日の言葉
    if user_text.strip() == "":
        if words:
            index = (datetime.utcnow() + timedelta(hours=9)).day % len(words)
            reply = words[index]
        else:
            reply = "（言葉がありません）"
        return jsonify({
            "reply": reply,
            "count": get_db_count()
        })
    # 通常入力（モード別）
    reply = generate_response(user_text, mode, history)

    return jsonify({
        "reply": reply,
        "count": get_db_count()
    })
    
if __name__ == "__main__":
    app.run(debug=True)
