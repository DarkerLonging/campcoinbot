import datetime
import discord

class ArgumentException(Exception):
    def __init__(self, text, data):
        super().__init__(text)
        self.data = data

class Arguments:
    def __init__(self, ctx, raw, args):
        self._ctx = ctx
        self._raw = raw
        self._args = args
        self._values = []

        self._usage = " ".join([x[0] for x in args])

        self._current = 0

        for arg in self._args:
            self._getNext(arg)

        self._ctx = None
        del self._ctx

    def _getNext(self, arg):
        if len(self._raw) != 0 and self._current < len(self._raw):
            if self._raw[self._current] == "-h":
                raise ArgumentException("Display Help", [self])
            if self._raw[self._current].startswith("-"):
                setattr(self, self._raw[self._current][2:], self._raw[self._current + 1])
                self._current += 2
        if arg[0].startswith("[") and arg[0].endswith("]") and not hasattr(self, arg[0][1:-1]):
            if self._current < len(self._raw):
                if arg[0][-2] == "+":
                    value = self._parse(arg, " ".join(self._raw[self._current:]))
                    setattr(self, arg[0][1:-2], value)
                    self._current = len(self._raw)
                else:
                    value = self._parse(arg, self._raw[self._current])
                    setattr(self, arg[0][1:-1], value)
                    self._current += 1
            else:
                setattr(self, arg[0][1:-1], arg[2])
                if arg[0][-2] == "+":
                    setattr(self, arg[0][1:-2], arg[2])
                else:
                    setattr(self, arg[0][1:-1], arg[2])
        elif arg[0].startswith("(") and arg[0].endswith(")"):
            if not hasattr(self, arg[0][1:-1]):
                setattr(self, arg[0][1:-1], None)
        else:
            if self._current == len(self._raw):
                raise ArgumentException("Not Enough Args", [self, arg[0]])
            else:
                if arg[0][-1] == "+":
                    value = self._parse(arg, " ".join(self._raw[self._current:]))
                    setattr(self, arg[0][:-1], value)
                    self._current = len(self._raw)
                else:
                    value = self._parse(arg, self._raw[self._current])
                    setattr(self, arg[0], value)
                    self._current += 1

    def _parse(self, arg, value):
        argtype = arg[1]
        arg = arg[0]
        #if argtype == Command:
        #    for ext in self._ctx._bot.extensions:
        #        for c in ext.commands:
        #            if c.name == value:
        #                c.extension = ext
        #                return c
        #    raise ArgumentException("Invalid Command", [self, arg, value])
        if argtype == discord.Member:
            if value.startswith("<@"):
                value = value[2:-1]
                if value.startswith("!"):
                    value = value[1:]
            try:
                value = int(value)
                member = self._ctx.message.channel.guild.get_member(value)
            except:
                value = value.lower()
                member = discord.utils.find(lambda m: m.name.lower() == value or m.display_name.lower() == value, self._ctx.message.channel.guild.members)
                if member == None:
                    raise ArgumentException("Member Not Found", [self, arg, value])
            if member == None:
                raise ArgumentException("Member Not Found", [self, arg, value])
            return member
        elif argtype == discord.Role:
            role = discord.utils.find(lambda m: m.name.lower() == value.lower() or str(m.id) == value, self._ctx.message.channel.guild.roles)
            if role == None:
                raise ArgumentException("Role Not Found", [self, arg, value])
            return role
        elif argtype == datetime.tzinfo:
            import pytz
            if value in pytz.all_timezones:
                return pytz.timezone(value)
            else:
                for tz in pytz.all_timezones:
                    if value.replace(" ","_").lower() in tz.lower():
                        return pytz.timezone(tz)
            raise ArgumentException("Timezone Not Found", [self, arg, value])
        elif argtype == int:
            try:
                value = int(value)
            except:
                try:
                    value = self._txt2int(value)
                except:
                    raise ArgumentException("TypeError", [self, arg, value, "number"])
        return value

    def _txt2int(self, textnum, numwords={}):
        if not numwords:
          units = [
            "zero", "one", "two", "three", "four", "five", "six", "seven", "eight",
            "nine", "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen",
            "sixteen", "seventeen", "eighteen", "nineteen",
          ]
          tens = ["", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety"]
          scales = ["hundred", "thousand", "million", "billion", "trillion"]
          numwords["and"] = (1, 0)
          for idx, word in enumerate(units):    numwords[word] = (1, idx)
          for idx, word in enumerate(tens):     numwords[word] = (1, idx * 10)
          for idx, word in enumerate(scales):   numwords[word] = (10 ** (idx * 3 or 2), 0)
        current = result = 0
        for word in textnum.split():
            if word not in numwords:
                raise Exception("Illegal word: " + word)
            scale, increment = numwords[word]
            current = current * scale + increment
            if scale > 100:
                result += current
                current = 0
        return result + current
