import feedparser
import google.generativeai as genai
import os
from datetime import datetime, timedelta, timezone
import json

# 1. AI 設定
api_key = os.environ.get("GEMINI_API_KEY")
genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-1.5-flash')

# 2. 來源設定 (增加來源以確保產量)
RSS_SOURCES = [
    "https://www.cna.com.tw/rss/aall.aspx",         # 中央社
    "https://news.pts.org.tw/xml/newsfeed.xml",     # 公視
    "https://money.udn.com/rssfeed/news/1001/5591/10511?ch=money", # 經濟日報
    "https://money.udn.com/rssfeed/news/1001/5588/10511?ch=money", # 經濟日報-產業
    "https://technews.tw/category/sharingeconomy/feed/", # 科技新報
    "https://www.rfi.fr/tw/rss",                   # 法廣
    "https://tchina.kyodonews.net/rss/news.xml",    # 共同社
    "https://e-info.org.tw/rss.xml"                # 環境資訊中心 (作為補充源)
]

# 擴充關鍵字，增加覆蓋率
KEYWORDS = [
    "循環經濟", "再生能源", "碳盤查", "碳足跡", "減碳", "淨零", "再生料", "氣候", 
    "能源", "永續", "ESG", "電價", "產品護照", "環境", "電力", "節能", "塑膠", 
    "海廢", "生態", "污染", "綠能", "光電", "風電", "核能", "水利", "回收"
]

def get_professional_summary(title, content):
    """AI 只負責翻譯與縮減，不負責過濾"""
    prompt = f"""你是專業環境編輯。請為以下新聞提供 50 字內的繁體中文摘要，並重點標註關鍵數據或政策變動：
    標題：{title}
    內容：{content}"""
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except:
        # AI 失敗時的備案：直接擷取前 120 字
        return content[:120].replace('<p>', '').replace('</p>', '') + "..."

def fetch_news():
    news_list = []
    seen = set()
    now = datetime.now(timezone.utc)
    day_ago = now - timedelta(hours=24)
    
    print(f"🚀 開始抓取 (目標 30 則)")

    for url in RSS_SOURCES:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries:
                # 時間過濾 (24小時)
                pub_time = None
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    pub_time = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
                
                if pub_time and pub_time < day_ago: 
                    continue
                
                title = entry.title
                link = entry.link
                desc = getattr(entry, 'summary', '') or getattr(entry, 'description', '')
                
                # 只要符合關鍵字且沒重複，就直接收錄
                if any(k in (title + desc) for k in KEYWORDS) and link not in seen:
                    print(f"📌 收錄: {title}")
                    # 進行 AI 摘要
                    summary = get_professional_summary(title, desc[:500])
                    news_list.append({"title": title, "link": link, "summary": summary})
                    seen.add(link)
                
                if len(news_list) >= 30: break # 目標 30 則
        except:
            continue
        if len(news_list) >= 30: break
            
    return news_list

