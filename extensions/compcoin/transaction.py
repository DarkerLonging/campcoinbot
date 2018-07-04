from . import keys
signData = keys.signData
verifyData = keys.verifyData
import base64

class Transaction:
    def __init__(self, sender, reciever, amount, signature=None):
        self.sender = sender
        self.reciever = reciever
        self.amount = amount
        if signature==None:
            self.signature = self.signTransaction()
        else:
            self.signature = signature

    def signTransaction(self):
        sender = str(base64.b64encode(self.sender.to_string()), "utf-8")
        signature = signData(sender + str(self.reciever) + str(self.amount), self.sender)
        return base64.b64encode(signature)

    def verifyTransaction(self, public_key_string):
        sender = str(base64.b64encode(self.sender.to_string()), "utf-8")
        return verifyData(sender + str(self.reciever) + str(self.amount),
                    public_key_string,
                    base64.b64decode(self.signature))

    def _asdict(self):
        data = self.__dict__.copy()
        data['sender'] = str(base64.b64encode(self.sender.to_string()), "utf-8")
        data['signature'] = data['signature'].decode("utf-8")
        return data
