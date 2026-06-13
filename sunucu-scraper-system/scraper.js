#!/usr/bin/env node
/**
 * Resmi Gazete, İŞKUR ve Kariyer.gov.tr Kamu İlanları Scraper (Node.js)
 * Her çalıştırıldığında O GÜNÜN TARİHİNİ dinamik olarak alır.
 * Çıktı dosya adı: kamu-hukuk-rehberi-YYYY-MM-DD.html
 */

const axios = require('axios');
const cheerio = require('cheerio');
const fs = require('fs');
const path = require('path');

const HEADERS = {
  'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
  'Accept-Language': 'tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7',
};

const AY_MAP = ['Ocak','Şubat','Mart','Nisan','Mayıs','Haziran','Temmuz','Ağustos','Eylül','Ekim','Kasım','Aralık'];
const GUN_MAP = ['Pazar','Pazartesi','Salı','Çarşamba','Perşembe','Cuma','Cumartesi'];

function getTurkishDate() {
  // Her çalıştırmada O ANDAKİ tarihi dinamik olarak alır
  const now = new Date(new Date().toLocaleString('en-US', { timeZone: 'Europe/Istanbul' }));
  const gun = now.getDate();
  const ay = AY_MAP[now.getMonth()];
  const yil = now.getFullYear();
  const gunAdi = GUN_MAP[now.getDay()];
  const saat = `${String(now.getHours()).padStart(2,'0')}:${String(now.getMinutes()).padStart(2,'0')}`;
  // ISO format: YYYY-MM-DD
  const iso = `${yil}-${String(now.getMonth()+1).padStart(2,'0')}-${String(gun).padStart(2,'0')}`;
  return { display: `${gun} ${ay} ${yil}, ${gunAdi}`, time: saat, iso };
}

function isSiyasi(text) {
  const keywords = ['parti','seçim','muhalefet','iktidar','milletvekili','meclis','siyasi','propaganda'];
  return keywords.some(k => text.toLowerCase().includes(k));
}

async function scrapeResmiGazete() {
  const results = [];
  try {
    const { data } = await axios.get('https://www.resmigazete.gov.tr/', { headers: HEADERS, timeout: 15000 });
    const $ = cheerio.load(data);
    const seen = new Set();
    $('a, h3, h4, li').each((_, el) => {
      const text = $(el).text().trim();
      let href = $(el).attr('href') || '';
      if (text && text.length > 10 && !seen.has(text) && !isSiyasi(text)) {
        if (href && !href.startsWith('http')) href = `https://www.resmigazete.gov.tr/${href}`;
        else if (!href) href = 'https://www.resmigazete.gov.tr/';
        seen.add(text);
        results.push({ title: text.substring(0,120), link: href, source: 'Resmi Gazete' });
      }
    });
  } catch (e) {
    console.error('   ⚠️ Resmi Gazete hatası:', e.message);
    results.push({ title: 'Resmi Gazete - Bugünkü Sayı', link: 'https://www.resmigazete.gov.tr/', source: 'Resmi Gazete' });
  }
  return results.slice(0, 10);
}

async function scrapeIskur() {
  const results = [];
  const kamuKeys = ['personel','alım','ilan','memur','işçi','kamu','belediye','hastane','sözleşmeli','kadro'];
  try {
    const { data } = await axios.get('https://esube.iskur.gov.tr/', { headers: HEADERS, timeout: 15000 });
    const $ = cheerio.load(data);
    const seen = new Set();
    $('a').each((_, el) => {
      const text = $(el).text().trim();
      let href = $(el).attr('href') || '';
      if (text && text.length > 15 && !seen.has(text) && kamuKeys.some(k => text.toLowerCase().includes(k))) {
        if (!href.startsWith('http')) href = `https://esube.iskur.gov.tr${href}`;
        seen.add(text);
        results.push({ title: text.substring(0,120), link: href, source: 'İŞKUR' });
      }
    });
  } catch (e) {
    console.error('   ⚠️ İŞKUR hatası:', e.message);
  }
  if (!results.length) {
    results.push(
      { title: 'İŞKUR Açık Kamu İş İlanları - Güncel Liste', link: 'https://esube.iskur.gov.tr/Istihdam/AcikIsIlan662.aspx', source: 'İŞKUR' },
      { title: 'İŞKUR TYP İlanları', link: 'https://esube.iskur.gov.tr/Istihdam/AcikIsIlan662.aspx', source: 'İŞKUR' }
    );
  }
  return results.slice(0, 10);
}

