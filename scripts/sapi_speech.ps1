param([Parameter(Mandatory=$true)][string]$TextFile,[Parameter(Mandatory=$true)][string]$OutputFile,[string]$VoiceName='', [string]$Language='zh-CN',[int]$Rate=0)
$ErrorActionPreference='Stop'
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$taskVoice=$null;$taskStream=$null
try {
    if (Test-Path -LiteralPath $OutputFile) { throw 'Output already exists' }
    $taskText=[System.IO.File]::ReadAllText($TextFile,[System.Text.Encoding]::UTF8)
    if ([string]::IsNullOrWhiteSpace($taskText) -or $taskText.Length -gt 10000) { throw 'Text must contain 1..10000 characters' }
    if ($Rate -lt -10 -or $Rate -gt 10) { throw 'Rate must be -10..10' }
    $taskVoice=New-Object -ComObject SAPI.SpVoice
    $taskVoices=@($taskVoice.GetVoices())
    if ($VoiceName) { $taskSelected=@($taskVoices | Where-Object { $_.GetDescription() -eq $VoiceName }) }
    else {
        $taskLCID=([System.Globalization.CultureInfo]::GetCultureInfo($Language)).LCID.ToString('x')
        $taskSelected=@($taskVoices | Where-Object { ($_.GetAttribute('Language').ToLower().Split(';')) -contains $taskLCID })
    }
    if ($taskSelected.Count -eq 0) { throw 'Requested local voice is not installed' }
    $taskVoice.Voice=$taskSelected[0]
    $taskVoice.Rate=$Rate
    $taskStream=New-Object -ComObject SAPI.SpFileStream
    $taskStream.Open($OutputFile,3,$false)
    $taskVoice.AudioOutputStream=$taskStream
    $null=$taskVoice.Speak($taskText,16)
    $taskStream.Close();$taskStream=$null
    @{voice=$taskVoice.Voice.GetDescription();engine='WINDOWS_SAPI';synthetic_voice=$true} | ConvertTo-Json -Compress
} catch {
    [Console]::Error.WriteLine('Local speech failed; verify installed voices, locale and file access.')
    exit 2
} finally {
    if ($null -ne $taskStream) { $taskStream.Close() }
    if ($null -ne $taskVoice) { [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($taskVoice) }
}
