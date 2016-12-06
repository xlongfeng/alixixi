QT += core gui widgets
TARGET = alixixi
TEMPLATE = app

SOURCES += \
    alixixi.pyw \
    cnalibabaopen.py \
    orderlist.py \
    settings.py \
    taobaoassistant.py
    

FORMS += \
    alixixi.ui \
    authorizedialog.ui \
    orderlistgetdialog.ui \
    orderlistreviewdialog.ui \
    proxysettingdialog.ui \
    salesreportingdialog.ui \
    taobaoassistantsettingdialog.ui \
    taobaoorderdetaildialog.ui \
    taobaoorderlogisticsupdatedialog.ui
    
	
TRANSLATIONS += alixixi_zh_CN.ts

RESOURCES += \
    alixixi.qrc
