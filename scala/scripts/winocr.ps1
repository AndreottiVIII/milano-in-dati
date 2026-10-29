# OCR con il motore integrato di Windows 11 (lingua it-IT, nessuna installazione). Stampa JSON: righe con parole e riquadri.
# Uso: powershell -NoProfile -ExecutionPolicy Bypass -File winocr.ps1 -Img <immagine.png|jpg>
param([string]$Img)
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
Add-Type -AssemblyName System.Runtime.WindowsRuntime
[void][Windows.Media.Ocr.OcrEngine, Windows.Foundation, ContentType=WindowsRuntime]
[void][Windows.Graphics.Imaging.BitmapDecoder, Windows.Foundation, ContentType=WindowsRuntime]
[void][Windows.Storage.StorageFile, Windows.Foundation, ContentType=WindowsRuntime]
$eng = [Windows.Media.Ocr.OcrEngine]::TryCreateFromUserProfileLanguages()
$asTask = ([System.WindowsRuntimeSystemExtensions].GetMethods() | ? { $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1' })[0]
function Await($op,$t){ $m=$asTask.MakeGenericMethod($t); $x=$m.Invoke($null,@($op)); $x.Wait(-1)|Out-Null; $x.Result }
$f = Await ([Windows.Storage.StorageFile]::GetFileFromPathAsync($Img)) ([Windows.Storage.StorageFile])
$s = Await ($f.OpenAsync([Windows.Storage.FileAccessMode]::Read)) ([Windows.Storage.Streams.IRandomAccessStream])
$d = Await ([Windows.Graphics.Imaging.BitmapDecoder]::CreateAsync($s)) ([Windows.Graphics.Imaging.BitmapDecoder])
$b = Await ($d.GetSoftwareBitmapAsync()) ([Windows.Graphics.Imaging.SoftwareBitmap])
$r = Await ($eng.RecognizeAsync($b)) ([Windows.Media.Ocr.OcrResult])
$out = @($r.Lines | % { @{ text=$_.Text; words=@($_.Words | % { @{ t=$_.Text; x=[int]$_.BoundingRect.X; y=[int]$_.BoundingRect.Y; w=[int]$_.BoundingRect.Width; h=[int]$_.BoundingRect.Height } }) } })
$out | ConvertTo-Json -Depth 5 -Compress
