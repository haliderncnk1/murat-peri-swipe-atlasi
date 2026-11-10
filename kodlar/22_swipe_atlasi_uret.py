"""GDAL ile mevcut verilerden coğrafi olarak hizalı, bağımsız Swipe atlası.
Önce 21_veri_envanteri.py çalıştırılır. Kaynaklar salt okunur; tüm yeni
ürünler bu yeni atlas klasöründedir. Ağ bağlantısı veya hesap gerekmez.
"""
from pathlib import Path
from html import escape
from itertools import combinations
import csv,hashlib,json,math,runpy,shutil
import numpy as np
from osgeo import gdal,ogr,osr
gdal.UseExceptions();gdal.SetCacheMax(128*1024*1024)
SITE=Path(__file__).resolve().parents[1];ROOT=SITE.parents[1];DOC=SITE/'belgeler';ASSET=SITE/'assets';MAPS=SITE/'haritalar'
env=runpy.run_path(str(SITE/'kodlar/21_veri_envanteri.py'));native_mask=env['native_mask']
SOURCES={
 'D01':{'name':'USGS/NASA Landsat kamu arşivi','url':'https://cloud.google.com/storage/docs/public-datasets/landsat'},
 'D02':{'name':'Copernicus Sentinel-2 L2A / Element 84 Earth Search','url':'https://earth-search.aws.element84.com/v1/collections/sentinel-2-l2a'},
 'D03':{'name':'JRC Global Surface Water v1.4','url':'https://global-surface-water.appspot.com/download'},
 'D08':{'name':'CORINE 2000, resmî EEA vektör servisi','url':'https://image.discomap.eea.europa.eu/arcgis/rest/services/Corine/CLC2000_WM/MapServer/0'},
 'D09':{'name':'CORINE 2018, resmî EEA vektör servisi','url':'https://image.discomap.eea.europa.eu/arcgis/rest/services/Corine/CLC2018_WM/MapServer/0'},
 'D11':{'name':'© OpenStreetMap katkıcıları, ODbL','url':'https://www.openstreetmap.org/copyright'}
}
CLC={1:('#b65b55','Yapay alan'),2:('#dfc665','Tarım'),3:('#7f9e68','Orman / yarı doğal'),4:('#ab9bc0','Sulak alan'),5:('#4197b2','Su')}

def dump(path,obj):path.write_text(json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
def epsg(code):
 s=osr.SpatialReference();s.ImportFromEPSG(code);s.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER);return s
UTM=epsg(32637);WEB=epsg(3857);WGS=epsg(4326)
TO_WEB=osr.CoordinateTransformation(UTM,WEB);TO_WGS=osr.CoordinateTransformation(UTM,WGS)

def hexrgb(value):return tuple(int(value[i:i+2],16) for i in [1,3,5])
def date(value):return '.'.join(reversed(value.split('-'))) if '-' in value else value
def n(value):return f'{value:.2f}'.replace('.',',')

def grid_for(region):
 x0,y0,x1,y1=region['bounds_utm37n'];edge=[]
 for t in np.linspace(0,1,25):edge.extend([(x0+(x1-x0)*t,y0),(x0+(x1-x0)*t,y1),(x0,y0+(y1-y0)*t),(x1,y0+(y1-y0)*t)])
 points=[TO_WEB.TransformPoint(*p) for p in edge];b=[min(p[0] for p in points),min(p[1] for p in points),max(p[0] for p in points),max(p[1] for p in points)]
 cap=1800 if region['kind']=='vadi' else 1536;ratio=(b[2]-b[0])/(b[3]-b[1]);w=cap if ratio>=1 else max(256,round(cap*ratio));h=cap if ratio<1 else max(256,round(cap/ratio))
 transform=[b[0],(b[2]-b[0])/w,0,b[3],0,-(b[3]-b[1])/h]
 return {'id':region['id'],'epsg':3857,'bounds_3857':b,'width':w,'height':h,'transform':transform,'bounds_utm37n':region['bounds_utm37n'],'native_crs_epsg':32637,'outer_lonlat':[list(TO_WGS.TransformPoint(x,y)[:2]) for x,y in [(x0,y0),(x1,y0),(x1,y1),(x0,y1)]]}

