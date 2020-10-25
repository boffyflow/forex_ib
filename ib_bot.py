import requests
import time
from datetime import date, datetime
import threading
import pandas

from ibapi import wrapper
from ibapi import utils
from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.utils import iswrapper
from candle import Candle, CandleGroup

import config
from contracts import ForexContract

class IBapi( EWrapper, EClient):

    def __init__( self, pairs):
        EClient.__init__( self, self)
        self.pairs = pairs
        self.data = []
        self.lastclose = 0.0
        self.datasize = 0
        
    def historicalData( self, reqId, bar):
        for cp in self.pairs:
            if reqId == cp.requestId():
                self.data.insert(0, [cp.string(), bar.date, bar.open, bar.high, bar.low, bar.close, bar.volume])
                self.datasize[cp.requestId()] = len( self.data[cp.requestId()])
                print( cp.string(), ':' , datetime.fromtimestamp( int(self.data[cp.requestId()][0][0])).strftime( '%b %d %Y %H:%M:%S'))

    def historicalDataUpdate( self, reqId, bar):
        for cp in self.pairs:
            if( bar.close != self.lastclose[cp.requestId()]):
                self.lastclose[cp.requestId()] = bar.close
                if bar.date > self.data[cp.requestId()][0][0]:
                    self.data[cp.requestId()].insert(0, [bar.date, bar.open, bar.high, bar.low, bar.close])
                    self.isdirty[cp.requestId()] = True
                elif bar.date == self.data[cp.requestId()][0][0]:
                    self.data[cp.requestId()][0] = [bar.date, bar.open, bar.high, bar.low, bar.close, bar.volume]
                ts = datetime.fromtimestamp( int( bar.date))
                print(cp.string(), ': closing rice:', bar.close, ', date:', ts.strftime( '%b %d %Y %H:%M:%S'))

    def isDirty(self, fc):
        if len( self.data[fc.requestId()]) != self.datasize[fc.requestId()]:
            self.datasize[fc.requestId()] = len( self.data[fc.requestId()])
            return True
        else:
            return False


pairs = []
for cp in config.CURRENCYPAIRS:
    pairs.append( ForexContract( cp))
app = IBapi( pairs)

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
    
    api_thread = threading.Thread( target=run_loop, daemon=True)
    api_thread.start()

    time.sleep( 1)

    for fc in pairs:
        app.reqHistoricalData( fc.requestid(), fc.contract(), '', '10 D', '1 hour', 'BID', 0, 2, True, [])

    try:
        while True:
            time.sleep( 1)
            for cp in pairs:
                if app.isDirty(cp):
                    candles = []
                    ts = datetime.fromtimestamp( int( app.data[cp.requestId()][1][0]))
                    print( cp.string(), ': checking for big shadow for candle @', ts.strftime( '%b %d %Y %H:%M:%S'))
                    for i in range( 1, config.BS_NUMCANDLES + 1):
                        candles.append( Candle( app.data[cp.requestId()][i][1], app.data[cp.requestId()][i][2], app.data[cp.requestId()][i][3], app.data[cp.requestId()][i][4]))
                    cg = CandleGroup( candles)
                    if cg.bigShadow( maxBodyRatio=config.BS_BODYRATIO, wickPercent=config.BS_WICKPERCENTAGE):
                        print( cp.string(), ': big shadow found for candle @', ts.strftime( '%b %d %Y %H:%M:%S'))
                        sendtext( ( cp.string(), ': found big shadow on USDCAD 1H @', ts.strftime( '%b %d %Y %H:%M:%S')))

    except KeyboardInterrupt:
        pass

    app.disconnect()


if __name__ == '__main__':
    main()
