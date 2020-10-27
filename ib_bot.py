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
        self.data = {}
        for cp in pairs:
            self.data[ cp.pair()] = []
        
    def historicalData( self, reqId, bar):
        for cp in self.pairs:
            if reqId == cp.requestId():
                self.data[ cp.pair()].insert(0, [bar.date, bar.open, bar.high, bar.low, bar.close, bar.volume])

    def historicalDataUpdate( self, reqId, bar):
        for cp in self.pairs:
            if reqId == cp.requestId():
                data = self.data[cp.pair()]
                if int(bar.date) > int(data[0][0]):
                    data.insert(0, [bar.date, bar.open, bar.high, bar.low, bar.close, bar.volume])
                elif int(bar.date) == int(data[0][0]):
                    data[0] = [bar.date, bar.open, bar.high, bar.low, bar.close, bar.volume]

###########################################

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
        app.reqHistoricalData( fc.requestId(), fc.contract(), '', '2 D', '1 hour', 'BID', 0, 2, True, [])

    try:
        lastTS = {}
        for cp in pairs:
            lastTS[cp.pair()] = -1

        while True:
            time.sleep( 10)
            for cp in pairs:
                data = app.data[cp.pair()]
                print('last close price for ', cp.pair(), 'is',data[0][4],'@',datetime.fromtimestamp( int(data[0][0])).strftime( '%b %d %Y %H:%M:%S'))
                if lastTS[cp.pair()] == data[0][0]:
                    continue
                lastTS[cp.pair()] = data[0][0]
                candles = []
                cnt = 1
                while len(candles) != config.BS_NUMCANDLES:
                    candles.append( Candle( data[cnt][1], data[cnt][2], data[cnt][3], data[cnt][4]))
                    if len( candles) == 1:
                        ts = datetime.fromtimestamp( int( data[cnt][0]))
                        print( cp.pair(), ': checking candle patterns @', ts.strftime( '%b %d %Y %H:%M:%S'))
                    cnt += 1
                
                cg = CandleGroup( candles)
                found = False
                msgString = ''
                if candles[0].isHammer():
                    msgString += cp.pair() + ' : hammer found for candle @ ' + ts.strftime( '%b %d %Y %H:%M:%S\n')
                    found = True
                if candles[0].isHangingMan():
                    msgString += cp.pair() + ' : hanging man found for candle @ ' + ts.strftime( '%b %d %Y %H:%M:%S\n')
                    found = True
                if cg.bigShadow( maxBodyRatio=config.BS_BODYRATIO, wickPercent=config.BS_WICKPERCENTAGE):
                    msgString += cp.pair() + ' : big shadow found for candle @ ' + ts.strftime( '%b %d %Y %H:%M:%S\n')
                    found = True

                if found:    
                    print( msgString)
                    sendtext( msgString)

    except KeyboardInterrupt:
        pass

    app.disconnect()


if __name__ == '__main__':
    main()
