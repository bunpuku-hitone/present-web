from flask import Flask, render_template

app = Flask(__name__)

@app.route("/")
def index():
    return render_template(
        "index.html",
        mode="gift",
        count=0,
        date_text="",
        tone="",
        user_text="こんにちは",
        reply="",
        today_word="言葉の贈り物２",
        enjoy_words=[]
    )

if __name__ == "__main__":
    app.run(debug=True)
