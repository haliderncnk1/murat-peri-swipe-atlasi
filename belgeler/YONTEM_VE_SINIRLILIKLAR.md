# Kaynaklar, yöntem ve veri sınırlılıkları

## Ne hazırlandı?
Bu atlas, mevcut yeni proje verilerinden 55 ayrı coğrafi Swipe haritası içerir: 42 uydu/su sınıflandırma karşılaştırması ve 13 CORINE karşılaştırması. On baraj/proje çevresi, Murat ve Peri koridorları ve 1984'ün gerçek veri penceresi ayrı bölgeler olarak ele alındı. Tüm eski dosyalar korunur; yalnız bu yeni atlas klasörüne çıktı yazılır. Kullanıcının Windows klasörüne doğrudan erişim yoktur; aynı projenin bulut kopyası kullanıldı.

## Gerçek görüntü tarihleri ve kapsam
- 06.07.1984: Landsat 5 TM, Collection 1 Level 1'den mevcut TOA dönüşümü. Gerçek veri yalnız Orta Peri / Özlüce çevresindedir. Eski tam Özlüce penceresinin su-maskesi geçerli kapsamı yaklaşık %86,3'tür; bu pencere 1984 için tam kapsamlı sayılmadı. Onun yerine 1984'ün gerçek geçerli piksel sınırlarına kırpılan 585330–615840 m doğu, 4328370–4350960 m kuzey (EPSG:32637) penceresi kullanıldı. Bu pencere tüm Özlüce rezervuarı değildir.
- 08.08.1990: Landsat 5 TM, Collection 1 Level 1 / TOA; sahne katalog bulutu %1. Bütün çalışma bölgelerinde kullanılabilir. Özlüce için 1990 inşaat sürecidir; inşaat öncesi saf doğal vadi olarak sunulmaz.
- 26.08.2020: Landsat 8 OLI, Collection 1 Level 1 / TOA; sahne katalog bulutu %0.
- 24.08.2026: Copernicus Sentinel-2 L2A / BOA; 37SEC, 37SFC, 37SED, 37SFD, sahne katalog bulutu %0–0,07. Mevcut ortak analiz bantları 20 m'dir; doğal görünür bantların 10 m oluşu bu dosyaların çözünürlüğünü 10 m yapmaz.
- 22.07.1984, 08.09.1984, 24.08.1990 ve 10.08.2020 için metadata bulunur, gerekli gerçek bant dosyaları yoktur. Bu tarihler için görüntü veya Swipe üretilmedi. 26.08.2020 RT ve T1 metadata kayıtları ayrı çekim tarihleri gibi sayılmadı.

## Kapsam seçimi ve NoData
Bir uydu tarihinin inceleme penceresinde en az %95 geçerli su-sınıflandırma kapsamı olması gerekir. Çiftin ortak geçerli kapsamı da en az %95 olmalıdır. 0 ve 1 geçerli sınıflardır; 255 NoData'dır. Bu eşik kalite seçim kuralıdır; %95 doğruluk veya güven aralığı değildir. Rasterin dış koordinat sınırı ile gerçek veri bulunan alan birbirine karıştırılmadı.

Her iki taraf tarayıcıda yalnız ortak geçerli maske üzerinden gösterilir. Eksik pikseller kara veya su kabul edilmez; dama deseniyle görünür. İki görüntü eşit ekran boyutuna yeniden boyutlandırılarak hizalanmadı. Eski JPEG/PNG karşılaştırmaları envantere alındı; yeni haritalar coğrafi referanslı GeoTIFF kaynaklarından yeniden görüntülendi.

## Coğrafi hizalama
Kaynak çalışma koordinat sistemi WGS 84 / UTM 37N (EPSG:32637) ve metredir. Her bölgenin sınırı 25 örnekle sıklaştırılan kenar noktalarıyla EPSG:3857'e dönüştürüldü. Bölgedeki bütün tarihler için aynı dış sınır, raster genişliği, yüksekliği ve altı parametreli dönüşüm kullanıldı. RGB bantlar bilineer; su ve kategorik sınıflar en yakın komşu/kategorik rasterleştirme ile hazırlandı. Her görsele dünya dosyası (JGW/PGW), ortak grid.json ve grid.prj eşlik eder.

Haritanın iki tarafı tek bir kamera kullanır; yakınlaştırma veya sürükleme tarafları ayrı hareket ettiremez. Enlem/boylam okuması WGS 84'tür. Ölçek çubuğu Web Mercator ölçeğini orta enlemin kosinüsüyle yerel yatay mesafeye düzeltir. Görüntüdeki kuzey yukarıdır. Yeniden örnekleme kaynak verinin 20/30 m ayrıntı sınırını veya konum doğruluğunu iyileştirmez.

Hizalama kaynak coğrafi referanslarına dayanır. Bağımsız yer kontrol noktalarıyla görüntüler arası mutlak kayma veya alt piksel konum doğruluğu kalibre edilmedi. Kaynak ortorektifikasyon ve piksel konum belirsizlikleri özellikle dar kıyılarda değişim görünümünü etkileyebilir. Ortak ızgara, mutlak saha konum doğruluğu sertifikası değildir.

## Renk ve su maskeleri
Aynı bant anlamları (kırmızı/yeşil/mavi), 0–0,38 görüntüleme aralığı ve 1/1,6 üs dönüşümü bütün uydu tarihlerinde korunur. Her görüntüye ayrı yüzdelik kontrast uygulanmaz. Landsat TOA ile Sentinel-2 BOA arasında atmosfer ve sensör farkı vardır; renk/parlaklık farkı nicel çevresel etki değildir.

