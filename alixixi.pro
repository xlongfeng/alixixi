QT += core gui widgets
TARGET = alixixi
TEMPLATE = app

SOURCES += \
    alixixi.pyw \
    cnalibabaopen.py \
    settings.py \
    orderlist.py

FORMS += \
    alixixi.ui \
    authorizedialog.ui \
    orderlistgetdialog.ui \
    orderlistreviewdialog.ui
	
TRANSLATIONS += alixixi_zh_CN.ts