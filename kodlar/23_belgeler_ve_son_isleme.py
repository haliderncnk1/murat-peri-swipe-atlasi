"""Yeni atlasa kaynak atıfları, yedi alanlı katalog ve yayın belgeleri ekler."""
from pathlib import Path
from html import escape
import csv,json,runpy,shutil,hashlib

SITE=Path(__file__).resolve().parents[1];ROOT=SITE.parents[1];DOC=SITE/'belgeler'

METHOD='''# Kaynaklar, yöntem ve veri sınırlılıkları

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
'''

SIDECAR='''# StoryMaps Sidecar aktarımı

Her karşılaştırma için ayrı harita HTML dosyası hazırdır. Haritayı normal bağlantıyla açınca önerilen hikâye metni, gözlem, kaynak ve sınırlar görünür. Aynı haritanın ?embed=1 sürümü yalnız harita alanını gösterir ve Sidecar medya paneli için hazırlanmıştır. Tarihler, veri atfı ve ortak geçerli alan gösterimi korunur.

1. Site dosyalarının tamamını aynı yapıda GitHub Pages'e veya uygun HTTPS statik sunucuya koyun. README.md / GITHUB_PAGES.md dosyaları dizini açıklar. Atlas bu oturumda çevrimiçi yayımlanmadı.
2. Yayımdan sonra gerçek site adresinizi storymaps_sidecar.csv / .json içindeki GITHUB_KULLANICI_ADI ve DEPO_ADI yer tutucularının yerine kullanın. Bunlar örnek şablondur, mevcut yayın bağlantısı değildir.
3. Bir Sidecar slaytının medya paneline haritanın HTTPS adresini Embed/yerleştirme olarak ekleyin; ?embed=1 görünümünü seçin. Uydu çiftinde yalnız su maskesi için ?embed=1&katman=su kullanılır.
4. Metin alanına aynı kaydın metin ve altyazı alanlarını ekleyin. Kaynak tarihlerini ve sınırlılıkları koruyun.

Her harita telefon/dar iframe boyutuna uyum sağlar. Kaydırıcı klavye oklarıyla da çalışır. Haritada sürükleme iki tarafı birlikte taşır; artı/eksi düğmeleri yakınlaştırır. Yeniden başlat düğmesi gerçek ortak coğrafi çerçeveye döner.

GitHub Pages'e hazır olmak çevrimiçi yayımlanmış olmak değildir. Bilgisayardaki dosya yolu veya Drive ZIP önizlemesi StoryMaps içinde canlı harita adresi sayılmaz. Yerel inceleme için ZIP'in tamamını çıkarıp index.html dosyasını açabilirsiniz; hesap/ArcGIS Pro/Python gerektirmez. Kurumsal tarayıcı yerel dosyaları engellerse HTTPS statik site üzerinden açılır. Üretim kodlarını çalıştırmak, hazır haritaları görüntülemek için gerekli değildir.
'''

PAGES='''# GitHub Pages'e hazır site

Bu dizin eksiksiz bir statik sitedir. Sunucu, veri tabanı, API anahtarı, hesap parolası, CDN veya derleme adımı gerekmez. Bu oturumda depo oluşturulmadı ve herkese açık yayın yapılmadı.

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
'''

def doc_page(title,text):
 return '<!doctype html><html lang="tr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'+escape(title)+'</title><link rel="stylesheet" href="../assets/site.css"></head><body><main class="wrap fulltext"><a href="../index.html">← Atlas</a><h1>'+escape(title)+'</h1><pre>'+escape(text)+'</pre></main></body></html>'

