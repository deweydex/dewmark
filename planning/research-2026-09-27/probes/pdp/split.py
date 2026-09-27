import re,sys,os
for fn in sorted(os.listdir('.')):
    if not fn.endswith('.html'): continue
    s=open(fn,encoding='utf-8').read()
    base=fn[:-5]
    os.makedirs('parts/'+base,exist_ok=True)
    m=re.search(r'<style>(.*?)</style>',s,re.S)
    style=m.group(1)
    m2=re.search(r'<script type="application/json" id="exam-src">(.*?)</script>',s,re.S)
    src=m2.group(1)
    # last inline script
    scripts=re.findall(r'<script>(.*?)</script>',s,re.S)
    js=scripts[-1]
    body=s[s.index('</style>'):s.index('<script type="application/json" id="exam-src">')]
    head=s[:s.index('<style>')]
    tail=s[m2.end():]
    for n,c in [('style.css',style),('exam-src.json',src),('script.js',js),('body.html',body),('head.html',head)]:
        open(f'parts/{base}/{n}','w').write(c)
    print(fn,len(style),len(src),len(js),len(body),len(head),len(scripts))