def warped(path,grid,kind='bilinear',nodata=-9999,dtype=gdal.GDT_Float32):
 ds=gdal.Warp('',str(path),format='MEM',dstSRS='EPSG:3857',outputBounds=grid['bounds_3857'],width=grid['width'],height=grid['height'],resampleAlg=kind,srcNodata=nodata,dstNodata=nodata,outputType=dtype,multithread=False)
 if not np.allclose(ds.GetGeoTransform(),grid['transform'],atol=1e-7):raise ValueError('GDAL ortak ızgara dönüşümü eşleşmedi.')
 a=ds.ReadAsArray();ds=None;return a

def save_image(path,rgb,grid,alpha=None):
 h,w=rgb.shape[:2];bands=4 if alpha is not None else 3
 ds=gdal.GetDriverByName('MEM').Create('',w,h,bands,gdal.GDT_Byte);ds.SetGeoTransform(grid['transform']);ds.SetProjection(WEB.ExportToWkt())
 for i in range(3):ds.GetRasterBand(i+1).WriteArray(rgb[:,:,i]);ds.GetRasterBand(i+1).SetColorInterpretation([gdal.GCI_RedBand,gdal.GCI_GreenBand,gdal.GCI_BlueBand][i])
 if alpha is not None:ds.GetRasterBand(4).WriteArray(alpha);ds.GetRasterBand(4).SetColorInterpretation(gdal.GCI_AlphaBand)
 if path.suffix=='.jpg':gdal.Translate(str(path),ds,format='JPEG',creationOptions=['QUALITY=91','PROGRESSIVE=YES'],bandList=[1,2,3])
 else:gdal.Translate(str(path),ds,format='PNG',creationOptions=['ZLEVEL=9'])
 gt=grid['transform'];worldfile=path.with_suffix('.jgw' if path.suffix=='.jpg' else '.pgw');worldfile.write_text('\n'.join(f'{v:.12f}' for v in [gt[1],gt[4],gt[2],gt[5],gt[0]+gt[1]/2,gt[3]+gt[5]/2])+'\n',encoding='ascii');ds=None

def render_scene(region,scene,grid):
 folder=ASSET/'data'/region['id'];folder.mkdir(parents=True,exist_ok=True);year=scene['year'];key=folder/year
 mask=warped(ROOT/scene['mask_file'],grid,'near',255,gdal.GDT_Byte);valid=np.isin(mask,[0,1]);bands=[]
 for filename in scene['rgb_files']:
  a=warped(ROOT/filename,grid);valid&=np.isfinite(a)&(a!=-9999);bands.append(a)
 rgb=np.stack(bands,axis=-1);rgb=(np.clip(rgb/.38,0,1)**(1/1.6)*255).astype('uint8');rgb[~valid]=[232,235,224]
 photo=Path(str(key)+'_rgb.jpg');save_image(photo,rgb,grid)
 blank=np.full_like(rgb,255);valid_path=Path(str(key)+'_valid.png');save_image(valid_path,blank,grid,valid.astype('uint8')*255)
 water=np.zeros_like(rgb);water[:]=[0,172,215];water_path=Path(str(key)+'_water.png');save_image(water_path,water,grid,((mask==1)&valid).astype('uint8')*255)
 return {'year':year,'date':scene['date'],'label':date(scene['date'])+' · '+scene['sensor'],'rgb':str(photo.relative_to(SITE)),'valid':str(valid_path.relative_to(SITE)),'water':str(water_path.relative_to(SITE)),'valid_fraction_web_grid':float(valid.mean()),'files':scene['rgb_files']+[scene['mask_file']],'grid_id':grid['id'],'radiometry':scene['radiometry'],'resolution_m':scene['resolution_m']}

def rectangle(bounds):
 x0,y0,x1,y1=bounds;r=ogr.Geometry(ogr.wkbLinearRing)
 for p in [(x0,y0),(x1,y0),(x1,y1),(x0,y1),(x0,y0)]:r.AddPoint_2D(*p)
 poly=ogr.Geometry(ogr.wkbPolygon);poly.AddGeometry(r);poly.AssignSpatialReference(UTM);return poly

