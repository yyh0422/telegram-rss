#!/usr/bin/env python3
"""抓取 Telegram 频道公开预览页 t.me/s/:channel，为每个频道生成独立 RSS。

用法: python3 fetch_tg.py <输出目录>
输出: <输出目录>/<channel>.xml，每 30 分钟由 GitHub Actions 重新生成。
"""
import html
import os
import re
import sys
import time
import urllib.request
from datetime import datetime
from email.utils import format_datetime
from xml.sax.saxutils import escape as xml_escape

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")

# (频道 id, 订阅显示名) —— 与 Inoreader 现有 11 个订阅一一对应
CHANNELS = [
    ("AgentNEO_HQ", "AgentNEO"),
    ("caozsay", "caoz的梦呓"),
    ("weekly_books", "小声读书 🙈"),
    ("BandwagonHostNews", "搬瓦工补货推送"),
    ("hayami_kiraa", "日常人间观察"),
    ("todayread", "無逸齋隨筆"),
    ("OutsightChina", "看鉴中国"),
    ("tnews365", "竹新社"),
    ("LinsBookA", "笔记本：Lin's 文字世界"),
    ("douban_read", "豆瓣精选"),
    ("bluebird_channel", "青鸟的频道"),
]

PAGES_BASE = "https://yyh0422.github.io/telegram-rss"


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=25) as r:
        return r.read().decode("utf-8", errors="replace")


def abs_url(u):
    if u.startswith("//"):
        return "https:" + u
    if u.startswith("/"):
        return "https://t.me" + u
    return u


def absolutize_html(h):
    h = re.sub(r'href="/', 'href="https://t.me/', h)
    h = re.sub(r"href='/'", "href='https://t.me/'", h)
    h = re.sub(r'src="/', 'src="https://t.me/', h)
    return h


def parse_block(block, channel):
    """解析单个消息块，返回 dict；无法解析返回 None。"""
    m = re.search(r'data-post="([^"]+)"', block)
    if not m:
        return None  # 系统消息，无 data-post
    post_id = m.group(1)  # "CHANNEL/123"
    link = f"https://t.me/{post_id}"

    m = re.search(r'<time datetime="([^"]+)"', block)
    pub = None
    if m:
        try:
            dt = datetime.fromisoformat(m.group(1))
            pub = format_datetime(dt)
        except Exception:  # noqa
            pub = None

    parts = []

    # 正文
    m = re.search(
        r'<div class="tgme_widget_message_text js-message_text"[^>]*>(.*?)</div>\s*'
        r'(?:<div class="tgme_widget_message_footer"|$)', block, re.S)
    if not m:
        m = re.search(
            r'<div class="tgme_widget_message_text js-message_text"[^>]*>(.*?)</div>',
            block, re.S)
    text_html = absolutize_html(m.group(1).strip()) if m else ""
    text_plain = re.sub(r"<br\s*/?>", "\n",
                        re.sub(r"<[^>]+>", "", text_html or "")).strip()

    # 图片（含相册分组、贴纸）：style 里的 background-image
    for img in re.findall(r"background-image:url\('([^']+)'", block):
        parts.append(
            f'<p><img src="{abs_url(img)}" referrerpolicy="no-referrer" '
            f'style="max-width:100%;height:auto;" loading="lazy"></p>')

    # 视频
    for v in re.findall(r"<video[^>]*>(.*?)</video>", block, re.S):
        src = re.search(r'<source[^>]+src="([^"]+)"', v)
        if src:
            parts.append(
                f'<p><video controls preload="metadata" style="max-width:100%;" '
                f'src="{abs_url(src.group(1))}"></video></p>')

    # 文件/文档
    for doc in re.finditer(
            r'<a class="tgme_widget_message_document_wrap" href="([^"]+)".*?'
            r'class="tgme_widget_message_document_title"[^>]*>([^<]*)<',
            block, re.S):
        parts.append(
            f'<p>📎 <a href="{abs_url(doc.group(1))}">'
            f'{html.escape(doc.group(2).strip())}</a></p>')

    # 投票
    pm = re.search(
        r'class="tgme_widget_message_poll_question"[^>]*>([^<]+)<', block)
    if pm:
        opts = re.findall(
            r'class="tgme_widget_message_poll_option"[^>]*>([^<]+)<', block)
        parts.append("<p>📊 <b>" + html.escape(pm.group(1).strip()) + "</b><br>" +
                     "<br>".join("○ " + html.escape(o.strip()) for o in opts) + "</p>")

    # 链接预览卡片
    for lp in re.finditer(
            r'<a class="tgme_widget_message_link_preview" href="([^"]+)">(.*?)</a>',
            block, re.S):
        inner = lp.group(2)
        site = re.search(r'link_preview_site_name[^"]*"[^>]*>([^<]{1,60})<', inner)
        title = re.search(r'link_preview_title[^"]*"[^>]*>([^<]{1,200})<', inner)
        desc = re.search(r'link_preview_description[^"]*"[^>]*>([^<]{1,300})<', inner)
        img = re.search(r"background-image:url\('([^']+)'", inner)
        card = "<blockquote style='border-left:3px solid #ccc;padding-left:8px;'>"
        if img:
            card += (f'<img src="{abs_url(img.group(1))}" referrerpolicy="no-referrer" '
                     f'style="max-width:100%;height:auto;" loading="lazy"><br>')
        if title:
            card += (f'<b><a href="{abs_url(lp.group(1))}">'
                     f'{html.escape(title.group(1).strip())}</a></b><br>')
        if site:
            card += f'<small>{html.escape(site.group(1).strip())}</small><br>'
        if desc:
            card += html.escape(desc.group(1).strip())
        card += "</blockquote>"
        parts.append(f"<p>{card}</p>")

    # 组装：正文在前，媒体在后
    body = ""
    if text_html:
        body += f"<div>{text_html}</div>"
    body += "".join(parts)
    if not body:
        return None

    title = text_plain.replace("\n", " ").strip()[:60]
    if not title:
        if "<video" in body:
            title = "视频消息"
        elif "📎" in body:
            title = "文件"
        elif "📊" in body:
            title = "投票"
        else:
            title = "图片消息"

    return {"guid": link, "link": link, "title": title,
            "pubDate": pub, "body": body}


