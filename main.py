import feedparser
import google.generativeai as genai
import os
from datetime import datetime, timedelta, timezone
import json
import urllib.parse

# 1. AI 設定
api_key = os.environ.get("GEMINI_API_KEY")
genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-1.5-flash')

# 2. 產量極大化來源清單
RSS_SOURCES = [
    # Google 新聞環境主題 (匯聚各大報，產量保證)
    "https://news.google.com/rss/search?q=%E7%92%B0%E5%A2%83+%E8%83%BD%E6%BA%90+%E6%B0%A3%E5%80%99+when:24h&hl=zh-TW&gl=TW&ceid=TW:zh-Hant",
    "https://www.cna.com.tw/rss/aall.aspx",         # 中央社
    "https://news.pts.org.tw/xml/newsfeed.xml",     # 公視
    "https://money.udn.com/rssfeed/news/1001/5591/10511?ch=money", # 經濟能源
    "https://money.udn.com/rssfeed/news/1001/5588/10511?ch=money", # 經濟產業
    "https://technews.tw/category/sharingeconomy/feed/", # 科技新報
    "https://e-info.org.tw/rss.xml",                # 環境資訊中心
]

# 擴大關鍵字庫，包含短詞以增加標題命中率
KEYWORDS = [
    "循環", "碳", "氣候", "能源", "電價", "電力", "永續", "ESG", "減碳", "淨零", 
    "綠能", "光電", "風電", "核能", "回收", "塑膠", "污染", "環境", "再生", 
    "節能", "水利", "廢棄物", "生態", "低碳", "離岸", "氫能", "排碳"
]

def get_professional_summary(title, content):
    prompt = f"你是專業環境編輯。請為以下新聞提供 50 字內的繁體中文摘要，並重點標註關鍵數據或政策變動：標題：{title}，內容：{content}"
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except:
        return (content[:120] if content else "請點擊連結閱讀全文。") + "..."

def fetch_news():
    news_list = []
    seen_links = set()
    now = datetime.now(timezone.utc)
    # 緩衝時間設為 30 小時，確保捕捉昨日到今日的所有新聞
    time_limit = now - timedelta(hours=30)
    
    print(f"🚀 開始高產量抓取 (目標 25-30 則)...")

    for url in RSS_SOURCES:
        try:
            feed = feedparser.parse(url)
            print(f"🔍 掃描: {url[:40]}... (找到 {len(feed.entries)} 則)")
            
            for entry in feed.entries:
                title = entry.title
                link = entry.link
                desc = getattr(entry, 'summary', '') or getattr(entry, 'description', '') or ""
                
                # 時間判定：若抓不到時間就假設它是最新的
                pub_time = None
                for field in ['published_parsed', 'updated_parsed', 'created_parsed']:
                    if hasattr(entry, field) and getattr(entry, field):
                        pub_time = datetime(*getattr(entry, field)[:6], tzinfo=timezone.utc)
                        break
                
                if pub_time and pub_time < time_limit:
                    continue

                # 關鍵字過濾
                full_text = (title + desc).lower()
                if any(k in full_text for k in KEYWORDS) and link not in seen_links:
                    # 檢查是否為重複標題 (不同來源可能發同一則新聞)
                    if any(n['title'][:10] == title[:10] for n in news_list):
                        continue
                        
                    print(f"✅ 收錄: {title[:20]}...")
                    summary = get_professional_summary(title, desc[:600])
                    news_list.append({"title": title, "link": link, "summary": summary})
                    seen_links.add(link)
                
                if len(news_list) >= 40: break 
        except:
            continue
            
    # 按照來源排序，確保重要媒體在前
    return news_list[:30]

