@echo off
chcp 65001 >nul
echo ===================================================
echo  正在推送至 GitHub: wualex0117/0921-test
echo ===================================================
set "PATH=C:\Users\fewo3\AppData\Local\Programs\MinGit\cmd;C:\Users\fewo3\AppData\Local\Programs\MinGit\ucrt64\bin;%PATH%"

echo 檢查目前 Git 狀態...
git status

echo.
echo 正在推送到遠端倉庫 origin/main ...
echo (如果第一次登入，系統可能會開啟瀏覽器進行 GitHub 授權)
echo.

git push -u origin main

if %ERRORLEVEL% equ 0 (
    echo.
    echo ===================================================
    echo  [成功] 程式碼已順利推送至 GitHub！
    echo  https://github.com/wualex0117/0921-test
    echo ===================================================
) else (
    echo.
    echo ===================================================
    echo  [失敗] 推送未完成，請確認 GitHub 登入權限。
    echo ===================================================
)

pause
