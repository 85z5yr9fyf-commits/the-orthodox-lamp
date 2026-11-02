# Rebuilds ask-content.json (the text "Ask the Lamp" searches and sends to the AI)
# from every page on the site. Run after editing pages: python3 build_ask_content.py
import json,re,glob,os,sys
from bs4 import BeautifulSoup
os.chdir(os.path.dirname(os.path.abspath(__file__)))
old={p['f']:p for p in json.load(open('ask-content.json',encoding='utf-8'))['pages']}
SKIP={'apostolic_grace.html','index.html','ortho_deploy.html','study.html','learning_paths.html','fathers.html'}
CH=1100
def clean(t): return re.sub(r'\s+',' ',t).strip()
def chunks(text):
    out=[];t=text
    while len(t)>CH:
        cut=t.rfind('. ',int(CH*0.6),CH)
        if cut<0: cut=t.rfind(' ',0,CH)
        out.append(t[:cut+1].strip()); t=t[cut+1:].strip()
    if t: out.append(t)
    return out
pages=[]
for f in sorted(glob.glob('*.html')):
    if f in SKIP: continue
    s=open(f,encoding='utf-8').read()
    soup=BeautifulSoup(s,'html.parser')
    title=old.get(f,{}).get('t') or clean(soup.title.get_text()).split(' — The Orthodox Lamp')[0]
    kw=old.get(f,{}).get('kw',[])
    for tag in soup(['script','style','noscript','nav']): tag.decompose()
    secs=[]
    if f in ('timeline.html','kings_timeline.html'):
        i=s.find('var EV'); j=s.find('[',i)
        ev,_=json.JSONDecoder().raw_decode(s[j:])
        buf=''
        for e in ev:
            item=clean(f"{e.get('date','')}: {e.get('t','')}. {BeautifulSoup(str(e.get('d','')),'html.parser').get_text()} ({e.get('src','') or ''})")
            if len(buf)+len(item)>CH and buf: secs.append({'a':'','h':'Timeline','x':buf.strip()}); buf=''
            buf+=item+' '
        if buf: secs.append({'a':'','h':'Timeline','x':buf.strip()})
    else:
        els=[el for el in soup.find_all(['div','section']) if el.get('id') and 'sec' in (el.get('class') or [])]
        els=[el for el in els if not any(p in els for p in el.parents)]
        if not els:
            body=soup.find('main') or soup.body
            for c in chunks(clean(body.get_text(' '))): secs.append({'a':'','h':'','x':c})
        for el in els:
            hd=el.find(['h2','h3']) or el.find(class_=re.compile(r'^sec-h'))
            h=clean(hd.get_text(' ')) if hd else ''
            h=re.sub(r'\s*[►▶▼]$','',h)
            txt=clean(el.get_text(' '))
            txt=re.sub(r'\s*[►▶▼]\s*',' ',txt)
            for c in chunks(txt): secs.append({'a':el['id'],'h':h,'x':c})
    if secs: pages.append({'f':f,'t':title,'kw':kw,'secs':secs})
out=json.dumps({'pages':pages},ensure_ascii=False,separators=(',',':'))
open('ask-content.json','w',encoding='utf-8').write(out)
print(len(pages),'pages',sum(len(p['secs']) for p in pages),'passages',len(out.encode())//1024,'KB')
