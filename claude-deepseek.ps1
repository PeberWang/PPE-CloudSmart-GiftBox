# Claude Code + DeepSeek V4 Launcher
# Run: .\claude-deepseek.ps1

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host ""
Write-Host "Setting up Claude Code -> DeepSeek V4 Pro..." -ForegroundColor Cyan

$env:ANTHROPIC_BASE_URL = "https://api.deepseek.com/anthropic"
$env:ANTHROPIC_AUTH_TOKEN = "sk-9894bf5a19424316b603c3d857dfd80b"
$env:ANTHROPIC_API_KEY = ""
$env:ANTHROPIC_MODEL = "deepseek-v4-pro"
$env:ANTHROPIC_DEFAULT_OPUS_MODEL = "deepseek-v4-pro"
$env:ANTHROPIC_DEFAULT_SONNET_MODEL = "deepseek-v4-pro"
$env:ANTHROPIC_DEFAULT_HAIKU_MODEL = "deepseek-v4-flash"
$env:CLAUDE_CODE_SUBAGENT_MODEL = "deepseek-v4-flash"
$env:CLAUDE_CODE_EFFORT_LEVEL = "max"

Write-Host "Done. Model: DeepSeek V4 Pro (subagent: V4 Flash)" -ForegroundColor Green
Write-Host "Launching Claude Code..." -ForegroundColor Cyan
Write-Host "(Close terminal to restore defaults)" -ForegroundColor DarkGray
Write-Host ""

claude
