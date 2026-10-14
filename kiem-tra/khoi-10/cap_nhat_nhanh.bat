@echo off
chcp 65001 >nul
title Cập Nhật Danh Sách Đề Thi Tự Động
echo ============================================================
echo   HỆ THỐNG CẬP NHẬT ĐỀ THI TỰ ĐỘNG - THPT HÙNG VƯƠNG
echo ============================================================
echo Đang quét các file đề thi trong thư mục...
echo.

python "%~dp0scan_exams.py"

echo.
echo ============================================================
echo Cập nhật hoàn tất! Bấm phím bất kỳ để đóng cửa sổ.
pause >nul
