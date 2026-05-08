import feedparser
import google.generativeai as genai
import os
from datetime import datetime, timedelta, timezone
import json

# 1. AI 模型設定
api_key = os.environ.get("GEMINI_API_KEY")
genai.configure(api_key=api_key)

def get_ai_model():
    for name in ['gemini-1.5-flash', 'gemini-pro']:
        try:
            m = genai.GenerativeModel(name)
            m.generate_content("test")
            print(f"✅ 成功啟動 AI 模型: {name}")
            return m
        except: continue
    return None

model = get_ai_model()

# 2. 來源設定 (調整權重順序)
RSS_SOURCES = [
    "https://www.cna.com.tw/rss/aall.aspx",         # 中央社
    "https://news.pts.org.tw/xml/newsfeed.xml",     # 公視
    "https://money.udn.com/rssfeed/news/1001/5591/10511?ch=money", # 經濟日報 (能源/產業)
    "https://technews.tw/category/sharingeconomy/feed/", # 科技新報 (綠色科技)
    "https://www.rfi.fr/tw/rss",                   # 法廣
    "https://tchina.kyodonews.net/rss/news.xml"     # 共同社
]

KEYWORDS = ["循環經濟", "再生能源", "碳盤查", "碳足跡", "綠色供應鏈", "淨零排放", "再生料", "氣候變遷", "能源轉型", "環境政策", "永續發展", "ESG", "電價", "產品護照", "環境", "氣候", "電力", "節能"]

def ai_process(title, content):
    if not model: 
        return content[:150] + "..." # 若 AI 故障則回傳原始內容片段
    
    # 放寬標準的 Prompt
    prompt = f"""你是專業環境編輯。
    請分析：標題「{title}」，內容「{content}」。
    
    任務：
    1. 只要這則新聞與「環境、氣候、能源、永續、減碳、循環經濟、環保、電費、污染、生態」中任何一項有微弱關聯，就請提供 50 字專業摘要。
    2. 請在摘要中對關鍵政策、數據或趨勢進行【重點標註】。
    3. 只有在內容完全無關（如娛樂、社會犯罪、體育、藝人）時才回傳「SKIP」。"""
    
    try:
        response = model.generate_content(prompt)
        res_text = response.text.strip()
        if "SKIP" in res_text.upper() and len(res_text) < 10:
            return None
        return res_text
    except Exception as e:
        print(f"⚠️ AI 處理失敗: {e}")
        return content[:150] + "..."

def fetch_news():
    news_list = []
    seen = set()
    now = datetime.now(timezone.utc)
    day_ago = now - timedelta(hours=24)
    
    print(f"🚀 開始抓取新聞 (基準時間: {day_ago})")

    for url in RSS_SOURCES:
        try:
            feed = feedparser.parse(url)
            print(f"🔍 掃描來源: {url} (發現 {len(feed.entries)} 則)")
            for entry in feed.entries:
                # 時間過濾
                pub_time = None
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    pub_time = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
                
                # 如果有明確發布時間且早於24小時前則跳過，否則保留(避免時間抓不到導致遺失)
                if pub_time and pub_time < day_ago: 
                    continue
                
                title = entry.title
                link = entry.link
                desc = getattr(entry, 'summary', '') or getattr(entry, 'description', '')
                
                # 初步關鍵字過濾
                if any(k in (title + desc) for k in KEYWORDS) and link not in seen:
                    print(f"📌 發現可能相關新聞: {title}")
                    summary = ai_process(title, desc[:500])
                    if summary:
                        print(f"   ✨ AI 摘要完成")
                        news_list.append({"title": title, "link": link, "summary": summary})
                        seen.add(link)
                    else:
                        print(f"   ⏭️ AI 決定 SKIP")
                
                if len(news_list) >= 25: break # 放寬到 25 則
        except Exception as e:
            print(f"❌ 來源錯誤 {url}: {e}")
            continue
        if len(news_list) >= 25: break
            
    print(f"✅ 最終收錄篇數: {len(news_list)}")
    return news_list

