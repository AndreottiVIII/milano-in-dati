import sys
P=sys.argv[1]
s=open(P+'/docs/medici-farmacie/index.html',encoding='utf-8').read()
css=s[s.index('<style>')+7:s.index('</style>')]
c=open(P+'/bozze-grafici/botteghe-v2/corpo.html',encoding='utf-8').read()
open(P+'/bozze-grafici/botteghe-v2/index.html','w',encoding='utf-8').write(c.replace('/*CSS*/',css))
print(len(css))
