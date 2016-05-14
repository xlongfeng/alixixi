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

from datetime import datetime

from sqlalchemy import Column, ForeignKey, \
     Integer, Float, String, DateTime, \
     create_engine
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class AliOrderModel(Base):
    __tablename__ = 'ali_order_model'
    
    id = Column(Integer, primary_key=True)
    createDate =  Column('create_date', DateTime)
    writeDate =  Column('write_date', DateTime)
    
    buyerPhone = Column('buyer_phone', String)
    carriage = Column('carriage', Float)
    gmtCreate = Column('gmt_create', DateTime)
    orderId = Column('order_id', String)
    status = Column('status', String)
    sumProductPayment = Column('sum_product_payment', Float)
    
    sumPayment = Column('sum_payment', Float)
    orderEntries = Column('order_entries', String)
    
    logisticsOrderList = Column('logistics_order_list', String)
    toFullName = Column('to_full_name', String)
    toMobile = Column('to_mobile', String)
    toArea = Column('to_area', String)
    
def aliTimeToDateTime(alitime):
    return datetime.strptime(alitime, '%Y%m%d%H%M%S%f+0800')

def dateTimeToAliTime(datetime):
    return datetime.strptime(time, '%Y%m%d%H%M%S%f+0800')

def ccyUnitConvert(value):
    return float(value / 100.0)

engine = create_engine('sqlite:///storage.sqlite')
Base.metadata.create_all(engine)

session = sessionmaker(engine)()