def main():
 module=runpy.run_path(str(SITE/'kodlar/22_swipe_atlasi_uret.py'));make_page=module['make_page'];maps=json.loads((DOC/'karsilastirma_manifesti.json').read_text())
 existing={s['id']:s for s in json.loads((ROOT/'07_Kaynakca/kaynakca.json').read_text())}
 with (ROOT/'02_Islenmis_Veriler/baraj_envanteri.csv').open(encoding='utf-8-sig') as f:dams={d['id']:d for d in csv.DictReader(f)}
 essential={'YUK':['S01'],'ASK':['S02'],'BE1':['S03'],'BE2':['S11','S12'],'KIG':['S05','S23'],'YED':['S10','S14'],'OZL':['S22'],'PEM':['S07'],'SEY':['S08'],'TAT':['S09']}
 source_map={}
 for m in maps:
  additions=[]
  for d in m['dams']:
   row=dams[d['id']]
   additions.append({'id':'K_'+d['id'],'name':d['name']+' — ikincil koordinat kaynağı','url':row['konum_kaynak']})
   for sid in essential[d['id']]:
    s=existing[sid];additions.append({'id':sid,'name':s['title'],'url':s['url']})
  sources={s['url']:s for s in m['sources']+additions};m['sources']=list(sources.values())
  if m['region_kind']=='proje_konumu' and m['kind']=='corine':m['limits']+=' Beyhan II’nin işletmeye girişi ve gövdesi doğrulanmadı; su sınıfı bu projenin rezervuarı olarak yorumlanmaz.'
  for s in m['sources']:source_map[s['url']]=s
  (SITE/m['map_file']).write_text(make_page(m),encoding='utf-8')
 (DOC/'karsilastirma_manifesti.json').write_text(json.dumps(maps,ensure_ascii=False,indent=2),encoding='utf-8')
 for name in ['site.css','map.js','gallery.js']:shutil.copyfile(SITE/'kodlar/sablonlar'/name,SITE/'assets'/name)
 # Aynı kayıttan liste ve Sidecar alanlarını güncelle; veri/alan hesabını değiştirme.
 listings=[];sidecars=[];entries=[];markdown=['# Bütün karşılaştırmalar','',f'Toplam {len(maps)} ayrı harita. Her kayıtta istenen yedi alan ve bilimsel sınır bulunur.','']
 for m in maps:
  row={'bolum_basligi':m['title'],'baraj_veya_vadi':m['region_name'],'karsilastirilan_yillar':' / '.join(m['years']),'kullanilan_veri_dosyalari':' | '.join(m['source_files']),'gozlemlenen_degisim':m['observation'],'onerilen_hikaye_metni':m['story_text'],'harita_dosya_yolu':str((SITE/m['map_file']).relative_to(ROOT)),'bilimsel_sinir':m['limits'],'goreli_web_yolu':m['map_file'],'sidecar_yolu':m['map_file']+'?embed=1','su_maskesi_sidecar_yolu':m['map_file']+'?embed=1&katman=su' if m['kind']=='uydu' else ''};listings.append(row)
  url='https://GITHUB_KULLANICI_ADI.github.io/DEPO_ADI/'+m['map_file']+'?embed=1';sidecars.append({'id':m['id'],'bolum_basligi':m['title'],'metin':m['story_text'],'altyazi':m['limits'],'goreli_yol':m['map_file']+'?embed=1','yayin_sonrasi_url_sablonu':url,'iframe_sablonu':'<iframe src="'+url+'" title="'+escape(m['title'],quote=True)+'" width="100%" height="640" style="border:0" loading="lazy" allowfullscreen></iframe>'})
  markdown+=['## '+m['title']]+['- **'+k.replace('_',' ')+':** '+v for k,v in row.items()]+['']
  labels=[('İlgili baraj / vadi',row['baraj_veya_vadi']),('Karşılaştırılan yıllar',row['karsilastirilan_yillar']),('Kullanılan veri dosyaları',row['kullanilan_veri_dosyalari']),('Gözlemlenen değişim',row['gozlemlenen_degisim']),('Önerilen hikâye metni',row['onerilen_hikaye_metni']),('Haritanın dosya yolu',row['harita_dosya_yolu']),('Bilimsel sınır',row['bilimsel_sinir'])]
  fields=''.join('<dt>'+escape(k)+'</dt><dd>'+escape(v)+'</dd>' for k,v in labels)
  entries.append('<article class="catalog-entry" id="'+m['id']+'"><h2>'+escape(m['title'])+'</h2><dl>'+fields+'</dl><p><a class="button" href="'+m['map_file']+'">Swipe haritasını aç</a> <a href="'+m['map_file']+'?embed=1">Sidecar görünümü</a></p></article>')
 for filename,data in [('karsilastirma_listesi.csv',listings),('storymaps_sidecar.csv',sidecars)]:
  with (DOC/filename).open('w',encoding='utf-8-sig',newline='') as f:w=csv.DictWriter(f,fieldnames=list(data[0]));w.writeheader();w.writerows(data)
 (DOC/'KARSILASTIRMA_LISTESI.md').write_text('\n'.join(markdown),encoding='utf-8');(DOC/'storymaps_sidecar.json').write_text(json.dumps(sidecars,ensure_ascii=False,indent=2),encoding='utf-8')
 (SITE/'karsilastirmalar.html').write_text('<!doctype html><html lang="tr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Karşılaştırmaların tam listesi</title><link rel="stylesheet" href="assets/site.css"></head><body><main class="wrap"><a href="index.html">← Atlas</a><h1>Karşılaştırmaların tam listesi</h1><p>Her bölüm için istenen yedi alan, bilimsel sınır ve ayrı harita bağlantısı. <a href="belgeler/karsilastirma_listesi.csv" download>CSV olarak indir</a></p>'+''.join(entries)+'</main></body></html>',encoding='utf-8')
 sources=list(source_map.values());(DOC/'kaynaklar.json').write_text(json.dumps(sources,ensure_ascii=False,indent=2),encoding='utf-8')
 lines=['# Kaynaklar','', 'Önceki veri/kaynak erişim kaydı: 08.11.2026. Atlas: 10.11.2026. Koordinatların bazıları ikincil kaynaktır; saha ölçümü değildir.','']
 lines+=['- '+s['name']+': '+s['url'] for s in sorted(sources,key=lambda s:s['name'])]
 (DOC/'KAYNAKLAR.md').write_text('\n'.join(lines),encoding='utf-8')
 for stem,title,text in [('YONTEM_VE_SINIRLILIKLAR','Kaynaklar, yöntem ve sınırlılıklar',METHOD),('STORYMAPS_SIDECAR','StoryMaps Sidecar aktarımı',SIDECAR),('GITHUB_PAGES','GitHub Pages yayın hazırlığı',PAGES)]:
  (DOC/(stem+'.md')).write_text(text,encoding='utf-8');(DOC/(stem+'.html')).write_text(doc_page(title,text),encoding='utf-8')
 inv=(DOC/'VERI_ENVANTERI.md').read_text();(DOC/'VERI_ENVANTERI.html').write_text(doc_page('Mevcut veri envanteri',inv),encoding='utf-8')
 rejection=json.loads((DOC/'uygun_bulunmayanlar.json').read_text());rejection.extend([
  {'product':'1984 tam baraj pencereleri','reason':'Özlüce tam penceresinde yaklaşık %86,3; diğer baraj pencerelerinde daha az/yok. %95 kapsam koşulunu sağlamadı. Gerçek 1984 penceresinde ayrı karşılaştırmalar üretildi.'},
  {'product':'Yalnız metadata tarihleri','dates':['1984-07-22','1984-09-08','1990-08-24','2020-08-10'],'reason':'Gerçek bant dosyaları yok; görüntü veya Swipe üretilmedi.'},
  {'product':'JRC 1984–2021','reason':'Dönem özetleri iki tarihli gerçek uydu fotoğrafı değildir; kesin ilk dolum yılı çıkarılmadı.'},
  {'product':'WorldCover 2020 v100 / 2021 v200','reason':'Algoritma sürümleri farklı; doğrudan fiziksel yıllık değişim ve baraj etkisi çıkarılmadı.'},
  {'product':'SRTM / GLO30','reason':'Dönem/datum ve yüzey farkları; gerçek yatak değişimi veya baraj etkisi sayılmadı.'},
  {'product':'NDTI 2026','reason':'Yalnız bir tarih ve kalibrasyonsuz göreli gösterge; tortu zamanı/miktarı karşılaştırması yapılmadı.'}])
 rejection=list({json.dumps(x,ensure_ascii=False,sort_keys=True):x for x in rejection}.values())
 (DOC/'uygun_bulunmayanlar.json').write_text(json.dumps(rejection,ensure_ascii=False,indent=2),encoding='utf-8')
 (SITE/'README.md').write_text(PAGES+'\n## Yerel inceleme\nZIP’in tamamını çıkarın ve index.html dosyasını açın. Haritalar, kaynaklar ve karşılaştırma listesi bu dizinde birlikte çalışır.\n\n## Yeniden üretim\nKaynak proje dizinleri korunarak sırasıyla kodlar/21_veri_envanteri.py, 22_swipe_atlasi_uret.py ve 23_belgeler_ve_son_isleme.py çalıştırılır. Python GDAL/OGR/OSR ve NumPy gerekir. 24_cografi_kontrol.py coğrafi kontrolü; 25_tarayici_kontrol.py Playwright/Chromium ile tarayıcı kontrolünü yapar. Hazır siteyi görüntülemek için bunları çalıştırmak gerekmez.\n',encoding='utf-8')
 inputs=set()
 for m in maps:
  for name in m['source_files']:
   p=ROOT/name.split(' :: ')[0]
   if p.exists():inputs.add(p)
 for p in [ROOT/'07_Kaynakca/kaynakca.json',ROOT/'02_Islenmis_Veriler/baraj_envanteri.csv',ROOT/'06_StoryMaps/karsilastirma_manifesti.json']:inputs.add(p)
 hashes={str(p.relative_to(ROOT)):hashlib.file_digest(p.open('rb'),'sha256').hexdigest() for p in sorted(inputs)}
 (DOC/'kaynak_dosya_sha256.json').write_text(json.dumps(hashes,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps({'maps':len(maps),'sources':len(sources),'source_hashes':len(hashes),'catalog_fields':list(listings[0]),'documentation_ready':True},ensure_ascii=False),flush=True)

if __name__=='__main__':main()
