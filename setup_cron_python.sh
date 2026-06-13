#!/bin/bash
# ============================================
# PYTHON SCRAPER - CRON KURULUM SCRIPTİ
# Kendi sunucunuzda çalıştırın
# ============================================

echo "🚀 Python Scraper Cron Kurulumu"
echo "================================"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Python bağımlılıkları
echo "📦 Bağımlılıklar yükleniyor..."
pip3 install -r "$SCRIPT_DIR/requirements.txt"

# Çıktı klasörü
mkdir -p "$SCRIPT_DIR/output"

# Test çalıştırması
echo "🧪 Test..."
python3 "$SCRIPT_DIR/scraper.py"

# Cron job ekle (her gün 04:00)
CRON_CMD="0 4 * * * cd $SCRIPT_DIR && /usr/bin/python3 scraper.py >> $SCRIPT_DIR/scraper.log 2>&1"
(crontab -l 2>/dev/null | grep -v "scraper.py"; echo "$CRON_CMD") | crontab -

echo ""
echo "✅ Kurulum tamamlandı!"
echo "   Scraper her gün 04:00'te çalışacak"
echo "   Çıktı: $SCRIPT_DIR/output/index.html"
echo "   Log: $SCRIPT_DIR/scraper.log"
echo ""
echo "📋 WordPress'e göndermek için:"
echo "   python3 wp-post.py"
echo ""
echo "🔧 Cron kontrol: crontab -l"