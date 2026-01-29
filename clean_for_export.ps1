# clean_for_export.ps1 - 清理项目以便迁移/压缩

$ErrorActionPreference = "Continue"

Write-Host "正在清理项目以便迁移..." -ForegroundColor Cyan

# 要清理的文件夹列表
$foldersToRemove = @(
    ".venv",
    "__pycache__",
    ".pytest_cache",
    ".idea",
    "build",
    "dist",
    "*.egg-info"
)

foreach ($item in $foldersToRemove) {
    if ($item -like "*.*") {
         # 这是一个文件模式，或者是特定后缀的文件夹模式
         Get-ChildItem -Path . -Include $item -Recurse -Directory -ErrorAction SilentlyContinue | ForEach-Object {
            Write-Host "删除文件夹: $($_.FullName)" -ForegroundColor Yellow
            Remove-Item -Path $_.FullName -Recurse -Force -ErrorAction SilentlyContinue
         }
          Get-ChildItem -Path . -Include $item -Recurse -File -ErrorAction SilentlyContinue | ForEach-Object {
            Write-Host "删除文件: $($_.FullName)" -ForegroundColor Yellow
            Remove-Item -Path $_.FullName -Force -ErrorAction SilentlyContinue
         }
    } else {
        # 直接是一个文件夹名字
        if (Test-Path $item) {
             Write-Host "删除文件夹: $item" -ForegroundColor Yellow
             Remove-Item -Path $item -Recurse -Force -ErrorAction SilentlyContinue
        }
    }
}

# 递归删除所有的 __pycache__
Get-ChildItem -Path . -Filter "__pycache__" -Recurse -Directory -ErrorAction SilentlyContinue | ForEach-Object {
    Write-Host "删除缓存: $($_.FullName)" -ForegroundColor DarkGray
    Remove-Item -Path $_.FullName -Recurse -Force -ErrorAction SilentlyContinue
}

Write-Host "`n清理完成！" -ForegroundColor Green
Write-Host "现在您可以安全地将项目文件夹复制到另一台电脑。" -ForegroundColor Cyan
Write-Host "在另一台电脑上，请运行 setup.ps1 来恢复环境。" -ForegroundColor Cyan
