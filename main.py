import feedparser
import google.generativeai as genai
import os
from datetime import datetime, timedelta, timezone
import time

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

# 2. 新聞來源
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

def fetch_recent_news():
    print("正在搜集 24 小時內的新聞...")
    news_list = []
    seen_links = set()
    
    # 設定 24 小時的時間邊界
    now = datetime.now(timezone.utc)
    day_ago = now - timedelta(hours=24)

    for url in RSS_SOURCES:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries:
                # 取得新聞發布時間
                published_time = None
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    published_time = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
                elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                    published_time = datetime(*entry.updated_parsed[:6], tzinfo=timezone.utc)
                
                # 如果抓不到時間，則預設為當前（避免遺漏），如果有時間則比對是否在 24 小時內
                if published_time and published_time < day_ago:
                    continue

                title = entry.title
                link = entry.link
                desc = getattr(entry, 'summary', '') or getattr(entry, 'description', '')
                
                if any(k in title or k in desc for k in KEYWORDS) and link not in seen_links:
                    fallback = desc.replace('<p>', '').replace('</p>', '')[:120] + "..."
                    news_list.append({"title": title, "link": link, "desc": fallback})
                    seen_links.add(link)
        except Exception as e:
            print(f"抓取 {url} 失敗: {e}")
            continue
            
    # 按照來源順序交叉排序後取前 20 篇
    return news_list[:20]

def main():
    all_news = fetch_recent_news()
    # 轉換為本地時間顯示
    now_local = datetime.now() + timedelta(hours=8) # 轉為台灣時間 UTC+8
    now_str = now_local.strftime("%Y-%m-%d %H:%M")
    
    import json
    news_json = json.dumps(all_news, ensure_ascii=False)

    html_template = f"""
    <!DOCTYPE html>
    <html lang="zh-Hant">
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>EcoNews 24H | 環境能源摘錄</title>
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/water.css@2/out/water.css">
        <style>
            :root {{ --main-color: #2e7d32; --bg: #f0f4f0; }}
            body {{ max-width: 1200px; background: var(--bg); font-family: "PingFang TC", sans-serif; }}
            header {{ text-align: center; padding: 40px 20px; background: white; border-radius: 0 0 20px 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.05); }}
            h1 {{ color: var(--main-color); margin: 0; font-size: 2.5em; }}
            .update-time {{ color: #666; font-size: 0.9em; margin-top: 10px; }}
            
            .nav-tabs {{ display: flex; justify-content: center; gap: 15px; margin: 30px 0; }}
            .nav-tabs button {{ background: #fff; color: #444; border: 1px solid #ddd; padding: 10px 25px; cursor: pointer; border-radius: 30px; font-weight: bold; transition: 0.2s; }}
            .nav-tabs button.active {{ background: var(--main-color); color: white; border-color: var(--main-color); }}

            .news-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 25px; }}
            .news-card {{ background: white; padding: 25px; border-radius: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.03); display: flex; flex-direction: column; border: 1px solid #eee; }}
            .news-card h3 {{ font-size: 1.15em; margin: 0 0 15px; color: #111; line-height: 1.5; min-height: 3em; }}
            .news-card p {{ font-size: 0.95em; color: #555; line-height: 1.7; flex-grow: 1; margin-bottom: 20px; }}
            
            .card-footer {{ display: flex; justify-content: space-between; align-items: center; padding-top: 15px; border-top: 1px solid #f0f0f0; }}
            .read-link {{ font-weight: bold; color: var(--main-color); text-decoration: none; }}
            .save-btn {{ background: #e8f5e9; color: #2e7d32; border: none; padding: 6px 12px; border-radius: 6px; cursor: pointer; font-size: 0.85em; }}
            .save-btn:hover {{ background: #c8e6c9; }}
            
            #page-fav .tag-badge {{ background: #fff3e0; color: #e65100; font-size: 0.75em; padding: 2px 8px; border-radius: 10px; margin-left: 8px; }}
            .hidden {{ display: none !important; }}
            footer {{ text-align: center; padding: 50px; color: #999; font-size: 0.8em; }}
        </style>
    </head>
    <body>
        <header>
            <h1>🌱 EcoNews 24H</h1>
            <p class="update-time">⏳ 聚焦 24 小時內全球環境動態 | 台灣時間：{now_str}</p>
        </header>

        <div class="nav-tabs">
            <button id="tab-all" class="active" onclick="showPage('all')">今日精選 (20)</button>
            <button id="tab-fav" onclick="showPage('fav')">個人收藏夾</button>
        </div>

        <div id="page-all" class="news-grid"></div>
        <div id="page-fav" class="news-grid hidden"></div>

        <footer>
            <p>每 12 小時自動更新一次。資料來源：中央社、公視、科技新報、RFI等。</p>
        </footer>

        <script>
            const newsData = {news_json};
            let favorites = JSON.parse(localStorage.getItem('eco_favs_v2')) || [];

            function renderNews() {{
                const container = document.getElementById('page-all');
                container.innerHTML = newsData.map((item, idx) => `
                    <div class="news-card">
                        <h3>${{item.title}}</h3>
                        <p>${{item.desc}}</p>
                        <div class="card-footer">
                            <a href="${{item.link}}" target="_blank" class="read-link">閱讀原文 ↗</a>
                            <button onclick="saveItem(${{idx}})" class="save-btn">⭐ 收藏</button>
                        </div>
                    </div>
                `).join('');
            }}

            function renderFavorites() {{
                const container = document.getElementById('page-fav');
                if (favorites.length === 0) {{
                    container.innerHTML = "<p style='grid-column: 1/-1; text-align: center; padding: 50px;'>尚未收藏任何文章。</p>";
                    return;
                }}
                container.innerHTML = favorites.map((item, idx) => `
                    <div class="news-card">
                        <h3>${{item.title}}<span class="tag-badge">${{item.tag}}</span></h3>
                        <p>${{item.desc}}</p>
                        <div class="card-footer">
                            <a href="${{item.link}}" target="_blank" class="read-link">查看</a>
                            <button onclick="deleteItem(${{idx}})" style="background:#ffebee; color:#c62828; border:none; padding:5px 10px; border-radius:6px; cursor:pointer;">移除</button>
                        </div>
                    </div>
                `).join('');
            }}

            function saveItem(idx) {{
                const item = newsData[idx];
                const tag = prompt("請輸入分類標籤（如：能源、氣候、重要）：", "預設");
                if (tag) {{
                    favorites.push({{ ...item, tag, favDate: new Date().toLocaleString() }});
                    localStorage.setItem('eco_favs_v2', JSON.stringify(favorites));
                    alert("已儲存至本地收藏分頁！");
                    
                    // 同步到 GitHub Issues
                    const repoOwner = window.location.hostname.split('.')[0];
                    const repoName = window.location.pathname.split('/')[1] || "eco-news-daily";
                    const issueBody = "### 🍀 收藏紀錄\\n- 標題: " + item.title + "\\n- 連結: " + item.link;
                    window.open(`https://github.com/${{repoOwner}}/${{repoName}}/issues/new?title=${{encodeURIComponent("[收藏] " + item.title)}}&body=${{encodeURIComponent(issueBody)}}&labels=${{encodeURIComponent(tag)}}`, '_blank');
                }}
            }}

            function deleteItem(idx) {{
                if (confirm("確定移除此收藏？")) {{
                    favorites.splice(idx, 1);
                    localStorage.setItem('eco_favs_v2', JSON.stringify(favorites));
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
