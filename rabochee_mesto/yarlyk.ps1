# Ярлык «Теплоснабжение» на рабочем месте: программа с сервера в отдельном окне
# Edge (или Chrome) на весь экран, без адресной строки и вкладок. Python не нужен.
param([string]$Adres = "http://Server-b:8020/")

$browser = $null
foreach ($p in @(
    "${env:ProgramFiles(x86)}\Microsoft\Edge\Application\msedge.exe",
    "$env:ProgramFiles\Microsoft\Edge\Application\msedge.exe",
    "${env:ProgramFiles(x86)}\Google\Chrome\Application\chrome.exe",
    "$env:ProgramFiles\Google\Chrome\Application\chrome.exe",
    "$env:LOCALAPPDATA\Google\Chrome\Application\chrome.exe",
    "$env:LOCALAPPDATA\Yandex\YandexBrowser\Application\browser.exe")) {
  if ($p -and (Test-Path $p)) { $browser = $p; break }
}
if (-not $browser) { Write-Host "Не найден Microsoft Edge или Google Chrome. Установите Edge и запустите ещё раз."; exit 1 }

$dir = Join-Path $env:LOCALAPPDATA "Teplo"
New-Item -ItemType Directory -Force -Path $dir | Out-Null
$icon = Join-Path $dir "teplo.ico"
try {
  (New-Object System.Net.WebClient).DownloadFile(($Adres.TrimEnd('/') + "/static/img/teplo.ico"), $icon)
} catch {
  Write-Host "Не удалось открыть $Adres - проверьте, что сервер программы запущен. Ярлык всё равно создаётся."
  $icon = $browser
}

$sh = New-Object -ComObject WScript.Shell
$lnk = $sh.CreateShortcut((Join-Path ([Environment]::GetFolderPath('Desktop')) 'Теплоснабжение.lnk'))
$lnk.TargetPath = $browser
$lnk.Arguments = "--app=$Adres --start-maximized --user-data-dir=""$dir\app-profile"" --no-first-run --no-default-browser-check"
$lnk.IconLocation = $icon
$lnk.Description = 'Теплоснабжение'
$lnk.Save()
Write-Host "Ярлык «Теплоснабжение» создан на рабочем столе ($Adres)."
