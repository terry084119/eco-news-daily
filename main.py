import feedparser
import google.generativeai as genai
import os
from datetime import datetime, timedelta, timezone
import json

# 1. AI 模型設定 (具備二次過濾邏輯)
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

# 2. 來源權重調整
RSS_SOURCES = [
    "https://www.cna.com.tw/rss/aall.aspx",         # 中央社
    "https://news.pts.org.tw/xml/newsfeed.xml",     # 公視
    "https://money.udn.com/rssfeed/news/1001/5588/10511?ch=money", # 經濟日報
    "https://technews.tw/category/sharingeconomy/feed/", # 科技新報
    "https://www.rfi.fr/tw/rss",                   # 法廣
    "https://tchina.kyodonews.net/rss/news.xml"     # 共同社
]

KEYWORDS = ["循環經濟", "再生能源", "碳盤查", "碳足跡", "綠色供應鏈", "淨零排放", "再生料", "氣候變遷", "能源轉型", "環境政策", "永續發展", "ESG", "電價", "產品護照"]

def ai_process(title, content):
    if not model: return content[:100]
    prompt = f"""你是個專業環境新聞編輯。分析以下內容：
    標題：{title}
    內容：{content}
    任務：判斷是否為「環境政策變動、國際環境趨勢、氣候、能源重大議題」？
    如果是，請提供50字專業摘要並對關鍵點進行【重點標註】。
    如果無關，請回傳「SKIP」。"""
    try:
        res = model.generate_content(prompt).text.strip()
        return None if "SKIP" in res.upper() else res
    except: return None

def fetch_news():
    news_list = []
    seen = set()
    now = datetime.now(timezone.utc)
    day_ago = now - timedelta(hours=24)
    for url in RSS_SOURCES:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries:
                pub_time = None
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    pub_time = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
                if pub_time and pub_time < day_ago: continue
                
                title = entry.title
                link = entry.link
                desc = getattr(entry, 'summary', '') or getattr(entry, 'description', '')
                if any(k in (title + desc) for k in KEYWORDS) and link not in seen:
                    summary = ai_process(title, desc[:400])
                    if summary:
                        news_list.append({{"title": title, "link": link, "summary": summary}})
                        seen.add(link)
                if len(news_list) >= 20: break
        except: continue
    return news_list

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
        <title>EcoNews 專業編輯版</title>
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/water.css@2/out/water.css">
        <style>
            :root {{ --main: #2e7d32; --bg: #f5f7f5; }}
            body {{ max-width: 1200px; background: var(--bg); }}
            header {{ text-align: center; padding: 30px; background: white; border-radius: 0 0 20px 20px; }}
            .nav-tabs {{ display: flex; justify-content: center; gap: 10px; margin: 25px 0; }}
            .nav-tabs button {{ background: #fff; border: 1px solid #ddd; padding: 8px 20px; border-radius: 20px; cursor: pointer; }}
            .nav-tabs button.active {{ background: var(--main); color: white; border-color: var(--main); }}
            
            .news-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 20px; }}
            .news-card {{ background: white; padding: 20px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.02); display: flex; flex-direction: column; border: 1px solid #eee; }}
            .news-card h3 {{ font-size: 1.1em; line-height: 1.4; margin-bottom: 12px; }}
            .news-card p {{ font-size: 0.95em; color: #444; flex-grow: 1; }}
            .card-footer {{ display: flex; justify-content: space-between; border-top: 1px solid #eee; padding-top: 12px; }}
            
            /* 收藏頁專用樣式 */
            .folder-section {{ background: white; margin-bottom: 20px; border-radius: 10px; border: 1px solid #ddd; }}
            .folder-header {{ padding: 15px 20px; background: #e8f5e9; cursor: pointer; font-weight: bold; display: flex; justify-content: space-between; }}
            .folder-content {{ padding: 15px; display: none; }}
            .folder-content.open {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 15px; }}
            .tag-pill {{ background: #e0e0e0; font-size: 0.75em; padding: 2px 8px; border-radius: 10px; margin-right: 5px; }}
            .hidden {{ display: none !important; }}
        </style>
    </head>
    <body>
        <header>
            <h1>🌱 EcoNews 環境精選</h1>
            <p>最後更新：{now_str} (每12小時由 AI 編輯更新)</p>
        </header>

        <div class="nav-tabs">
            <button id="tab-all" class="active" onclick="showPage('all')">今日重點</button>
            <button id="tab-fav" onclick="showPage('fav')">分類資料夾</button>
        </div>

        <div id="page-all" class="news-grid"></div>
        <div id="page-fav" class="hidden">
            </div>

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
                            <a href="${{item.link}}" target="_blank">閱讀原文 ↗</a>
                            <button onclick="saveItem(${{idx}})" style="background:#e8f5e9; color:#2e7d32; border:none; padding:4px 10px; border-radius:6px; cursor:pointer;">⭐ 收藏</button>
                        </div>
                    </div>
                `).join('');
            }}

            function saveItem(idx) {{
                const item = newsData[idx];
                const tagInput = prompt("請輸入分類標籤（多個標籤請用逗號隔開）：", "政策,氣候");
                if (tagInput) {{
                    const tags = tagInput.split(',').map(t => t.trim()).filter(t => t !== "");
                    favorites.push({{ ...item, tags }});
                    localStorage.setItem('eco_favs_v3', JSON.stringify(favorites));
                    alert("已儲存！");
                    
                    // 同步到 GitHub
                    const repoOwner = window.location.hostname.split('.')[0];
                    const repoName = window.location.pathname.split('/')[1] || "eco-news-daily";
                    window.open(`https://github.com/${{repoOwner}}/${{repoName}}/issues/new?title=${{encodeURIComponent("[收藏] "+item.title)}}&body=${{encodeURIComponent(item.link)}}&labels=${{encodeURIComponent(tags.join(','))}}`, '_blank');
                }}
            }}

            function renderFolders() {{
                const container = document.getElementById('page-fav');
                container.innerHTML = "";
                
                // 1. 提取所有不重複標籤
                const allTags = new Set();
                favorites.forEach(f => f.tags.forEach(t => allTags.add(t)));
                
                if (allTags.size === 0) {{
                    container.innerHTML = "<p style='text-align:center;'>尚未有分類。請在收藏時輸入標籤！</p>";
                    return;
                }}

                // 2. 依照標籤建立資料夾
                Array.from(allTags).sort().forEach(tag => {{
                    const folder = document.createElement('div');
                    folder.className = 'folder-section';
                    
                    const filteredNews = favorites.filter(f => f.tags.includes(tag));
                    
                    folder.innerHTML = `
                        <div class="folder-header" onclick="this.nextElementSibling.classList.toggle('open')">
                            <span>📁 ${{tag}} (${{filteredNews.length}})</span>
                            <span>展開/收合</span>
                        </div>
                        <div class="folder-content">
                            ${{filteredNews.map((n, i) => `
                                <div class="news-card">
                                    <h4>${{n.title}}</h4>
                                    <div class="card-footer">
                                        <a href="${{n.link}}" target="_blank">原文</a>
                                        <button onclick="deleteItem(${{favorites.indexOf(n)}})" style="background:#fff1f1; color:red; border:none; padding:2px 8px; border-radius:4px;">移除</button>
                                    </div>
                                </div>
                            `).join('')}}
                        </div>
                    `;
                    container.appendChild(folder);
                }});
            }}

            function deleteItem(globalIdx) {{
                if (confirm("移除此收藏？")) {{
                    favorites.splice(globalIdx, 1);
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
