from playwright.sync_api import sync_playwright
import glob,os,json
pages=sorted(glob.glob('*.html'))+sorted(glob.glob('newsletters/*.html'))
os.makedirs('shots',exist_ok=True)
JS="""()=>{const vw=innerWidth,r=[];
const sw=document.documentElement.scrollWidth;
for(const e of document.querySelectorAll('body *')){const b=e.getBoundingClientRect();if(!b.width||!b.height)continue;
 const cs=getComputedStyle(e);
 if(b.right>vw+1&&cs.position!=='fixed'){let p=e.parentElement,clip=false;while(p&&p!==document.body){const s=getComputedStyle(p);if(s.overflowX!=='visible'&&p.getBoundingClientRect().right<=vw+1){clip=true;break}p=p.parentElement}
  if(!clip)r.push('OVERFLOW '+e.tagName+' "'+(e.innerText||e.alt||'').trim().slice(0,50)+'" right='+Math.round(b.right))}
 if(e.children.length===0&&e.innerText&&e.scrollWidth>e.clientWidth+2&&cs.overflowX!=='visible')r.push('CLIPPED TEXT '+e.tagName+' "'+e.innerText.trim().slice(0,50)+'"');
 if(['A','BUTTON'].includes(e.tagName)&&vw<500&&b.height<30&&b.width<30)r.push('SMALL TAP '+e.tagName+' "'+(e.innerText||'').trim().slice(0,30)+'" '+Math.round(b.width)+'x'+Math.round(b.height));
}
const broken=[...document.images].filter(i=>i.complete&&i.naturalWidth===0).map(i=>i.getAttribute('src'));
const noalt=[...document.images].filter(i=>!i.hasAttribute('alt')).length;
return {sw,issues:[...new Set(r)].slice(0,25),broken,noalt,title:document.title}}"""
rep={}
with sync_playwright() as p:
    b=p.chromium.launch()
    for rel in pages:
        for w in (1280,390):
            pg=b.new_page(viewport={'width':w,'height':900})
            errs=[]; pg.on('pageerror',lambda e:errs.append(str(e)[:200]))
            pg.goto('http://localhost:8765/'+rel,wait_until='networkidle'); pg.wait_for_timeout(1500)
            h=pg.evaluate("Math.max(...[...document.querySelectorAll('*')].map(e=>e.scrollHeight))")
            pg.set_viewport_size({'width':w,'height':min(h+50,20000)}); pg.wait_for_timeout(800)
            pg.evaluate("()=>{document.querySelectorAll('img[loading=lazy]').forEach(i=>i.loading='eager')}"); pg.wait_for_load_state('networkidle'); pg.wait_for_timeout(1500)
            r=pg.evaluate(JS); r['errors']=errs; r['height']=h
            rep[f'{rel} @{w}']=r
            pg.screenshot(path='shots/'+rel.replace('/','_').replace('.html','')+f'_{w}.jpg',type='jpeg',quality=70)
            pg.close()
    b.close()
json.dump(rep,open('shots/report.json','w'),indent=1)