def render_corine(region,year,grid,source):
 layer=source.GetLayerByName('CORINE_'+year);layer.SetSpatialFilterRect(*region['bounds_utm37n']);layer.ResetReading();mem=ogr.GetDriverByName('Memory').CreateDataSource('');target=mem.CreateLayer('classes',WEB,ogr.wkbUnknown);target.CreateField(ogr.FieldDefn('class',ogr.OFTInteger));areas={k:0. for k in CLC};box=rectangle(region['bounds_utm37n'])
 for feature in layer:
  code=int(str(feature.GetField('sinif'))[0]);native=feature.GetGeometryRef().Clone()
  if code not in CLC:raise ValueError('CORINE sınıfı beklenen hiyerarşide değil.')
  if not native.IsValid():native=native.MakeValid()
  clipped=native.Intersection(box)
  if clipped:areas[code]+=clipped.GetArea()/1e6
  native.Transform(TO_WEB);f=ogr.Feature(target.GetLayerDefn());f.SetField('class',code);f.SetGeometry(native);target.CreateFeature(f);f=None
 layer.SetSpatialFilter(None)
 ds=gdal.GetDriverByName('MEM').Create('',grid['width'],grid['height'],1,gdal.GDT_Byte);ds.SetGeoTransform(grid['transform']);ds.SetProjection(WEB.ExportToWkt());ds.GetRasterBand(1).Fill(0);ds.GetRasterBand(1).SetNoDataValue(0)
 gdal.RasterizeLayer(ds,[1],target,options=['ATTRIBUTE=class']);a=ds.ReadAsArray();ds=None;mem=None;valid=np.isin(a,list(CLC));rgb=np.full((*a.shape,3),235,dtype='uint8')
 for code,(color,_) in CLC.items():rgb[a==code]=hexrgb(color)
 folder=ASSET/'data'/region['id'];folder.mkdir(exist_ok=True,parents=True);photo=folder/f'CLC{year}_rgb.png';vp=folder/f'CLC{year}_valid.png';save_image(photo,rgb,grid);save_image(vp,np.full_like(rgb,255),grid,valid.astype('uint8')*255)
 return {'year':year,'date':year,'label':year+' · CORINE','rgb':str(photo.relative_to(SITE)),'valid':str(vp.relative_to(SITE)),'grid_id':grid['id'],'files':['02_Islenmis_Veriler/Murat_Peri.gpkg :: CORINE_'+year,'01_Ham_Veriler/Diger/CORINE_'+year+'.geojson'],'areas_km2':areas,'valid_fraction_web_grid':float(valid.mean())}

def photo_story(region,a,b,metrics):
 prefix='Su sınıflandırması, iki tarihte de geçerli sabit inceleme penceresinde '+n(metrics['water_before_km2'])+' km²’den '+n(metrics['water_after_km2'])+' km²’ye değişiyor.'
 if region['kind']=='proje_konumu':
  meaning='Bu görüntüler Beyhan II proje konumunun çevresini gösterir. İşletmeye girişi ve mevcut gövdesi doğrulanmadığı için görünen su yüzeyleri Beyhan II gölü olarak adlandırılmaz.';phase='Proje çevresi; işletme öncesi/sonrası değil'
 elif region['kind']=='vadi':
  meaning='Bu çift '+region['name']+' için aynı coğrafi pencereyi karşılaştırır. Bölgede birden fazla vadi kolu veya tesis bulunabileceğinden toplam su izi tek bir baraja atanmaz.';phase='Vadi koridorunda tarihli gözlem'
 else:
  dam=region['dams'][0];opened=int(float(dam['yil'])) if dam['yil'] else None
  if int(a['year'])<opened<=int(b['year']):meaning='İki gözlem, kaynaktaki işletmeye giriş yılının iki tarafında yer alıyor. Su izinin genişlemesi, vadinin su altında kalan kesimlerini okumaya yardım eder; su tutmanın tam başlangıç gününü belirlemez.';phase='İşletme öncesi / sonrası dönem'
  elif int(a['year'])>=opened:meaning='Her iki görüntü de kaynak kaydındaki işletme başlangıcından sonradır. Bu, baraj kurulmadan önce/sonra çifti değildir; iki tarihteki kıyı ve su izi karşılaştırmasıdır.';phase='İşletme sonrası iki gözlem'
  else:meaning='Her iki tarih de işletmeye girişten öncedir. Özlüce çevresinde 1990 inşaat sürecine denk gelir; bu görüntü saf bir inşaat öncesi doğal vadi olarak etiketlenmez.';phase='İşletme öncesi iki gözlem'
 if region['id']=='OZL':meaning+=' Özlüce için 1990, inşaat öncesi doğal durum değildir.'
 if region['id']=='OZL_1984_PENCERE':meaning+=' 1984 verisiyle sınırlandırılan bu pencere, Özlüce rezervuarının tamamını kapsamaz. 1984 inşaat öncesi, 1990 ise inşaat sürecindeki gözlemdir.'
 limit='Bu iki görüntü değişimin yalnız '+date(a['date'])+' ile '+date(b['date'])+' arasındaki görünümünü sınırlar; olayın tam yılını veya nedenini tek başına kanıtlamaz. Mevsim, işletme su düzeyi, sensör/atmosfer ve sınıflandırma farkları sonucu etkileyebilir. Yerleşim kaybı, ekolojik zarar veya tortu miktarı bu karşılaştırmadan doğrulanmaz.'
 if a['year']=='2020' and b['year']=='2026':limit+=' Landsat TOA ile Sentinel-2 yüzey yansıtması ve küçük su lekesi eleme işlemleri farklıdır.'
 observed=prefix+' Ortak geçerli alan, inceleme penceresinin %'+f'{metrics["common_valid_fraction"]*100:.2f}'.replace('.',',')+'’idir; NoData bölgeleri su veya kara sayılmadı.'
 text=date(a['date'])+' ve '+date(b['date'])+' görüntülerinde '+region['name']+' çevresine aynı yerden bakıyoruz. '+prefix+' '+meaning+' Bu değerler normal rezervuar alanı veya doluluk oranı değildir.'
 return observed,text,limit,phase

