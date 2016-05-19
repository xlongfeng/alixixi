call pyuic5.bat alixixi.ui -o ui_alixixi.py
call pyuic5.bat authorizedialog.ui -o ui_authorizedialog.py
call pyuic5.bat orderlistgetdialog.ui -o ui_orderlistgetdialog.py
call pyuic5.bat orderlistreviewdialog.ui -o ui_orderlistreviewdialog.py
call pyuic5.bat salesreportingdialog.ui -o ui_salesreportingdialog.py
call pyuic5.bat taobaoassistantsettingdialog.ui -o ui_taobaoassistantsettingdialog.py
call pyuic5.bat taobaoorderlogisticsupdatedialog.ui -o ui_taobaoorderlogisticsupdatedialog.py
pylupdate5.exe alixixi.pro
pyrcc5.exe alixixi.qrc -o alixixi_rc.py
pause