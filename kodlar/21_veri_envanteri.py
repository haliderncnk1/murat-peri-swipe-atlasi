"""Önce envanter: yalnız mevcut proje dosyalarını okur; çıktılar yeni atlasta.
Çalıştırma: /usr/bin/python3 kodlar/21_veri_envanteri.py (GDAL + NumPy).
"""
from pathlib import Path
import csv,json,re,sqlite3
import numpy as np
from osgeo import gdal,osr
gdal.UseExceptions();gdal.SetCacheMax(128*1024*1024)
SITE=Path(__file__).resolve().parents[1];ROOT=SITE.parents[1];PROC=ROOT/'02_Islenmis_Veriler';DOC=SITE/'belgeler'

def native_mask(path,bounds):
    xmin,ymin,xmax,ymax=bounds
    w=round((xmax-xmin)/30);h=round((ymax-ymin)/30)
    ds=gdal.Warp('',str(path),format='MEM',dstSRS='EPSG:32637',outputBounds=bounds,width=w,height=h,resampleAlg='near',srcNodata=255,dstNodata=255,outputType=gdal.GDT_Byte)
    a=ds.ReadAsArray();ds=None;return a

def dump(path,obj):
    path.write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf-8')

def main():
    comparisons=json.loads((ROOT/'06_StoryMaps/karsilastirma_manifesti.json').read_text())
    with (PROC/'baraj_envanteri.csv').open(encoding='utf-8-sig') as f:dams={d['id']:d for d in csv.DictReader(f)}
    regions=[]
    for item in comparisons:
        b=item['extent_utm37n'];bounds=[int(np.floor(b[0]/30))*30,int(np.floor(b[1]/30))*30,int(np.ceil(b[2]/30))*30,int(np.ceil(b[3]/30))*30]
        regions.append({'id':item['id'],'name':item['ad'],'river':dams[item['id']]['nehir'],'kind':'proje_konumu' if item['id']=='BE2' else 'baraj','bounds_utm37n':bounds,'dam_ids':[item['id']],'dams':[dams[item['id']]]})
    for river,rid in [('Murat','MURAT_VADI'),('Peri','PERI_VADI')]:
        chosen=[x for x in regions if x['river']==river and x['kind']=='baraj'];b=[min(x['bounds_utm37n'][0] for x in chosen),min(x['bounds_utm37n'][1] for x in chosen),max(x['bounds_utm37n'][2] for x in chosen),max(x['bounds_utm37n'][3] for x in chosen)]
        ids=[x['id'] for x in chosen];regions.append({'id':rid,'name':river+' barajlar koridoru','river':river,'kind':'vadi','bounds_utm37n':b,'dam_ids':ids,'dams':[dams[k] for k in ids]})
    # 1984'ün tam eski Özlüce penceresini kapsadığı varsayılmaz.
    d84=gdal.Open(str(PROC/'LS_1984_su_30m.tif'));a84=d84.ReadAsArray();yy,xx=np.where(np.isin(a84,[0,1]));gt=d84.GetGeoTransform()
    b84=[int(round(gt[0]+xx.min()*gt[1])),int(round(gt[3]+(yy.max()+1)*gt[5])),int(round(gt[0]+(xx.max()+1)*gt[1])),int(round(gt[3]+yy.min()*gt[5]))];d84=None
    wgs=osr.SpatialReference();wgs.ImportFromEPSG(4326);wgs.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)
    utm=osr.SpatialReference();utm.ImportFromEPSG(32637);utm.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER);transform=osr.CoordinateTransformation(wgs,utm)
    ids84=[]
    for k,d in dams.items():
        x,y,_=transform.TransformPoint(float(d['boylam']),float(d['enlem']))
        if b84[0]<=x<=b84[2] and b84[1]<=y<=b84[3]:ids84.append(k)
    regions.append({'id':'OZL_1984_PENCERE','name':'Özlüce / Orta Peri — 1984 kapsama penceresi','river':'Peri','kind':'vadi','bounds_utm37n':b84,'dam_ids':ids84,'dams':[dams[k] for k in ids84],'extent_note':'1984 su maskesinin gerçek geçerli piksel sınırlarına kırpılmış ortak pencere; Özlüce rezervuarının tamamı değildir.'})
    selected=json.loads((ROOT/'01_Ham_Veriler/Landsat/secilen_sahneler.json').read_text())
    scenes=[]
    for year,date,sensor,cloud in [('1984','1984-07-06','Landsat 5 TM',0),('1990','1990-08-08','Landsat 5 TM',1),('2020','2020-08-26','Landsat 8 OLI',0),('2026','2026-08-24','Sentinel-2 MSI',None)]:
        prefix=f'LS_{year}';rgb=[f'{prefix}_{band}_TOA_30m.tif' for band in ['red','green','blue']] if year!='2026' else [f'S2_20260824_{band}_20m.tif' for band in ['red','green','blue']]
        mask=f'{prefix}_su_30m.tif' if year!='2026' else 'Su_maskesi_20260824_20m.tif'
        meta=next((x for x in selected if x['date']==date),{})
        scenes.append({'year':year,'date':date,'sensor':sensor,'rgb_files':['02_Islenmis_Veriler/'+x for x in rgb],'mask_file':'02_Islenmis_Veriler/'+mask,'resolution_m':20 if year=='2026' else 30,'radiometry':'L2A / BOA' if year=='2026' else 'Collection 1 L1 / TOA','cloud_catalog_percent':'0–0,07' if year=='2026' else cloud,'source':meta.get('source','https://earth-search.aws.element84.com/v1/collections/sentinel-2-l2a')})
    raster_entries=[]
    for folder in [ROOT/'01_Ham_Veriler',PROC]:
        for p in sorted(folder.rglob('*')):
            if not p.is_file() or p.suffix.lower() not in ['.tif','.hgt']:continue
            ds=gdal.Open(str(p),gdal.GA_ReadOnly);gt=ds.GetGeoTransform();srs=ds.GetSpatialRef();band=ds.GetRasterBand(1)
            corners=[[gt[0]+x*gt[1]+y*gt[2],gt[3]+x*gt[4]+y*gt[5]] for x,y in [(0,0),(ds.RasterXSize,0),(ds.RasterXSize,ds.RasterYSize),(0,ds.RasterYSize)]]
            entry={'path':str(p.relative_to(ROOT)),'bytes':p.stat().st_size,'width':ds.RasterXSize,'height':ds.RasterYSize,'bands':ds.RasterCount,'transform':gt,'crs_wkt':srs.ExportToWkt() if srs else None,'epsg':srs.GetAuthorityCode(None) if srs else None,'nodata':band.GetNoDataValue(),'data_type':gdal.GetDataTypeName(band.DataType),'outer_corners_native':corners}
            if srs:
                srs.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER);wgs=osr.SpatialReference();wgs.ImportFromEPSG(4326);wgs.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER);tx=osr.CoordinateTransformation(srs,wgs);entry['outer_corners_lonlat']=[list(tx.TransformPoint(*c)[:2]) for c in corners]
            if p.parent==PROC:
                small=band.GetMaskBand().ReadAsArray(buf_xsize=min(512,ds.RasterXSize),buf_ysize=min(512,ds.RasterYSize));valid=small>0;entry['approx_valid_fraction_thumbnail']=float(valid.mean())
            raster_entries.append(entry);ds=None
    mtl=[]
    for p in sorted((ROOT/'01_Ham_Veriler/Landsat').glob('*MTL.txt')):
        text=p.read_text();meta={k:v.strip().strip('"') for k,v in re.findall(r'^\s*(\w+)\s*=\s*(.*?)\s*$',text,re.M)};sid=p.name[:-8];bands=[x.name for x in p.parent.glob(sid+'*.tif')]
        mtl.append({'metadata_file':str(p.relative_to(ROOT)),'date':meta.get('DATE_ACQUIRED'),'scene_id':sid,'cloud_percent':meta.get('CLOUD_COVER'),'available_band_files':bands,'status':'gercek_bantlar_mevcut' if bands else 'yalniz_metadata_goruntu_yok'})
    derived=[]
    for folder in ['04_Haritalar','05_Grafikler','06_StoryMaps']:
        for p in (ROOT/folder).rglob('*'):
            if not p.is_file() or SITE in p.parents:continue
            if p.suffix.lower() in ['.png','.jpg','.pdf','.html','.csv','.json','.txt','.md']:
                derived.append({'path':str(p.relative_to(ROOT)),'bytes':p.stat().st_size,'embedded_geo_reference':False if p.suffix.lower() in ['.png','.jpg'] else 'uygulanamaz','note':'Swipe üretiminde GeoTIFF kaynakları kullanılır; mevcut görseller yeniden ölçeklenerek hizalanmaz.'})
    analyses=[]
    for folder in [PROC,ROOT/'09_Raporlar',ROOT/'07_Kaynakca']:
        for p in sorted(folder.glob('*')):
            if p.suffix.lower()=='.csv':
                with p.open(encoding='utf-8-sig') as f:reader=csv.DictReader(f);vals=list(reader);analyses.append({'path':str(p.relative_to(ROOT)),'rows':len(vals),'fields':reader.fieldnames,'first_record':vals[0] if vals else None})
            elif p.suffix.lower() in ['.md','.txt','.json']:
                text=p.read_text(encoding='utf-8-sig');preview=text[:600]
                if 'Drive' in p.name or 'teslim_paketleri' in p.name:preview='Aktarım/teslim kaydı; hesaba özel bağlantılar yayıma hazır bilimsel envantere alınmadı.'
                analyses.append({'path':str(p.relative_to(ROOT)),'characters':len(text),'preview':preview})
    db=sqlite3.connect('file:'+str(PROC/'Murat_Peri.gpkg')+'?mode=ro',uri=True);tables=[]
    for name,srid,kind in db.execute('SELECT table_name,srs_id,data_type FROM gpkg_contents'):
        q='"'+name.replace('"','""')+'"';tables.append({'name':name,'epsg':srid,'kind':kind,'rows':db.execute('SELECT COUNT(*) FROM '+q).fetchone()[0],'fields':[x[1] for x in db.execute('PRAGMA table_info('+q+')')]})
    db.close()
    coverage=[]
    for region in regions:
        available=[];masks={}
        for scene in scenes:
            a=native_mask(ROOT/scene['mask_file'],region['bounds_utm37n']);masks[scene['year']]=a;fraction=float(np.isin(a,[0,1]).mean());coverage.append({'region_id':region['id'],'name':region['name'],'year':scene['year'],'date':scene['date'],'valid_fraction':fraction,'native_30m_width':a.shape[1],'native_30m_height':a.shape[0],'eligible_95pct':fraction>=.95})
            if fraction>=.95:available.append(scene['year'])
        region['available_years_95pct']=available
        region['pair_common_coverage']={f'{a}_{b}':float((np.isin(masks[a],[0,1])&np.isin(masks[b],[0,1])).mean()) for i,a in enumerate(available) for b in available[i+1:]}
    dump(DOC/'veri_envanteri.json',{'scenes':scenes,'raster_files':raster_entries,'landsat_metadata_records':mtl,'derived_existing_outputs':derived,'existing_analyses':analyses,'geopackage_tables':tables,'period_products':{'CORINE':['2000','2018'],'WorldCover':['2020 v100','2021 v200'],'JRC':'1984–2021 özet ürünleri; yıllık sahne değildir.','SRTM':'Şubat 2000; uydu RGB görüntüsü değildir.','GLO30':'Ağırlıkla 2011–2015 yüzey alımları; 2026 görüntüsü değildir.'}})
    dump(DOC/'bolgeler_ve_kapsam.json',{'regions':regions,'coverage':coverage,'selection_rule':'Her tarihte ve iki tarihin ortak maskesinde en az %95 geçerli piksel; 0 ve 1 geçerli, 255 NoData.'})
    with (DOC/'yil_bolge_kapsami.csv').open('w',encoding='utf-8-sig',newline='') as f:w=csv.DictWriter(f,fieldnames=list(coverage[0]));w.writeheader();w.writerows(coverage)
    lines=['# Mevcut veri envanteri — 10 Kasım 2026','', 'Gerçek görüntü tarihleri: 06.07.1984, 08.08.1990, 26.08.2020, 24.08.2026. Başka metadata tarihleri görüntü kabul edilmez.','', '| Bölge | En az %95 geçerli su-sınıflandırma kapsamı olan yıllar |','|---|---|']
    for region in regions:lines.append('| '+region['name']+' | '+', '.join(region['available_years_95pct'])+' |')
    lines+=['','## Ayrı değerlendirilen ürünler','CORINE 2000/2018 tematik karşılaştırmaya uygundur; bunlar gerçek renkli tek tarihli uydu fotoğrafları değildir. WorldCover 2020 v100/2021 v200 algoritmaları farklı olduğu için bunlardan doğrudan baraj etkisi veya bir yıllık fiziksel değişim hikâyesi çıkarılmaz. JRC dönem özetleri kesin ilk dolum yılı veya 1984/2021 fotoğraf çifti değildir. DEM ve NDTI tek tarihli/çok tarihli yüzey-gösterge analizleri bağlam kaydı olarak incelendi.','',f'Taranan GeoTIFF/HGT sayısı: {len(raster_entries)}; Landsat MTL kaydı: {len(mtl)}; mevcut görsel/belge kaydı: {len(derived)}; GeoPackage tablosu: {len(tables)}.']
    (DOC/'VERI_ENVANTERI.md').write_text('\n'.join(lines),encoding='utf-8')
    print(json.dumps({'raster_count':len(raster_entries),'regions':[{k:r[k] for k in ['id','name','available_years_95pct','pair_common_coverage']} for r in regions],'metadata_only_dates':sorted({m['date'] for m in mtl if not m['available_band_files']}-{s['date'] for s in scenes})},ensure_ascii=False),flush=True)

if __name__=='__main__':main()