async function scrapeKariyerGov() {
  const results = [];
  const kamuKeys = ['personel','alım','memur','kamu','belediye','bakanlık','müdürlük','başkanlık','üniversite'];
  try {
    const { data } = await axios.get('https://www.kariyer.gov.tr/', { headers: HEADERS, timeout: 15000 });
    const $ = cheerio.load(data);
    const seen = new Set();
    $('a').each((_, el) => {
      const text = $(el).text().trim();
      let href = $(el).attr('href') || '';
      if (text && text.length > 15 && !seen.has(text) && !isSiyasi(text) && kamuKeys.some(k => text.toLowerCase().includes(k))) {
        if (!href.startsWith('http')) href = `https://www.kariyer.gov.tr${href}`;
        seen.add(text);
        results.push({ title: text.substring(0,120), link: href, source: 'Kariyer.gov.tr' });
      }
    });
  } catch (e) {
    console.error('   ⚠️ Kariyer.gov.tr hatası:', e.message);
  }
  if (!results.length) {
    results.push(
      { title: 'Kariyer.gov.tr - Kamu Personel Alım İlanları', link: 'https://www.kariyer.gov.tr/', source: 'Kariyer.gov.tr' },
      { title: 'Kariyer.gov.tr - Devlet Memuru Alım Duyuruları', link: 'https://www.kariyer.gov.tr/kamu-ilanlari', source: 'Kariyer.gov.tr' }
    );
  }
  return results.slice(0, 10);
}

