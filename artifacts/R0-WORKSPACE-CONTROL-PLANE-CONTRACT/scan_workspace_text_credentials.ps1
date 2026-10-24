param(
    [string]$Root = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
)

$ErrorActionPreference = 'Stop'
$Root = (Resolve-Path -LiteralPath $Root).Path
$Extensions = @('.py', '.js', '.mjs', '.cjs', '.ts', '.tsx', '.json', '.md', '.yaml', '.yml', '.toml', '.ini', '.cfg', '.txt', '.csv', '.html', '.css', '.sh', '.ps1', '.xml', '.env', '.properties')
$ExcludedDirectoryNames = @('.git', 'node_modules', '__pycache__', '.venv', 'venv', 'dist', 'build')
$ExcludedFiles = @(
    [IO.Path]::GetFullPath($PSCommandPath),
    [IO.Path]::GetFullPath((Join-Path $PSScriptRoot 'WORKSPACE_CREDENTIAL_SCAN_REPORT_2026-09-25.md'))
)
$Rules = [ordered]@{
    private_key = '-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----'
    aws_access_key = '(?<![A-Z0-9])AKIA[0-9A-Z]{16}(?![A-Z0-9])'
    github_token = '(?i)\bgh[pousr]_[A-Za-z0-9_]{30,}\b'
    gitlab_token = '(?i)\bglpat-[A-Za-z0-9_-]{20,}\b'
    slack_token = '(?i)\bxox[baprs]-[A-Za-z0-9-]{20,}\b'
    google_api_key = '\bAIza[0-9A-Za-z_-]{35}\b'
    openai_key = '(?i)\bsk-(?:proj-)?[A-Za-z0-9_-]{24,}\b'
    generic_credential_assignment = '(?i)\b(?:api[_-]?key|access[_-]?token|client[_-]?secret|secret|password|passwd)\b\s*[:=]\s*["' + "'" + '`]?([A-Za-z0-9/+_=.-]{20,})'
}
$Placeholder = '(?i)^(?:example|sample|dummy|fake|test|placeholder|changeme|replace|your|insert|redacted|none|unknown|xxx|sk-test|sk-example)[A-Za-z0-9/+_=.-]*$'
$Findings = [System.Collections.Generic.List[object]]::new()
$ReadErrors = [System.Collections.Generic.List[string]]::new()
$Scanned = 0
$SkippedBinary = 0
$SkippedLarge = 0

$PendingDirectories = [System.Collections.Generic.Stack[string]]::new()
$PendingDirectories.Push($Root)
while ($PendingDirectories.Count -gt 0) {
    $Directory = $PendingDirectories.Pop()
    try {
        $Children = Get-ChildItem -LiteralPath $Directory -Force
    }
    catch {
        $ReadErrors.Add($Directory.Substring($Root.Length).TrimStart('\', '/') + ':' + $_.Exception.GetType().Name)
        continue
    }
    foreach ($Child in $Children) {
        if (($Child.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) { continue }
        if ($Child.PSIsContainer) {
            if ($ExcludedDirectoryNames -notcontains $Child.Name) { $PendingDirectories.Push($Child.FullName) }
            continue
        }
        if ($Extensions -notcontains $Child.Extension.ToLowerInvariant()) { continue }
        if ($ExcludedFiles -contains [IO.Path]::GetFullPath($Child.FullName)) { continue }
        if ($Child.Length -gt 5MB) {
            $SkippedLarge++
            continue
        }
        try {
            $Content = [IO.File]::ReadAllText($Child.FullName)
            if ($Content.Contains([char]0)) {
                $SkippedBinary++
                continue
            }
            $Scanned++
            $Lines = $Content -split "`r?`n"
            for ($Index = 0; $Index -lt $Lines.Length; $Index++) {
                foreach ($RuleName in $Rules.Keys) {
                    $Match = [regex]::Match($Lines[$Index], $Rules[$RuleName])
                    if (-not $Match.Success) { continue }
                    if ($RuleName -eq 'generic_credential_assignment' -and $Match.Groups[1].Success -and $Match.Groups[1].Value -match $Placeholder) { continue }
                    $RelativePath = $Child.FullName.Substring($Root.Length).TrimStart('\', '/')
                    $Findings.Add([pscustomobject]@{ rule = $RuleName; path = $RelativePath; line = $Index + 1 })
                }
            }
        }
        catch {
            $ReadErrors.Add($Child.FullName.Substring($Root.Length).TrimStart('\', '/') + ':' + $_.Exception.GetType().Name)
        }
    }
}

"TEXT_FILES_SCANNED=$Scanned"
"SKIPPED_BINARY_OR_NUL=$SkippedBinary"
"SKIPPED_OVER_5_MIB=$SkippedLarge"
"READ_ERRORS=$($ReadErrors.Count)"
"FINDINGS=$($Findings.Count)"
if ($Findings.Count -gt 0) {
    $Findings | Sort-Object path, line, rule | Format-Table -AutoSize
}
if ($ReadErrors.Count -gt 0) {
    'READ_ERROR_PATHS_AND_TYPES:'
    $ReadErrors | Sort-Object
}
"ENGINE=custom high-confidence indicators; not a replacement for Gitleaks, TruffleHog, or a dedicated secret scanner"
