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

# 2. 新聞來源分類
SOURCES_TW = [
    "https://www.cna.com.tw/rss/aall.aspx",         # 中央社
    "https://news.pts.org.tw/xml/newsfeed.xml",     # 公視
    "https://technews.tw/feed/",                   # 科技新報
    "https://e-info.org.tw/rss.xml"                # 環境資訊中心
]
SOURCES_INT = [
    "https://www.rfi.fr/tw/rss",                   # 法廣
    "https://tchina.kyodonews.net/rss/news.xml",    # 共同社
    "https://feeds.feedburner.com/EnvironmentalNewsNetwork" # ENN
]

KEYWORDS = ["環境", "碳排放", "減碳", "永續", "氣候", "生態", "開發", "野生動物", "循環", "動物", "能源", "電力", "核能", "太陽能", "地熱", "水力發電", "風力發電", "減塑", "海廢"]

def fetch_and_process(urls, limit=15):
    processed = []
    seen = set()
    for url in urls:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries:
                title = entry.title
                link = entry.link
                desc = getattr(entry, 'summary', '') or getattr(entry, 'description', '')
                if any(k in title or k in desc for k in KEYWORDS) and link not in seen:
                    fallback = desc.replace('<p>', '').replace('</p>', '')[:100] + "..."
                    processed.append({"title": title, "link": link, "fallback": fallback})
                    seen.add(link)
        except: continue
    return processed[:limit]

def generate_card_html(news_data, section_id):
    html = ""
    for idx, item in enumerate(news_data):
        summary = ""
        if model:
            try:
                prompt = f"摘要這則新聞（30字內）：{item['title']} {item['fallback']}"
                summary = model.generate_content(prompt).text.strip()
            except: summary = item['fallback']
        else: summary = item['fallback']
        
        # 這裡的 idx 加上 section_id 避免 JS 衝突
        unique_idx = f"{section_id}_{idx}"
        html += f"""
        <div class="news-card" data-title="{item['title']}" data-link="{item['link']}">
            <h3>{item['title']}</h3>
            <p>{summary}</p>
            <div class="card-footer">
                <a href="{item['link']}" target="_blank" class="read-more">閱讀全文</a>
                <button onclick="saveToCloud('{unique_idx}')" class="save-btn">⭐ 收藏</button>
            </div>
        </div>
        """
    return html

def main():
    tw_news = fetch_and_process(SOURCES_TW, 12)
    int_news = fetch_and_process(SOURCES_INT, 12)
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    tw_html = generate_card_html(tw_news, "TW")
    int_html = generate_card_html(int_news, "INT")

    html_template = f"""
    <!DOCTYPE html>
    <html lang="zh-Hant">
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>EcoNews | 環境新聞摘要</title>
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/water.css@2/out/water.css">
        <style>
            :root {{ --main-green: #2e7d32; --accent: #f57f17; }}
            body {{ max-width: 1200px; background-color: #f5f7f5; }}
            header {{ text-align: center; padding: 30px; background: white; border-radius: 15px; margin-bottom: 20px; }}
            h1 {{ color: var(--main-green); font-size: 2.5em; }}
            
            h2 {{ border-left: 8px solid var(--main-green); padding-left: 15px; margin: 40px 0 20px; color: #333; }}
            
            /* 關鍵：網格佈局 */
            .news-grid {{ 
                display: grid; 
                grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); 
                gap: 20px; 
            }}
            
            .news-card {{ 
                background: white; padding: 20px; border-radius: 12px; 
                display: flex; flex-direction: column; justify-content: space-between;
                box-shadow: 0 2px 8px rgba(0,0,0,0.06); height: 100%;
            }}
            .news-card h3 {{ font-size: 1.15em; margin-bottom: 10px; line-height: 1.4; color: #111; }}
            .news-card p {{ font-size: 0.95em; color: #555; line-height: 1.6; flex-grow: 1; }}
            
            .card-footer {{ display: flex; justify-content: space-between; align-items: center; padding-top: 15px; border-top: 1px solid #eee; }}
            .read-more {{ font-size: 0.9em; font-weight: bold; color: var(--main-green); text-decoration: none; }}
            .save-btn {{ background: #fff8e1; color: var(--accent); border: 1px solid #ffe082; padding: 4px 10px; border-radius: 6px; font-size: 0.85em; cursor: pointer; }}
            
            footer {{ text-align: center; margin-top: 50px; padding: 20px; color: #888; }}

            @media (max-width: 600px) {{
                .news-grid {{ grid-template-columns: 1fr; }}
            }}
        </style>
    </head>
    <body>
        <header>
            <h1>🌱 EcoNews 環境全球報</h1>
            <p>自動化搜集關鍵字：環境、能源、永續 | 更新時間：{now_str}</p>
        </header>

        <h2>📍 台灣環境新聞</h2>
        <div class="news-grid">{tw_html}</div>

        <h2>🌐 國際環境視角</h2>
        <div class="news-grid">{int_html}</div>

        <footer>
            <p>© {datetime.now().year} 由 Gemini AI 與 GitHub Actions 自動驅動</p>
        </footer>

        <script>
            function saveToCloud(id) {{
                const card = document.querySelectorAll('.news-card')[parseInt(id.split('_')[1]) + (id.split('_')[0] === 'INT' ? {len(tw_news)} : 0)];
                const title = card.getAttribute('data-title');
                const link = card.getAttribute('data-link');
                const tag = prompt("請輸入標籤：", id.split('_')[0] === 'TW' ? "台灣" : "國際");
                if (tag) {{
                    const repoOwner = window.location.hostname.split('.')[0];
                    const repoName = window.location.pathname.split('/')[1] || "eco-news-daily";
                    const issueTitle = encodeURIComponent("[收藏] " + title);
                    const issueBody = encodeURIComponent("### 🍀 收藏內容\\n**標題**： " + title + "\\n**來源**： " + (id.split('_')[0] === 'TW' ? "台灣" : "國際") + "\\n**連結**： " + link);
                    window.open(`https://github.com/${{repoOwner}}/${{repoName}}/issues/new?title=${{issueTitle}}&body=${{issueBody}}&labels=${{encodeURIComponent(tag)}}`, '_blank');
                }}
            }}
        </script>
    </body>
    </html>
    """
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_template)

if __name__ == "__main__":
    main()
