/**
 * LINE AI 隨身好友「小光」- Google Apps Script 24H 雲端程式 (Code.gs)
 * -------------------------------------------------------------
 * 特點：
 * 1. 內建自建即時連網引擎（即時新聞 + 維基百科），完全避開 Google 429 限制！
 * 2. 隨時可查 2026 年最新諾貝爾獎、今日即時新聞與最新時事。
 * 3. 24 小時全自動在線、電腦關機也能秒回。
 */

const CONFIG = {
  BOT_NAME: "小光",
  GEMINI_MODEL: "gemini-3.8-flash",
  CHANNEL_ACCESS_TOKEN: "YOUR_CHANNEL_ACCESS_TOKEN",
  GEMINI_API_KEY: "YOUR_GEMINI_API_KEY"
};

// 系統提示詞
const SYSTEM_INSTRUCTION = `你是使用者的專屬 AI 摯友「${CONFIG.BOT_NAME}」。
現在的現實年份是 2026 年。
你的特點與風格：
1. 像一個溫暖、真誠、富有幽默感的好朋友，懂傾聽、會關心對方的生活與心情。
2. 說話語氣自然親切（台灣口吻、正體中文），適度使用日常語助詞（例如：啦、呀、哈哈、耶、喔、讚）與貼切的 Emoji 😊✨。
3. 知識豐富、頭腦清晰。當後台有抓取到【網路即時搜尋到的最新資料】時，請務必以此作為最新事實依據回答朋友（例如 2026 諾貝爾獎、最新時事新聞等）！
4. 回覆時請主動列出【資訊來源】（例如參考的 Google 新聞或維基百科），回覆長度適中，排版清晰易讀。`;

// 接收 LINE 訊息進入點
function doPost(e) {
  try {
    const data = JSON.parse(e.postData.contents);
    const events = data.events;
    if (!events || events.length === 0) return ContentService.createTextOutput("OK");

    for (let i = 0; i < events.length; i++) {
      const event = events[i];
      if (event.type === "message" && event.message.type === "text") {
        const userMessage = event.message.text.trim();
        const replyToken = event.replyToken;

        // 呼叫 Gemini (含即時連網)
        const aiReply = askGemini(userMessage);

        // 回傳給 LINE 使用者
        replyToLine(replyToken, aiReply);
      }
    }
    return ContentService.createTextOutput("OK");
  } catch (err) {
    console.error("doPost 處理錯誤: " + err.stack);
    return ContentService.createTextOutput("ERROR: " + err.message);
  }
}

// 自建免付費即時連網搜尋引擎（新聞 + 維基）
function fetchLiveSearchData(query) {
  let searchResult = "";

  // 1. 抓取 Google 即時新聞 RSS
  try {
    const encoded = encodeURIComponent(query);
    const newsUrl = `https://news.google.com/rss/search?q=${encoded}&hl=zh-TW&gl=TW&ceid=TW:zh-Hant`;
    const res = UrlFetchApp.fetch(newsUrl, { muteHttpExceptions: true });
    if (res.getResponseCode() === 200) {
      const xml = res.getContentText();
      const items = xml.match(/<item>[\s\S]*?<title>(.*?)<\/title>[\s\S]*?<pubDate>(.*?)<\/pubDate>/g);
      if (items && items.length > 0) {
        searchResult += "【即時新聞搜尋結果】：\n";
        for (let i = 0; i < Math.min(items.length, 3); i++) {
          const t = items[i].match(/<title>(.*?)<\/title>/);
          const d = items[i].match(/<pubDate>(.*?)<\/pubDate>/);
          if (t) {
            const cleanTitle = t[1].replace(/<!\[CDATA\[(.*?)\]\]>/g, '$1').replace(/&amp;/g, '&');
            searchResult += `• ${cleanTitle} (${d ? d[1].slice(0, 16) : ''})\n`;
          }
        }
      }
    }
  } catch (e) {
    console.log("新聞搜尋略過: " + e.message);
  }

  // 2. 抓取維基百科最新詞條摘要
  try {
    const wikiUrl = `https://zh.wikipedia.org/w/api.php?action=opensearch&search=${encodeURIComponent(query)}&limit=2&format=json`;
    const wikiRes = UrlFetchApp.fetch(wikiUrl, { muteHttpExceptions: true });
    if (wikiRes.getResponseCode() === 200) {
      const data = JSON.parse(wikiRes.getContentText());
      if (data && data[1] && data[1].length > 0 && data[2] && data[2].length > 0) {
        searchResult += "\n【維基百科資料庫】：\n";
        for (let i = 0; i < data[1].length; i++) {
          if (data[2][i]) searchResult += `• ${data[1][i]}：${data[2][i]}\n`;
        }
      }
    }
  } catch (e) {
    console.log("維基百科略過: " + e.message);
  }

  return searchResult.trim();
}

// 呼叫 Gemini 3.8 Flash (融入即時搜尋結果)
function askGemini(promptText) {
  const apiKey = CONFIG.GEMINI_API_KEY.trim();
  const url = `https://generativelanguage.googleapis.com/v1beta/models/${CONFIG.GEMINI_MODEL}:generateContent?key=${apiKey}`;

  // 先進行即時網路資料抓取
  const liveData = fetchLiveSearchData(promptText);
  let finalPrompt = `${SYSTEM_INSTRUCTION}\n\n`;
  if (liveData) {
    finalPrompt += `【系統剛剛為你上網抓取到的即時網路資料】：\n${liveData}\n\n`;
  }
  finalPrompt += `朋友問你的問題是：「${promptText}」\n請根據以上即時資料與你的好朋友風格親切回答，並註明參考資訊來源：`;

  const payload = {
    contents: [{ role: "user", parts: [{ text: finalPrompt }] }],
    generationConfig: { temperature: 0.7 }
  };

  const options = {
    method: "post",
    contentType: "application/json",
    payload: JSON.stringify(payload),
    muteHttpExceptions: true
  };

  try {
    const res = UrlFetchApp.fetch(url, options);
    const result = JSON.parse(res.getContentText());

    if (result.candidates && result.candidates.length > 0) {
      return result.candidates[0].content.parts[0].text;
    } else if (result.error) {
      return `小光卡住了 😵 (錯誤: ${result.error.message})`;
    }
    return "（笑著看著你，不知道怎麼回）😊";
  } catch (e) {
    return `連線異常：${e.message}`;
  }
}

// 回傳訊息給 LINE
function replyToLine(replyToken, messageText) {
  const token = CONFIG.CHANNEL_ACCESS_TOKEN.trim();
  const url = "https://api.line.me/v2/bot/message/reply";

  const payload = {
    replyToken: replyToken,
    messages: [{ type: "text", text: messageText }]
  };

  const options = {
    method: "post",
    headers: {
      "Content-Type": "application/json",
      "Authorization": "Bearer " + token
    },
    payload: JSON.stringify(payload),
    muteHttpExceptions: true
  };

  UrlFetchApp.fetch(url, options);
}
