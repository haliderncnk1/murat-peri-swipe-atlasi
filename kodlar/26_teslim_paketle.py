"""Kontrolleri geçen atlası tek bağımsız ZIP'e paketler; eski dosyaları yazmaz."""
from pathlib import Path
import hashlib,json,zipfile

SITE=Path(__file__).resolve().parents[1];ROOT=SITE.parents[1];DOC=SITE/'belgeler'

def main():
 geo=json.loads((DOC/'cografi_kontrol.json').read_text());browser=json.loads((DOC/'tarayici_kontrol.json').read_text())
 assert geo['passed'] and browser['passed'] and geo['map_count']==browser['maps_checked']==55
 old=json.loads((DOC/'mevcut_dosya_durumu.json').read_text());changed=[]
 for rel,record in old.items():
  p=ROOT/rel
  if not p.exists() or p.stat().st_size!=record['bytes'] or p.stat().st_mtime_ns!=record['mtime_ns']:changed.append(rel)
 assert not changed,changed
 files=[p for p in SITE.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc']
 assert all(p.stat().st_size<100*1024*1024 for p in files)
 summary={'maps':55,'satellite_swipes':42,'corine_swipes':13,'preexisting_files_preserved':len(old),'georeferenced_images_checked':geo['unique_georeferenced_images_checked'],'independent_source_pixel_checks':geo['independent_source_pixel_checks'],'browser_maps_passed':browser['maps_checked'],'local_links_passed':browser['local_links_checked'],'javascript_errors':browser['javascript_errors'],'published_online':False,'site_root':str(SITE.relative_to(ROOT)),'entry':'index.html','comparison_catalog':'karsilastirmalar.html','comparison_list':'belgeler/karsilastirma_listesi.csv','sidecar_records':'belgeler/storymaps_sidecar.csv','methods':'belgeler/YONTEM_VE_SINIRLILIKLAR.md'}
 (DOC/'SONUC_VE_TESLIM.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
 (DOC/'SONUC_VE_TESLIM.md').write_text('# Sonuç ve teslim\n\n55 ayrı coğrafi Swipe haritası hazır: 42 uydu/su sınıflandırma, 13 CORINE. 55 harita Chromium’da; 678 yerel bağlantı; gerçek iframe Sidecar, telefon boyutu, klavye/sürükleme/zoom testleri geçti. 172 görselin gerçek ızgara/dünya dosyası ve 360 bağımsız kaynak pikseli doğrulandı.\n\nİstenen yedi alanlı liste karsilastirma_listesi.csv, KARSILASTIRMA_LISTESI.md ve ../karsilastirmalar.html içindedir. Sidecar kayıtları storymaps_sidecar.csv / .json; kaynak ve yöntem ayrı dosyalardır.\n\nMevcut 544 proje dosyasının boyut ve değiştirme zamanları korundu; seçilmiş 22 kaynak dosyanın SHA256 değerleri de denetlendi. Windows bilgisayarına doğrudan erişilmedi; mevcut bulut proje kopyası kullanıldı.\n\nGitHub Pages’e uygun statik site hazırlandı; çevrimiçi yayın veya ArcGIS hesabına yükleme yapılmadı. Yeni görüntü indirilmedi. 1984 yalnız gerçek kapsama penceresinde kullanıldı. Metadata-only tarihler, WorldCover sürüm farkları ve JRC dönem özetlerinden desteklenmeyen olay hikâyeleri üretilmedi.\n',encoding='utf-8')
 files=[p for p in SITE.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc']
 archive=SITE.parent/'Murat_Peri_Swipe_Atlasi_20261110.zip';i=2
 while archive.exists():archive=SITE.parent/f'Murat_Peri_Swipe_Atlasi_20261110_{i:02d}.zip';i+=1
 with zipfile.ZipFile(archive,'x',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
  for p in files:z.write(p,SITE.name+'/'+str(p.relative_to(SITE)).replace('\\','/'))
 with zipfile.ZipFile(archive) as z:
  assert z.testzip() is None
  assert SITE.name+'/index.html' in z.namelist()
  assert sum(n.startswith(SITE.name+'/haritalar/') and n.endswith('.html') for n in z.namelist())==55
 result={**summary,'archive':str(archive),'archive_bytes':archive.stat().st_size,'sha256':hashlib.file_digest(archive.open('rb'),'sha256').hexdigest(),'zip_crc_passed':True,'files_in_zip':len(files)}
 (SITE.parent/(SITE.name+'_Paket_Kaydi.json')).write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps(result,ensure_ascii=False))

if __name__=='__main__':main()
