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

# 2. 定義新聞源（混合所有來源，由程式後續判斷內容分類）
ALL_SOURCES = [
    "https://www.cna.com.tw/rss/aall.aspx",         # 中央社
    "https://news.pts.org.tw/xml/newsfeed.xml",     # 公視
    "https://technews.tw/feed/",                   # 科技新報
    "https://www.rfi.fr/tw/rss",                   # 法廣
    "https://tchina.kyodonews.net/rss/news.xml",    # 共同社
    "https://e-info.org.tw/rss.xml",                # 環境資訊中心
    "https://feeds.feedburner.com/EnvironmentalNewsNetwork" # ENN
]

# 環境與能源相關關鍵字
KEYWORDS = ["環境", "碳排放", "減碳", "永續", "氣候", "生態", "開發", "野生動物", "循環", "動物", "能源", "電力", "核能", "太陽能", "地熱", "水力發電", "風力發電", "減塑", "海廢"]

# 台灣相關特徵詞 (用於輔助分類)
TW_KEYWORDS = ["台灣", "台北", "台中", "台南", "高雄", "台電", "中油", "環保署", "環境部", "行政院", "經濟部"]

def fetch_and_classify():
    tw_list = []
    int_list = []
    seen = set()

    for url in ALL_SOURCES:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries:
                title = entry.title
                link = entry.link
                desc = getattr(entry, 'summary', '') or getattr(entry, 'description', '')
                full_text = title + desc

                # 先判斷是否符合環境/能源關鍵字
                if any(k in full_text for k in KEYWORDS) and link not in seen:
                    news_item = {
                        "title": title,
                        "link": link,
                        "fallback": desc.replace('<p>', '').replace('</p>', '')[:100] + "..."
                    }
                    
                    # 分類邏輯：如果標題或內容提到台灣關鍵字，歸類為台灣；其餘歸類為國際
                    # 法廣、共同社、ENN 預設優先歸類為國際
                    is_int_source = any(domain in link for domain in ["rfi.fr", "kyodonews", "feedburner"])
                    has_tw_keyword = any(twk in full_text for twk in TW_KEYWORDS)
                    
                    if has_tw_keyword and not is_int_source:
                        tw_list.append(news_item)
                    else:
                        int_list.append(news_item)
                    
                    seen.add(link)
        except: continue
    
    return tw_list[:15], int_list[:15] # 個別取最多 15 則

def generate_card_html(news_data, section_id):
    html = ""
    for idx, item in enumerate(news_data):
        summary = ""
        if model:
            try:
                # 讓 AI 針對內容進行超短摘要
                prompt = f"摘要這則新聞（30字內）：{item['title']} {item['fallback']}"
                summary = model.generate_content(prompt).text.strip()
            except: summary = item['fallback']
        else: summary = item['fallback']
        
        unique_idx = f"{section_id}_{idx}"
        html += f"""
        <div class="news-card" data-title="{item['title']}" data-link="{item['link']}">
            <div class="card-content">
                <h3>{item['title']}</h3>
                <p>{summary}</p>
            </div>
            <div class="card-footer">
                <a href="{item['link']}" target="_blank" class="read-more">閱讀全文 ↗</a>
                <button onclick="saveToCloud('{section_id}', '{idx}')" class="save-btn">⭐ 收藏</button>
            </div>
        </div>
        """
    return html

def main():
    tw_news, int_news = fetch_and_classify()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    tw_html = generate_card_html(tw_news, "TW")
    int_html = generate_card_html(int_news, "INT")

    html_template = f"""
    <!DOCTYPE html>
    <html lang="zh-Hant">
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>EcoNews | 環境永續日報</title>
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/water.css@2/out/water.css">
        <style>
            :root {{ --main-green: #2e7d32; --bg: #f8faf8; }}
            body {{ max-width: 1300px; background-color: var(--bg); font-family: "PingFang TC", "Microsoft JhengHei", sans-serif; }}
            header {{ text-align: center; padding: 40px 20px; background: white; border-bottom: 5px solid var(--main-green); }}
            h1 {{ color: var(--main-green); font-size: 2.8em; margin: 0; }}
            
            section {{ padding: 20px 0; }}
            h2 {{ background: var(--main-green); color: white; padding: 10px 20px; border-radius: 5px; display: inline-block; margin-bottom: 25px; }}
            
            .news-grid {{ 
                display: grid; 
                grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); 
                gap: 25px; 
                margin-bottom: 40px;
            }}
            
            .news-card {{ 
                background: white; border-radius: 12px; display: flex; flex-direction: column;
                box-shadow: 0 4px 12px rgba(0,0,0,0.05); border: 1px solid #eee; overflow: hidden;
            }}
            .card-content {{ padding: 20px; flex-grow: 1; }}
            .news-card h3 {{ font-size: 1.1em; margin-bottom: 12px; color: #1a1a1a; min-height: 2.8em; }}
            .news-card p {{ font-size: 0.95em; color: #666; line-height: 1.6; margin: 0; }}
            
            .card-footer {{ background: #fafafa; padding: 15px 20px; display: flex; justify-content: space-between; border-top: 1px solid #eee; }}
            .read-more {{ font-size: 0.85em; font-weight: bold; color: var(--main-green); }}
            .save-btn {{ background: white; border: 1px solid #ddd; padding: 4px 12px; border-radius: 4px; font-size: 0.8em; cursor: pointer; }}
            
            @media (max-width: 600px) {{ .news-grid {{ grid-template-columns: 1fr; }} }}
        </style>
    </head>
    <body>
        <header>
            <h1>🌱 EcoNews 環境快報</h1>
            <p>每 12 小時自動更新全球與台灣環境資訊 | {now_str}</p>
        </header>

        <section>
            <h2>📍 台灣在地脈動</h2>
            <div class="news-grid">{tw_html}</div>
        </section>

        <section>
            <h2>🌐 國際環境視野</h2>
            <div class="news-grid">{int_html}</div>
        </section>

        <script>
            function saveToCloud(section, idx) {{
                const selector = `.news-grid:nth-of-type(${{section === 'TW' ? 1 : 2}}) .news-card`;
                const cards = document.querySelectorAll(selector);
                const card = cards[idx];
                const title = card.getAttribute('data-title');
                const link = card.getAttribute('data-link');
                const tag = prompt("請輸入收藏標籤：", section === 'TW' ? "台灣新聞" : "國際新聞");
                
                if (tag) {{
                    const repoOwner = window.location.hostname.split('.')[0];
                    const repoName = window.location.pathname.split('/')[1] || "eco-news-daily";
                    const body = "### 🍀 收藏紀錄\\n- **標題**: " + title + "\\n- **分類**: " + (section === 'TW' ? "台灣" : "國際") + "\\n- **網址**: " + link;
                    window.open(`https://github.com/${{repoOwner}}/${{repoName}}/issues/new?title=${{encodeURIComponent("[收藏] " + title)}}&body=${{encodeURIComponent(body)}}&labels=${{encodeURIComponent(tag)}}`, '_blank');
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