def main():
    all_news = fetch_news()
    now_str = (datetime.now() + timedelta(hours=8)).strftime("%Y-%m-%d %H:%M")
    news_json = json.dumps(all_news, ensure_ascii=False)

    # HTML 保持原本的多標籤分類收藏功能
    html_template = f"""
    <!DOCTYPE html>
    <html lang="zh-Hant">
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>EcoNews 30 | 環境能源摘要</title>
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/water.css@2/out/water.css">
        <style>
            :root {{ --main: #2e7d32; --bg: #f0f2f0; }}
            body {{ max-width: 1200px; background: var(--bg); font-family: "PingFang TC", sans-serif; }}
            header {{ text-align: center; padding: 40px 20px; background: white; border-bottom: 5px solid var(--main); border-radius: 0 0 15px 15px; }}
            .nav-tabs {{ display: flex; justify-content: center; gap: 10px; margin: 25px 0; }}
            .nav-tabs button {{ background: #fff; border: 1px solid #ddd; padding: 8px 20px; border-radius: 20px; cursor: pointer; font-weight: bold; }}
            .nav-tabs button.active {{ background: var(--main); color: white; border-color: var(--main); }}
            .news-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 20px; }}
            .news-card {{ background: white; padding: 25px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.02); display: flex; flex-direction: column; border: 1px solid #eee; }}
            .news-card h3 {{ font-size: 1.1em; line-height: 1.4; margin-bottom: 12px; }}
            .news-card p {{ font-size: 0.95em; color: #444; flex-grow: 1; }}
            .card-footer {{ display: flex; justify-content: space-between; border-top: 1px solid #eee; padding-top: 12px; }}
            .save-btn {{ background: #e8f5e9; color: var(--main); border: none; padding: 4px 10px; border-radius: 6px; cursor: pointer; }}
            .folder-section {{ background: white; margin-bottom: 15px; border-radius: 10px; border: 1px solid #ddd; overflow: hidden; }}
            .folder-header {{ padding: 15px 20px; background: #fff; cursor: pointer; font-weight: bold; display: flex; justify-content: space-between; }}
            .folder-content {{ padding: 15px; display: none; background: #fafafa; }}
            .folder-content.open {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 15px; }}
            .hidden {{ display: none !important; }}
        </style>
    </head>
    <body>
        <header>
            <h1>🌱 EcoNews 每日摘要</h1>
            <p>24H 關鍵字全收錄 (目標 30 則) | 更新時間：{now_str}</p>
        </header>

        <div class="nav-tabs">
            <button id="tab-all" class="active" onclick="showPage('all')">最新動態</button>
            <button id="tab-fav" onclick="showPage('fav')">分類資料夾</button>
        </div>

        <div id="page-all" class="news-grid"></div>
        <div id="page-fav" class="hidden"></div>

        <script>
            const newsData = {news_json};
            let favorites = JSON.parse(localStorage.getItem('eco_favs_v3')) || [];

            function renderNews() {{
                const container = document.getElementById('page-all');
                container.innerHTML = newsData.map((item, idx) => `
                    <div class="news-card">
                        <h3>${{item.title}}</h3>
                        <p>${{item.summary}}</p>
                        <div class="card-footer">
                            <a href="${{item.link}}" target="_blank">原文 ↗</a>
                            <button onclick="saveItem(${{idx}})" class="save-btn">⭐ 收藏</button>
                        </div>
                    </div>
                `).join('');
            }}

            function saveItem(idx) {{
                const item = newsData[idx];
                const tagInput = prompt("請輸入分類（多個標籤請用逗號隔開）：", "未分類");
                if (tagInput) {{
                    const tags = tagInput.split(/[,，]/).map(t => t.trim()).filter(t => t !== "");
                    favorites.push({{ ...item, tags }});
                    localStorage.setItem('eco_favs_v3', JSON.stringify(favorites));
                    alert("收藏成功！");
                }}
            }}

            function renderFolders() {{
                const container = document.getElementById('page-fav');
                container.innerHTML = "";
                const allTags = new Set();
                favorites.forEach(f => f.tags.forEach(t => allTags.add(t)));
                
                if (allTags.size === 0) {{
                    container.innerHTML = "<p style='text-align:center;'>目前沒有收藏。</p>";
                    return;
                }}

                Array.from(allTags).sort().forEach(tag => {{
                    const folder = document.createElement('div');
                    folder.className = 'folder-section';
                    const filtered = favorites.filter(f => f.tags.includes(tag));
                    folder.innerHTML = `
                        <div class="folder-header" onclick="this.nextElementSibling.classList.toggle('open')">
                            <span>📁 ${{tag}} (${{filtered.length}})</span>
                            <span>展開/收合</span>
                        </div>
                        <div class="folder-content">
                            ${{filtered.map((n, i) => `
                                <div class="news-card">
                                    <h4>${{n.title}}</h4>
                                    <div class="card-footer">
                                        <a href="${{n.link}}" target="_blank">連結</a>
                                        <button onclick="deleteItem(${{favorites.indexOf(n)}})" style="background:none; color:red; border:none; cursor:pointer;">移除</button>
                                    </div>
                                </div>
                            `).join('')}}
                        </div>
                    `;
                    container.appendChild(folder);
                }});
            }}

            function deleteItem(idx) {{
                if (confirm("確定移除？")) {{
                    favorites.splice(idx, 1);
                    localStorage.setItem('eco_favs_v3', JSON.stringify(favorites));
                    renderFolders();
                }}
            }}

            function showPage(page) {{
                document.getElementById('page-all').classList.toggle('hidden', page !== 'all');
                document.getElementById('page-fav').classList.toggle('hidden', page !== 'fav');
                document.getElementById('tab-all').classList.toggle('active', page === 'all');
                document.getElementById('tab-fav').classList.toggle('active', page === 'fav');
                if (page === 'fav') renderFolders();
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
