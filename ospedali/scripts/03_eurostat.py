"""Popolazione al 1 gennaio (Eurostat demo_pjan, CC BY 4.0): Italia e Lombardia, 2010-2024. Una richiesta."""
import subprocess, pathlib
OUT = pathlib.Path(__file__).resolve().parent.parent / "dati_grezzi" / "eurostat_demo_r_d2jan_IT_ITC4.json"
U = ("https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/demo_r_d2jan"
     "?format=JSON&lang=EN&age=TOTAL&sex=T&unit=NR&geo=IT&geo=ITC4&sinceTimePeriod=2010")
subprocess.run(["curl","-sS","--fail","-A","milano-in-dati/1.0",U,"-o",str(OUT)],check=True)
print(OUT.stat().st_size)