function generateHTML(gazetteItems, iskurItems, kariyerItems) {
  const { display, time, iso } = getTurkishDate();
  
  const makeButtons = (items, bgColor, icon) => items.map(i => `
    <div style="margin:15px 0;text-align:center;">
      <a href="${i.link}" target="_blank" rel="noopener noreferrer" style="display:inline-block;padding:16px 30px;background-color:${bgColor};color:#fff;font-size:18px;font-weight:bold;font-family:sans-serif;text-decoration:none;border-radius:8px;box-shadow:0 4px 6px rgba(0,0,0,.15);text-transform:uppercase;max-width:90%;line-height:1.4;">${icon} ${i.title.substring(0,80)}</a>
      <p style="font-size:12px;color:#666;margin:5px 0;">(${i.source} - Resmi Kamu Kaynağıdır)</p>
    </div>`).join('');

  const gazetteButtons = makeButtons(gazetteItems, '#1a5276', '📋');
  const iskurButtons = makeButtons(iskurItems, '#27ae60', '💼');
  const kariyerButtons = makeButtons(kariyerItems, '#8e44ad', '🏛️');

  return `<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Kamu Hukuk Rehberi - ${display} | Resmi Gazete & İŞKUR & Kariyer.gov.tr</title>
<meta name="description" content="${display} tarihli Resmi Gazete kararları, İŞKUR ve Kariyer.gov.tr kamu personel alım ilanları.">
<style>*{margin:0;padding:0;box-sizing:border-box}body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:#f5f5f5;color:#333;line-height:1.6;padding:10px}.c{max-width:800px;margin:0 auto;background:#fff;border-radius:12px;box-shadow:0 2px 20px rgba(0,0,0,.1);overflow:hidden}.hd{background:linear-gradient(135deg,#c0392b,#e74c3c);color:#fff;padding:25px 20px;text-align:center}.hd h1{font-size:24px;margin-bottom:8px}.nt{background:#fff3cd;border:2px solid #ffc107;padding:12px 20px;margin:15px;border-radius:8px;font-size:14px;text-align:center}.sc{padding:20px;border-bottom:3px solid #f0f0f0}.sc h2{font-size:22px;color:#2c3e50;margin-bottom:15px;padding-bottom:10px;border-bottom:2px solid #eee}.qk{background:#eaf2f8;padding:20px;margin:15px;border-radius:8px}.ft{background:#2c3e50;color:#ecf0f1;padding:20px;text-align:center;font-size:13px}.bg{display:inline-block;background:#27ae60;color:#fff;padding:4px 12px;border-radius:20px;font-size:12px;margin-top:8px}.info{margin-top:20px;padding:15px;background:#f8f9fa;border-radius:8px;border-left:4px solid #1a5276;font-size:14px;color:#555}@media(max-width:600px){.hd h1{font-size:20px}.sc h2{font-size:18px}}</style>
</head>
<body>
<div class="c">
<div class="hd"><h1>🇹🇷 KAMU HUKUK REHBERİ</h1><p>${display}</p><span class="bg">✅ Otomatik Güncellendi - ${time}</span></div>
<div class="nt">🌍 <strong>For English / Für Deutsch / Pour Français / للعربية:</strong><br>Kendi dilinizde okumak için tarayıcınızın çeviri butonunu kullanın.</div>
<div class="qk"><h3 style="font-size:18px;margin-bottom:10px;color:#1a5276;">⚡ HIZLI ERİŞİM</h3>
<div style="text-align:center;">
<a href="https://www.resmigazete.gov.tr/" target="_blank" style="display:inline-block;padding:14px 24px;background:#e50914;color:#fff;font-size:16px;font-weight:bold;font-family:sans-serif;text-decoration:none;border-radius:8px;margin:5px;box-shadow:0 3px 6px rgba(0,0,0,.15);">👉 RESMİ GAZETE 👈</a>
<a href="https://esube.iskur.gov.tr/Istihdam/AcikIsIlan662.aspx" target="_blank" style="display:inline-block;padding:14px 24px;background:#27ae60;color:#fff;font-size:16px;font-weight:bold;font-family:sans-serif;text-decoration:none;border-radius:8px;margin:5px;box-shadow:0 3px 6px rgba(0,0,0,.15);">👉 İŞKUR İLANLARI 👈</a>
<a href="https://www.kariyer.gov.tr/" target="_blank" style="display:inline-block;padding:14px 24px;background:#8e44ad;color:#fff;font-size:16px;font-weight:bold;font-family:sans-serif;text-decoration:none;border-radius:8px;margin:5px;box-shadow:0 3px 6px rgba(0,0,0,.15);">👉 KARİYER.GOV.TR 👈</a>
<a href="https://www.mhrs.gov.tr/" target="_blank" style="display:inline-block;padding:14px 24px;background:#16a085;color:#fff;font-size:16px;font-weight:bold;font-family:sans-serif;text-decoration:none;border-radius:8px;margin:5px;box-shadow:0 3px 6px rgba(0,0,0,.15);">👉 HASTANE RANDEVUSU 👈</a>
</div></div>
<div class="sc"><h2>📋 RESMİ GAZETE - ${display.toUpperCase()} KARARLARI</h2><p style="font-size:14px;color:#666;margin-bottom:15px;">Bugün (${display}) yayımlanan resmi kararlara doğrudan ulaşın.</p>${gazetteButtons}<div class="info"><strong>📌 Bilgi:</strong> Resmi Gazete, T.C. Cumhurbaşkanlığı tarafından her gün yayımlanır.</div></div>
<div class="sc"><h2>💼 İŞKUR - KAMU PERSONEL ALIMLARI</h2><p style="font-size:14px;color:#666;margin-bottom:15px;">Güncel kamu personeli alım ilanlarına başvurun.</p>${iskurButtons}<div class="info" style="border-left-color:#27ae60;"><strong>📌 Nasıl Başvurulur?</strong><br>1. Yeşil butona tıklayın<br>2. T.C. Kimlik No ile giriş yapın<br>3. "Başvur" butonuna basın</div></div>
<div class="sc"><h2>🏛️ KARİYER.GOV.TR - DEVLET MEMURLUK İLANLARI</h2><p style="font-size:14px;color:#666;margin-bottom:15px;">Kariyer.gov.tr üzerinden güncel kamu alım duyurularına ulaşın.</p>${kariyerButtons}<div class="info" style="border-left-color:#8e44ad;"><strong>📌 Kariyer.gov.tr:</strong> T.C. Cumhurbaşkanlığı İnsan Kaynakları Ofisi resmi portalıdır.</div></div>
<div class="sc"><h2>🔗 DİĞER HİZMETLER</h2>
<div style="text-align:center;margin:10px 0;">
<a href="https://www.turkiye.gov.tr/" target="_blank" style="display:inline-block;padding:14px 24px;background:#2980b9;color:#fff;font-size:16px;font-weight:bold;font-family:sans-serif;text-decoration:none;border-radius:8px;margin:5px;">🏛️ E-DEVLET</a>
<a href="https://sonuc.osym.gov.tr/" target="_blank" style="display:inline-block;padding:14px 24px;background:#d35400;color:#fff;font-size:16px;font-weight:bold;font-family:sans-serif;text-decoration:none;border-radius:8px;margin:5px;">📝 ÖSYM SONUÇ</a>
<a href="https://www.mhrs.gov.tr/" target="_blank" style="display:inline-block;padding:14px 24px;background:#16a085;color:#fff;font-size:16px;font-weight:bold;font-family:sans-serif;text-decoration:none;border-radius:8px;margin:5px;">🏥 MHRS RANDEVU</a>
</div></div>
<div class="ft"><p>Bu sayfa her gün cron job ile otomatik güncellenir.</p><p>Son güncelleme: ${display} ${time} (Türkiye Saati)</p><p style="margin-top:5px;">Dosya: kamu-hukuk-rehberi-${iso}.html</p><p style="margin-top:10px;font-size:11px;opacity:.7;">Tüm linkler resmi kamu kurumlarına aittir. Siyasi içerik barındırmaz.</p></div>
</div>
</body></html>`;
}

