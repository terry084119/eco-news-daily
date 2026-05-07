import feedparser
import google.generativeai as genai
import os
from datetime import datetime
import time

# 1. 設定 AI
try:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("找不到 GEMINI_API_KEY，請檢查 GitHub Secrets 設定")
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    print(f"AI 設定失敗: {e}")

# 2. 擴充新聞來源 (包含你提供的來源)
RSS_SOURCES = [
    "https://www.cna.com.tw/rss/aall.aspx",         # 中央社
    "https://news.pts.org.tw/xml/newsfeed.xml",     # 公視
    "https://technews.tw/feed/",                   # 科技新報
    "https://www.rfi.fr/tw/rss",                   # 法廣
    "https://tchina.kyodonews.net/rss/news.xml",    # 共同社
    "https://feeds.feedburner.com/EnvironmentalNewsNetwork" # ENN 環境新聞
]

# 3. 關鍵字
KEYWORDS = ["環境", "碳排放", "減碳", "永續", "氣候", "生態", "開發", "野生動物", "循環", "動物", "能源", "電力", "核能", "太陽能", "地熱", "水力發電", "風力發電"]

def fetch_and_filter():
    filtered_news = []
    print("開始抓取新聞...")
    for url in RSS_SOURCES:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries:
                title = entry.title
                desc = getattr(entry, 'summary', '')
                # 檢查關鍵字
                if any(k in title or k in desc for k in KEYWORDS):
                    filtered_news.append(f"標題：{title}\n連結：{entry.link}")
        except Exception as e:
            print(f"抓取 {url} 失敗: {e}")
            continue
    
    # 去除重複並限制數量
    unique_news = list(set(filtered_news))
    print(f"共找到 {len(unique_news)} 則相關新聞")
    return unique_news[:20]

def main():
    news_list = fetch_and_filter()
    
    if not news_list:
        summary_text = "今日暫無偵測到與環境、能源相關的新聞更新。"
    else:
        news_combined = "\n\n".join(news_list)
        prompt = f"你是一位專業的環境議題分析師，請針對以下新聞清單，用繁體中文整理出一份結構清晰的每日環境新聞摘錄。包含一個引人入勝的標題、重點分類摘要、以及簡短的評論。請保留原始新聞連結：\n\n{news_combined}"
        
        try:
            response = model.generate_content(prompt)
            summary_text = response.text
        except Exception as e:
            summary_text = f"AI 生成摘要失敗: {e}\n\n原始新聞連結：\n{news_combined}"

    # 產生 HTML
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    html_template = f"""
    <!DOCTYPE html>
    <html lang="zh-Hant">
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>每日環境新聞摘錄</title>
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/water.css@2/out/water.css">
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; line-height: 1.8; }}
            .content {{ white-space: pre-wrap; }}
            h1 {{ color: #2e7d32; }}
        </style>
    </head>
    <body>
        <h1>🌱 每日環境新聞摘要</h1>
        <p>🕒 更新時間：{now} (每 12 小時自動更新)</p>
        <hr>
        <div class="content">{summary_text}</div>
        <footer>
            <hr>
            <p style="font-size: 0.8em; color: #666;">
                資料來源：中央社、公視、科技新報、共同社等。由 AI 自動篩選與摘要。
            </p>
        </footer>
    </body>
    </html>
    """
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_template)
    print("網頁更新成功！")

if __name__ == "__main__":
    main()