def main():
    all_news = fetch_news()
    now_str = (datetime.now() + timedelta(hours=8)).strftime("%Y-%m-%d %H:%M")
    news_json = json.dumps(all_news, ensure_ascii=False)

    # HTML 部分維持強大的分類收藏功能
    html_template = f"""
    <!DOCTYPE html>
    <html lang="zh-Hant">
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>EcoNews | 專業環境編輯版</title>
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/water.css@2/out/water.css">
        <style>
            :root {{ --main: #2e7d32; --bg: #f5f7f5; }}
            body {{ max-width: 1200px; background: var(--bg); font-family: "PingFang TC", sans-serif; }}
            header {{ text-align: center; padding: 40px 20px; background: white; border-bottom: 4px solid var(--main); }}
            .nav-tabs {{ display: flex; justify-content: center; gap: 15px; margin: 30px 0; }}
            .nav-tabs button {{ background: #fff; border: 1px solid #ddd; padding: 10px 25px; border-radius: 30px; cursor: pointer; font-weight: bold; }}
            .nav-tabs button.active {{ background: var(--main); color: white; border-color: var(--main); }}
            .news-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 20px; }}
            .news-card {{ background: white; padding: 25px; border-radius: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); display: flex; flex-direction: column; }}
            .news-card h3 {{ font-size: 1.15em; line-height: 1.5; margin-bottom: 12px; min-height: 3em; }}
            .card-footer {{ display: flex; justify-content: space-between; border-top: 1px solid #f0f0f0; padding-top: 15px; margin-top: auto; }}
            .save-btn {{ background: #e8f5e9; color: var(--main); border: none; padding: 6px 12px; border-radius: 6px; cursor: pointer; }}
            .folder-section {{ background: white; margin-bottom: 15px; border-radius: 10px; border: 1px solid #eee; overflow: hidden; }}
            .folder-header {{ padding: 15px 20px; background: #fff; cursor: pointer; font-weight: bold; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #eee; }}
            .folder-content {{ padding: 20px; display: none; background: #fafafa; }}
            .folder-content.open {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 15px; }}
            .hidden {{ display: none !important; }}
        </style>
    </head>
    <body>
        <header>
            <h1>🌱 EcoNews</h1>
            <p>專業環境編輯 AI 每日摘要 | 台灣時間：{now_str}</p>
        </header>

        <div class="nav-tabs">
            <button id="tab-all" class="active" onclick="showPage('all')">今日重點</button>
            <button id="tab-fav" onclick="showPage('fav')">分類資料夾</button>
        </div>

        <div id="page-all" class="news-grid"></div>
        <div id="page-fav" class="hidden"></div>

        <script>
            const newsData = {news_json};
            let favorites = JSON.parse(localStorage.getItem('eco_favs_v3')) || [];

            function renderNews() {{
                const container = document.getElementById('page-all');
                if (newsData.length === 0) {{
                    container.innerHTML = "<p style='grid-column:1/-1; text-align:center;'>今日暫無符合條件的新聞，請稍後再試。</p>";
                    return;
                }}
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
                const tagInput = prompt("請輸入分類（多個標籤請用逗號隔開）：", "政策");
                if (tagInput) {{
                    const tags = tagInput.split(/[,，]/).map(t => t.trim()).filter(t => t !== "");
                    favorites.push({{ ...item, tags, date: new Date().toLocaleDateString() }});
                    localStorage.setItem('eco_favs_v3', JSON.stringify(favorites));
                    alert("已存入資料夾！");
                }}
            }}

            function renderFolders() {{
                const container = document.getElementById('page-fav');
                container.innerHTML = "";
                const allTags = new Set();
                favorites.forEach(f => f.tags.forEach(t => allTags.add(t)));
                
                if (allTags.size === 0) {{
                    container.innerHTML = "<p style='text-align:center; padding:50px;'>尚未有收藏。收藏時輸入標籤即可自動分類。</p>";
                    return;
                }}

                Array.from(allTags).sort().forEach(tag => {{
                    const folder = document.createElement('div');
                    folder.className = 'folder-section';
                    const filtered = favorites.filter(f => f.tags.includes(tag));
                    folder.innerHTML = `
                        <div class="folder-header" onclick="this.nextElementSibling.classList.toggle('open')">
                            <span>📁 ${{tag}} (${{filtered.length}})</span>
                            <span>↕️</span>
                        </div>
                        <div class="folder-content">
                            ${{filtered.map((n, i) => `
                                <div class="news-card">
                                    <h4>${{n.title}}</h4>
                                    <div class="card-footer">
                                        <a href="${{n.link}}" target="_blank">原文</a>
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
                if (confirm("移除此收藏？")) {{
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
