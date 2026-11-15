"""Scarica i dati grezzi della pagina «La falda che risale» in falda/dati_grezzi/ (non pubblicati)."""
import urllib.request, pathlib
base = pathlib.Path(__file__).resolve().parent.parent / "dati_grezzi"
base.mkdir(exist_ok=True)
L = "https://www.dati.lombardia.it/resource/%s.geojson?$limit=50000"
FILE = {
    "piezo_2007_03.geojson": L % "t34c-5qeq", "piezo_2007_09.geojson": L % "vxmx-t3zq",
    "piezo_2009_03.geojson": L % "dmse-82se", "piezo_2009_09.geojson": L % "875x-wqng",
    "piezo_2010_03.geojson": L % "72vq-8vpk", "piezo_2010_09.geojson": L % "253s-q2hp",
    "piezo_2011_03.geojson": L % "sb4i-gr6d", "piezo_2011_09.geojson": L % "354f-iu45",
    "piezo_2012_03.geojson": L % "2xpi-jryy", "piezo_2012_09.geojson": L % "qs2b-225i",
    "piezo_2013_09.geojson": L % "832x-mcv2",
    "piezo_2022_03.geojson": L % "wp7j-awzt", "piezo_2022_09.geojson": L % "9j8c-7map",
    "piezo_2022_09_controllo.geojson": L % "krur-6ms9",
    "soggiacenza_2022_03.geojson": L % "u3wq-chcr",
    "ds587.csv": "https://dati.comune.milano.it/dataset/2cb10fcf-5703-4b49-89f9-ff4888e6b40a/resource/d121502c-032d-45d3-9893-c299da2f4e4e/download/ds587_punti_rete_di_monitoragg_3xuq-hj34_final.csv",
}
for nome, url in FILE.items():
    dest = base / nome
    if dest.exists():
        print("già presente", nome); continue
    with urllib.request.urlopen(url, timeout=120) as r:
        dest.write_bytes(r.read())
    print("scaricato", nome, dest.stat().st_size)
