# AutoTyper Pro 3.0

macOS ve Windows için otomatik yazma, Mouse Jiggler / Anti-AFK ve yerel makro kaydı. Varsayılan arayüz İngilizcedir; Settings bölümünden Türkçe seçilebilir. Hesap gerekmez, telemetri yoktur, açılışta etkinlik başlamaz.

[macOS / Windows paketlerini indir](https://github.com/hamitcf1/AutoTyperPro/releases/tag/v3.0.0) · [English documentation](README.md) · [Kurulum ve izinler](docs/INSTALLATION.md)

## Kurulum

Mac: işlemcine uygun DMG’yi aç, uygulamayı Applications’a sürükle, disk imajını çıkar ve kurulu kopyayı aç. Apple Silicon için arm64, Intel için x64 seç.

Windows: Setup installer kullan veya portable ZIP’in tamamını çıkarıp uygulama klasöründeki EXE’yi aç. İlk açılış tanıtımı atlanabilir ve uygulamadan tekrar gösterilebilir.

Paketler Developer ID notarizasyonu veya Windows Authenticode imzası içermez. SHA256 dosyaları ve platform doğrulama raporları release’e eklenmiştir.

## Araçlar

- **Auto Typer:** altı hız seçeneği, 0–60 saniye başlangıç beklemesi, doğal ritim, kelime arası duraklama ve satır davranışı. Metnini yapıştır, başlat ve geri sayım sırasında hedef uygulamaya geç.
- **Mouse Jiggler / Anti-AFK:** önerilen Gentle, Balanced ve Keyboard-only ayarları; özelleştirilebilir boşta eşiği, aralık, hareket mesafesi, yönü, süresi ve tuş/kısayol. Varsayılan tuş etkinliği kapalıdır. Tıklama yapmaz; yazma ve makro sırasında bekler.
- **Macros:** fare hareketi, tıklama, fiziksel tuş ve kaydırma ayrı ayrı kaydedilebilir. Hareket kaydı varsayılandır. Yolu önizle, kaydet, hızını ve tekrarlarını ayarlayarak oynat. Kayıtlar en fazla beş dakika / 10.000 olaydır. Klavye kayıtları kendi işletim sisteminde oynatılır ve klavye düzenine bağlıdır.
- **Profiller ve ayarlar:** yazma/Anti-AFK profillerini kaydet, yeniden adlandır, çoğalt, JSON olarak içe/dışa aktar. İngilizce/Türkçe, koyu/açık/sistem teması ve ses tercihleri kalıcıdır.

**ESC bütün etkinlikleri durdurur.** Kayıt ve oynatma yalnızca sen başlatınca çalışır; uygulamayı kapatınca durur. Makrolar, profiller ve metin cihazında kalır. Klavye kaydı hassas giriş içerebilir; yalnızca ihtiyacın olan kategorileri seç.

## macOS izinleri

Sistem Ayarları → Gizlilik ve Güvenlik → Erişilebilirlik bölümünde kurulu AutoTyperPro kopyasını etkinleştir. Yeni macOS sürümlerinde bölümün adı Aygıt Denetimi ve Veri Erişimi olabilir. Kaynaktan çalıştırırken Python veya terminal izni gerekebilir.

İzin açık görünmesine rağmen uygulama reddedildiğini bildiriyorsa aynı kurulu kopyayı açtığından emin ol, etkinliği durdur ve uygulamanın yeniden başlatma eylemini kullan. Yeniden derlenen ad-hoc imzalı paketin kimliği değişebilir; eski izin kaydını kaldırıp mevcut kopyayı eklemek gerekebilir. Yeniden başlatma metin ve ayarları korur.

## Kaynaktan çalışma ve katkı

Python 3.11+ ve Tk desteği gerekir. macOS başlatıcısı: `./run_mac.command`. Windows komutları, testler ve paketleme için [English README](README.md) ve [Contributing](CONTRIBUTING.md) belgelerini kullan.
