#!/usr/bin/env python3
"""
Resmi Gazete, İŞKUR ve Kariyer.gov.tr Kamu İlanları Scraper
Kendi sunucunuzda cron job ile günlük otomatik çalışır.
Her çalıştırıldığında O GÜNÜN TARİHİNİ dinamik olarak alır.
Çıktı dosya adı: kamu-hukuk-rehberi-YYYY-MM-DD.html
"""

import os
import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone, timedelta

# Türkiye saat dilimi (UTC+3)
TR_TZ = timezone(timedelta(hours=3))

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
}

# Türkçe ay ve gün isimleri
AY_MAP = {
    1: "Ocak", 2: "Şubat", 3: "Mart", 4: "Nisan",
    5: "Mayıs", 6: "Haziran", 7: "Temmuz", 8: "Ağustos",
    9: "Eylül", 10: "Ekim", 11: "Kasım", 12: "Aralık"
}
GUN_MAP = {
    0: "Pazartesi", 1: "Salı", 2: "Çarşamba",
    3: "Perşembe", 4: "Cuma", 5: "Cumartesi", 6: "Pazar"
}


def get_turkish_date():
    """Türkiye saatine göre BUGÜNÜN tarihini dinamik olarak döndürür."""
    now = datetime.now(TR_TZ)
    gun = now.day
    ay = AY_MAP[now.month]
    yil = now.year
    gun_adi = GUN_MAP[now.weekday()]
    saat = now.strftime("%H:%M")
    iso_date = now.strftime("%Y-%m-%d")
    return {
        "display": f"{gun} {ay} {yil}, {gun_adi}",
        "time": saat,
        "iso": iso_date,
        "now": now
    }


def is_siyasi(text):
    """Siyasi içerik filtresi."""
    keywords = ["parti", "seçim", "muhalefet", "iktidar", "milletvekili",
                "meclis", "siyasi", "muhalif", "oy", "propaganda"]
    return any(k in text.lower() for k in keywords)


def scrape_resmi_gazete():
    """Resmi Gazete'nin bugünkü sayısını çeker."""
    results = []
    date_info = get_turkish_date()

    try:
        url = "https://www.resmigazete.gov.tr/"
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.encoding = "utf-8"

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "lxml")
            seen = set()

            for item in soup.find_all(["a", "h3", "h4", "li"], limit=80):
                text = item.get_text(strip=True)
                if text and len(text) > 10 and text not in seen and not is_siyasi(text):
                    href = item.get("href", "")
                    if href and not href.startswith("http"):
                        href = f"https://www.resmigazete.gov.tr/{href}"
                    elif not href:
                        href = url

                    seen.add(text)
                    results.append({
                        "title": text[:120],
                        "link": href,
                        "source": "Resmi Gazete"
                    })

        if not results:
            results.append({
                "title": f"Resmi Gazete - {date_info['display']} Tarihli Sayı",
                "link": "https://www.resmigazete.gov.tr/",
                "source": "Resmi Gazete"
            })

    except Exception as e:
        print(f"   ⚠️ Resmi Gazete hatası: {e}")
        results.append({
            "title": f"Resmi Gazete - {date_info['display']}",
            "link": "https://www.resmigazete.gov.tr/",
            "source": "Resmi Gazete"
        })

    return results[:10]


