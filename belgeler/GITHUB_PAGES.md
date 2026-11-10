# GitHub Pages'e hazır site

Bu dizin eksiksiz bir statik sitedir. Sunucu, veri tabanı, API anahtarı, hesap parolası, CDN veya derleme adımı gerekmez. Bu yayın kopyası, kullanıcı talebiyle yeni bir GitHub deposunda yayımlanmıştır. Canlı adres: https://haliderncnk1.github.io/murat-peri-swipe-atlasi/

Yayın dizini:
- index.html — bütün karşılaştırmaların filtrelenebilir girişi
- karsilastirmalar.html — her karşılaştırmanın istenen yedi alanlı tam kaydı
- haritalar/ — 55 bağımsız Swipe haritası; ?embed=1 Sidecar görünümü
- assets/ — yerel JavaScript/CSS, ortak gridde görüntüler, maskeler ve dünya dosyaları
- belgeler/ — veri envanteri, CSV/JSON aktarım kayıtları, kaynak/yöntem ve kontrol sonuçları
- kodlar/ — yeniden üretim ve tarayıcı kontrol kodları
- .nojekyll — dosyaların Jekyll dönüşümü olmadan sunulmasını sağlar

Bu dizinin içeriği bir deponun köküne veya seçtiğiniz yayın alt dizinine konabilir. GitHub Pages için Settings > Pages bölümünde uygun branch ve root/docs dizini seçilir. Bağlantılar göreli olduğundan bir proje deposunun /DEPO_ADI/ alt yolunda da çalışır. Büyük ham GeoTIFF'ler siteye eklenmez; yalnız hafif türetilmiş görseller sunulur. Her görsel 100 MiB GitHub dosya sınırının altındadır.

Gerçek yayın adresi site yayımlandıktan sonra oluşur. Bu paketteki https://GITHUB_KULLANICI_ADI.github.io/DEPO_ADI/ adresleri yalnız açıkça işaretlenmiş şablonlardır. Otomatik olarak açılmış ya da çalıştığı doğrulanmış bir yayın adresi değildir.

Kaynak veriler projenin 01_Ham_Veriler ve 02_Islenmis_Veriler klasörlerinde kalır. Bu site 06_StoryMaps altında yeni oluşturulmuştur; önceki dosyalar değiştirilmez. Düzenlenebilir bir ArcGIS web map veya otomatik StoryMaps içe aktarma projesi yerine bağımsız etkileşimli haritalar teslim edilir.
