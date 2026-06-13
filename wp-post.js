#!/usr/bin/env node
/**
 * WordPress REST API ile otomatik makale gönderme (Node.js versiyonu).
 * 
 * Kullanım:
 *   node wp-post.js
 * 
 * Önce config.json dosyasını düzenleyin.
 */

const fs = require('fs');
const path = require('path');
const https = require('https');
const http = require('http');

function loadConfig() {
  const configPath = path.join(__dirname, 'config.json');
  
  if (!fs.existsSync(configPath)) {
    console.error('❌ config.json bulunamadı!');
    console.error('   config.example.json dosyasını config.json olarak kopyalayıp düzenleyin:');
    console.error('   cp config.example.json config.json');
    return null;
  }
  
  return JSON.parse(fs.readFileSync(configPath, 'utf-8'));
}

function postToWordPress(htmlContent, title) {
  return new Promise((resolve, reject) => {
    const config = loadConfig();
    if (!config) { reject(new Error('Config yok')); return; }
    
    const wp = config.wordpress;
    const now = new Date();
    const dateStr = now.toLocaleDateString('tr-TR', { timeZone: 'Europe/Istanbul' });
    
    if (!title) {
      title = `Günlük Kamu Rehberi - ${dateStr}`;
    }
    
    const postData = JSON.stringify({
      title: title,
      content: htmlContent,
      status: 'publish',
      categories: [wp.category_id || 1]
    });
    
    const url = new URL(`${wp.url.replace(/\/$/, '')}/wp-json/wp/v2/posts`);
    const auth = Buffer.from(`${wp.username}:${wp.app_password}`).toString('base64');
    
    const options = {
      hostname: url.hostname,
      port: url.port || (url.protocol === 'https:' ? 443 : 80),
      path: url.pathname,
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Basic ${auth}`,
        'Content-Length': Buffer.byteLength(postData)
      }
    };
    
    const client = url.protocol === 'https:' ? https : http;
    
    const req = client.request(options, (res) => {
      let data = '';
      res.on('data', chunk => { data += chunk; });
      res.on('end', () => {
        if (res.statusCode === 201) {
          const post = JSON.parse(data);
          console.log('✅ WordPress\'e yayınlandı!');
          console.log(`   URL: ${post.link || 'N/A'}`);
          console.log(`   ID: ${post.id || 'N/A'}`);
          resolve(true);
        } else {
          console.error(`❌ WordPress hatası: ${res.statusCode}`);
          console.error(`   Yanıt: ${data.substring(0, 200)}`);
          resolve(false);
        }
      });
    });
    
    req.on('error', (e) => {
      console.error(`❌ Bağlantı hatası: ${e.message}`);
      reject(e);
    });
    
    req.write(postData);
    req.end();
  });
}

async function main() {
  const outputPath = path.join(__dirname, 'output', 'index.html');
  
  if (!fs.existsSync(outputPath)) {
    console.error('❌ output/index.html bulunamadı. Önce scraper çalıştırın.');
    return;
  }
  
  const htmlContent = fs.readFileSync(outputPath, 'utf-8');
  
  // Body içeriğini çıkar
  const bodyMatch = htmlContent.match(/<body[^>]*>([\s\S]*)<\/body>/i);
  const content = bodyMatch ? bodyMatch[1] : htmlContent;
  
  console.log('📤 WordPress\'e gönderiliyor...');
  await postToWordPress(content);
}

main().catch(console.error);