def build_feed(channel, disp_name, items):
    now = format_datetime(datetime.now().astimezone())
    parts = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<rss version="2.0">', "<channel>",
             f"<title>{xml_escape('Telegram - ' + disp_name)}</title>",
             f"<link>https://t.me/s/{channel}</link>",
             f"<description>{xml_escape(disp_name)} 频道更新（自建抓取）</description>",
             f"<lastBuildDate>{now}</lastBuildDate>",
             "<language>zh-cn</language>"]
    for it in items:
        parts.append("<item>")
        parts.append(f"<title>{xml_escape(it['title'])}</title>")
        parts.append(f"<link>{xml_escape(it['link'])}</link>")
        parts.append(f"<guid isPermaLink=\"true\">{xml_escape(it['guid'])}</guid>")
        if it["pubDate"]:
            parts.append(f"<pubDate>{it['pubDate']}</pubDate>")
        parts.append(f"<description><![CDATA[{it['body']}]]></description>")
        parts.append("</item>")
    parts += ["</channel>", "</rss>"]
    return "\n".join(parts)


def main():
    outdir = sys.argv[1] if len(sys.argv) > 1 else "."
    os.makedirs(outdir, exist_ok=True)
    total = 0
    for channel, disp_name in CHANNELS:
        try:
            data = fetch(f"https://t.me/s/{channel}")
        except Exception as e:  # noqa
            print(f"WARN {channel}: 抓取失败 {e}")
            continue
        blocks = data.split("tgme_widget_message_wrap js-widget_message_wrap")[1:]
        items = []
        for b in blocks:
            it = parse_block(b, channel)
            if it:
                items.append(it)
        items.reverse()  # 新的在前
        xml = build_feed(channel, disp_name, items)
        with open(os.path.join(outdir, f"{channel}.xml"), "w",
                  encoding="utf-8") as f:
            f.write(xml)
        total += len(items)
        print(f"OK {channel}: {len(items)} 条 -> {channel}.xml")
        time.sleep(1)
    print(f"全部完成，共 {total} 条")


if __name__ == "__main__":
    main()
