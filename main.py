import feedparser
import google.generativeai as genai
import os
from datetime import datetime

# 1. 設定 AI
genai.configure(api_key=os.environ["GEMINI_API_KEY"])
model = genai.GenerativeModel('gemini-1.5-flash')

# 2. 新聞來源 (使用 RSS 格式更穩定)
RSS_SOURCES = [
    "https://www.cna.com.tw/rss/aall.aspx",      # 中央社
    "https://news.pts.org.tw/xml/newsfeed.xml",  # 公視
    "https://technews.tw/feed/",                # 科技新報
    "https://www.rfi.fr/tw/rss",                # 法廣
    "https://tchina.kyodonews.net/rss/news.xml" # 共同社
]

# 3. 關鍵字過濾
KEYWORDS = ["環境", "碳排放", "減碳", "永續", "氣候", "生態", "開發", "野生動物", "循環", "動物", "能源", "電力", "核能", "太陽能", "地熱", "水力發電", "風力發電"]

def fetch_and_filter():
    filtered_news = []
    for url in RSS_SOURCES:
        feed = feedparser.parse(url)
        for entry in feed.entries:
            title = entry.title
            desc = entry.get('summary', '')
            # 檢查標題或內容是否包含關鍵字
            if any(k in title or k in desc for k in KEYWORDS):
                filtered_news.append(f"標題：{title}\n連結：{entry.link}\n內容摘要：{desc[:100]}...")
    return filtered_news[:15] # 限制最多 15 則，避免 AI 處理太久

def main():
    news_list = fetch_and_filter()
    if not news_list:
        summary = "今日暫無相關環境新聞。"
    else:
        news_text = "\n\n".join(news_list)
        prompt = f"你是一個環境新聞專家，請將以下新聞整理成一份中文摘要網頁內容。包含一個大標題、條列式重點、以及每則新聞的簡短評論與連結：\n\n{news_text}"
        response = model.generate_content(prompt)
        summary = response.text

    # 產生 HTML 網頁
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    html = f"""
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>每日環境新聞摘錄</title>
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/water.css@2/out/water.css">
    </head>
    <body>
        <h1>🌱 每日環境新聞摘要</h1>
        <p>更新時間：{now} (每 12 小時更新一次)</p>
        <hr>
        <div style="white-space: pre-wrap;">{summary}</div>
        <footer>
            <hr>
            <p>資料來源：中央社、公視、共同社等。由 AI 自動產生。</p>
        </footer>
    </body>
    </html>
    """
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)

if __name__ == "__main__":
    main()