def scrape_iskur():
    """İŞKUR kamu personeli alım ilanlarını çeker."""
    results = []

    try:
        url = "https://esube.iskur.gov.tr/"
        response = requests.get(url, headers=HEADERS, timeout=15)

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "lxml")
            seen = set()
            kamu_keywords = ["personel", "alım", "ilan", "memur", "işçi",
                           "kamu", "belediye", "hastane", "sözleşmeli", "kadro"]

            for link in soup.find_all("a", href=True, limit=50):
                text = link.get_text(strip=True)
                href = link["href"]

                if text and len(text) > 15 and text not in seen:
                    if not href.startswith("http"):
                        href = f"https://esube.iskur.gov.tr{href}"

                    if any(k in text.lower() for k in kamu_keywords):
                        seen.add(text)
                        results.append({
                            "title": text[:120],
                            "link": href,
                            "source": "İŞKUR"
                        })

    except Exception as e:
        print(f"   ⚠️ İŞKUR hatası: {e}")

    if not results:
        results = [
            {
                "title": "İŞKUR Açık Kamu İş İlanları - Güncel Liste",
                "link": "https://esube.iskur.gov.tr/Istihdam/AcikIsIlan662.aspx",
                "source": "İŞKUR"
            },
            {
                "title": "İŞKUR TYP (Toplum Yararına Program) İlanları",
                "link": "https://esube.iskur.gov.tr/Istihdam/AcikIsIlan662.aspx",
                "source": "İŞKUR"
            }
        ]

    return results[:10]


def scrape_kariyer_gov():
    """Kariyer.gov.tr kamu personel alım ilanlarını çeker."""
    results = []

    try:
        url = "https://www.kariyer.gov.tr/"
        response = requests.get(url, headers=HEADERS, timeout=15)

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "lxml")
            seen = set()
            kamu_keywords = ["personel", "alım", "memur", "kamu", "belediye",
                           "bakanlık", "müdürlük", "başkanlık", "üniversite"]

            for link in soup.find_all("a", href=True, limit=60):
                text = link.get_text(strip=True)
                href = link["href"]

                if text and len(text) > 15 and text not in seen and not is_siyasi(text):
                    if not href.startswith("http"):
                        href = f"https://www.kariyer.gov.tr{href}"

                    if any(k in text.lower() for k in kamu_keywords):
                        seen.add(text)
                        results.append({
                            "title": text[:120],
                            "link": href,
                            "source": "Kariyer.gov.tr"
                        })

    except Exception as e:
        print(f"   ⚠️ Kariyer.gov.tr hatası: {e}")

    if not results:
        results = [
            {
                "title": "Kariyer.gov.tr - Kamu Personel Alım İlanları",
                "link": "https://www.kariyer.gov.tr/",
                "source": "Kariyer.gov.tr"
            },
            {
                "title": "Kariyer.gov.tr - Devlet Memuru Alım Duyuruları",
                "link": "https://www.kariyer.gov.tr/kamu-ilanlari",
                "source": "Kariyer.gov.tr"
            }
        ]

    return results[:10]


