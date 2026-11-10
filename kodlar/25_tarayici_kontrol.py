"""55 haritanın gerçek Chromium kontrolleri; yalnız 127.0.0.1 kullanılır."""
from pathlib import Path
from functools import partial
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from html.parser import HTMLParser
from urllib.parse import urlsplit,unquote
import json,threading,hashlib
from playwright.sync_api import sync_playwright

SITE=Path(__file__).resolve().parents[1];DOC=SITE/'belgeler';PREVIEW=SITE/'onizlemeler'

class Links(HTMLParser):
 def __init__(self):super().__init__();self.values=[]
 def handle_starttag(self,tag,attrs):
  for k,v in attrs:
   if k in ['href','src'] and v:self.values.append(v)

def main():
 maps=json.loads((DOC/'karsilastirma_manifesti.json').read_text());local_links=0
 for p in SITE.rglob('*.html'):
  parser=Links();parser.feed(p.read_text())
  for value in parser.values:
   u=urlsplit(value)
   if u.scheme or not u.path:continue
   target=(p.parent/unquote(u.path)).resolve();assert target.is_relative_to(SITE) and target.exists(),(p,value);local_links+=1
 class Quiet(SimpleHTTPRequestHandler):
  def log_message(self,*args):pass
 server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(SITE)));threading.Thread(target=server.serve_forever,daemon=True).start();base=f'http://127.0.0.1:{server.server_port}/'
 errors=[];bad_resources=[];checked=[]
 with sync_playwright() as p:
  browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox','--disable-dev-shm-usage'])
  page=browser.new_page(viewport={'width':1440,'height':1000});page.on('pageerror',lambda e:errors.append(str(e)));page.on('response',lambda r:bad_resources.append({'status':r.status,'url':r.url}) if r.status>=400 else None)
  page.goto(base);page.wait_for_function('window.atlasGallery!==undefined');assert page.locator('.card').count()==55
  page.screenshot(path=str(PREVIEW/'01_atlas_masaustu.png'),full_page=False)
  page.locator('#pair').select_option('1984_2026');assert page.locator('.card:visible').count()==1
  page.locator('#pair').select_option('');page.locator('#kind').select_option('corine');assert page.locator('.card:visible').count()==13
  page.locator('#kind').select_option('');page.locator('#region').select_option('BE2');assert page.locator('.card:visible').count()==4
  for i,m in enumerate(maps):
   page.goto(base+m['map_file'],wait_until='domcontentloaded');page.wait_for_function('window.swipeApp && window.swipeApp.ready()',timeout=30000)
   assert not page.locator('#loading').is_visible();assert page.evaluate('swipeApp.data.id')==m['id']
   page.locator('#swipe').evaluate('(e)=>{e.value=25;e.dispatchEvent(new Event("input",{bubbles:true}));}');assert abs(page.evaluate('swipeApp.getView().ratio')-.25)<1e-9
   before=page.evaluate('swipeApp.getView().renderCount');page.locator('#swipe').evaluate('(e)=>{e.value=75;e.dispatchEvent(new Event("input",{bubbles:true}));}');assert page.evaluate('swipeApp.getView().renderCount')>before
   assert page.locator('#coords').count()==1
   if m['kind']=='uydu':
    page.locator('[data-mode=mask]').click();assert page.evaluate('swipeApp.getView().mode')=='mask';page.locator('[data-mode=overlay]').click();assert page.evaluate('swipeApp.getView().mode')=='overlay';page.locator('[data-mode=rgb]').click()
   old=page.evaluate('swipeApp.getView().scale');page.locator('#plus').click();assert page.evaluate('swipeApp.getView().scale')>old;page.locator('#reset').click()
   if m['dams']:
    dam=m['dams'][0];ll=page.evaluate('(p)=>swipeApp.unproject(...swipeApp.project(...p))',[dam['lon'],dam['lat']]);assert abs(ll[0]-dam['lon'])<1e-9 and abs(ll[1]-dam['lat'])<1e-9
   assert page.evaluate('document.documentElement.scrollWidth<=window.innerWidth'),m['id']
   if m['id'] in ['yuk_1990_2026','ozl_1984_pencere_1984_2026','pem_2020_2026','ozl_corine_2000_2018']:
    page.screenshot(path=str(PREVIEW/(m['id']+'.png')),full_page=True)
   checked.append({'id':m['id'],'ready':True,'swipe_slider':True,'zoom_reset':True,'common_camera':True,'coordinate_roundtrip':True})
   if (i+1)%10==0:print(json.dumps({'browser_maps_checked':i+1}),flush=True)
  # Gerçek işaretçi sürükleme ve klavye, tek kamerada pan.
  sample=next(m for m in maps if m['id']=='yuk_1990_2026');page.goto(base+sample['map_file']);page.wait_for_function('window.swipeApp && swipeApp.ready()');handle=page.locator('#handle');handle.focus();page.keyboard.press('ArrowRight');assert abs(page.evaluate('swipeApp.getView().ratio')-.52)<1e-9
  hb=handle.bounding_box();fb=page.locator('.frame').bounding_box();page.mouse.move(hb['x']+hb['width']/2,hb['y']+hb['height']/2);page.mouse.down();page.mouse.move(fb['x']+.7*fb['width'],fb['y']+.5*fb['height'],steps=8);page.mouse.up();assert abs(page.evaluate('swipeApp.getView().ratio')-.7)<.02
  old=page.evaluate('swipeApp.getView()');page.mouse.move(fb['x']+.25*fb['width'],fb['y']+.65*fb['height']);page.mouse.down();page.mouse.move(fb['x']+.35*fb['width'],fb['y']+.65*fb['height'],steps=8);page.mouse.up();new=page.evaluate('swipeApp.getView()');assert new['x']>old['x'] and new['ratio']==old['ratio']
  # Gerçek iframe içindeki Sidecar görünümü.
  host=browser.new_page(viewport={'width':900,'height':800});host.set_content('<iframe title="Sidecar testi" src="'+base+sample['map_file']+'?embed=1" width="620" height="650"></iframe>');frame=host.frames[1];frame.wait_for_function('window.swipeApp && swipeApp.ready()');assert not frame.locator('.story-pane').is_visible();host.screenshot(path=str(PREVIEW/'06_sidecar_iframe.png'))
  page.set_viewport_size({'width':390,'height':844});page.goto(base+sample['map_file']+'?embed=1&katman=su');page.wait_for_function('window.swipeApp && swipeApp.ready()');assert page.evaluate('swipeApp.getView().mode')=='mask';assert page.evaluate('document.documentElement.scrollWidth<=window.innerWidth');page.screenshot(path=str(PREVIEW/'07_telefon_sidecar.png'),full_page=True)
  page.goto(base);page.wait_for_function('window.atlasGallery!==undefined');assert page.evaluate('document.documentElement.scrollWidth<=window.innerWidth');page.screenshot(path=str(PREVIEW/'08_telefon_atlas.png'),full_page=False)
  assert not errors,errors;assert not bad_resources,bad_resources
  browser.close()
 server.shutdown()
 report={'passed':True,'maps_checked':len(checked),'maps':checked,'local_links_checked':local_links,'gallery_filters_checked':True,'keyboard_and_pointer_swipe_checked':True,'pan_single_camera_checked':True,'real_iframe_sidecar_checked':True,'mobile_checked':True,'javascript_errors':errors,'bad_http_resources':bad_resources,'browser_origin':'127.0.0.1 only','limitations':'Kullanıcının kurumsal tarayıcısındaki file:// izni ve gerçek ArcGIS StoryMaps kuruluş hesabının embed politikası bu ortamda sınanmadı. GitHub Pages yayını yapılmadı.'}
 (DOC/'tarayici_kontrol.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps({k:v for k,v in report.items() if k!='maps'},ensure_ascii=False))

if __name__=='__main__':main()
