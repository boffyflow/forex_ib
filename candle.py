class Candle:

    CANDLELONG = 'Long'
    CANDLESHORT = 'Short'
    CANDLENEUTRAL = 'Neutral'

    def __init__ (self, o = 0.0, h = 0.0, l = 0.0, c = 0.0):
        self.o = o
        self.h = h
        self.l = l
        self.c = c

    def body( self):
        return abs( self.c - self.o)

    def range( self):
        return abs( self.h - self.l)
    
    def direction( self):
        if self.c == self.o:
            return self.CANDLENEUTRAL
        if self.c > self.o:
            return self.CANDLELONG
        else:
            return self.CANDLESHORT

    def open( self):
        return self.o
    
    def high( self):
        return self.h

    def low( self):
        return self.l

    def close( self):
        return self.c

    def wickPercentage( self, direction):
        w = 0.0
        if direction == self.CANDLELONG:
            if self.direction() == self.CANDLELONG:
                w = self.h - self.c
            elif self.direction() ==self. CANDLESHORT:
                w = self.h - self.o
        if direction == self.CANDLESHORT:
            if self.direction() == self.CANDLELONG:
                w = self.o - self.l
            elif self.direction() == self.CANDLESHORT:
                w = self.c - self.l
        
        return abs(w) / ( self.body() + 0.00000001)

class CandleGroup:

    def __init__ (self, candles):  # must current candle at index 0
        self.candles = candles

    def bigShadow( self, maxBodyRatio = 3.0, wickPercent = 0.05):
        
        # 1. condition: body of current candle is larger than all the remaining candles
        b = 0.0
        pos = -1
        aveBody = 0.0
        for i in range( 0, len( self.candles)):
            c = self.candles[i]
            aveBody += c.body()
            if c.body() > b:
                b = c.body()
                pos = i
        aveBody = aveBody / len( self.candles)

        if pos != 0:
            print( '#1 largest candle (out of', len(self.candles ), ') : FALSE')
            return False

        print( '#1 largest candle (out of', len(self.candles ), ') : TRUE')

        currCandle = self.candles[0]
        
        # 2. condition: make sure the current candle is not too large (avoid huge stops)
        if currCandle.body() > ( maxBodyRatio * aveBody):
            print( '#2. largest candle not too large (factor:', maxBodyRatio, ') : FALSE')
            return False
        print( '#2. largest candle not too large (factor:', maxBodyRatio, ') : TRUE')
        
        # 3. condition: ensure that the wick of the current candle is not too long
        if currCandle.wickPercentage( currCandle.direction()) > wickPercent:
            print( '#3. largest candle has short wick (factor:', wickPercent, ') : FALSE')
            return False
        print( '#3. largest candle has short wick (factor:', wickPercent, ') : TRUE')

        # 4. condition: is the current candle a reversal candle?
        if (currCandle.direction() == self.candles[1].direction()) or ( self.candles[1].direction == Candle.CANDLENEUTRAL):
            print( '#4. largest candle is a reversal candle : FALSE')
            return False
        print( '#4. largest candle is a reversal candle : TRUE')

        # 5. condition: does the current candle engulf the previous one?
        state = True
        if currCandle.direction() == Candle.CANDLELONG:
            if currCandle.open() > self.candles[1].close():
                state = False
            if currCandle.close() < self.candles[1].open():
                state = False
        if currCandle.direction() == Candle.CANDLESHORT:
            if currCandle.open() < self.candles[1].close():
                state = False
            if currCandle.close() > self.candles[1].open():
                state = False

        if state:
            print( '#5. largest candle is engulfing : TRUE')
        else:    
            print( '#5. largest candle is engulfing : FALSE')

        return state
        