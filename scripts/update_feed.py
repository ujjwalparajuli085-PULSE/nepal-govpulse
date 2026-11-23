#!/usr/bin/env python3
"""
Nepal GovPulse — Automated Feed Updater
Fetches live RSS/JSON feeds from NRB and Nepali news portals,
updates data.json in place, and preserves fallback records if a feed is down.
Uses only Python standard library (no pip install required).
"""

import datetime
import json
import os
import re
import urllib.request
import xml.etree.ElementTree as ET
from html import unescape

DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data.json")
USER_AGENT = "NepalGovPulseBot/1.0 (+https://github.com/)"

RSS_FEEDS = [
    ("The Kathmandu Post", "https://kathmandupost.com/rss"),
    ("OnlineKhabar", "https://english.onlinekhabar.com/feed"),
    ("Ratopati", "https://english.ratopati.com/feed"),
    ("Nepal News", "https://english.nepalnews.com/feed/"),
]

NRB_FOREX_API = "https://www.nrb.org.np/api/forex/v1/rates"


def fetch_url(url: str, timeout: int = 15) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", errors="replace")


def clean_html(text: str) -> str:
    text = unescape(text or "")
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def parse_rss(source_name: str, xml_text: str, limit: int = 12):
    items = []
    try:
        root = ET.fromstring(xml_text)
        for item in root.findall(".//item")[:limit]:
            title = clean_html(item.findtext("title", ""))
            link = (item.findtext("link", "") or "").strip()
            desc = clean_html(item.findtext("description", ""))
            if title and link:
                items.append({
                    "sourceName": source_name,
                    "sourceUrl": link,
                    "title": title,
                    "summary": desc[:260] + ("..." if len(desc) > 260 else ""),
                })
    except Exception as exc:
        print(f"[WARN] RSS parse failed for {source_name}: {exc}")
    return items


def fetch_nrb_forex():
    try:
        today = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=5, minutes=45))).strftime("%Y-%m-%d")
        url = f"{NRB_FOREX_API}?page=1&per_page=1&from={today}&to={today}"
        raw = fetch_url(url)
        payload = json.loads(raw)
        rates = payload.get("data", {}).get("payload", [])
        if not rates:
            return None
        out = []
        for r in rates[0].get("rates", []):
            cur = r.get("currency", {})
            iso = cur.get("iso3", "")
            if iso in {"USD", "INR", "EUR", "GBP", "AUD", "AED", "SAR", "QAR", "CNY", "JPY"}:
                out.append({
                    "currency": f"{iso} ({cur.get('name', iso)})",
                    "unit": str(cur.get("unit", 1)),
                    "buy": str(r.get("buy", "")),
                    "sell": str(r.get("sell", "")),
                })
        return out if out else None
    except Exception as exc:
        print(f"[WARN] NRB Forex fetch failed: {exc}")
        return None


def classify_item(item):
    text = (item["title"] + " " + item["summary"]).lower()
    if any(k in text for k in ["protest", "maitighar", "strike", "dharna", "agitation", "demonstration"]):
        return "protest"
    if any(k in text for k in ["rumor", "fake", "fact check", "misleading", "deepfake", "rebuttal", "denies", "clarifies"]):
        return "rumor"
    if any(k in text for k in ["court", "ciaa", "cib", "arrest", "warrant", "summon", "supreme court", "police"]):
        return "Judiciary & Law"
    if any(k in text for k in ["india", "china", "un ", "foreign", "embassy", "treaty", "mou", "bilateral", "diplomat"]):
        return "Official & Diplomatic"
    if any(k in text for k in ["press council", "journalist", "fnj", "media", "ordinance"]):
        return "Media & Civic"
    return "Domestic & Ministries"


def main():
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    kst_now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=5, minutes=45)))
    today_label = kst_now.strftime("%b %d, %Y")
    data["adDate"] = kst_now.strftime("%A, %B %d, %Y")

    fetched_all = []
    for name, url in RSS_FEEDS:
        try:
            xml_text = fetch_url(url)
            fetched_all.extend(parse_rss(name, xml_text))
        except Exception as exc:
            print(f"[WARN] Failed to fetch {name}: {exc}")

    if fetched_all:
        new_activities = []
        new_protests = []
        new_rumors = []
        for idx, item in enumerate(fetched_all):
            cat = classify_item(item)
            if cat == "protest":
                new_protests.append({
                    "id": f"prot-live-{idx}",
                    "zone": "Maitighar Mandala" if "maitighar" in (item["title"] + item["summary"]).lower() else "National / Kathmandu",
                    "location": "Maitighar Mandala" if "maitighar" in (item["title"] + item["summary"]).lower() else "Kathmandu / Nepal",
                    "date": today_label,
                    "group": item["title"],
                    "demand": item["summary"] or item["title"],
                    "status": "Reported Today",
                    "sourceName": item["sourceName"],
                    "sourceUrl": item["sourceUrl"],
                })
            elif cat == "rumor":
                new_rumors.append({
                    "id": f"rum-live-{idx}",
                    "status": "Active Controversy",
                    "title": item["title"],
                    "circulatingOn": f"{item['sourceName']} ({today_label})",
                    "claim": item["title"],
                    "verification": item["summary"] or "See linked report for verification details.",
                    "sourceName": item["sourceName"],
                    "sourceUrl": item["sourceUrl"],
                })
            else:
                new_activities.append({
                    "id": f"act-live-{idx}",
                    "category": cat,
                    "time": today_label,
                    "agency": item["sourceName"],
                    "title": item["title"],
                    "summary": item["summary"] or item["title"],
                    "sourceName": item["sourceName"],
                    "sourceUrl": item["sourceUrl"],
                })

        if new_activities:
            data["leadDispatch"] = {
                "kicker": f"Lead Dispatch • {new_activities[0]['agency']}",
                "title": new_activities[0]["title"],
                "summary": new_activities[0]["summary"],
                "primaryLinkText": f"Read on {new_activities[0]['sourceName']}",
                "primaryLinkUrl": new_activities[0]["sourceUrl"],
            }
            data["breakingTicker"] = [a["title"] for a in new_activities[:4]]
            data["activities"] = new_activities[:12]
        if new_protests:
            data["protests"] = new_protests[:8]
        if new_rumors:
            data["rumors"] = new_rumors[:8]

    forex = fetch_nrb_forex()
    if forex:
        data["forexRates"] = forex

    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"[OK] Updated {DATA_PATH} for {data['adDate']}")


if __name__ == "__main__":
    main()