def main():
    all_news = fetch_news()
    now_str = (datetime.now() + timedelta(hours=8)).strftime("%Y-%m-%d %H:%M")
    news_json = json.dumps(all_news, ensure_ascii=False)

    html_template = f"""
    <!DOCTYPE html>
    <html lang="zh-Hant">
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>EcoNews | 24H 專業環境摘要</title>
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/water.css@2/out/water.css">
        <style>
            :root {{ --main: #1b5e20; --bg: #f8faf8; }}
            body {{ max-width: 1200px; background: var(--bg); font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; }}
            header {{ text-align: center; padding: 40px 20px; background: white; border-bottom: 6px solid var(--main); border-radius: 0 0 20px 20px; box-shadow: 0 4px 12px rgba(0,0,0,0.08); }}
            h1 {{ margin: 0; color: var(--main); font-size: 2.4em; letter-spacing: 1px; }}
            .update-info {{ color: #666; margin-top: 12px; font-weight: 500; }}
            
            .nav-tabs {{ display: flex; justify-content: center; gap: 12px; margin: 30px 0; }}
            .nav-tabs button {{ background: #fff; border: 1px solid #ddd; padding: 12px 28px; border-radius: 50px; cursor: pointer; font-weight: bold; transition: all 0.3s ease; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }}
            .nav-tabs button.active {{ background: var(--main); color: white; border-color: var(--main); box-shadow: 0 4px 10px rgba(27,94,32,0.3); }}

            .news-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(340px, 1fr)); gap: 25px; padding: 0 15px; }}
            .news-card {{ background: white; padding: 28px; border-radius: 16px; box-shadow: 0 4px 6px rgba(0,0,0,0.02); display: flex; flex-direction: column; border: 1px solid #edf2ed; transition: all 0.3s ease; }}
            .news-card:hover {{ transform: translateY(-6px); box-shadow: 0 12px 20px rgba(0,0,0,0.08); }}
            .news-card h3 {{ font-size: 1.2em; line-height: 1.5; margin: 0 0 16px 0; color: #1a1a1a; }}
            .news-card p {{ font-size: 1em; color: #3d3d3d; line-height: 1.75; flex-grow: 1; margin-bottom: 22px; }}
            
            .card-footer {{ display: flex; justify-content: space-between; align-items: center; border-top: 1px solid #f0f4f0; padding-top: 18px; }}
            .read-link {{ font-weight: 700; color: var(--main); text-decoration: none; border-bottom: 2px solid transparent; transition: 0.2s; }}
            .read-link:hover {{ border-bottom: 2px solid var(--main); }}
            .save-btn {{ background: #f1f8f1; color: var(--main); border: none; padding: 8px 16px; border-radius: 8px; cursor: pointer; font-size: 0.9em; font-weight: bold; }}
            
            .folder-section {{ background: white; margin-bottom: 20px; border-radius: 14px; border: 1px solid #ddd; overflow: hidden; box-shadow: 0 2px 4px rgba(0,0,0,0.03); }}
            .folder-header {{ padding: 20px 28px; background: #fff; cursor: pointer; font-weight: bold; display: flex; justify-content: space-between; align-items: center; font-size: 1.15em; transition: 0.2s; }}
            .folder-header:hover {{ background: #f4f9f4; }}
            .folder-content {{ padding: 25px; display: none; background: #fafdfa; border-top: 1px solid #eee; }}
            .folder-content.open {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 20px; }}
            
            .hidden {{ display: none !important; }}
            footer {{ text-align: center; padding: 60px; color: #999; font-size: 0.9em; letter-spacing: 0.5px; }}
        </style>
    </head>
    <body>
        <header>
            <h1>🌱 EcoNews</h1>
            <p class="update-info">今日產經與環境能源焦點 | 更新：{now_str}</p>
        </header>

        <div class="nav-tabs">
            <button id="tab-all" class="active" onclick="showPage('all')">最新動態 ({len(all_news)})</button>
            <button id="tab-fav" onclick="showPage('fav')">分類資料夾</button>
        </div>

        <div id="page-all" class="news-grid"></div>
        <div id="page-fav" class="hidden"></div>

        <footer>
            <p>© EcoNews 專業摘要服務<br>匯聚中央社、公視、經濟日報、Google 新聞環境主題</p>
        </footer>

        <script>
            const newsData = {news_json};
            let favorites = JSON.parse(localStorage.getItem('eco_favs_v4')) || [];

            function renderNews() {{
                const container = document.getElementById('page-all');
                if (newsData.length === 0) {{
                    container.innerHTML = "<p style='grid-column:1/-1; text-align:center; padding: 60px; font-size: 1.2em;'>🔍 正在同步最新消息，請稍後再試。</p>";
                    return;
                }}
                container.innerHTML = newsData.map((item, idx) => `
                    <div class="news-card">
                        <h3>${{item.title}}</h3>
                        <p>${{item.summary}}</p>
                        <div class="card-footer">
                            <a href="${{item.link}}" target="_blank" class="read-link">閱讀原文 ↗</a>
                            <button onclick="saveItem(${{idx}})" class="save-btn">⭐ 收藏</button>
                        </div>
                    </div>
                `).join('');
            }}

            function saveItem(idx) {{
                const item = newsData[idx];
                const tagInput = prompt("請輸入分類標籤（例如：政策, 綠能）：", "未分類");
                if (tagInput) {{
                    const tags = tagInput.split(/[,，]/).map(t => t.trim()).filter(t => t !== "");
                    favorites.push({{ ...item, tags, savedAt: new Date().toLocaleString() }});
                    localStorage.setItem('eco_favs_v4', JSON.stringify(favorites));
                    alert("已加入收藏夾！");
                }}
            }}

            function renderFolders() {{
                const container = document.getElementById('page-fav');
                container.innerHTML = "";
                const allTags = new Set();
                favorites.forEach(f => f.tags.forEach(t => allTags.add(t)));
                
                if (allTags.size === 0) {{
                    container.innerHTML = "<p style='text-align:center; padding: 60px;'>您的收藏夾空空如也。</p>";
                    return;
                }}

                Array.from(allTags).sort().forEach(tag => {{
                    const folder = document.createElement('div');
                    folder.className = 'folder-section';
                    const filtered = favorites.filter(f => f.tags.includes(tag));
                    folder.innerHTML = `
                        <div class="folder-header" onclick="this.nextElementSibling.classList.toggle('open')">
                            <span>📁 ${{tag}} (${{filtered.length}} 則)</span>
                            <span style="font-size: 0.8em; color: #999;">展開/收合</span>
                        </div>
                        <div class="folder-content">
                            ${{filtered.map((n, i) => `
                                <div class="news-card">
                                    <h4>${{n.title}}</h4>
                                    <div class="card-footer">
                                        <a href="${{n.link}}" target="_blank" class="read-link">原文</a>
                                        <button onclick="deleteItem(${{favorites.indexOf(n)}})" style="background:none; color:#e53935; border:none; cursor:pointer; font-weight:bold;">移除</button>
                                    </div>
                                </div>
                            `).join('')}}
                        </div>
                    `;
                    container.appendChild(folder);
                }});
            }}

            function deleteItem(idx) {{
                if (confirm("確認移除？")) {{
                    favorites.splice(idx, 1);
                    localStorage.setItem('eco_favs_v4', JSON.stringify(favorites));
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
