pyinstaller.exe -n �������� --hidden-import fdb -w -i images/alixixi.ico alixixi.pyw
copy config.ini dist\��������
copy alixixi_zh_CN.qm dist\��������
copy storage.sqlite dist\��������
md dist\��������\templates
xcopy templates dist\��������\templates /S
pause