# Bir Nehrin Hafızası — Murat–Peri Swipe Atlası

Canlı site: https://haliderncnk1.github.io/murat-peri-swipe-atlasi/
Kaynak depo: https://github.com/haliderncnk1/murat-peri-swipe-atlasi

55 ayrı coğrafi Swipe haritası: 42 uydu/su maskesi, 13 CORINE karşılaştırması. Uydu tarihleri: 06.07.1984, 08.08.1990, 26.08.2020 ve 24.08.2026. CORINE ürün yılları: 2000 ve 2018.

- Harita ve hikâye listesi: https://haliderncnk1.github.io/murat-peri-swipe-atlasi/karsilastirmalar.html
- Karşılaştırma CSV'si: https://haliderncnk1.github.io/murat-peri-swipe-atlasi/belgeler/karsilastirma_listesi.csv
- Gerçek Sidecar bağlantıları: https://haliderncnk1.github.io/murat-peri-swipe-atlasi/belgeler/storymaps_sidecar.csv
- Kaynak ve yöntem: https://haliderncnk1.github.io/murat-peri-swipe-atlasi/belgeler/YONTEM_VE_SINIRLILIKLAR.html

## StoryMaps Sidecar

Her haritanın `?embed=1` adresi Sidecar medya paneline yerleştirmek içindir. Uydu çiftlerinde yalnız su maskesi için `?embed=1&katman=su` kullanılır. `storymaps_sidecar.csv` ve `.json` içinde gerçek yayın bağlantıları, kısa metinler ve iframe örnekleri vardır. Yerleştirme, ArcGIS kuruluşunun izinlerine bağlıdır.

1984 yalnız gerçek kapsamı bulunan Orta Peri / Özlüce penceresinde kullanılır; rezervuarın tamamını kapsadığı iddia edilmez. Beyhan II bir proje konumudur. Sınıflandırma farkı tek başına yerleşim kaybı veya ekolojik zarar kanıtı sayılmaz.

## Teknik yapı

Statik HTML/CSS/JavaScript; haritalar ve görseller kendi içinde bulunur. API anahtarı, sunucu veya derleme adımı gerekmez. `.nojekyll` korunur; Pages kaynağı `main` ve `/(root)` dizinidir. Ham GeoTIFF'ler yayıma eklenmez. Yeniden üretim kodları `kodlar/`, bilimsel veri envanteri ve kontroller `belgeler/` altındadır. Yerel dosya koruma kontrolünün kurum içi dosya listesi yayın paketine alınmaz.

Atlas üretimi: 10 Kasım 2026. GitHub Pages yayını: 11 Kasım 2026. Bu yayın kopyası orijinal proje ve atlas dosyalarını değiştirmeden hazırlandı.
