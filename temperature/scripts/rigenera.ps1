# Rigenera tutto: serie unica (da splice.json) e dati del sito (docs/temperature/data).
# uso: powershell -File temperature\scripts\rigenera.ps1   (da qualsiasi cartella)
$ErrorActionPreference = 'Stop'
$t = Split-Path -Parent $PSScriptRoot            # ...\temperature
$root = Split-Path -Parent $t                    # ...\milano-in-dati
python -I "$t\scripts\costruisci_serie.py" "$t\raw" "$t\splice.json" "$t\serie\serie_unica.csv"
if ($LASTEXITCODE -ne 0) { throw 'costruisci_serie.py fallito' }
python -I "$t\scripts\statistiche.py" "$t\serie\serie_unica.csv" "$t\splice.json" "$root\docs\temperature\data"
if ($LASTEXITCODE -ne 0) { throw 'statistiche.py fallito' }
Write-Host 'Fatto. Dati del sito in docs\temperature\data (pagina: docs\temperature\index.html).'
