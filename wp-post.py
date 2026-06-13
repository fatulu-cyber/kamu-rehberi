#!/usr/bin/env python3
"""
WordPress REST API ile otomatik makale gönderme.
Scraper çıktısını WordPress'e otomatik yayınlar.

Kullanım:
  python3 wp-post.py

Önce config.json dosyasını düzenleyin.
WordPress → Kullanıcılar → Profiliniz → Uygulama Şifreleri bölümünden
yeni bir uygulama şifresi oluşturun.
"""

import os
import json
import requests
from datetime import datetime, timezone, timedelta

TR_TZ = timezone(timedelta(hours=3))


def load_config():
    """config.json dosyasını yükler."""
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
    
    if not os.path.exists(config_path):
        # Örnek config oluştur
        example_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.example.json")
        print(f"❌ config.json bulunamadı!")
        print(f"   config.example.json dosyasını config.json olarak kopyalayıp düzenleyin:")
        print(f"   cp config.example.json config.json")
        return None
    
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def post_to_wordpress(html_content, title=None):
    """HTML içeriğini WordPress'e gönderi olarak yayınlar."""
    config = load_config()
    if not config:
        return False

    wp = config["wordpress"]
    now = datetime.now(TR_TZ)
    
    if not title:
        title = f"Günlük Kamu Rehberi - {now.strftime('%d.%m.%Y')}"

    # WordPress REST API endpoint
    api_url = f"{wp['url'].rstrip('/')}/wp-json/wp/v2/posts"

    post_data = {
        "title": title,
        "content": html_content,
        "status": "publish",
        "categories": [wp.get("category_id", 1)],
        "meta": {
            "_yoast_wpseo_metadesc": f"Bugünün Resmi Gazete kararları ve İŞKUR ilanları - {now.strftime('%d.%m.%Y')}"
        }
    }

    try:
        response = requests.post(
            api_url,
            json=post_data,
            auth=(wp["username"], wp["app_password"]),
            headers={"Content-Type": "application/json"},
            timeout=30
        )

        if response.status_code == 201:
            post = response.json()
            print(f"✅ WordPress'e yayınlandı!")
            print(f"   URL: {post.get('link', 'N/A')}")
            print(f"   ID: {post.get('id', 'N/A')}")
            return True
        else:
            print(f"❌ WordPress hatası: {response.status_code}")
            print(f"   Yanıt: {response.text[:200]}")
            return False

    except Exception as e:
        print(f"❌ Bağlantı hatası: {e}")
        return False


def main():
    """Scraper çıktısını okuyup WordPress'e gönderir."""
    output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output", "index.html")
    
    if not os.path.exists(output_path):
        print("❌ output/index.html bulunamadı. Önce scraper.py çalıştırın.")
        print("   python3 scraper.py")
        return

    with open(output_path, "r", encoding="utf-8") as f:
        html_content = f.read()

    # Body içeriğini çıkar (WordPress için sadece body kısmı)
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html_content, "lxml")
    body = soup.find("body")
    
    if body:
        content = str(body.decode_contents())
    else:
        content = html_content

    print("📤 WordPress'e gönderiliyor...")
    post_to_wordpress(content)


if __name__ == "__main__":
    main()