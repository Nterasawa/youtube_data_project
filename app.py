from flask import Flask, render_template, request
from googleapiclient.discovery import build

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # ここにYouTube Data API処理を追加
        return render_template('results.html')
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)