@echo off
chcp 65001 >nul
title Subir videos a Reels Estudio PWA
echo ==================================================
echo   Actualizando biblioteca de Reels Estudio PWA...
echo ==================================================
echo.

cd /d "C:\Users\User\Desktop\Turbo\Reels Estudio PWA"
python actualizar_biblioteca.py --push

echo.
if %errorlevel% equ 0 (
    echo Listo. En ~1 minuto los cambios estaran en tu celular.
) else (
    echo Ocurrio un error al actualizar o subir a GitHub.
)
echo.
pause
