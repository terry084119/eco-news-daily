import feedparser
import google.generativeai as genai
import os
from datetime import datetime

# 1. AI 模型設定 (自動嘗試多種名稱以防 404)
api_key = os.environ.get("GEMINI_API_KEY")
genai.configure(api_key=api_key)

def get_ai_model():
    for name in ['gemini-1.5-flash', 'gemini-pro', 'gemini-1.0-pro']:
        try:
            m = genai.GenerativeModel(name)
            # 測試模型是否可用
            m.generate_content("test")
            print(f"目前使用 AI 模型: {name}")
            return m
        except:
            continue
    return None

model = get_ai_model()

# 2. 新聞來源與關鍵字
RSS_SOURCES = [
    "https://www.cna.com.tw/rss/aall.aspx",         # 中央社
    "https://news.pts.org.tw/xml/newsfeed.xml",     # 公視
    "https://technews.tw/feed/",                   # 科技新報
    "https://www.rfi.fr/tw/rss",                   # 法廣
    "https://tchina.kyodonews.net/rss/news.xml",    # 共同社
    "https://e-info.org.tw/rss.xml"                # 環境資訊中心
]

KEYWORDS = ["環境", "碳排放", "減碳", "永續", "氣候", "生態", "開發", "野生動物", "循環", "動物", "能源", "電力", "核能", "太陽能", "地熱", "水力發電", "風力發電", "減塑", "海廢"]

def fetch_news():
    print("正在搜集新聞...")
    news_list = []
    seen_links = set()
    for url in RSS_SOURCES:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries:
                title = entry.title
                link = entry.link
                # 取得內容，若無則用標題替代
                desc = getattr(entry, 'summary', '') or getattr(entry, 'description', '')
                
                if any(k in title or k in desc for k in KEYWORDS) and link not in seen_links:
                    # 擷取第一段作為 AI 失敗時的備案
                    fallback_text = desc.replace('<p>', '').replace('</p>', '')[:150] + "..."
                    news_list.append({
                        "title": title, 
                        "link": link, 
                        "fallback": fallback_text
                    })
                    seen_links.add(link)
        except Exception as e:
            print(f"抓取 {url} 時發生錯誤: {e}")
    return news_list[:15] # 限制 15 則以確保 AI 處理穩定

def main():
    news_data = fetch_news()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    # 建立新聞卡片的 HTML
    cards_html = ""
    for idx, item in enumerate(news_data):
        summary = ""
        if model:
            try:
                prompt = f"請將這則環境新聞做 50 字以內的繁體中文摘要：標題「{item['title']}」，內容「{item['fallback']}」"
                response = model.generate_content(prompt)
                summary = response.text.strip()
            except:
                summary = item['fallback']
        else:
            summary = item['fallback']
        
        cards_html += f"""
        <div class="news-card" data-title="{item['title']}" data-link="{item['link']}">
            <div class="card-tag">今日精選</div>
            <h3>{item['title']}</h3>
            <p>{summary}</p>
            <div class="card-footer">
                <a href="{item['link']}" target="_blank" class="read-more">閱讀原文 ↗</a>
                <button onclick="saveToCloud({idx})" class="save-btn">⭐ 雲端收藏</button>
            </div>
        </div>
        """

    # 3. 網頁模板 (包含新聞風格 CSS 與 雲端收藏 JS)
    html_template = f"""
    <!DOCTYPE html>
    <html lang="zh-Hant">
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>EcoNews | 每日環境新聞摘要</title>
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/water.css@2/out/water.css">
        <style>
            :root {{ --main-green: #2e7d32; --bg-gray: #f0f2f0; }}
            body {{ max-width: 800px; background-color: var(--bg-gray); font-family: "PingFang TC", sans-serif; }}
            header {{ text-align: center; padding: 50px 20px; background: white; border-radius: 0 0 30px 30px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); }}
            h1 {{ color: var(--main-green); font-size: 2.8em; margin: 0; }}
            .subtitle {{ color: #666; margin-top: 10px; }}
            .news-grid {{ margin-top: 30px; }}
            .news-card {{ background: white; padding: 25px; border-radius: 15px; margin-bottom: 25px; box-shadow: 0 4px 6px rgba(0,0,0,0.02); transition: 0.3s; border: 1px solid #eee; }}
            .news-card:hover {{ transform: translateY(-5px); box-shadow: 0 10px 20px rgba(0,0,0,0.05); }}
            .card-tag {{ background: var(--main-green); color: white; display: inline-block; padding: 2px 10px; border-radius: 20px; font-size: 0.7em; margin-bottom: 10px; }}
            h3 {{ margin: 0 0 15px 0; color: #1a1a1a; line-height: 1.4; }}
            p {{ color: #444; font-size: 1.05em; line-height: 1.7; }}
            .card-footer {{ display: flex; justify-content: space-between; align-items: center; margin-top: 20px; border-top: 1px solid #f0f0f0; padding-top: 15px; }}
            .read-more {{ color: var(--main-green); font-weight: bold; text-decoration: none; }}
            .save-btn {{ background: #fff8e1; color: #f57f17; border: 1px solid #ffe082; padding: 6px 15px; cursor: pointer; border-radius: 8px; font-weight: bold; }}
            .save-btn:hover {{ background: #fff176; }}
            footer {{ text-align: center; padding: 40px; color: #888; font-size: 0.8em; }}
        </style>
    </head>
    <body>
        <header>
            <h1>🌱 EcoNews</h1>
            <p class="subtitle">為您守護地球的每一份資訊</p>
            <p><small>更新時間：{now_str} (每 12 小時自動更新)</small></p>
        </header>

        <div class="news-grid">
            {cards_html}
        </div>

        <footer>
            <p>本站由 GitHub Actions 與 Google Gemini AI 自動驅動</p>
            <p>收藏之內容將儲存於專案 Issue 雲端資料庫</p>
        </footer>

        <script>
            function saveToCloud(idx) {{
                const card = document.querySelectorAll('.news-card')[idx];
                const title = card.getAttribute('data-title');
                const link = card.getAttribute('data-link');
                const tag = prompt("請輸入收藏標籤（例如：能源、減碳、重要）：", "一般");
                
                if (tag) {{
                    // 自動抓取目前的網址來判斷 Repo 路徑
                    const pathParts = window.location.pathname.split('/');
                    const repoName = pathParts[1] || "eco-news-daily"; 
                    const repoOwner = window.location.hostname.split('.')[0];

                    const issueTitle = encodeURIComponent("[收藏] " + title);
                    const issueBody = encodeURIComponent("### 🍀 收藏新聞\\n**標題**： " + title + "\\n\\n**分類標籤**： #" + tag + "\\n**原始連結**： " + link + "\\n\\n--- \\n> 來自我的 EcoNews 自動化摘要站");
                    
                    const githubUrl = `https://github.com/${{repoOwner}}/${{repoName}}/issues/new?title=${{issueTitle}}&body=${{issueBody}}&labels=${{encodeURIComponent(tag)}}`;
                    
                    if(confirm("將前往 GitHub 建立雲端 Issue 存檔。請點擊新分頁中的『Submit new issue』按鈕。")) {{
                        window.open(githubUrl, '_blank');
                    }}
                }}
            }}
        </script>
    </body>
    </html>
    """
    
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_template)
    print("網頁更新成功！")

if __name__ == "__main__":
    main()