def generate_html(resmi_gazete_items, iskur_items, kariyer_items):
    """Yaşlı dostu, büyük butonlu, sidebar destekli, AdSense reklam alanlı HTML sayfası oluşturur."""
    date_info = get_turkish_date()

    # Resmi Gazete butonları
    gazete_buttons = ""
    for i, item in enumerate(resmi_gazete_items):
        gazete_buttons += f'''
        <div style="margin: 15px 0; text-align: center;">
            <a href="{item['link']}" target="_blank" rel="noopener noreferrer"
               style="display: inline-block; padding: 16px 30px; background-color: #1a5276; color: #ffffff; font-size: 18px; font-weight: bold; font-family: sans-serif; text-decoration: none; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.15); text-transform: uppercase; max-width: 90%; line-height: 1.4;">
                📋 {item["title"][:80]}
            </a>
            <p style="font-size: 12px; color: #666; margin: 5px 0;">(Resmi Gazete - T.C. Cumhurbaşkanlığı Resmi Kaynağıdır)</p>
        </div>'''
        # Her 3 haberden sonra içerik arası reklam alanı
        if (i + 1) % 3 == 0 and i < len(resmi_gazete_items) - 1:
            gazete_buttons += '''
        <!-- ═══════════ ADSENSE REKLAM ALANI: İÇERİK ARASI ═══════════ -->
        <!-- Buraya in-article reklam birimi kodunuzu yapıştırın -->
        <!-- Örnek: -->
        <!-- <ins class="adsbygoogle"
             style="display:block; text-align:center;"
             data-ad-layout="in-article"
             data-ad-format="fluid"
             data-ad-client="ca-pub-XXXXXXXXXXXXXXXX"
             data-ad-slot="XXXXXXXXXX"></ins>
        <script>(adsbygoogle = window.adsbygoogle || []).push({});</script> -->
        <!-- ═══════════ ADSENSE REKLAM ALANI SONU ═══════════ -->
        <div style="margin: 10px auto; padding: 8px; background: #f9f9f9; border: 1px dashed #ddd; border-radius: 4px; text-align: center; max-width: 90%;">
            <span style="font-size: 11px; color: #999;">📢 Reklam Alanı</span>
        </div>'''

    # İŞKUR butonları
    iskur_buttons = ""
    for i, item in enumerate(iskur_items):
        iskur_buttons += f'''
        <div style="margin: 15px 0; text-align: center;">
            <a href="{item['link']}" target="_blank" rel="noopener noreferrer"
               style="display: inline-block; padding: 16px 30px; background-color: #27ae60; color: #ffffff; font-size: 18px; font-weight: bold; font-family: sans-serif; text-decoration: none; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.15); text-transform: uppercase; max-width: 90%; line-height: 1.4;">
                💼 {item["title"][:80]}
            </a>
            <p style="font-size: 12px; color: #666; margin: 5px 0;">({item["source"]} - Resmi Kamu Kaynağıdır)</p>
        </div>'''
        # Her 4 ilandan sonra içerik arası reklam alanı
        if (i + 1) % 4 == 0 and i < len(iskur_items) - 1:
            iskur_buttons += '''
        <!-- ═══════════ ADSENSE REKLAM ALANI: İÇERİK ARASI ═══════════ -->
        <!-- Buraya in-article reklam birimi kodunuzu yapıştırın -->
        <!-- <ins class="adsbygoogle"
             style="display:block; text-align:center;"
             data-ad-layout="in-article"
             data-ad-format="fluid"
             data-ad-client="ca-pub-XXXXXXXXXXXXXXXX"
             data-ad-slot="XXXXXXXXXX"></ins>
        <script>(adsbygoogle = window.adsbygoogle || []).push({});</script> -->
        <!-- ═══════════ ADSENSE REKLAM ALANI SONU ═══════════ -->
        <div style="margin: 10px auto; padding: 8px; background: #f9f9f9; border: 1px dashed #ddd; border-radius: 4px; text-align: center; max-width: 90%;">
            <span style="font-size: 11px; color: #999;">📢 Reklam Alanı</span>
        </div>'''

    # Kariyer.gov.tr butonları
    kariyer_buttons = ""
    for i, item in enumerate(kariyer_items):
        kariyer_buttons += f'''
        <div style="margin: 15px 0; text-align: center;">
            <a href="{item['link']}" target="_blank" rel="noopener noreferrer"
               style="display: inline-block; padding: 16px 30px; background-color: #8e44ad; color: #ffffff; font-size: 18px; font-weight: bold; font-family: sans-serif; text-decoration: none; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.15); text-transform: uppercase; max-width: 90%; line-height: 1.4;">
                🏛️ {item["title"][:80]}
            </a>
            <p style="font-size: 12px; color: #666; margin: 5px 0;">({item["source"]} - Resmi Kamu Kaynağıdır)</p>
        </div>'''
        # Her 4 ilandan sonra içerik arası reklam alanı
        if (i + 1) % 4 == 0 and i < len(kariyer_items) - 1:
            kariyer_buttons += '''
        <!-- ═══════════ ADSENSE REKLAM ALANI: İÇERİK ARASI ═══════════ -->
        <!-- Buraya in-article reklam birimi kodunuzu yapıştırın -->
        <!-- <ins class="adsbygoogle"
             style="display:block; text-align:center;"
             data-ad-layout="in-article"
             data-ad-format="fluid"
             data-ad-client="ca-pub-XXXXXXXXXXXXXXXX"
             data-ad-slot="XXXXXXXXXX"></ins>
        <script>(adsbygoogle = window.adsbygoogle || []).push({});</script> -->
        <!-- ═══════════ ADSENSE REKLAM ALANI SONU ═══════════ -->
        <div style="margin: 10px auto; padding: 8px; background: #f9f9f9; border: 1px dashed #ddd; border-radius: 4px; text-align: center; max-width: 90%;">
            <span style="font-size: 11px; color: #999;">📢 Reklam Alanı</span>
        </div>'''

    html = f'''<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Kamu Hukuk Rehberi - {date_info["display"]} | Resmi Gazete & İŞKUR & Kariyer.gov.tr</title>
    <meta name="description" content="{date_info['display']} tarihli Resmi Gazete kararları, İŞKUR ve Kariyer.gov.tr kamu personel alım ilanları. Günlük otomatik güncellenir.">

    <!-- ═══════════ ADSENSE ANA KODU ═══════════ -->
    <!-- Aşağıdaki satırdaki ca-pub-XXXXXXXXXXXXXXXX kısmını kendi yayıncı kimliğinizle değiştirin -->
    <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-XXXXXXXXXXXXXXXX" crossorigin="anonymous"></script>
    <!-- ═══════════ ADSENSE ANA KODU SONU ═══════════ -->

    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f5f5; color: #333; line-height: 1.6; padding: 10px; }}
        .page-wrapper {{ max-width: 1100px; margin: 0 auto; display: flex; gap: 20px; }}
        .main-content {{ flex: 7; min-width: 0; }}
        .sidebar {{ flex: 3; min-width: 250px; }}
        .container {{ background: #fff; border-radius: 12px; box-shadow: 0 2px 20px rgba(0,0,0,0.1); overflow: hidden; }}
        .header {{ background: linear-gradient(135deg, #c0392b, #e74c3c); color: white; padding: 25px 20px; text-align: center; }}
        .header h1 {{ font-size: 24px; margin-bottom: 8px; }}
        .header .date {{ font-size: 16px; opacity: 0.9; }}
        .notice {{ background: #fff3cd; border: 2px solid #ffc107; padding: 12px 20px; margin: 15px; border-radius: 8px; font-size: 14px; text-align: center; }}
        .section {{ padding: 20px; border-bottom: 3px solid #f0f0f0; }}
        .section h2 {{ font-size: 22px; color: #2c3e50; margin-bottom: 15px; padding-bottom: 10px; border-bottom: 2px solid #eee; }}
        .quick {{ background: #eaf2f8; padding: 20px; margin: 15px; border-radius: 8px; }}
        .quick h3 {{ font-size: 18px; margin-bottom: 10px; color: #1a5276; }}
        .footer {{ background: #2c3e50; color: #ecf0f1; padding: 20px; text-align: center; font-size: 13px; }}
        .badge {{ display: inline-block; background: #27ae60; color: white; padding: 4px 12px; border-radius: 20px; font-size: 12px; margin-top: 8px; }}
        .info {{ margin-top: 20px; padding: 15px; background: #f8f9fa; border-radius: 8px; border-left: 4px solid #1a5276; font-size: 14px; color: #555; }}
        .sidebar-ad {{ background: #fff; border-radius: 12px; box-shadow: 0 2px 10px rgba(0,0,0,0.08); padding: 15px; margin-bottom: 20px; text-align: center; }}
        .sidebar-ad .ad-label {{ font-size: 11px; color: #999; margin-bottom: 8px; }}
        .sidebar-sticky {{ position: sticky; top: 20px; }}
        @media (max-width: 768px) {{
            .page-wrapper {{ flex-direction: column; }}
            .sidebar {{ display: none; }}
            .header h1 {{ font-size: 20px; }}
            .section h2 {{ font-size: 18px; }}
        }}
    </style>
</head>
<body>
    <div class="page-wrapper">
        <!-- ═══════════ ANA İÇERİK ALANI (%70) ═══════════ -->
        <div class="main-content">
            <div class="container">
                <div class="header">
                    <h1>🇹🇷 KAMU HUKUK REHBERİ</h1>
                    <p class="date">{date_info["display"]}</p>
                    <span class="badge">✅ Otomatik Güncellendi - {date_info["time"]}</span>
                </div>

                <!-- ═══════════ ADSENSE REKLAM ALANI: ÜST BANNER ═══════════ -->
                <!-- Buraya AdSense reklam birimi kodunuzu yapıştırın -->
                <!-- Örnek: -->
                <!-- <ins class="adsbygoogle"
                     style="display:block"
                     data-ad-client="ca-pub-XXXXXXXXXXXXXXXX"
                     data-ad-slot="XXXXXXXXXX"
                     data-ad-format="auto"
                     data-full-width-responsive="true"></ins>
                <script>(adsbygoogle = window.adsbygoogle || []).push({{}});</script> -->
                <!-- ═══════════ ADSENSE REKLAM ALANI SONU ═══════════ -->
                <div style="margin: 10px 15px; padding: 12px; background: #f0f8ff; border: 2px dashed #b8d4e8; border-radius: 8px; text-align: center;">
                    <span style="font-size: 12px; color: #7ba7c9;">📢 Üst Banner Reklam Alanı (728x90 veya Responsive)</span>
                </div>

                <div class="notice">
                    🌍 <strong>For English / Für Deutsch / Pour Français / للعربية:</strong><br>
                    Kendi dilinizde okumak için tarayıcınızın çeviri butonunu kullanın.<br>
                    <em>Use your browser's translate button to read in your language.</em>
                </div>

                <div class="quick">
                    <h3>⚡ HIZLI ERİŞİM BUTONLARI</h3>
                    <div style="margin: 10px 0; text-align: center;">
                        <a href="https://www.resmigazete.gov.tr/" target="_blank" rel="noopener noreferrer"
                           style="display: inline-block; padding: 14px 24px; background-color: #e50914; color: #ffffff; font-size: 16px; font-weight: bold; font-family: sans-serif; text-decoration: none; border-radius: 8px; margin: 5px; box-shadow: 0 3px 6px rgba(0,0,0,0.15);">
                            👉 RESMİ GAZETE'Yİ AÇ 👈
                        </a>
                        <a href="https://esube.iskur.gov.tr/Istihdam/AcikIsIlan662.aspx" target="_blank" rel="noopener noreferrer"
                           style="display: inline-block; padding: 14px 24px; background-color: #27ae60; color: #ffffff; font-size: 16px; font-weight: bold; font-family: sans-serif; text-decoration: none; border-radius: 8px; margin: 5px; box-shadow: 0 3px 6px rgba(0,0,0,0.15);">
                            👉 İŞKUR İLANLARINI GÖR 👈
                        </a>
                        <a href="https://www.kariyer.gov.tr/" target="_blank" rel="noopener noreferrer"
                           style="display: inline-block; padding: 14px 24px; background-color: #8e44ad; color: #ffffff; font-size: 16px; font-weight: bold; font-family: sans-serif; text-decoration: none; border-radius: 8px; margin: 5px; box-shadow: 0 3px 6px rgba(0,0,0,0.15);">
                            👉 KARİYER.GOV.TR 👈
                        </a>
                        <a href="https://www.mhrs.gov.tr/" target="_blank" rel="noopener noreferrer"
                           style="display: inline-block; padding: 14px 24px; background-color: #16a085; color: #ffffff; font-size: 16px; font-weight: bold; font-family: sans-serif; text-decoration: none; border-radius: 8px; margin: 5px; box-shadow: 0 3px 6px rgba(0,0,0,0.15);">
                            👉 HASTANE RANDEVUSU AL 👈
                        </a>
                    </div>
                </div>

                <div class="section">
                    <h2>📋 RESMİ GAZETE - {date_info["display"].upper()} KARARLARI</h2>
                    <p style="font-size: 14px; color: #666; margin-bottom: 15px;">Bugün ({date_info["display"]}) yayımlanan resmi kararlara doğrudan ulaşın.</p>
                    {gazete_buttons}
                    <div class="info">
                        <strong>📌 Bilgi:</strong> Resmi Gazete, T.C. Cumhurbaşkanlığı tarafından her gün yayımlanır. Kanun değişiklikleri, atama kararları ve kamu ilanları burada duyurulur.
                    </div>
                </div>

                <div class="section">
                    <h2>💼 İŞKUR - KAMU PERSONEL ALIMLARI</h2>
                    <p style="font-size: 14px; color: #666; margin-bottom: 15px;">Güncel kamu personeli alım ilanlarına aşağıdan doğrudan başvurabilirsiniz.</p>
                    {iskur_buttons}
                    <div class="info" style="border-left-color: #27ae60;">
                        <strong>📌 Nasıl Başvurulur?</strong><br>
                        1. Adım: Yukarıdaki yeşil butona tıklayın<br>
                        2. Adım: T.C. Kimlik numaranızla giriş yapın<br>
                        3. Adım: İstediğiniz ilana "Başvur" butonuna basın
                    </div>
                </div>

                <div class="section">
                    <h2>🏛️ KARİYER.GOV.TR - DEVLET MEMURLUK İLANLARI</h2>
                    <p style="font-size: 14px; color: #666; margin-bottom: 15px;">Kariyer.gov.tr üzerinden güncel kamu alım duyurularına ulaşın.</p>
                    {kariyer_buttons}
                    <div class="info" style="border-left-color: #8e44ad;">
                        <strong>📌 Kariyer.gov.tr Nedir?</strong><br>
                        T.C. Cumhurbaşkanlığı İnsan Kaynakları Ofisi tarafından yönetilen resmi kamu istihdam portalıdır.
                    </div>
                </div>

                <div class="section">
                    <h2>🔗 DİĞER FAYDALI KAMU HİZMETLERİ</h2>
                    <div style="margin: 10px 0; text-align: center;">
                        <a href="https://www.turkiye.gov.tr/" target="_blank" rel="noopener noreferrer"
                           style="display: inline-block; padding: 14px 24px; background-color: #2980b9; color: #ffffff; font-size: 16px; font-weight: bold; font-family: sans-serif; text-decoration: none; border-radius: 8px; margin: 5px; box-shadow: 0 3px 6px rgba(0,0,0,0.15);">
                            🏛️ E-DEVLET GİRİŞ
                        </a>
                        <a href="https://sonuc.osym.gov.tr/" target="_blank" rel="noopener noreferrer"
                           style="display: inline-block; padding: 14px 24px; background-color: #d35400; color: #ffffff; font-size: 16px; font-weight: bold; font-family: sans-serif; text-decoration: none; border-radius: 8px; margin: 5px; box-shadow: 0 3px 6px rgba(0,0,0,0.15);">
                            📝 ÖSYM SINAV SONUÇLARI
                        </a>
                        <a href="https://www.mhrs.gov.tr/" target="_blank" rel="noopener noreferrer"
                           style="display: inline-block; padding: 14px 24px; background-color: #16a085; color: #ffffff; font-size: 16px; font-weight: bold; font-family: sans-serif; text-decoration: none; border-radius: 8px; margin: 5px; box-shadow: 0 3px 6px rgba(0,0,0,0.15);">
                            🏥 MHRS RANDEVU AL
                        </a>
                    </div>
                    <p style="text-align: center; font-size: 12px; color: #666; margin-top: 10px;">(Tüm linkler resmi kamu kurumlarına aittir)</p>
                </div>

                <!-- ═══════════ ADSENSE REKLAM ALANI: ALT BANNER ═══════════ -->
                <!-- Buraya AdSense reklam birimi kodunuzu yapıştırın -->
                <!-- Örnek: -->
                <!-- <ins class="adsbygoogle"
                     style="display:block"
                     data-ad-client="ca-pub-XXXXXXXXXXXXXXXX"
                     data-ad-slot="XXXXXXXXXX"
                     data-ad-format="auto"
                     data-full-width-responsive="true"></ins>
                <script>(adsbygoogle = window.adsbygoogle || []).push({{}});</script> -->
                <!-- ═══════════ ADSENSE REKLAM ALANI SONU ═══════════ -->
                <div style="margin: 10px 15px; padding: 12px; background: #f0fff0; border: 2px dashed #a8d8a8; border-radius: 8px; text-align: center;">
                    <span style="font-size: 12px; color: #6ba86b;">📢 Alt Banner Reklam Alanı (728x90 veya Responsive)</span>
                </div>

                <div class="footer">
                    <p>Bu sayfa her gün cron job ile otomatik güncellenir.</p>
                    <p>Son güncelleme: {date_info["display"]} {date_info["time"]} (Türkiye Saati)</p>
                    <p style="margin-top: 5px;">Dosya: kamu-hukuk-rehberi-{date_info["iso"]}.html</p>
                    <p style="margin-top: 10px; font-size: 11px; opacity: 0.7;">Tüm linkler resmi kamu kurumlarına aittir. Siyasi içerik barındırmaz.</p>
                </div>
            </div>
        </div>

        <!-- ═══════════ YAN MENÜ / SIDEBAR (%30) ═══════════ -->
        <aside class="sidebar">
            <div class="sidebar-sticky">

                <!-- ═══════════ ADSENSE REKLAM ALANI: YAN MENÜ 1 ═══════════ -->
                <!-- Buraya 300x250 (Orta Dikdörtgen) reklam birimi kodunuzu yapıştırın -->
                <!-- Örnek: -->
                <!-- <ins class="adsbygoogle"
                     style="display:inline-block;width:300px;height:250px"
                     data-ad-client="ca-pub-XXXXXXXXXXXXXXXX"
                     data-ad-slot="XXXXXXXXXX"></ins>
                <script>(adsbygoogle = window.adsbygoogle || []).push({{}});</script> -->
                <!-- ═══════════ ADSENSE REKLAM ALANI SONU ═══════════ -->
                <div class="sidebar-ad">
                    <p class="ad-label">📢 Reklam Alanı (300x250)</p>
                    <div style="width: 100%; height: 250px; background: #f8f8f8; border: 2px dashed #ddd; border-radius: 8px; display: flex; align-items: center; justify-content: center;">
                        <span style="color: #aaa; font-size: 13px;">AdSense 300x250</span>
                    </div>
                </div>

                <!-- Sidebar Bilgi Kutusu -->
                <div class="sidebar-ad" style="background: #eaf2f8; border: 1px solid #b8d4e8;">
                    <h4 style="font-size: 14px; color: #1a5276; margin-bottom: 8px;">📌 Günlük Bilgi</h4>
                    <p style="font-size: 12px; color: #555; line-height: 1.5;">Bu sayfa her gün otomatik güncellenir. Resmi Gazete, İŞKUR ve Kariyer.gov.tr kaynaklarından güncel bilgiler sunulur.</p>
                </div>

                <!-- ═══════════ ADSENSE REKLAM ALANI: YAN MENÜ 2 ═══════════ -->
                <!-- Buraya 160x600 (Geniş Gökdelen) veya 300x600 reklam birimi kodunuzu yapıştırın -->
                <!-- Örnek: -->
                <!-- <ins class="adsbygoogle"
                     style="display:inline-block;width:300px;height:600px"
                     data-ad-client="ca-pub-XXXXXXXXXXXXXXXX"
                     data-ad-slot="XXXXXXXXXX"></ins>
                <script>(adsbygoogle = window.adsbygoogle || []).push({{}});</script> -->
                <!-- ═══════════ ADSENSE REKLAM ALANI SONU ═══════════ -->
                <div class="sidebar-ad">
                    <p class="ad-label">📢 Reklam Alanı (300x600)</p>
                    <div style="width: 100%; height: 400px; background: #f8f8f8; border: 2px dashed #ddd; border-radius: 8px; display: flex; align-items: center; justify-content: center;">
                        <span style="color: #aaa; font-size: 13px;">AdSense 300x600</span>
                    </div>
                </div>

                <!-- ═══════════ ADSENSE REKLAM ALANI: YAN MENÜ 3 (EK) ═══════════ -->
                <!-- İsteğe bağlı: Buraya ek bir 300x250 reklam birimi ekleyebilirsiniz -->
                <!-- <ins class="adsbygoogle"
                     style="display:inline-block;width:300px;height:250px"
                     data-ad-client="ca-pub-XXXXXXXXXXXXXXXX"
                     data-ad-slot="XXXXXXXXXX"></ins>
                <script>(adsbygoogle = window.adsbygoogle || []).push({{}});</script> -->
                <!-- ═══════════ ADSENSE REKLAM ALANI SONU ═══════════ -->
                <div class="sidebar-ad">
                    <p class="ad-label">📢 Ek Reklam Alanı (300x250)</p>
                    <div style="width: 100%; height: 250px; background: #fff8f0; border: 2px dashed #f0d0a0; border-radius: 8px; display: flex; align-items: center; justify-content: center;">
                        <span style="color: #c0a060; font-size: 13px;">AdSense 300x250</span>
                    </div>
                </div>

            </div>
        </aside>
    </div>
</body>
</html>'''

    return html