async function main() {
  const dateInfo = getTurkishDate();
  console.log('🚀 Kamu Hukuk Rehberi Scraper başlatılıyor...');
  console.log(`📅 Dinamik Tarih: ${dateInfo.display} ${dateInfo.time}`);
  console.log(`📄 Çıktı: kamu-hukuk-rehberi-${dateInfo.iso}.html`);
  
  const outputDir = path.join(__dirname, 'output');
  if (!fs.existsSync(outputDir)) fs.mkdirSync(outputDir, { recursive: true });
  
  console.log('\n📋 Resmi Gazete taranıyor...');
  const gazette = await scrapeResmiGazete();
  console.log(`   ✅ ${gazette.length} öğe`);
  
  console.log('\n💼 İŞKUR taranıyor...');
  const iskur = await scrapeIskur();
  console.log(`   ✅ ${iskur.length} öğe`);
  
  console.log('\n🏛️ Kariyer.gov.tr taranıyor...');
  const kariyer = await scrapeKariyerGov();
  console.log(`   ✅ ${kariyer.length} öğe`);
  
  console.log('\n🔨 HTML oluşturuluyor...');
  const html = generateHTML(gazette, iskur, kariyer);
  
  // Dinamik dosya adı
  const filename = `kamu-hukuk-rehberi-${dateInfo.iso}.html`;
  
  // output/ klasörüne kaydet
  fs.writeFileSync(path.join(outputDir, filename), html, 'utf-8');
  console.log(`   ✅ output/${filename}`);
  
  // /workspace/ altına da kaydet
  fs.writeFileSync(`/workspace/${filename}`, html, 'utf-8');
  console.log(`   ✅ /workspace/${filename}`);
  
  // index.html olarak da (en güncel)
  fs.writeFileSync(path.join(outputDir, 'index.html'), html, 'utf-8');
  console.log('   ✅ output/index.html (en güncel)');
  
  console.log(`\n🎉 Tamamlandı! Dosya: ${filename}`);
}

module.exports = { main };
if (require.main === module) main().catch(console.error);