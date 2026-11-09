@echo off
chcp 65001 >nul
title Hệ Thống So Sánh Độ Điển Trai Nam Giới - FastAPI
echo =========================================================================
echo   HỆ THỐNG SO SÁNH ĐỘ ĐIỂN TRAI DỰA TRÊN TIÊU CHÍ THẨM MỸ THẾ GIỚI
echo =========================================================================
echo.
echo Đang khởi động FastAPI Server...
echo Mở trình duyệt tại địa chỉ: http://127.0.0.1:8000
echo.
py -m uvicorn handsome_app.main:app --host 127.0.0.1 --port 8000 --reload
pause
