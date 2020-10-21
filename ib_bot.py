import requests
import time
from datetime import date, datetime
import threading
import pandas

from ibapi import wrapper
from ibapi import utils
from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
from ibapi.utils import iswrapper
from candle import Candle, CandleGroup

import config

class IBapi( EWrapper, EClient):

    def __init__( self):
        EClient.__init__( self, self)
        self.data = []
        self.lastclose = 0.0
        self.datasize = 0

    def historicalData( self, reqId, bar):
        self.data.insert(0, [bar.date, bar.open, bar.high, bar.low, bar.close, bar.volume])
        self.datasize = len( self.data)
        print( datetime.fromtimestamp( int(self.data[0][0])).strftime( '%b %d %Y %H:%M:%S'))

    def historicalDataUpdate( self, reqId, bar):
        if( bar.close != self.lastclose):
            self.lastclose = bar.close
            if bar.date > self.data[0][0]:
                self.data.insert(0, [bar.date, bar.open, bar.high, bar.low, bar.close])
                self.isdirty = True
            elif bar.date == self.data[0][0]:
                self.data[0] = [bar.date, bar.open, bar.high, bar.low, bar.close, bar.volume]
            ts = datetime.fromtimestamp( int( bar.date))
            print('closing price price:', bar.close, ', date:', ts.strftime( '%b %d %Y %H:%M:%S'))

    def isDirty(self):
        if len( self.data) != self.datasize:
            self.datasize = len( self.data)
            return True
        else:
            return False

app = IBapi()

def run_loop():

    app.run()

def sendtext( text):

    token = config.TELEGRAM_TOKEN
    params = { 'chat_id': '977708575', 'text': text}
    resp = requests.post( 'https://api.telegram.org/bot{}/sendMessage'.format( token), params)
    print( resp)
    resp.raise_for_status()

def main():

    app.connect( '127.0.0.1', 7496, 123)
    
    api_thread =threading.Thread( target=run_loop, daemon=True)
    api_thread.start()

    time.sleep( 1)

    usdcad_contract = Contract()
    usdcad_contract.symbol = 'USD'
    usdcad_contract.secType = 'CASH'
    usdcad_contract.exchange = 'IDEALPRO'
    usdcad_contract.currency = 'CAD'

    requestID = 100
    app.reqHistoricalData( requestID, usdcad_contract, '', '10 D', '1 hour', 'BID', 0, 2, True, [])

    try:
        while True:
            time.sleep( 3)
            if app.isDirty():
                candles = []
                ts = datetime.fromtimestamp( int( app.data[1][0]))
                print('checking for big shadow for candle @', ts.strftime( '%b %d %Y %H:%M:%S'))
                for i in range( 1, config.BS_NUMCANDLES + 1):
                    candles.append( Candle( app.data[i][1], app.data[i][2], app.data[i][3], app.data[i][4]))
                cg = CandleGroup( candles)
                if cg.bigShadow( maxBodyRatio=config.BS_BODYRATIO, wickPercent=config.BS_WICKPERCENTAGE):
                    print('big shadow found for candle @', ts.strftime( '%b %d %Y %H:%M:%S'))
                    sendtext( ( 'found big shadow on USDCAD 1H @', ts.strftime( '%b %d %Y %H:%M:%S')))

    except KeyboardInterrupt:
        pass

    app.disconnect()


if __name__ == '__main__':
    main()