Mevcut su maskeleri kullanıldı. MNDWI=(yeşil−SWIR1)/(yeşil+SWIR1); su için MNDWI>0, NIR<0,15, SWIR1<0,10 ve kaynak bulut/gölge koşulları uygulanmıştı. Landsat'ta mevcut BQA, Sentinel-2'de mevcut SCL geçerlilik ölçütleri korunur. Sentinel-2'de 0,01 km² altı küçük lekeleri eleme adımı vardır; Landsat ile bu işlem farkı özellikle 2020–2026 için belirsizliktir. SCL 2/7 koyu göl suyu da içerdiğinden önceki spektral karar korunmuştur. Bu atlas yeni saha doğruluk örneklemesi veya yeni su sınıflandırma kalibrasyonu yapmaz.

## Sayısal gözlem ne anlama geliyor?
Uydu çiftlerindeki alanlar, sabit dikdörtgen inceleme penceresinde iki tarihte de geçerli piksellerden hesaplandı. Ortak analiz grid'i EPSG:32637, 30 m; bir piksel 0,0009 km²'dir. Sayılar normal rezervuar alanı, depolama hacmi veya doluluk oranı değildir; penceredeki bütün su sınıflarını kapsayabilir. Komşu haritalar örtüştüğünden bu sayılar toplanarak tekil havza su artışı elde edilmez. İki gözlem aradaki değişimi sınırlar; su tutmanın kesin başlangıç yılını veya gününü saptamaz.

İki tarih de işletmeden sonraysa başlık/metin bunu açıkça söyler. 2020–2026 çifti yeni bir barajın oluşum anı olarak anlatılmaz. Beyhan II bir proje konumu kaydıdır; işletme/gövde doğrulanmadı. Çevresindeki su yüzeyi Beyhan II rezervuarı sayılmaz. Baraj işaretleri mevcut ikincil koordinatlardan gelir; saha/jeodezik ölçüm değildir.

## CORINE 2000 / 2018
Mevcut CORINE_2000 ve CORINE_2018 vektörleri aynı beş ana sınıfa ayrıldı. Kategorik haritalar aynı coğrafi gridde gösterilir. Alanlar EPSG:32637'de gerçek vektör geometrilerinin sabit pencereyle kesişiminden hesaplandı. Ürün yılları tek günlük uydu görüntüsü değildir. 25 ha en küçük haritalama birimi küçük kıyı, parsel ve yol değişimlerini kaçırabilir. Raster gösterim grid'i ürünün mekânsal ayrıntısını artırmaz.

CORINE 2000, Özlüce'de işletme sonrasıdır; CORINE 2018, Aşağı Kaleköy'ün 2020 üretim başlangıcından öncedir. Her tesis için aynı iki yıl gerçek baraj öncesi/sonrası çifti sayılmaz. Sınıf deseni değişikliği tek başına barajın neden olduğu arazi kaybını kanıtlamaz.

## İncelenen ancak tarihli fotoğraf çifti yapılmayan analizler
- JRC v1.4 occurrence, seasonality ve transitions: 1984–2021 dönem özetleridir. 1984 ve 2021'e ait iki gerçek fotoğraf veya kesin ilk dolum yılı üretmez; bu nedenle yıllık görüntü çifti gibi kullanılmadı.
- ESA WorldCover 2020 v100 ve 2021 v200: algoritma sürümleri farklıdır. Fark doğrudan bir yıllık fiziksel arazi değişimi veya baraj etkisi sayılmadı; bu atlas için neden-sonuç Swipe hikâyesi üretilmedi.
- SRTM 2000 ve GLO-30: farklı tarihler/düşey referanslar ve yüzey düzeltmeleri vardır. Farklar su altında gerçek yatak veya baraj etkisi olarak yorumlanmadı; uydu RGB Swipe'ına çevrilmedi.
- NDTI yalnız 24.08.2026'da mevcuttur; göreli optik göstergedir. Zamansal tortu tutulması, mg/L veya kütle karşılaştırması üretilmedi.
- Güncel OSM yerleşim/yol yakınlıkları tarihsel yerleşim kaybı veya yol deplasmanı envanteri değildir. Önceki kaynaklı tarihsel örnekler bu görsel farklardan yeniden türetilmedi.

## Kaynaklar
Landsat: USGS/NASA, Google Cloud açık arşivi. Sentinel-2: Copernicus, Element 84 Earth Search açık STAC. CORINE: Copernicus/EEA resmî vektör servisleri. © OpenStreetMap katkıcıları, ODbL. Kaynakların tıklanabilir tam listesi KAYNAKLAR.md / kaynaklar.json içinde; her bölümde de ilgili kayıtlar vardır. Önceki kaynak erişim kaydı 08.11.2026, atlas üretimi 10.11.2026'dır. Yeni görüntü indirilmedi.

## İddia sınırı
Yerleşim kaybı, taşınan kişi/hane sayısı, ekolojik zarar, tarihsel olaylar veya tortu miktarı yalnız görüntü farkına dayanarak kesinleştirilmez. Sınıflandırılmış su/örtü deseninin farklı olması, nedenin baraj olduğunu tek başına kanıtlamaz. Kalibrasyon, saha doğrulaması, yıllık seri ve bağımsız tarihsel kanıt gereken sorular açık bırakılır.
