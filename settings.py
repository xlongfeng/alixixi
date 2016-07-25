#!/usr/bin/env python


#############################################################################
##
## Copyright (C) 2016 xlongfeng<xlongfeng@126.com>.
## All rights reserved.
##
## $QT_BEGIN_LICENSE:BSD$
## You may use this file under the terms of the BSD license as follows:
##
## "Redistribution and use in source and binary forms, with or without
## modification, are permitted provided that the following conditions are
## met:
##   * Redistributions of source code must retain the above copyright
##     notice, this list of conditions and the following disclaimer.
##   * Redistributions in binary form must reproduce the above copyright
##     notice, this list of conditions and the following disclaimer in
##     the documentation and/or other materials provided with the
##     distribution.
##   * Neither the name of Nokia Corporation and its Subsidiary(-ies) nor
##     the names of its contributors may be used to endorse or promote
##     products derived from this software without specific prior written
##     permission.
##
## THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
## "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
## LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
## A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
## OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
## SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
## LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
## DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
## THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
## (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
## OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE."
## $QT_END_LICENSE$
##
#############################################################################


from PyQt5.QtCore import QSettings, pyqtSignal, pyqtProperty
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
    
class Settings(QSettings):
    pInstance = None

    def __init__(self, parent=None):
        super(Settings, self).__init__('config.ini', QSettings.IniFormat, parent)
        
        
    @classmethod
    def instance(cls):
        if cls.pInstance is None:
            cls.pInstance = cls()
        return cls.pInstance
    
    access_token_changed = pyqtSignal(str)
    
    @pyqtProperty(str)
    def access_token(self):
        return self.value('access_token', '')
    
    @access_token.setter
    def access_token(self, value):
        self.setValue('access_token', value)
        self.access_token_changed.emit(value)
        
    aliId_changed = pyqtSignal(str)
    
    @pyqtProperty(str)
    def aliId(self):
        return self.value('aliId', '')
    
    @aliId.setter
    def aliId(self, value):
        self.setValue('aliId', value)
        self.aliId_changed.emit(value)
        
    expires_in_changed = pyqtSignal(str)
    
    @pyqtProperty(str)
    def expires_in(self):
        return self.value('expires_in', '')
    
    @expires_in.setter
    def expires_in(self, value):
        self.setValue('expires_in', value)
        self.expires_in_changed.emit(value)
        
    memberId_changed = pyqtSignal(str)
    
    @pyqtProperty(str)
    def memberId(self):
        return self.value('memberId', '')
    
    @memberId.setter
    def memberId(self, value):
        self.setValue('memberId', value)
        self.memberId_changed.emit(value)
        
    refresh_token_changed = pyqtSignal(str)
    
    @pyqtProperty(str)
    def refresh_token(self):
        return self.value('refresh_token', '')
    
    @refresh_token.setter
    def refresh_token(self, value):
        self.setValue('refresh_token', value)
        self.refresh_token_changed.emit(value)
        
    refresh_token_timeout_changed = pyqtSignal(str)
    
    @pyqtProperty(str)
    def refresh_token_timeout(self):
        return self.value('refresh_token_timeout', '')
    
    @refresh_token_timeout.setter
    def refresh_token_timeout(self, value):
        self.setValue('refresh_token_timeout', value)
        self.refresh_token_timeout_changed.emit(value)
        
    resource_owner_changed = pyqtSignal(str)
    
    @pyqtProperty(str)
    def resource_owner(self):
        return self.value('resource_owner', '')
    
    @resource_owner.setter
    def resource_owner(self, value):
        self.setValue('resource_owner', value)
        self.resource_owner_changed.emit(value)
        
    @pyqtProperty(str)
    def access_token_expires_in(self):
        return self.value('access_token_expires_in', datetime.now() + timedelta(days=-2))
    
    @access_token_expires_in.setter
    def access_token_expires_in(self, value):
        self.setValue('access_token_expires_in', value)
    
    taobao_assistant_install_path_changed = pyqtSignal(str)
    
    @pyqtProperty(str)
    def taobao_assistant_install_path(self):
        return self.value('taobao_assistant_install_path', '')
    
    @taobao_assistant_install_path.setter
    def taobao_assistant_install_path(self, value):
        self.setValue('taobao_assistant_install_path', value)
        self.taobao_assistant_install_path_changed.emit(value)
    
    @pyqtProperty(str)
    def ali_order_last_update_time(self):
        return self.value('ali_order_last_update_time', datetime.today() - relativedelta(months = 1))
    
    @ali_order_last_update_time.setter
    def ali_order_last_update_time(self, value):
        self.setValue('ali_order_last_update_time', value)