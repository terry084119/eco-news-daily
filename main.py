import feedparser
import google.generativeai as genai
import os
from datetime import datetime
import time

# 1. AI 模型設定 - 修正 404 問題
try:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("找不到 GEMINI_API_KEY，請檢查 GitHub Secrets")
    
    genai.configure(api_key=api_key)
    
    # 嘗試多種可能的模型名稱，增加穩定性
    model_names = ['gemini-1.5-flash', 'gemini-pro', 'gemini-1.0-pro']
    model = None
    for name in model_names:
        try:
            model = genai.GenerativeModel(name)
            # 測試一下模型是否可用
            model.generate_content("test")
            print(f"成功使用模型: {name}")
            break
        except:
            continue
    
    if not model:
        raise Exception("無法載入任何 Gemini 模型")

except Exception as e:
    print(f"AI 設定初始錯誤: {e}")

# 2. 新聞來源列表 (RSS 連結)
RSS_SOURCES = [
    "https://www.cna.com.tw/rss/aall.aspx",         # 中央社
    "https://news.pts.org.tw/xml/newsfeed.xml",     # 公視
    "https://technews.tw/feed/",                   # 科技新報
    "https://www.rfi.fr/tw/rss",                   # 法廣
    "https://tchina.kyodonews.net/rss/news.xml",    # 共同社
    "https://feeds.feedburner.com/EnvironmentalNewsNetwork", # ENN
    "https://e-info.org.tw/rss.xml"                # 環境資訊中心 (額外增加)
]

# 3. 關鍵字過濾
KEYWORDS = ["環境", "碳排放", "減碳", "永續", "氣候", "生態", "開發", "野生動物", "循環", "動物", "能源", "電力", "核能", "太陽能", "地熱", "水力發電", "風力發電", "減塑", "汙染"]

def fetch_news():
    print("正在抓取新聞來源...")
    filtered_news = []
    seen_links = set()

    for url in RSS_SOURCES:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries:
                title = entry.title
                link = entry.link
                desc = getattr(entry, 'summary', '') + getattr(entry, 'description', '')
                
                # 關鍵字比對
                if any(k in title or k in desc for k in KEYWORDS):
                    if link not in seen_links:
                        filtered_news.append(f"標題：{title}\n連結：{link}")
                        seen_links.add(link)
        except Exception as e:
            print(f"抓取失敗 {url}: {e}")
            continue
            
    print(f"篩選完成，共 {len(filtered_news)} 則新聞")
    return filtered_news[:20] # 限制 20 則交給 AI 摘要

def main():
    news_data = fetch_news()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    if not news_data:
        summary_result = "今日暫無偵測到相關關鍵字的新聞更新。"
    else:
        news_combined = "\n\n".join(news_data)
        prompt = f"""
        你是一位環境科學與能源政策專家。請根據以下新聞列表，為我製作一份「每日環境新聞摘錄」。
        要求：
        1. 使用繁體中文。
        2. 給這份日報一個亮點標題。
        3. 將新聞分類（例如：氣候變遷、能源轉型、生態保育）。
        4. 每則新聞請提供 1-2 句的重點摘要 + 原始連結。
        5. 最後加上一段專業的今日評論。
        
        新聞內容：
        {news_combined}
        """
        try:
            response = model.generate_content(prompt)
            summary_result = response.text
        except Exception as e:
            print(f"AI 生成失敗: {e}")
            summary_result = f"摘要生成時發生錯誤，請直接參考以下原始連結：\n\n{news_combined}"

    # 4. 產生 HTML 網頁 (使用 Water.css 讓排版變漂亮)
    html_content = f"""
    <!DOCTYPE html>
    <html lang="zh-Hant">
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>每日環境新聞摘要</title>
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/water.css@2/out/water.css">
        <style>
            body {{ font-family: "PingFang TC", "Microsoft JhengHei", sans-serif; }}
            .news-box {{ background: #f9f9f9; padding: 20px; border-left: 5px solid #2e7d32; border-radius: 5px; }}
            .time {{ color: #666; font-size: 0.9em; }}
            pre {{ white-space: pre-wrap; word-wrap: break-word; font-family: inherit; font-size: 1.1em; background: none; border: none; padding: 0; }}
        </style>
    </head>
    <body>
        <h1>🌱 每日環境新聞摘要</h1>
        <p class="time">🕒 最後更新時間：{now_str} (每 12 小時自動更新)</p>
        <hr>
        <div class="news-box">
            <pre>{summary_result}</pre>
        </div>
        <footer>
            <p><small>來源：中央社、公視、科技新報、共同社、RFI等。AI 技術支持：Google Gemini。</small></p>
        </body>
    </html>
    """
    
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_content)
    print("index.html 已成功更新")

if __name__ == "__main__":
    main()