def make_page(m):
 title=escape(m['title']);data=json.dumps(m,ensure_ascii=False).replace('</','<\\/');src=''.join('<li><a target="_blank" rel="noopener noreferrer" href="'+escape(s['url'],quote=True)+'">'+escape(s['name'])+'</a></li>' for s in m['sources'])
 modes='<button data-mode="rgb" aria-pressed="true">Uydu</button><button data-mode="overlay" aria-pressed="false">Uydu + su</button><button data-mode="mask" aria-pressed="false">Su maskesi</button>' if m['kind']=='uydu' else '<span class="small">CORINE tematik sınıfları</span>'
 legend=''.join('<span><i style="background:'+c+'"></i>'+escape(name)+'</span>' for c,name in m['legend'])+'<span>▧ Ortak geçerli veri yok</span>'
 warning=('<div class="clip-message">'+escape(m['extent_note'])+'</div>') if m.get('extent_note') else ''
 return f'''<!doctype html><html lang="tr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{title} | Bir Nehrin Hafızası</title><meta name="description" content="{escape(m['observation'],quote=True)}"><link rel="stylesheet" href="../assets/site.css"></head><body>
<header class="masthead"><a href="../index.html">← Bütün karşılaştırmalar</a><h1>{title}</h1><div class="badges"><span class="badge">{escape(m['region_name'])}</span><span class="badge">{escape(m['phase'])}</span></div></header>
<main class="viewer"><aside class="story-pane"><p class="kicker">STORYMAPS İÇİN ÖNERİLEN METİN</p><p>{escape(m['story_text'])}</p><h2>Görüntüde ne gözleniyor?</h2><p>{escape(m['observation'])}</p><h2>Yorumun sınırı</h2><p>{escape(m['limits'])}</p><details><summary>Veri dosyaları ve yöntem</summary><p>{escape(m['method'])}</p><ul class="source-list">{''.join('<li><code>'+escape(x)+'</code></li>' for x in m['source_files'])}</ul></details><details><summary>Kaynaklar</summary><ul class="source-list">{src}</ul><p>Veri erişim kaydı: 08.11.2026. Atlas: 10.11.2026.</p></details><p class="small"><a href="../belgeler/YONTEM_VE_SINIRLILIKLAR.html">Tam yöntem ve sınırlılıklar</a> · <a href="../karsilastirmalar.html#{m['id']}">Bu bölümün aktarım kaydı</a></p></aside>
<section id="mapPanel" class="map-panel" aria-label="Coğrafi olarak hizalanmış Swipe haritası"><div class="map-top"><strong>{escape(m['region_name'])}</strong><div class="modes">{modes}</div><button class="secondary fullscreen" id="fullscreen">Tam ekran</button></div>{warning}<div class="frame"><canvas id="map" aria-label="İki tarihli harita; yakınlaştırmak için düğmeler, karşılaştırmak için kaydırıcı kullanın."></canvas><div class="dates"><span class="date">{escape(m['before']['label'])}</span><span class="date">{escape(m['after']['label'])}</span></div><div class="zoom"><button id="plus" aria-label="Yakınlaştır">+</button><button id="minus" aria-label="Uzaklaştır">−</button><button id="reset" class="reset" aria-label="Başlangıç görünümü">⌂</button></div><div class="north"><span>↑</span>K</div><div class="divider" id="divider"><button id="handle" role="slider" aria-label="Tarihleri karşılaştırma çizgisi" aria-valuemin="1" aria-valuemax="99" aria-valuenow="50">↔</button></div><div class="loading" id="loading" role="status">Coğrafi olarak hizalanmış görüntüler yükleniyor…</div></div><div class="rangebar"><label for="swipe">Karşılaştır</label><input id="swipe" type="range" min="1" max="99" value="50"><output id="percent">50%</output><span>Sürükle: haritada gezin</span></div><div class="legend">{legend}</div><div class="map-bottom"><span>{escape(m['attribution'])}</span><span id="coords">WGS 84 · İmleçle koordinat oku</span></div></section></main><script>window.MAP_DATA={data};</script><script src="../assets/map.js"></script></body></html>'''

