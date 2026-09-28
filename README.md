# Telegram 频道 RSS（自建）

原来用的自建 RSSHub（152.67.198.206:1200）已失效，改用 GitHub Actions 每 30 分钟
直接抓取 Telegram 公开预览页 `t.me/s/:channel`，为每个频道生成独立 RSS，
通过 GitHub Pages 对外提供。

## 订阅地址

`https://yyh0422.github.io/telegram-rss/<频道id>.xml`

| 频道 | 订阅地址 |
|---|---|
| AgentNEO | `https://yyh0422.github.io/telegram-rss/AgentNEO_HQ.xml` |
| caoz的梦呓 | `https://yyh0422.github.io/telegram-rss/caozsay.xml` |
| 小声读书 🙈 | `https://yyh0422.github.io/telegram-rss/weekly_books.xml` |
| 搬瓦工补货推送 | `https://yyh0422.github.io/telegram-rss/BandwagonHostNews.xml` |
| 日常人间观察 | `https://yyh0422.github.io/telegram-rss/hayami_kiraa.xml` |
| 無逸齋隨筆 | `https://yyh0422.github.io/telegram-rss/todayread.xml` |
| 看鉴中国 | `https://yyh0422.github.io/telegram-rss/OutsightChina.xml` |
| 竹新社 | `https://yyh0422.github.io/telegram-rss/tnews365.xml` |
| 笔记本：Lin's 文字世界 | `https://yyh0422.github.io/telegram-rss/LinsBookA.xml` |
| 豆瓣精选 | `https://yyh0422.github.io/telegram-rss/douban_read.xml` |
| 青鸟的频道 | `https://yyh0422.github.io/telegram-rss/bluebird_channel.xml` |

## 说明

- 每条包含正文全文、图片、视频、文件链接与原文链接。
- `t.me/s` 预览页只保留最近约 20 条消息，RSS 同样只含最近消息；Inoreader 按 GUID 去重，不会重复。
- 若某频道开启了预览限制或改名，对应 feed 会变空，需手动处理。
