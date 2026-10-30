import struct, json, sys, os
root=sys.argv[1]
def dbf(path):
    b=open(path,"rb").read(); n,hl,rl=struct.unpack("<IHH",b[4:12])
    fields=[]; o=32
    while b[o]!=0x0D:
        name=b[o:o+11].split(b"\0")[0].decode("latin1"); fields.append((name,chr(b[o+11]),b[o+16])); o+=32
    recs=[]
    for i in range(n):
        r=b[hl+i*rl:hl+(i+1)*rl]; p=1; d={}
        for name,t,l in fields: d[name]=r[p:p+l].decode("utf-8","replace").strip(); p+=l
        recs.append(d)
    return fields,recs
def num(v):
    try: return round(float(v))
    except: return None
def area(r): return sum((r[i][0]*r[i+1][1]-r[i+1][0]*r[i][1]) for i in range(len(r)-1))/2
def shp_geoms(path, want):
    b=open(path,"rb").read(); o=100; i=0; out={}
    while o<len(b):
        rn,cl=struct.unpack(">ii",b[o:o+8]); o+=8; c=b[o:o+cl*2]; o+=cl*2
        if i in want:
            t=struct.unpack("<i",c[:4])[0]
            if t in (5,15):
                np_,npt=struct.unpack("<ii",c[36:44]); parts=struct.unpack(f"<{np_}i",c[44:44+4*np_]); q=44+4*np_
                pts=[struct.unpack("<dd",c[q+16*k:q+16*k+16]) for k in range(npt)]
                rings=[pts[parts[k]:(parts[k+1] if k+1<np_ else npt)] for k in range(np_)]
                polys=[]
                for r in rings:
                    r=[[round(x,1),round(y,1)] for x,y in r]
                    if area(r)<0 or not polys: polys.append([r])   # orario = esterno (shapefile)
                    else: polys[-1].append(r)
                out[i]={"type":"MultiPolygon","coordinates":polys}
        i+=1
    return out
jobs={1991:"R03_91_WGS84/R03_91_WGS84",2001:"R03_01_WGS84/R03_01_WGS84",2011:"R03_11_WGS84/R03_11_WGS84",2021:"R03_21/SHP/R03_21_WGS84"}
for y,base in jobs.items():
    d=root+"/raw/estratti/"+(base if y==2021 else base.split("/")[0]+"/"+base)
    fields,recs=dbf(d+".dbf"); print(y,[f[0] for f in fields])
    key="PRO_COM"
    want={i for i,r in enumerate(recs) if num(r.get(key,""))==15146}
    g=shp_geoms(d+".shp",want)
    feats=[{"type":"Feature","properties":recs[i],"geometry":g.get(i)} for i in sorted(want)]
    fc={"type":"FeatureCollection","crs":{"type":"name","properties":{"name":"urn:ogc:def:crs:EPSG::32632"}},"features":feats}
    json.dump(fc,open(f"{root}/pulito/geometrie/sezioni_{y}_Milano.geojson","w"),separators=(",",":"))
    print(y,len(feats),sum(1 for f in feats if f["geometry"]),os.path.getsize(f"{root}/pulito/geometrie/sezioni_{y}_Milano.geojson"))
