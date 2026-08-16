param(
    [string]$OutPath = (Join-Path $env:TEMP "fonts_data.json")
)

Add-Type -AssemblyName System.Drawing

$fc = New-Object System.Drawing.Text.InstalledFontCollection
$familyNames = @{}
$famObjBy = @{}
foreach ($f in $fc.Families) {
    $familyNames[$f.Name] = $true
    $famObjBy[$f.Name] = $f
}

$regKeys = @(
    "HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts",
    "HKCU:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts"
)

$entries = @()
foreach ($key in $regKeys) {
    try {
        $reg = Get-ItemProperty $key -ErrorAction Stop
    } catch {
        continue
    }
    foreach ($p in $reg.PSObject.Properties) {
        if ($p.Name -like 'PS*') { continue }
        $file = [string]$p.Value
        $ext = [System.IO.Path]::GetExtension($file).ToLower()
        if ($ext -in '.ttf', '.ttc', '.otf') {
            $entries += [PSCustomObject]@{
                DisplayName = $p.Name
                File        = [System.IO.Path]::GetFileName($file)
            }
        }
    }
}

function Get-FontFamilyName([string]$displayName) {
    $n = $displayName -replace ' \((TrueType|OpenType)\)$', ''
    $n = $n -replace ' Bold Italic$', '' -replace ' Italic$', '' -replace ' Bold$', '' -replace ' Regular$', ''
    return $n.Trim()
}

$fontMap = New-Object 'System.Collections.Generic.Dictionary[string,object]' ([System.StringComparer]::OrdinalIgnoreCase)

foreach ($fam in $familyNames.Keys) {
    $matched = @($entries | Where-Object {
        $dn = Get-FontFamilyName $_.DisplayName
        $dn -eq $fam -or $dn.StartsWith($fam + ' ')
    } | ForEach-Object { $_.File } | Sort-Object -Unique)
    $zh = ''
    try { $zh = [string]$famObjBy[$fam].GetName(0x804) } catch { $zh = '' }
    $fontMap[$fam] = [PSCustomObject]@{ Name = $fam; ZhName = $zh.Trim(); Files = $matched }
}

# 补充扫描“当前用户”字体目录：受限环境下看不到该用户的字体注册表，
# 改为直接读取字体文件并解析字体族名，个人安装的字体也能被收录。
$userFontDir = Join-Path $env:LOCALAPPDATA 'Microsoft\Windows\Fonts'
if (Test-Path $userFontDir) {
    $userFontFiles = Get-ChildItem -LiteralPath $userFontDir -File -ErrorAction SilentlyContinue | Where-Object {
        [System.IO.Path]::GetExtension($_.Name).ToLower() -in '.ttf', '.ttc', '.otf'
    }
    $skipCount = 0
    foreach ($fontFile in $userFontFiles) {
        $pc = New-Object System.Drawing.Text.PrivateFontCollection
        try {
            $pc.AddFontFile($fontFile.FullName)
            $seenInFile = @{}
            foreach ($family in $pc.Families) {
                $famName = [string]$family.Name
                if ($seenInFile.ContainsKey($famName)) { continue }
                $seenInFile[$famName] = $true
                $zh = ''
                try { $zh = [string]$family.GetName(0x804) } catch { $zh = '' }
                if (-not $fontMap.ContainsKey($famName)) {
                    $fontMap[$famName] = [PSCustomObject]@{ Name = $famName; ZhName = $zh.Trim(); Files = @() }
                } elseif (-not $fontMap[$famName].ZhName -and $zh.Trim()) {
                    $fontMap[$famName].ZhName = $zh.Trim()
                }
                $merged = @($fontMap[$famName].Files + $fontFile.Name) | Sort-Object -Unique
                $fontMap[$famName].Files = @($merged)
            }
        } catch {
            $skipCount++
        } finally {
            $pc.Dispose()
        }
    }
    if ($skipCount -gt 0) {
        Write-Warning "有 $skipCount 个字体文件无法读取，已跳过"
    }
}

$sorted = $fontMap.Values | Sort-Object Name
$sorted | ConvertTo-Json -Depth 3 | Set-Content -Encoding UTF8 $OutPath
Write-Host "Wrote $OutPath with $($sorted.Count) families"