def main():
 inv=json.loads((DOC/'veri_envanteri.json').read_text());coverage=json.loads((DOC/'bolgeler_ve_kapsam.json').read_text());regions=coverage['regions'];scenes={s['year']:s for s in inv['scenes']};maps=[];assets={};grids={};rejections=[]
 for name in ['site.css','map.js','gallery.js']:shutil.copyfile(SITE/'kodlar/sablonlar'/name,ASSET/name)
 db=ogr.Open(str(ROOT/'02_Islenmis_Veriler/Murat_Peri.gpkg'),0)
 for region in regions:
  rid=region['id'];grid=grid_for(region);grids[rid]=grid;folder=ASSET/'data'/rid;folder.mkdir(exist_ok=True,parents=True);dump(folder/'grid.json',grid);(folder/'grid.prj').write_text(WEB.ExportToWkt(),encoding='utf-8')
  native={};products={}
  for year in region['available_years_95pct']:
   scene=scenes[year];products[year]=render_scene(region,scene,grid);native[year]=native_mask(ROOT/scene['mask_file'],region['bounds_utm37n'])
  dams=[{'id':d['id'],'name':d['ad'],'lon':float(d['boylam']),'lat':float(d['enlem']),'project':d['id']=='BE2'} for d in region['dams']]
  for a,b in combinations(region['available_years_95pct'],2):
   ma,mb=native[a],native[b];common=np.isin(ma,[0,1])&np.isin(mb,[0,1]);fraction=float(common.mean())
   if fraction<.95:rejections.append({'region':rid,'pair':a+'_'+b,'reason':'Ortak geçerli piksel oranı %95 altında.','fraction':fraction});continue
   metrics={'common_valid_fraction':fraction,'common_valid_area_km2':int(common.sum())*.0009,'water_before_km2':int(np.sum(common&(ma==1)))*.0009,'water_after_km2':int(np.sum(common&(mb==1)))*.0009,'land_to_water_km2':int(np.sum(common&(ma==0)&(mb==1)))*.0009,'water_to_land_km2':int(np.sum(common&(ma==1)&(mb==0)))*.0009,'analysis_epsg':32637,'analysis_cell_size_m':30,'area_definition':'Sabit dikdörtgen inceleme penceresi ve iki tarihte ortak geçerli pikseller; tek bir rezervuarın normal alanı değildir.'}
   pa,pb=products[a],products[b];observed,text,limit,phase=photo_story(region,pa,pb,metrics);uid=rid.lower()+'_'+a+'_'+b
   title=region['name']+' · '+a+'–'+b
   source_ids=['D01','D11']+(['D02'] if b=='2026' else [])
   m={'id':uid,'kind':'uydu','title':title,'region_id':rid,'region_name':region['name'],'river':region['river'],'region_kind':region['kind'],'years':[a,b],'phase':phase,'grid':grid,'before':pa,'after':pb,'dams':dams,'observation':observed,'story_text':text,'limits':limit,'method':'RGB: kırmızı/yeşil/mavi; ortak 0–0,38 gösterim aralığı, gama 1/1,6. Görseller EPSG:3857 aynı kapsam ve aynı piksel ızgarasına bilineer; maskeler en yakın komşuyla dönüştürüldü. İki taraf yalnız ortak geçerli alanda gösterilir. Sayısal alanlar ayrıca EPSG:32637, 30 m gridde hesaplanır.','source_files':list(dict.fromkeys(pa['files']+pb['files'])),'sources':[SOURCES[k] for k in source_ids],'legend':[['#00acd7','Su sınıfı (maskeyi açın)'],['#e7e5d7','Su dışı sınıf']],'attribution':'Landsat: USGS/NASA · Sentinel-2: Copernicus · Konumlar: mevcut kaynaklar / OSM','metrics':metrics,'extent_note':region.get('extent_note',''),'map_file':'haritalar/'+uid+'.html'}
   maps.append(m)
  # Aynı hiyerarşide CORINE; WorldCover sürüm farkı fiziksel değişim sayılmaz.
  ca=render_corine(region,'2000',grid,db);cb=render_corine(region,'2018',grid,db)
  if min(ca['valid_fraction_web_grid'],cb['valid_fraction_web_grid'])>=.90:
   uid=rid.lower()+'_corine_2000_2018';change=cb['areas_km2'][5]-ca['areas_km2'][5]
   observed='Sabit inceleme penceresindeki CORINE su sınıfı 2000’de '+n(ca['areas_km2'][5])+' km², 2018’de '+n(cb['areas_km2'][5])+' km² olarak haritalanmıştır. Bu, CORINE sınıf desenidir; aynı günün uydu su izi değildir.'
   limit='CORINE’in en küçük haritalama birimi 25 ha’dır; küçük parsel, yol ve kıyı değişimleri ayrışmayabilir. Ürün yılları her tesiste gerçek işletme öncesi/sonrası değildir. Haritalanan sınıf farkı tek başına barajın neden olduğu arazi kaybını, taşınan hane sayısını veya ekolojik zararı kanıtlamaz.'
   if rid=='OZL':limit+=' Özlüce 1999’da işletmededir; 2000 zaten işletme sonrasıdır.'
   if rid=='ASK':limit+=' Aşağı Kaleköy 2020’de üretime başladı; 2018 bu tarihten öncedir.'
   maps.append({'id':uid,'kind':'corine','title':region['name']+' · arazi örtüsü 2000–2018','region_id':rid,'region_name':region['name'],'river':region['river'],'region_kind':region['kind'],'years':['2000','2018'],'phase':'CORINE tematik sınıflandırma karşılaştırması','grid':grid,'before':ca,'after':cb,'dams':dams,'observation':observed,'story_text':region['name']+' çevresine iki arazi örtüsü kaydından bakıyoruz. '+observed+' Tarım, orman ve su sınıflarının mekânsal desenini birlikte okumak, kıyı çevresindeki farklılaşmayı görünür kılıyor.','limits':limit,'method':'Mevcut GeoPackage CORINE_2000 / CORINE_2018 vektörleri, kodun ilk basamağıyla aynı beş ana sınıfa gruplandı. Geometriler EPSG:3857’e dönüştürülüp aynı gösterim ızgarasına kategorik olarak rasterleştirildi. Sınıf alanları EPSG:32637’de pencereyle gerçek vektör kesişiminden hesaplandı. Gösterim piksel boyutu ürünün 25 ha ayrıntı sınırını iyileştirmez.','source_files':ca['files']+cb['files'],'sources':[SOURCES[k] for k in ['D08','D09','D11']],'legend':[[v[0],v[1]] for v in CLC.values()],'attribution':'Copernicus CORINE / EEA 2000 ve 2018 · © OpenStreetMap katkıcıları','metrics':{'water_class_before_km2':ca['areas_km2'][5],'water_class_after_km2':cb['areas_km2'][5],'area_definition':'Sabit inceleme penceresindeki vektör sınıf alanı; gözlenen rezervuar su izi değildir.'},'extent_note':region.get('extent_note',''),'map_file':'haritalar/'+uid+'.html'})
  else:rejections.append({'region':rid,'pair':'CORINE2000_2018','reason':'Tematik vektör kapsamı gösterim penceresinde %90 altında.'})
  print(json.dumps({'region_completed':rid,'scene_assets':list(products),'maps_so_far':len(maps)},ensure_ascii=False),flush=True)
 db=None
 for m in maps:(SITE/m['map_file']).write_text(make_page(m),encoding='utf-8')
 dump(DOC/'karsilastirma_manifesti.json',maps);dump(DOC/'cografi_hizalama_izgaralari.json',grids);dump(DOC/'uygun_bulunmayanlar.json',rejections)
 # İstenen yedi alan, hem CSV hem Markdown hem web katalogda bulunur.
 listing=[]
 for m in maps:
  listing.append({'bolum_basligi':m['title'],'baraj_veya_vadi':m['region_name'],'karsilastirilan_yillar':' / '.join(m['years']),'kullanilan_veri_dosyalari':' | '.join(m['source_files']),'gozlemlenen_degisim':m['observation'],'onerilen_hikaye_metni':m['story_text'],'harita_dosya_yolu':str((SITE/m['map_file']).relative_to(ROOT)),'bilimsel_sinir':m['limits'],'goreli_web_yolu':m['map_file'],'sidecar_yolu':m['map_file']+'?embed=1','su_maskesi_sidecar_yolu':m['map_file']+'?embed=1&katman=su' if m['kind']=='uydu' else ''})
 with (DOC/'karsilastirma_listesi.csv').open('w',encoding='utf-8-sig',newline='') as f:w=csv.DictWriter(f,fieldnames=list(listing[0]));w.writeheader();w.writerows(listing)
 md=['# Karşılaştırma listesi','',f'Toplam {len(maps)} ayrı coğrafi Swipe haritası. Dosya yolları proje köküne göredir.','']
 entries=[]
 for row,m in zip(listing,maps):
  md+=['## '+row['bolum_basligi']]+['- **'+k.replace('_',' ')+':** '+str(v) for k,v in row.items()]+['']
  fields=[('İlgili baraj / vadi',row['baraj_veya_vadi']),('Karşılaştırılan yıllar',row['karsilastirilan_yillar']),('Kullanılan veri dosyaları','<br/>'.join('<code>'+escape(p)+'</code>' for p in m['source_files'])),('Gözlemlenen değişim',row['gozlemlenen_degisim']),('Önerilen hikâye metni',row['onerilen_hikaye_metni']),('Bilimsel sınır',row['bilimsel_sinir']),('Haritanın dosya yolu','<code>'+escape(row['harita_dosya_yolu'])+'</code>')]
  dl=''.join('<dt>'+escape(k)+'</dt><dd>'+(v if k in ['Kullanılan veri dosyaları','Haritanın dosya yolu'] else escape(v))+'</dd>' for k,v in fields)
  entries.append('<article class="catalog-entry" id="'+m['id']+'"><h2>'+escape(row['bolum_basligi'])+'</h2><dl>'+dl+'</dl><p><a class="button" href="'+m['map_file']+'">Swipe haritasını aç</a> <a href="'+m['map_file']+'?embed=1">Sidecar görünümü</a></p></article>')
 (DOC/'KARSILASTIRMA_LISTESI.md').write_text('\n'.join(md),encoding='utf-8')
 (SITE/'karsilastirmalar.html').write_text('<!doctype html><html lang="tr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Karşılaştırmaların tam listesi</title><link rel="stylesheet" href="assets/site.css"></head><body><main class="wrap"><a href="index.html">← Atlas</a><h1>Karşılaştırmaların tam listesi</h1><p>Her bölüm için istenen yedi alan, bilimsel sınır ve ayrı harita bağlantısı.</p>'+''.join(entries)+'</main></body></html>',encoding='utf-8')
 cards=[]
 for m in maps:
  brief=m['observation'].split(' Ortak')[0]
  cards.append('<article class="card"><a class="thumb" href="'+m['map_file']+'" aria-label="'+escape(m['title'],quote=True)+'"><img loading="lazy" src="'+m['before']['rgb']+'" alt="'+escape(m['before']['label'],quote=True)+'"><img class="after" loading="lazy" src="'+m['after']['rgb']+'" alt="'+escape(m['after']['label'],quote=True)+'"></a><div class="card-body"><div class="badges"><span class="badge">'+' → '.join(m['years'])+'</span><span class="badge">'+('Uydu + su maskesi' if m['kind']=='uydu' else 'Arazi örtüsü')+'</span></div><h3><a href="'+m['map_file']+'">'+escape(m['region_name'])+'</a></h3><p>'+escape(brief)+'</p><p class="small">'+escape(m['phase'])+'</p><a href="'+m['map_file']+'">Karşılaştırmayı aç →</a></div></article>')
 options=''.join('<option value="'+r['id']+'">'+escape(r['name'])+'</option>' for r in regions)
 pairs=sorted({tuple(m['years']) for m in maps});pair_options=''.join('<option value="'+'_'.join(p)+'">'+' / '.join(p)+'</option>' for p in pairs)
 photo_count=sum(m['kind']=='uydu' for m in maps);corine_count=len(maps)-photo_count
 index=f'''<!doctype html><html lang="tr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Bir Nehrin Hafızası | Murat–Peri Swipe Atlası</title><meta name="description" content="1984, 1990, 2020 ve 2026 gerçek uydu görüntüleriyle Murat–Peri karşılaştırmaları."><link rel="stylesheet" href="assets/site.css"></head><body><main class="wrap"><header class="hero"><div class="eyebrow">Murat–Peri · Bir Nehrin Hafızası</div><h1>Aynı vadiye,<br/>farklı zamanlardan bakmak.</h1><p class="lead">Uydu görüntülerini aynı coğrafi pencerede karşılaştırın. Sınırı sürükleyin; suyun izini, kıyıları ve arazi örtüsü desenlerini birlikte okuyun.</p><div class="badges"><span class="badge">{photo_count} uydu / su karşılaştırması</span><span class="badge">{corine_count} CORINE karşılaştırması</span><span class="badge">4 gerçek görüntü tarihi</span></div></header><div class="note"><b>1984’ün kapsamı sınırlı.</b> O yılın karşılaştırmaları yalnız gerçek veri bulunan Özlüce / Orta Peri penceresindedir. 1990, 2020 ve 2026 daha geniş alanlarda kullanılabilir. CORINE 2000/2018 tematik sınıflardır. Bu atlas, görünüm farkını tek başına yerleşim kaybı veya ekolojik zarar olarak sunmaz.</div><nav class="links"><a class="button" href="karsilastirmalar.html">Bölüm ve hikâye listesini aç</a><a class="button secondary" href="belgeler/karsilastirma_listesi.csv" download>Listeyi CSV indir</a><a href="belgeler/VERI_ENVANTERI.html">Veri envanteri</a><a href="belgeler/YONTEM_VE_SINIRLILIKLAR.html">Kaynak ve yöntem</a><a href="belgeler/STORYMAPS_SIDECAR.html">Sidecar aktarımı</a></nav><section class="filterbar" aria-label="Karşılaştırmaları filtrele"><label>Bölge<select id="region"><option value="">Bütün bölgeler</option>{options}</select></label><label>Yıllar<select id="pair"><option value="">Bütün yıl çiftleri</option>{pair_options}</select></label><label>Ürün<select id="kind"><option value="">Bütün ürünler</option><option value="uydu">Uydu ve su maskeleri</option><option value="corine">CORINE arazi örtüsü</option></select></label><label>Ara<input id="search" type="search" placeholder="Baraj veya vadi adı"></label></section><p id="count" class="count"></p><section class="cards">{''.join(cards)}</section><p id="empty" hidden>Eşleşen karşılaştırma yok. Filtreleri değiştirin.</p><footer class="foot">Landsat: USGS/NASA · Sentinel-2 ve CORINE: Copernicus / EEA · © OpenStreetMap katkıcıları. Tarih, kaynak, hizalama ve sınırlılıklar her haritada korunmuştur. Atlas: 10 Kasım 2026. GitHub Pages’e yayımlanmaya hazır statik site; bu çalışma çevrimiçi yayımlama yapmaz.</footer></main><script>window.ATLAS_DATA={json.dumps([{'title':m['title'],'region_name':m['region_name'],'river':m['river'],'region_id':m['region_id'],'years':m['years'],'kind':m['kind']} for m in maps],ensure_ascii=False)};</script><script src="assets/gallery.js"></script></body></html>'''
 (SITE/'index.html').write_text(index,encoding='utf-8');(SITE/'.nojekyll').write_text('',encoding='utf-8')
 # Yayın izni verilmediğinden gerçek alan adı uydurulmaz.
 sidecar=[]
 for m in maps:
  template='https://GITHUB_KULLANICI_ADI.github.io/DEPO_ADI/'+m['map_file']+'?embed=1'
  sidecar.append({'id':m['id'],'bolum_basligi':m['title'],'metin':m['story_text'],'altyazi':m['limits'],'goreli_yol':m['map_file']+'?embed=1','yayin_sonrasi_url_sablonu':template,'iframe_sablonu':'<iframe src="'+template+'" title="'+escape(m['title'],quote=True)+'" width="100%" height="640" style="border:0" loading="lazy" allowfullscreen></iframe>'})
 with (DOC/'storymaps_sidecar.csv').open('w',encoding='utf-8-sig',newline='') as f:w=csv.DictWriter(f,fieldnames=list(sidecar[0]));w.writeheader();w.writerows(sidecar)
 dump(DOC/'storymaps_sidecar.json',sidecar)
 summary={'maps_total':len(maps),'satellite_swipes':photo_count,'corine_swipes':corine_count,'regions':len(regions),'actual_image_dates':[s['date'] for s in scenes.values()],'preexisting_files_modified':False,'published_online':False,'site_root':str(SITE.relative_to(ROOT)),'crs':'EPSG:3857, ortak raster ızgarası; alan hesabı EPSG:32637','builder':'kodlar/22_swipe_atlasi_uret.py'}
 dump(DOC/'uretim_ozeti.json',summary)
 print(json.dumps(summary,ensure_ascii=False),flush=True)

if __name__=='__main__':main()
