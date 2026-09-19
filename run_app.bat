@echo off
chcp 65001 > nul
echo ========================================================
echo   PDF to Excel Custom Converter
echo   ระบบเเปลงรายงาน PDF เป็น Excel ตามหัวข้อที่ต้องการ
echo ========================================================
echo.
echo กำลังเริ่มต้น Web Application...
"C:\Python312\python.exe" -m streamlit run app.py
pause
