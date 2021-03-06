import discord
import bot
import urllib.request
from . import keys
from . import transaction
from ecdsa import VerifyingKey, SigningKey
import campcoin_api
import os
import base64
import simplejson as json
import asyncio

cc = campcoin_api.CompCampsCashApi("http://compcamps-cash.herokuapp.com/")

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

    @bot.argument("amount", float)
    @bot.argument("user+", discord.Member)
    @bot.command()
    async def transfer(ctx, message):
        if ctx.args.amount < 0:
            await message.channel.send("No negatives! :(")
            return
        keyjson = json.load(open("keys.json"))
        if str(ctx.args.user.id) in keyjson and str(message.author.id) in keyjson:
            public_key = VerifyingKey.from_pem(keyjson[str(message.author.id)]["public"])
            sender_publickey = str(base64.b64encode(public_key.to_string()), "utf-8")
            balance = float(cc.getBalance(sender_publickey))
            if ctx.args.amount > float(balance):
                await message.channel.send("You dont have enough coins!")
                return
            await message.channel.send("{} will be taken from your account, do you still want to continue?".format(ctx.args.amount+(ctx.args.amount*0.07)))
            await message.channel.send("y/n")
            def is_correct(m):
                return m.author.id == message.author.id and m.content.strip().lower() in ["y","n"]
            try:
                confirm = await ctx._bot.wait_for("message", check=is_correct, timeout=5)
            except asyncio.TimeoutError:
                await message.channel.send("Transfer Cancelled")
                return
            if not confirm:
                return
            if message.author.id != 266918350645362688:
                private_key = SigningKey.from_pem(keyjson[str(message.author.id)]["private"])
                public_key = VerifyingKey.from_pem(keyjson[str(266918350645362688)]["public"])
                publickey = str(base64.b64encode(public_key.to_string()), "utf-8")
                trx = transaction.Transaction(sender_publickey, publickey, ctx.args.amount + (ctx.args.amount * 0.07), None, private_key)
                cc.postTransaction(trx)
                if ctx.args.user.id != 266918350645362688:
                    public_key = VerifyingKey.from_pem(keyjson[str(266918350645362688)]["public"])
                    sender_publickey = str(base64.b64encode(public_key.to_string()), "utf-8")
                    private_key = SigningKey.from_pem(keyjson[str(266918350645362688)]["private"])
                    public_key = VerifyingKey.from_pem(keyjson[str(ctx.args.user.id)]["public"])
                    publickey = str(base64.b64encode(public_key.to_string()), "utf-8")
                    trx = transaction.Transaction(sender_publickey, publickey, ctx.args.amount, None, private_key)
                    cc.postTransaction(trx)

            else:
                private_key = SigningKey.from_pem(keyjson[str(266918350645362688)]["private"])
                public_key = VerifyingKey.from_pem(keyjson[str(ctx.args.user.id)]["public"])
                publickey = str(base64.b64encode(public_key.to_string()), "utf-8")
                trx = transaction.Transaction(sender_publickey, publickey, ctx.args.amount, None, private_key)
                cc.postTransaction(trx)

            await message.channel.send("Transaction Complete!")
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
    @bot.argument("public", str)
    @bot.command()
    async def whois(ctx, message):
        keyjson = json.load(open("keys.json"))
        for key in keyjson:
            public_key = VerifyingKey.from_pem(keyjson[key]["public"])
            out = str(base64.b64encode(public_key.to_string()), "utf-8")
            if ctx.args.public in out:
                user = message.channel.guild.get_member(int(key))
                await message.channel.send(user.display_name)

    @bot.command()
    async def value(ctx, message):
        import urllib.request, json
        contents = urllib.request.urlopen("https://cash.compcamps.com/api/stats/blocksPerHour").read()
        data = json.loads(contents)
        total = 0
        for day in data:
            for hour in data[day]:
                total += int(data[day][hour])
                cad = 10 * round(1/(0.025*total) * 1000) / 1000 
        await message.channel.send(f"${cad} CAD")

    @bot.command()
    async def blocks(ctx, message):
        import urllib.request, json
        contents = urllib.request.urlopen("https://cash.compcamps.com/api/stats/blocksPerHour").read()
        data = json.loads(contents)
        total = 0
        for day in data:
            for hour in data[day]:
                total += int(data[day][hour])
        await message.channel.send(f"A total of {total} blocks have been mined.")

    @bot.command()
    async def help(ctx, message):
        await message.channel.send("You can type:")
        await message.channel.send("`!transfer _amount_ @username` to send coins from your account to someone else's. With amount being the amount to send and @username to be the person your sending to. There will be a transfer fee of 7% applied.\n")
        await message.channel.send("`!balance @username` to check your or someone else's current balance. With @username being the person's balance that your checking.\n")
        await message.channel.send("`!value` to see the current value of one CampCoin\n")
        await message.channel.send("`!blocks` to see how many blocks have been mined\n")
        await message.channel.send("Make sure to DM the bot your .pem files. You can DM the bot by right clicking on it in the users list and pressing message. Both files can be added by drag n' drop in the DM chat.\n")
