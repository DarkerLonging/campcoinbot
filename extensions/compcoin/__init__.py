import discord
import bot
import urllib.request
from . import keys
from . import transaction
from ecdsa import VerifyingKey, SigningKey
import campcoin_api
import os
import json
import base64

cc = campcoin_api.CampCoin("https://campcoin.herokuapp.com")

class CompCoin(bot.Extension):
    """Code for CompCoin Bot"""

    @bot.event("on_message")
    async def getkeys(ctx, message):
        if os.path.exists("public.pem"):
            os.remove("public.pem")
        if os.path.exists("lastupload.txt"):
            with open("lastupload.txt") as fobj:
                id = int(fobj.read())
                if id != message.author.id:
                    if os.path.exists("private.pem"):
                        os.remove("private.pem")
        for attachment in message.attachments:
            filename = attachment.url.split("/")[-1]
            opener = urllib.request.build_opener()
            opener.addheaders = [('User-agent', 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11')]
            urllib.request.install_opener(opener)
            urllib.request.urlretrieve(attachment.url, filename)
            if filename == "private.pem":
                with open("lastupload.txt", "w") as fobj:
                    fobj.write(str(message.author.id))
            elif filename == "public.pem":
                if not os.path.exists("private.pem"):
                    await message.channel.send("Upload the private key first")
        if os.path.exists("public.pem") and os.path.exists("private.pem"):
            await message.channel.send("Thank You :thumbsup:")
            with open("private.pem") as fobj:
                privatekey = fobj.read()
            with open("public.pem") as fobj:
                publickey = fobj.read()
            await message.channel.send(publickey)
            if os.path.exists("keys.json"):
                keyjson = json.load(open("keys.json"))
            else:
                keyjson = {}
            keyjson[str(message.author.id)] = {
                "public": publickey,
                "private": privatekey
            }
            with open("keys.json", mode='w', encoding='utf-8') as feedsjson:
                json.dump(keyjson, feedsjson)

    @bot.argument("amount", int)
    @bot.argument("user+", discord.Member)
    @bot.command()
    async def transfer(ctx, message):
        keyjson = json.load(open("keys.json"))
        if str(ctx.args.user.id) in keyjson and str(message.author.id) in keyjson:
            public_key = VerifyingKey.from_pem(keyjson[str(message.author.id)]["public"])
            publickey = str(base64.b64encode(public_key.to_string()), "utf-8")
            balance = int(cc.getBalance(publickey))
            if ctx.args.amount > balance:
                await message.channel.send("You dont have enough coins!")
                return
            private_key = SigningKey.from_pem(keyjson[str(message.author.id)]["private"])
            public_key = VerifyingKey.from_pem(keyjson[str(ctx.args.user.id)]["public"])
            publickey = str(base64.b64encode(public_key.to_string()), "utf-8")
            trx = transaction.Transaction(private_key, publickey, ctx.args.amount)
            #print(type(trx._asdict()))
            print(json.dumps(trx._asdict()))
            cc.postTransaction(trx)
        else:
            await message.channel.send("Users are not linked")

    @bot.argument("user+", discord.Member)
    @bot.command()
    async def balance(ctx, message):
        keyjson = json.load(open("keys.json"))
        if str(ctx.args.user.id) in keyjson:
            public_key = VerifyingKey.from_pem(keyjson[str(ctx.args.user.id)]["public"])
            publickey = str(base64.b64encode(public_key.to_string()), "utf-8")
            balance = cc.getBalance(publickey)
            await message.channel.send("This user has {} CampCoins!".format(str(balance)))
        else:
            await message.channel.send("The person hasn't linked their pem files! DM the CampCoin bot your files by drag and dropping the files onto the DM chat, click Upload twice and you should get a response.")
