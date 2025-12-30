# VS Code Extension Installation Script
# Run this script in PowerShell on the target machine to install the same extensions.

Write-Host "Installing VS Code Extensions..." -ForegroundColor Cyan

$extensions = @(
    "anthropic.claude-code",
    "batisteo.vscode-django",
    "bracketpaircolordlw.bracket-pair-color-dlw",
    "cweijan.dbclient-jdbc",
    "cweijan.vscode-redis-client",
    "davidanson.vscode-markdownlint",
    "donjayamanne.githistory",
    "donjayamanne.python-environment-manager",
    "donjayamanne.python-extension-pack",
    "eamodio.gitlens",
    "esbenp.prettier-vscode",
    "github.copilot",
    "github.copilot-chat",
    "grapecity.gc-excelviewer",
    "graphite.gti-vscode",
    "kevinrose.vsc-python-indent",
    "mechatroner.rainbow-csv",
    "mhutchie.git-graph",
    "micnil.vscode-checkpoints",
    "mongodb.mongodb-vscode",
    "ms-azure-load-testing.microsoft-testing",
    "ms-azuretools.azure-dev",
    "ms-azuretools.vscode-azure-github-copilot",
    "ms-azuretools.vscode-azure-mcp-server",
    "ms-azuretools.vscode-azureappservice",
    "ms-azuretools.vscode-azurecontainerapps",
    "ms-azuretools.vscode-azurefunctions",
    "ms-azuretools.vscode-azureresourcegroups",
    "ms-azuretools.vscode-azurestaticwebapps",
    "ms-azuretools.vscode-azurestorage",
    "ms-azuretools.vscode-azurevirtualmachines",
    "ms-azuretools.vscode-containers",
    "ms-azuretools.vscode-cosmosdb",
    "ms-azuretools.vscode-docker",
    "ms-ceintl.vscode-language-pack-zh-hans",
    "ms-kubernetes-tools.vscode-kubernetes-tools",
    "ms-python.debugpy",
    "ms-python.pylint",
    "ms-python.python",
    "ms-python.vscode-pylance",
    "ms-python.vscode-python-envs",
    "ms-vscode.cmake-tools",
    "ms-vscode.cpptools",
    "ms-vscode.cpptools-extension-pack",
    "ms-vscode.cpptools-themes",
    "ms-vscode.makefile-tools",
    "ms-vscode.vscode-node-azure-pack",
    "njpwerner.autodocstring",
    "pkief.material-icon-theme",
    "redhat.vscode-yaml",
    "sdras.night-owl",
    "shd101wyy.markdown-preview-enhanced",
    "streetsidesoftware.code-spell-checker",
    "teamsdevapp.vscode-ai-foundry",
    "twxs.cmake",
    "wholroyd.jinja",
    "yzhang.markdown-all-in-one"
)

foreach ($ext in $extensions) {
    Write-Host "Installing $ext..."
    code --install-extension $ext --force
}

Write-Host "All extensions installed!" -ForegroundColor Green
