@echo off
setlocal

set "ROOT=%~dp0"
set "BACKEND_MARKER=%ROOT%.storyforge-backend.pid"
set "FRONTEND_MARKER=%ROOT%.storyforge-frontend.pid"

powershell -NoProfile -ExecutionPolicy Bypass -Command "Add-Type -AssemblyName PresentationFramework; $answer=[System.Windows.MessageBox]::Show('确定要关闭 StoryForge 后端和前端服务吗？这会停止端口 8000、5173、4173，并结束由一键启动创建的命令行窗口。','StoryForge 一键关闭','YesNo','Question'); if ($answer -ne 'Yes') { exit 2 }" >nul 2>nul
if errorlevel 2 exit /b 0

powershell -NoProfile -ExecutionPolicy Bypass -Command "function Stop-Tree([int]$ProcessId) { if ($ProcessId -eq $PID) { return }; $children = Get-CimInstance Win32_Process -Filter "ParentProcessId=$ProcessId" -ErrorAction SilentlyContinue; foreach ($child in $children) { Stop-Tree ([int]$child.ProcessId) }; Stop-Process -Id $ProcessId -Force -ErrorAction SilentlyContinue }; function Stop-Marker($path) { if (Test-Path $path) { $raw = Get-Content $path -ErrorAction SilentlyContinue | Select-Object -First 1; [int]$storedPid = 0; if ([int]::TryParse($raw, [ref]$storedPid)) { Stop-Tree $storedPid }; Remove-Item $path -Force -ErrorAction SilentlyContinue } }; function Stop-Port($port) { $connections = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue; foreach ($connection in $connections) { if ($connection.OwningProcess) { Stop-Tree ([int]$connection.OwningProcess) } } }; function Stop-StoryForgeWindow($title) { Get-Process -ErrorAction SilentlyContinue | Where-Object { $_.Id -ne $PID -and $_.MainWindowTitle -like $title } | ForEach-Object { Stop-Tree ([int]$_.Id) } }; Stop-Marker '%BACKEND_MARKER%'; Stop-Marker '%FRONTEND_MARKER%'; Stop-Port 8000; Stop-Port 5173; Stop-Port 4173; Get-CimInstance Win32_Process | Where-Object { ($_.ProcessId -ne $PID) -and (($_.CommandLine -like '*python -m storyforge*') -or ($_.CommandLine -like '*npm run dev*') -or ($_.CommandLine -like '*vite*') -or ($_.CommandLine -like '*start_storyforge.bat*') -or ($_.CommandLine -like '*StoryForge-Backend*') -or ($_.CommandLine -like '*StoryForge-Frontend*') -or ($_.CommandLine -like '*StoryForge Launcher*')) } | ForEach-Object { Stop-Tree ([int]$_.ProcessId) }; Stop-StoryForgeWindow 'StoryForge-Backend*'; Stop-StoryForgeWindow 'StoryForge-Frontend*'; Stop-StoryForgeWindow 'StoryForge Launcher*'" >nul 2>nul

powershell -NoProfile -ExecutionPolicy Bypass -Command "Add-Type -AssemblyName PresentationFramework; [System.Windows.MessageBox]::Show('StoryForge 已关闭。已停止后端、前端以及相关子进程。','StoryForge 关闭完成','OK','Information')" >nul 2>nul

endlocal
