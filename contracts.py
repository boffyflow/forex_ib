from ibapi.contract import Contract

class ForexContract:

    def __init__(self, s='USDCAD'):
        self.symbol = s
        id = 0
        for c in s[0:4]:
            id += ord( c)
        self.requestid = id

    def contract(self):
        contract = Contract()
        contract.symbol = self.symbol[0:3]
        contract.secType = 'CASH'
        contract.currency = self.symbol[-3:]
        contract.exchange = 'IDEALPRO'
        return contract
    
    def pair(self):
        return self.symbol

    def requestId(self):
        return self.requestid

