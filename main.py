import feedparser
import google.generativeai as genai
import os
from datetime import datetime

# 1. AI 模型設定
api_key = os.environ.get("GEMINI_API_KEY")
genai.configure(api_key=api_key)

def get_ai_model():
    for name in ['gemini-1.5-flash', 'gemini-pro']:
        try:
            m = genai.GenerativeModel(name)
            m.generate_content("test")
            return m
        except: continue
    return None

model = get_ai_model()

# 2. 新聞來源與關鍵字 (回歸統一抓取)
RSS_SOURCES = [
    "https://www.cna.com.tw/rss/aall.aspx",
    "https://news.pts.org.tw/xml/newsfeed.xml",
    "https://technews.tw/feed/",
    "https://www.rfi.fr/tw/rss",
    "https://tchina.kyodonews.net/rss/news.xml",
    "https://e-info.org.tw/rss.xml",
    "https://feeds.feedburner.com/EnvironmentalNewsNetwork"
]

KEYWORDS = ["環境", "碳排放", "減碳", "永續", "氣候", "生態", "開發", "野生動物", "循環", "動物", "能源", "電力", "核能", "太陽能", "地熱", "水力發電", "風力發電", "減塑", "海廢"]

def fetch_all_news():
    news_list = []
    seen = set()
    for url in RSS_SOURCES:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries:
                title = entry.title
                link = entry.link
                desc = getattr(entry, 'summary', '') or getattr(entry, 'description', '')
                if any(k in title or k in desc for k in KEYWORDS) and link not in seen:
                    fallback = desc.replace('<p>', '').replace('</p>', '')[:120] + "..."
                    news_list.append({"title": title, "link": link, "desc": fallback})
                    seen.add(link)
        except: continue
    return news_list[:30] # 增加顯示數量至 30 則

def main():
    all_news = fetch_all_news()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    # 產生新聞卡片的 HTML (由 JavaScript 動態控制顯示)
    import json
    news_json = json.dumps(all_news, ensure_ascii=False)

    html_template = f"""
    <!DOCTYPE html>
    <html lang="zh-Hant">
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>EcoNews | 環境能源摘錄</title>
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/water.css@2/out/water.css">
        <style>
            :root {{ --main-color: #2e7d32; --bg: #f4f4f4; }}
            body {{ max-width: 1100px; background: var(--bg); font-family: sans-serif; }}
            header {{ text-align: center; padding: 30px; background: white; border-radius: 10px; margin-bottom: 20px; }}
            
            /* 分頁按鈕 */
            .nav-tabs {{ display: flex; justify-content: center; gap: 10px; margin-bottom: 20px; }}
            .nav-tabs button {{ background: #ddd; color: #333; border: none; padding: 10px 20px; cursor: pointer; border-radius: 5px; font-weight: bold; }}
            .nav-tabs button.active {{ background: var(--main-color); color: white; }}

            .news-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 20px; }}
            .news-card {{ background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); display: flex; flex-direction: column; }}
            .news-card h3 {{ font-size: 1.1em; margin: 0 0 10px; color: #111; line-height: 1.4; }}
            .news-card p {{ font-size: 0.9em; color: #555; flex-grow: 1; }}
            
            .card-footer {{ display: flex; justify-content: space-between; margin-top: 15px; padding-top: 10px; border-top: 1px solid #eee; }}
            .save-btn {{ background: #fff3e0; color: #e65100; border: none; padding: 5px 10px; border-radius: 4px; cursor: pointer; }}
            
            #favorites-list .tag-badge {{ background: #e8f5e9; color: #2e7d32; font-size: 0.8em; padding: 2px 6px; border-radius: 4px; }}
            .hidden {{ display: none !important; }}
        </style>
    </head>
    <body>
        <header>
            <h1>🌱 EcoNews 每日摘要</h1>
            <p>最後更新：{now_str}</p>
        </header>

        <div class="nav-tabs">
            <button id="tab-all" class="active" onclick="showPage('all')">最新新聞</button>
            <button id="tab-fav" onclick="showPage('fav')">我的收藏</button>
        </div>

        <div id="page-all" class="news-grid">
            </div>

        <div id="page-fav" class="news-grid hidden">
            </div>

        <script>
            const newsData = {news_json};
            let favorites = JSON.parse(localStorage.getItem('eco_favorites')) || [];

            function renderNews() {{
                const container = document.getElementById('page-all');
                container.innerHTML = newsData.map((item, idx) => `
                    <div class="news-card">
                        <h3>${{item.title}}</h3>
                        <p>${{item.desc}}</p>
                        <div class="card-footer">
                            <a href="${{item.link}}" target="_blank">原文 ↗</a>
                            <button onclick="saveItem(${{idx}})" class="save-btn">⭐ 收藏</button>
                        </div>
                    </div>
                `).join('');
            }}

            function renderFavorites() {{
                const container = document.getElementById('page-fav');
                if (favorites.length === 0) {{
                    container.innerHTML = "<p style='grid-column: 1/-1; text-align: center;'>目前還沒有收藏文章喔！</p>";
                    return;
                }}
                container.innerHTML = favorites.map((item, idx) => `
                    <div class="news-card">
                        <h3>${{item.title}} <span class="tag-badge">#${{item.tag}}</span></h3>
                        <div class="card-footer">
                            <a href="${{item.link}}" target="_blank">原文 ↗</a>
                            <button onclick="deleteItem(${{idx}})" style="background:#ffebee; color:#c62828; border:none; border-radius:4px; cursor:pointer;">刪除</button>
                        </div>
                    </div>
                `).join('');
            }}

            function saveItem(idx) {{
                const item = newsData[idx];
                const tag = prompt("請輸入分類標籤（例如：能源、減碳）：", "一般");
                if (tag) {{
                    favorites.push({{ ...item, tag }});
                    localStorage.setItem('eco_favorites', JSON.stringify(favorites));
                    alert("已加入收藏！");
                    
                    // 同步到 GitHub Issue (雲端備份)
                    const repoOwner = window.location.hostname.split('.')[0];
                    const repoName = window.location.pathname.split('/')[1] || "eco-news-daily";
                    window.open(`https://github.com/${{repoOwner}}/${{repoName}}/issues/new?title=${{encodeURIComponent("[收藏] "+item.title)}}&body=${{encodeURIComponent(item.link)}}&labels=${{encodeURIComponent(tag)}}`, '_blank');
                }}
            }}

            function deleteItem(idx) {{
                if (confirm("確定要刪除這筆收藏嗎？")) {{
                    favorites.splice(idx, 1);
                    localStorage.setItem('eco_favorites', JSON.stringify(favorites));
                    renderFavorites();
                }}
            }}

            function showPage(page) {{
                document.getElementById('page-all').classList.toggle('hidden', page !== 'all');
                document.getElementById('page-fav').classList.toggle('hidden', page !== 'fav');
                document.getElementById('tab-all').classList.toggle('active', page === 'all');
                document.getElementById('tab-fav').classList.toggle('active', page === 'fav');
                if (page === 'fav') renderFavorites();
            }}

            window.onload = renderNews;
        </script>
    </body>
    </html>
    """
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_template)

if __name__ == "__main__":
    main()
