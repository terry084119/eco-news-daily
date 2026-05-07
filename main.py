# (前面 fetch_news 和 AI 摘要的部分保持不變，我們重點修改 HTML 裡的 JavaScript)

    # ... (前面的程式碼)

    # 最終網頁模板
    html_template = f"""
    <!DOCTYPE html>
    <html lang="zh-Hant">
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>EcoNews 雲端收藏版</title>
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/water.css@2/out/water.css">
        <style>
            :root {{ --main-color: #2e7d32; }}
            body {{ max-width: 900px; background-color: #f4f7f4; }}
            header {{ text-align: center; padding: 40px 0; background: white; }}
            .news-card {{ background: white; padding: 25px; border-radius: 12px; margin-bottom: 20px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
            .save-btn {{ background: #2e7d32; color: white; border: none; padding: 8px 15px; cursor: pointer; border-radius: 5px; }}
            .cloud-note {{ background: #e8f5e9; padding: 10px; border-radius: 5px; font-size: 0.9em; margin-bottom: 20px; color: #2e7d32; border: 1px solid #c8e6c9; }}
        </style>
    </head>
    <body>
        <header>
            <h1>🌱 EcoNews 環境日報</h1>
            <div class="cloud-note">☁️ 本版本支援「GitHub Issue 雲端存檔」，收藏將永久儲存於您的專案中。</div>
        </header>

        <main>
            <div class="news-grid">{cards_html}</div>
        </main>

        <script>
            // 修改後的雲端收藏邏輯
            function saveArticle(idx) {{
                const card = document.querySelectorAll('.news-card')[idx];
                const title = card.getAttribute('data-title');
                const link = card.getAttribute('data-link');
                const tag = prompt("請輸入標籤（例如：能源、減碳）：", "一般");
                
                if (tag) {{
                    // 設定你的 GitHub Repository 資訊
                    const repoOwner = "你的GitHub帳號"; // 這裡要改寫成你的帳號
                    const repoName = "eco-news-daily"; // 這裡改為你的專案名
                    
                    // 構建 GitHub Issue 的 URL
                    // 這會自動幫你填好標題、標籤和內容
                    const issueTitle = encodeURIComponent("[收藏] " + title);
                    const issueBody = encodeURIComponent("### 新聞標題\\n" + title + "\\n\\n### 標籤\\n" + tag + "\\n\\n### 連結\\n" + link + "\\n\\n--- \\n來自 EcoNews 自動化收藏");
                    const githubUrl = `https://github.com/${{repoOwner}}/${{repoName}}/issues/new?title=${{issueTitle}}&body=${{issueBody}}&labels=${{encodeURIComponent(tag)}}`;
                    
                    // 引導使用者去 GitHub 存檔
                    if(confirm("即將前往 GitHub 建立雲端存檔（Issue），請點擊『Submit new issue』完成收藏。")) {{
                        window.open(githubUrl, '_blank');
                    }}
                }}
            }}
        </script>
    </body>
    </html>
    """
