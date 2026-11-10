"""Çıktı ızgaralarını ve gerçek kaynak piksellerini bağımsız denetler."""
from pathlib import Path
import json,hashlib
import numpy as np
from osgeo import gdal,osr
gdal.UseExceptions()
SITE=Path(__file__).resolve().parents[1];ROOT=SITE.parents[1];DOC=SITE/'belgeler'

def main():
 maps=json.loads((DOC/'karsilastirma_manifesti.json').read_text());seen=set();tested=0;pixel_checks=0;failures=[]
 web=osr.SpatialReference();web.ImportFromEPSG(3857);web.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)
 utm=osr.SpatialReference();utm.ImportFromEPSG(32637);utm.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER);tx=osr.CoordinateTransformation(web,utm)
 for m in maps:
  grid=m['grid'];assert m['before']['grid_id']==m['after']['grid_id']==grid['id']
  for side in ['before','after']:
   product=m[side]
   for name in ['rgb','valid']+(['water'] if m['kind']=='uydu' else []):
    rel=product[name]
    if rel in seen:continue
    seen.add(rel);p=SITE/rel;ds=gdal.Open(str(p));srs=ds.GetSpatialRef()
    assert ds.RasterXSize==grid['width'] and ds.RasterYSize==grid['height'],rel
    assert srs is not None and srs.GetAuthorityCode(None)=='3857',rel
    assert np.allclose(ds.GetGeoTransform(),grid['transform'],atol=1e-7),rel
    gt=grid['transform'];world=[float(x) for x in p.with_suffix('.jgw' if p.suffix=='.jpg' else '.pgw').read_text().split()]
    expected=[gt[1],gt[4],gt[2],gt[5],gt[0]+gt[1]/2,gt[3]+gt[5]/2];assert np.allclose(world,expected,atol=1e-7)
    ds=None;tested+=1
   if m['kind']=='uydu' and product['water']+'_sample' not in seen:
    seen.add(product['water']+'_sample');source=gdal.Open(str(ROOT/product['files'][-1]));inv=gdal.InvGeoTransform(source.GetGeoTransform());alpha=gdal.Open(str(SITE/product['water'])).GetRasterBand(4).ReadAsArray() if False else None
    target=gdal.Open(str(SITE/product['water']));alpha=target.GetRasterBand(4).ReadAsArray();gt=grid['transform']
    for fx in [.19,.43,.77]:
     for fy in [.17,.51,.83]:
      col=min(grid['width']-1,int(grid['width']*fx));row=min(grid['height']-1,int(grid['height']*fy));wx=gt[0]+(col+.5)*gt[1];wy=gt[3]+(row+.5)*gt[5];x,y,_=tx.TransformPoint(wx,wy);sc=int(np.floor(inv[0]+x*inv[1]+y*inv[2]));sr=int(np.floor(inv[3]+x*inv[4]+y*inv[5]));v=255
      if 0<=sc<source.RasterXSize and 0<=sr<source.RasterYSize:v=int(source.GetRasterBand(1).ReadAsArray(sc,sr,1,1)[0,0])
      actual=int(alpha[row,col])>0
      if actual!=(v==1):failures.append({'map':m['id'],'year':product['year'],'pixel':[col,row],'source_class':v,'target_water':actual})
      pixel_checks+=1
    source=None;target=None
  if '1984' in m['years']:assert m['region_id']=='OZL_1984_PENCERE'
  assert (SITE/m['map_file']).exists()
 assert not failures,failures
 old=json.loads((DOC/'mevcut_dosya_durumu.json').read_text());changed=[]
 for rel,before in old.items():
  p=ROOT/rel
  if not p.exists() or p.stat().st_size!=before['bytes'] or p.stat().st_mtime_ns!=before['mtime_ns']:changed.append(rel)
 assert not changed,changed
 hashes=json.loads((DOC/'kaynak_dosya_sha256.json').read_text())
 for rel,digest in hashes.items():assert hashlib.file_digest((ROOT/rel).open('rb'),'sha256').hexdigest()==digest,rel
 report={'passed':True,'map_count':len(maps),'unique_georeferenced_images_checked':tested,'independent_source_pixel_checks':pixel_checks,'pixel_mismatches':failures,'shared_grid_crs_size_transform_and_worldfiles_match':True,'1984_only_in_real_footprint':True,'preexisting_files_checked':len(old),'preexisting_files_changed':changed,'input_hashes_checked':len(hashes),'published_online':False}
 (DOC/'cografi_kontrol.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(report,ensure_ascii=False))

if __name__=='__main__':main()
