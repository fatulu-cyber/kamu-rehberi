#!/usr/bin/env node
/**
 * Cron Runner - Scraper'ı her gün otomatik çalıştırır.
 * Her çalıştırmada O GÜNÜN tarihini dinamik olarak alır.
 * 
 * PM2 ile sürekli çalıştırma:
 *   npm install -g pm2
 *   pm2 start cron-runner.js --name "kamu-scraper"
 *   pm2 save && pm2 startup
 */

const cron = require('node-cron');
const { main: runScraper } = require('./scraper');

console.log('⏰ Kamu Hukuk Rehberi Cron Runner başlatıldı');
console.log('📅 Her gün saat 04:00 (Türkiye) otomatik çalışacak');
console.log('📄 Çıktı: kamu-hukuk-rehberi-YYYY-MM-DD.html (dinamik)');
console.log('💡 Manuel: node scraper.js');
console.log('---');

// Her gün 04:00 Türkiye saati
cron.schedule('0 4 * * *', async () => {
  const now = new Date().toISOString();
  console.log(`\n🔄 [${now}] Zamanlanmış çalıştırma başlıyor...`);
  try {
    await runScraper();
    console.log('✅ Günlük güncelleme tamamlandı');
  } catch (err) {
    console.error('❌ Hata:', err.message);
  }
}, { timezone: 'Europe/Istanbul' });

// İlk çalıştırma (başlangıçta bir kez)
console.log('🚀 İlk çalıştırma yapılıyor...');
runScraper().catch(e => console.error('İlk çalıştırma hatası:', e.message));