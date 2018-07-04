from . import keys
signData = keys.signData
verifyData = keys.verifyData
import base64

class Transaction:
    def __init__(self, sender, reciever, amount, signature=None, private = None):
        self.sender = sender
        self.reciever = reciever
        self.amount = amount
        self.private = private
        if signature==None:
            self.signature = self.signTransaction()
        else:
            self.signature = signature

    def signTransaction(self):
        signature = signData(str(self.sender) + str(self.reciever) + str(self.amount), self.private)
        return base64.b64encode(signature)

    def verifyTransaction(self, public_key_string):
        return verifyData(str(self.sender) + str(self.reciever) + str(self.amount),
                    public_key_string,
                    base64.b64decode(self.signature))

    def _asdict(self):
        print(self.signature)
        data = self.__dict__.copy()
        del data['private']
        return data
