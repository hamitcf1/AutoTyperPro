# AutoTyper Pro

Mac için iki yerel araç: doğal ritimde otomatik yazma ve bağımsız Mouse Jiggler. Yenilenen Türkçe arayüz, grafit yüzeyler, geniş metin editörü, canlı ilerleme ve açık çalışma durumları sunar. Veriler cihazında kalır.

[English documentation](README_EN.md)

## Bu Mac’te çalıştırma

Bu Mac’e kurulan uygulama: `~/Applications/AutoTyperPro.app`. Finder’dan çift tıklayarak aç. Yeniden oluşturulan paket `dist/AutoTyperPro.app` altında bulunur.

Kaynak koddan:

```bash
./run_mac.command
```

Python 3.11 veya üstü, Tk desteği ve macOS gerekir. Bu sürüm Apple Silicon üzerinde Python 3.14 ile geliştirilmiştir. İlk kaynak çalıştırma bir `.venv` oluşturur; başlatıcı her çalıştırmada bağımlılıkları kontrol edip eksikleri yükler.

## Erişilebilirlik izni

Klavye ve fare olaylarını gönderebilmek için **Sistem Ayarları → Gizlilik ve Güvenlik → Erişilebilirlik** bölümünde AutoTyperPro’yu etkinleştir. Kaynaktan çalıştırırken Python veya başlatan terminal uygulamasının izni gerekebilir. Uygulamanın izin çubuğu ilgili ayarları açar. İzin verdikten sonra uygulamayı yeniden açman gerekebilir. Yönetici/root olarak çalıştırma gerekmez.

Dağıtım paketi yerel olarak imzalanır; Apple Developer sertifikasıyla imzalanmış veya notarize edilmiş bir sürüm değildir. Başka Mac’lerde Gatekeeper tarafından ek kullanıcı onayı istenebilir.

## Auto Typer

1. Metnini yaz veya yapıştır.
2. Hız seç: çok hızlı (30 ms), hızlı (60 ms), dengeli (100 ms), yavaş (150 ms), çok yavaş (250 ms) veya rastgele (10–5000 ms).
3. Başlangıç beklemesini (0–60 saniye), doğal yazmayı, kelime arası beklemeyi ve satır davranışını ayarla.
4. **Yazmaya başla** düğmesine bas; geri sayım sırasında hedef uygulamaya geç.
5. ESC ile durdur. ESC her iki aracı da durdurur.

Satır sonları boşluğa çevrilebilir, Shift+Enter olarak gönderilebilir veya atlanabilir. Türkçe ve diğer Unicode karakterleri macOS’un yerel olaylarıyla gönderilir. Hedef uygulamanın Unicode girişini ve seçtiğin satır davranışını desteklemesi gerekir. İlerleme ve tahmini süre yazma boyunca güncellenir. Tahmin, hedef uygulamanın kendi gecikmesini kapsamaz.

## Mouse Jiggler

Ayrı sekmeden **Jiggler’ı başlat** düğmesine bas. Varsayılan olarak 60 saniye giriş yapılmadığında yaklaşık 1 noktalık hareket yapıp 80 ms sonra imleci yerine getirir. Hareketler arasında en az 30 saniye bekler. İki süre de 5–3600 saniye aralığında ayarlanabilir. macOS sentetik olayları da boşta süre hesabına dahil edebilir; sonraki hareket için hem eşik hem aralık sağlanmalıdır.

- Tıklama yapmaz, açılışta kendiliğinden başlamaz.
- Yazma etkinliğinde bekler; sekme değiştirilince çalışmaya devam eder.
- Kullanıcı hareket sırasında fareyi taşırsa imleci eski konuma zorlamaz.
- F18 tuş etkinliği isteğe bağlıdır ve varsayılan olarak kapalıdır; bazı uygulamalarda kısayol tetikleyebilir.
- Durdur, ESC veya uygulamayı kapatma etkinliği bitirir.
- İşletim sisteminin uyku veya başka uygulamaların durum davranışını garanti etmez.

## Test ve paketleme

```bash
.venv/bin/python -m unittest discover -s tests -v
./make_executable_mac.sh
```

Paket çıktısı `dist/AutoTyperPro.app` olur. Sesler ve CustomTkinter kaynakları pakete dahil edilir. Sanal ortam ve paket çıktıları Git’e eklenmez. `requirements-lock.txt`, bu Mac’te doğrulanan bağımlılık sürümlerini kaydeder; macOS’a özgü PyObjC paketleri içerir. Diğer platformlarda `requirements.txt` kullan.

Windows’ta yazma için pynput adaptörü ve `make_executable.bat` korunur; bu sürümün Windows paketi burada doğrulanmamıştır. Mouse Jiggler bu sürümde macOS’a özeldir.