def main():
    """Ana çalıştırma fonksiyonu - her çalıştırmada O GÜNÜN tarihini alır."""
    print("🚀 Kamu Hukuk Rehberi Scraper başlatılıyor...")
    date_info = get_turkish_date()
    print(f"📅 Dinamik Tarih: {date_info['display']} {date_info['time']}")
    print(f"📄 Çıktı dosyası: kamu-hukuk-rehberi-{date_info['iso']}.html")

    # Çıktı klasörünü oluştur
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(script_dir, "output")
    os.makedirs(output_dir, exist_ok=True)

    # Resmi Gazete
    print("\n📋 Resmi Gazete taranıyor...")
    resmi_gazete_items = scrape_resmi_gazete()
    print(f"   ✅ {len(resmi_gazete_items)} öğe bulundu")

    # İŞKUR
    print("\n💼 İŞKUR ilanları taranıyor...")
    iskur_items = scrape_iskur()
    print(f"   ✅ {len(iskur_items)} öğe bulundu")

    # Kariyer.gov.tr
    print("\n🏛️ Kariyer.gov.tr taranıyor...")
    kariyer_items = scrape_kariyer_gov()
    print(f"   ✅ {len(kariyer_items)} öğe bulundu")

    # HTML oluştur
    print("\n🔨 HTML sayfası oluşturuluyor...")
    html_content = generate_html(resmi_gazete_items, iskur_items, kariyer_items)

    # Dinamik dosya adı: kamu-hukuk-rehberi-YYYY-MM-DD.html
    filename = f"kamu-hukuk-rehberi-{date_info['iso']}.html"

    # output/ klasörüne kaydet
    output_path = os.path.join(output_dir, filename)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"   ✅ {output_path}")

    # Ayrıca /workspace/ altına da kaydet (kullanıcı isteği)
    workspace_path = f"/workspace/{filename}"
    with open(workspace_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"   ✅ {workspace_path}")

    # index.html olarak da kaydet (web sunucusu için en güncel versiyon)
    index_path = os.path.join(output_dir, "index.html")
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"   ✅ {index_path} (en güncel)")

    print(f"\n🎉 Scraper başarıyla tamamlandı!")
    print(f"   Tarih: {date_info['display']}")
    print(f"   Dosya: {filename}")
    return html_content


if __name__ == "__main__":
    main()