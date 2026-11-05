# Legge il testo delle locandine con il motore integrato di Windows 11, senza installare nulla.
# Per ogni immagine scrive una riga JSON: file e righe di testo con l'altezza media delle parole.
# Se il file di uscita esiste già, salta le immagini già lette: si può interrompere e riprendere.
# Uso: powershell -NoProfile -ExecutionPolicy Bypass -File locandine_ocr.ps1 -Elenco <percorsi.txt> -Uscita <testo.jsonl> [-Scala 3] [-Parole]
param([string]$Elenco, [string]$Uscita, [int]$Scala = 1, [switch]$Parole)
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
Add-Type -AssemblyName System.Runtime.WindowsRuntime
[void][Windows.Media.Ocr.OcrEngine, Windows.Foundation, ContentType=WindowsRuntime]
[void][Windows.Graphics.Imaging.BitmapDecoder, Windows.Foundation, ContentType=WindowsRuntime]
[void][Windows.Storage.StorageFile, Windows.Foundation, ContentType=WindowsRuntime]
$eng = [Windows.Media.Ocr.OcrEngine]::TryCreateFromUserProfileLanguages()
$asTask = ([System.WindowsRuntimeSystemExtensions].GetMethods() | ? { $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1' })[0]
function Await($op,$t){ $m=$asTask.MakeGenericMethod($t); $x=$m.Invoke($null,@($op)); $x.Wait(-1)|Out-Null; $x.Result }
$fatti = @{}
if (Test-Path $Uscita) { foreach ($l in [IO.File]::ReadLines($Uscita)) { try { $fatti[($l | ConvertFrom-Json).file] = 1 } catch {} } }
$utf8 = New-Object System.Text.UTF8Encoding($false)
$sw = New-Object System.IO.StreamWriter($Uscita, $true, $utf8)
$n = 0
foreach ($p in [IO.File]::ReadLines($Elenco)) {
  $nome = [IO.Path]::GetFileName($p)
  if ($fatti.ContainsKey($nome)) { continue }
  try {
    $f = Await ([Windows.Storage.StorageFile]::GetFileFromPathAsync($p)) ([Windows.Storage.StorageFile])
    $s = Await ($f.OpenAsync([Windows.Storage.FileAccessMode]::Read)) ([Windows.Storage.Streams.IRandomAccessStream])
    $d = Await ([Windows.Graphics.Imaging.BitmapDecoder]::CreateAsync($s)) ([Windows.Graphics.Imaging.BitmapDecoder])
    if ($Scala -gt 1) {
      # ingrandire prima di leggere: le scritte piccole (cantanti, prezzi) diventano leggibili
      $t = New-Object Windows.Graphics.Imaging.BitmapTransform
      $t.ScaledWidth = $d.PixelWidth * $Scala
      $t.ScaledHeight = $d.PixelHeight * $Scala
      $t.InterpolationMode = [Windows.Graphics.Imaging.BitmapInterpolationMode]::Fant
      $b = Await ($d.GetSoftwareBitmapAsync([Windows.Graphics.Imaging.BitmapPixelFormat]::Bgra8, [Windows.Graphics.Imaging.BitmapAlphaMode]::Premultiplied, $t, [Windows.Graphics.Imaging.ExifOrientationMode]::RespectExifOrientation, [Windows.Graphics.Imaging.ColorManagementMode]::DoNotColorManage)) ([Windows.Graphics.Imaging.SoftwareBitmap])
    } else {
      $b = Await ($d.GetSoftwareBitmapAsync()) ([Windows.Graphics.Imaging.SoftwareBitmap])
    }
    $r = Await ($eng.RecognizeAsync($b)) ([Windows.Media.Ocr.OcrResult])
    $righe = @($r.Lines | % { $w = @($_.Words); @{ t = $_.Text; h = [int](($w | % { $_.BoundingRect.Height } | Measure-Object -Average).Average); y = [int]$w[0].BoundingRect.Y } })
    if ($Parole) {
      # ogni parola con la sua posizione: serve per capire in quale colonna sta un nome
      $pp = @($r.Lines | % { $_.Words } | % { @{ t = $_.Text; x = [int]$_.BoundingRect.X; y = [int]$_.BoundingRect.Y; w = [int]$_.BoundingRect.Width; h = [int]$_.BoundingRect.Height } })
      $sw.WriteLine((@{ file = $nome; parole = $pp } | ConvertTo-Json -Depth 4 -Compress))
    } else {
      $sw.WriteLine((@{ file = $nome; righe = $righe } | ConvertTo-Json -Depth 4 -Compress))
    }
    $b.Dispose(); $s.Dispose()
  } catch {
    $sw.WriteLine((@{ file = $nome; errore = "$($_.Exception.Message)" } | ConvertTo-Json -Compress))
  }
  $n++
  if ($n % 25 -eq 0) { $sw.Flush() }
}
$sw.Close()
Write-Output "letti $n"
