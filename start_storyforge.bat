@echo off
chcp 65001 >nul
title StoryForge Launcher

cd /d C:\Users\25109\Desktop\StoryForge

echo [1/2] Starting backend (FastAPI)...
start "StoryForge-Backend" cmd /k "title StoryForge-Backend && echo [StoryForge Backend] && echo. && python -m storyforge"

timeout /t 3 /nobreak >nul

echo [2/2] Starting frontend (Vue 3)...
start "StoryForge-Frontend" cmd /k "cd /d C:\Users\25109\Desktop\StoryForge\storyforge\frontend && title StoryForge-Frontend && echo [StoryForge Frontend] && echo. && npm run dev"

timeout /t 3 /nobreak >nul

start http://localhost:5173

echo.
echo ============================================
echo   Both started!
echo   Frontend: http://localhost:5173
echo   Backend:  http://localhost:8000
echo ============================================
echo.
echo   Close the backend window to stop the server.
echo.
pause
