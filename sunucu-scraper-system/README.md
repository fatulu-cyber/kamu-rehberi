# 🇹🇷 Kamu Rehberi Scraper - Kendi Sunucunuz İçin

Resmi Gazete kararlarını ve İŞKUR kamu personel alım ilanlarını her gün otomatik kazıyıp HTML sayfası oluşturan ve isteğe bağlı olarak WordPress'e otomatik gönderen sistem.

**Atoms platformundan bağımsız, kendi sunucunuzda (VPS/DigitalOcean/Hetzner vb.) çalışır.**

---

## ⚠️ ÖNEMLİ: BAĞIMSIZ SİSTEM UYARISI

> **Bu sistem ana sitenizden (istanbulburda.com) TAMAMEN BAĞIMSIZDIR.**
>
> - ❌ Ana sitenizin veritabanına dokunmaz
> - ❌ Ana sitenizin tema dosyalarını değiştirmez
> - ❌ Mevcut AdSense kodlarınızı etkilemez
> - ❌ Ana sitenizin altyapısına müdahale etmez
> - ✅ Sadece WordPress REST API ile yeni makale ekler
> - ✅ Ayrı bir sunucuda veya ayrı bir klasörde çalışır
> - ✅ İstanbulburda.com'un mevcut altyapısını etkilemez
>
> **Kurulum önerisi:** Ayrı bir VPS veya aynı sunucuda farklı bir dizin kullanın:
> ```
> /home/kullanici/scraper-system/   ← Scraper sistemi (BU)
> /var/www/istanbulburda.com/       ← Ana siteniz (DOKUNULMAZ)
> ```

---

## 📁 Dosya Yapısı

```
sunucu-scraper-system/
├── scraper.py              ← Python scraper (AdSense reklam alanlı)
├── scraper.js              ← Node.js scraper (alternatif)
├── wp-post.py              ← WordPress'e otomatik gönderi (Python)
├── wp-post.js              ← WordPress'e otomatik gönderi (Node.js)
├── cron-runner.js          ← Node.js dahili cron zamanlayıcı
├── config.example.json     ← WordPress ayarları şablonu
├── requirements.txt        ← Python bağımlılıkları
├── package.json            ← Node.js bağımlılıkları
├── setup_cron_python.sh    ← Python cron kurulum scripti
├── setup_cron_node.sh      ← Node.js cron kurulum scripti
├── .github/
│   └── workflows/
│       └── main.yml        ← (Opsiyonel) GitHub Actions versiyonu
└── README.md               ← Bu dosya
```

---

## 🅰️ Python ile Kurulum (En Basit)

### 1. Sunucuya dosyaları yükleyin
```bash
scp -r sunucu-scraper-system/ kullanici@sunucu:/home/kullanici/
```

### 2. Bağımlılıkları yükleyin ve test edin
```bash
cd /home/kullanici/sunucu-scraper-system
pip3 install -r requirements.txt
python3 scraper.py
```

### 3. Otomatik cron kurulumu
```bash
chmod +x setup_cron_python.sh
./setup_cron_python.sh
```

Bu komut:
- Bağımlılıkları yükler
- Test çalıştırması yapar
- Her gün saat 04:00'te çalışacak cron job ekler

### 4. WordPress'e otomatik gönderi (Opsiyonel)
```bash
cp config.example.json config.json
nano config.json  # WordPress bilgilerinizi girin
python3 wp-post.py
```

Cron'a WordPress gönderisini de eklemek için:
```bash
crontab -e
# Şu satırı ekleyin (04:05'te, scraper'dan 5 dk sonra):
5 4 * * * cd /home/kullanici/sunucu-scraper-system && /usr/bin/python3 wp-post.py >> wp-post.log 2>&1
```

---

## 🅱️ Node.js ile Kurulum

### 1. Bağımlılıkları yükleyin
```bash
cd sunucu-scraper-system
npm install
```

### 2. Test
```bash
node scraper.js
```

### 3. PM2 ile sürekli çalıştırma (Önerilen)
```bash
npm install -g pm2
pm2 start cron-runner.js --name "kamu-scraper"
pm2 save
pm2 startup  # Sunucu yeniden başlasa bile çalışır
```

### 4. Veya otomatik kurulum scripti
```bash
chmod +x setup_cron_node.sh
./setup_cron_node.sh
```

---

## 📢 AdSense Reklam Kodlarınızı Ekleme

Scraper'ın ürettiği HTML sayfalarında (kamu-hukuk-rehberi-YYYY-MM-DD.html) reklam alanları hazır olarak gelir. Kendi AdSense kodlarınızı eklemek için aşağıdaki adımları izleyin:

### Adım 1: Publisher ID'nizi Ekleyin

`scraper.py` dosyasındaki `<head>` bölümünde şu satırı bulun:
```html
<!-- ═══════════ ADSENSE ANA KODU ═══════════ -->
<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-XXXXXXXXXXXXXXXX" crossorigin="anonymous"></script>
<!-- ═══════════ ADSENSE ANA KODU SONU ═══════════ -->
```

`ca-pub-XXXXXXXXXXXXXXXX` kısmını **kendi Publisher ID'nizle** değiştirin.

### Adım 2: Reklam Birimlerini Yerleştirin

HTML çıktısında 6 farklı reklam alanı bulunur. Her birini `═══════════` yorum satırlarıyla kolayca bulabilirsiniz:

| Konum | Yorum İşareti | Önerilen Boyut |
|-------|---------------|----------------|
| Header altı (üst banner) | `ADSENSE REKLAM ALANI: ÜST BANNER` | 728x90 veya Responsive |
| İçerik araları | `ADSENSE REKLAM ALANI: İÇERİK ARASI` | In-article (fluid) |
| Footer üstü (alt banner) | `ADSENSE REKLAM ALANI: ALT BANNER` | 728x90 veya Responsive |
| Yan menü 1 | `ADSENSE REKLAM ALANI: YAN MENÜ 1` | 300x250 |
| Yan menü 2 | `ADSENSE REKLAM ALANI: YAN MENÜ 2` | 300x600 veya 160x600 |
| Yan menü 3 (ek) | `ADSENSE REKLAM ALANI: YAN MENÜ 3` | 300x250 |

### Adım 3: Yorum Satırlarını Aktifleştirin

Her reklam alanında örnek kod yorum satırı olarak verilmiştir. Aktifleştirmek için:

1. `<!-- ` ve ` -->` işaretlerini kaldırın
2. `ca-pub-XXXXXXXXXXXXXXXX` → Kendi Publisher ID'niz
3. `data-ad-slot="XXXXXXXXXX"` → AdSense'den aldığınız reklam birimi slot numarası

**Örnek (Üst Banner):**
```html
<!-- ÖNCE (yorum satırı - pasif): -->
<!-- <ins class="adsbygoogle"
     style="display:block"
     data-ad-client="ca-pub-XXXXXXXXXXXXXXXX"
     data-ad-slot="XXXXXXXXXX"
     data-ad-format="auto"
     data-full-width-responsive="true"></ins>
<script>(adsbygoogle = window.adsbygoogle || []).push({});</script> -->

<!-- SONRA (aktif): -->
<ins class="adsbygoogle"
     style="display:block"
     data-ad-client="ca-pub-1234567890123456"
     data-ad-slot="9876543210"
     data-ad-format="auto"
     data-full-width-responsive="true"></ins>
<script>(adsbygoogle = window.adsbygoogle || []).push({});</script>
```

### Adım 4: Placeholder Kutularını Kaldırın (Opsiyonel)

Reklam kodlarınızı ekledikten sonra, görsel placeholder kutularını (`📢 Reklam Alanı` yazan kutuları) silebilirsiniz. Bunlar sadece geliştirme sırasında konumları göstermek içindir.

### ⚠️ Önemli Notlar

- **ads.txt dosyanız:** Bu sistem mevcut ads.txt dosyanıza dokunmaz. ads.txt'nizin doğru olduğundan emin olun.
- **Mevcut reklamlar:** Ana sitenizde zaten çalışan AdSense reklamları bu sistemden etkilenmez.
- **Sayfa düzeni:** Flexbox tabanlı layout: Ana içerik %70, Sidebar %30. Mobilde sidebar gizlenir.
- **Otomatik reklamlar:** Publisher ID'yi ekledikten sonra Google'ın otomatik reklam yerleştirmesi de çalışır.

---

## 🌐 Web Sunucusu Entegrasyonu

Oluşturulan `output/index.html` dosyasını web sunucunuzla yayınlayın:

### Nginx
```nginx
server {
    listen 80;
    server_name kamu.siteniz.com;
    
    location / {
        root /home/kullanici/sunucu-scraper-system/output;
        index index.html;
        add_header Cache-Control "public, max-age=3600";
    }
}
```

### Apache
```apache
<VirtualHost *:80>
    ServerName kamu.siteniz.com
    DocumentRoot /home/kullanici/sunucu-scraper-system/output
    <Directory /home/kullanici/sunucu-scraper-system/output>
        Require all granted
    </Directory>
</VirtualHost>
```

---

## 📰 WordPress Entegrasyonu

### Uygulama Şifresi Oluşturma
1. WordPress Admin → Kullanıcılar → Profiliniz
2. "Uygulama Şifreleri" bölümüne gidin
3. Yeni şifre adı: "Scraper" → "Yeni Uygulama Şifresi Ekle"
4. Oluşan şifreyi `config.json`'a yapıştırın

### config.json Örneği
```json
{
  "wordpress": {
    "url": "https://www.istanbulburda.com",
    "username": "admin",
    "app_password": "abcd 1234 efgh 5678 ijkl 9012",
    "category_id": 1
  }
}
```

### Tam Otomatik Akış
```bash
# Tek komutla: kazı + WordPress'e gönder
npm run full
# veya Python ile:
python3 scraper.py && python3 wp-post.py
```

---

## ⏰ Zamanlama Özeti

| Saat (TR) | İşlem |
|-----------|-------|
| 04:00 | Scraper çalışır, HTML güncellenir |
| 04:05 | WordPress'e otomatik gönderi (opsiyonel) |

---

## 🔧 Sorun Giderme

### Log dosyalarını kontrol edin
```bash
tail -f scraper.log
tail -f wp-post.log
```

### Cron çalışıyor mu?
```bash
crontab -l
# veya PM2 ile:
pm2 status
pm2 logs kamu-scraper
```

### Manuel test
```bash
python3 scraper.py   # veya: node scraper.js
cat output/index.html | head -20
```

---

## ⚠️ Önemli Notlar

- **Tamamen ücretsiz** - Kendi sunucunuzda çalışır, ek maliyet yok
- **Ana siteden bağımsız** - istanbulburda.com'un hiçbir dosyasına dokunmaz
- **Ayrı sunucu/klasör** - Kendi dizininde bağımsız çalışır
- **Atoms'tan bağımsız** - Hiçbir dış platforma bağımlılık yok
- **Siyaset içermez** - Otomatik filtre ile siyasi içerik engellenir
- **Mobil uyumlu** - Responsive, büyük butonlu, yaşlı dostu tasarım
- **WordPress uyumlu** - REST API ile otomatik makale gönderimi
- **TE Bilişim uyumlu** - Inline CSS, site şablonunu bozmaz
- **AdSense hazır** - Reklam alanları yerleştirilmiş, sadece kodlarınızı yapıştırın