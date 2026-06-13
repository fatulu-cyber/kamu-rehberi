#!/bin/bash
# ============================================
# NODE.JS SCRAPER - CRON KURULUM SCRIPTİ
# Kendi sunucunuzda çalıştırın
# ============================================

echo "🚀 Node.js Scraper Cron Kurulumu"
echo "================================="

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Node bağımlılıkları
echo "📦 Bağımlılıklar yükleniyor..."
cd "$SCRIPT_DIR" && npm install

# Çıktı klasörü
mkdir -p "$SCRIPT_DIR/output"

# Test çalıştırması
echo "🧪 Test..."
node "$SCRIPT_DIR/scraper.js"

echo ""
echo "✅ Test başarılı!"
echo ""
echo "📋 Otomatik çalıştırma seçenekleri:"
echo ""
echo "--- SEÇENEK A: PM2 (Önerilen) ---"
echo "   npm install -g pm2"
echo "   pm2 start $SCRIPT_DIR/cron-runner.js --name kamu-scraper"
echo "   pm2 save && pm2 startup"
echo ""
echo "--- SEÇENEK B: Sistem Cron ---"
CRON_CMD="0 4 * * * cd $SCRIPT_DIR && /usr/bin/node scraper.js >> $SCRIPT_DIR/scraper.log 2>&1"
echo "   Crontab'a eklemek için:"
echo "   crontab -e"
echo "   Satır: $CRON_CMD"
echo ""

# Kullanıcıya sor
read -p "PM2 ile otomatik kurulsun mu? (e/h): " CEVAP
if [ "$CEVAP" = "e" ] || [ "$CEVAP" = "E" ]; then
    npm install -g pm2 2>/dev/null || sudo npm install -g pm2
    pm2 start "$SCRIPT_DIR/cron-runner.js" --name "kamu-scraper"
    pm2 save
    echo "✅ PM2 ile kuruldu! pm2 status ile kontrol edin."
else
    (crontab -l 2>/dev/null | grep -v "scraper.js"; echo "$CRON_CMD") | crontab -
    echo "✅ Cron job eklendi! crontab -l ile kontrol edin."
fi