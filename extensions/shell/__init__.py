import bot
import subprocess
import asyncio
import os

class Shell(bot.Extension):
    """Provides TeamSpeak commands"""

    async def shell(ctx, channel):
        import fcntl
        def setNonBlocking(fd):
            flags = fcntl.fcntl(fd, fcntl.F_GETFL)
            flags = flags | os.O_NONBLOCK
            fcntl.fcntl(fd, fcntl.F_SETFL, flags)
        ctx.extension.shells[channel.id] = subprocess.Popen("python3 shell.py", shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, stdin=subprocess.PIPE, bufsize=1)
        setNonBlocking(ctx.extension.shells[channel.id].stdout)
        while True:
            await asyncio.sleep(0.2)
            output = ctx.extension.shells[channel.id].stdout.readline()
            if output == "" and ctx.extension.shells[channel.id].poll() is not None:
                break
            if output:
                await channel.send(output.decode("UTF-8"))
        ctx.extension.shells[channel.id].poll()
        ctx.extension.shells[channel.id] = None

    @bot.event("on_message")
    async def execute(ctx, message):
        """Deletes any messages containing the TeamSpeak Server"""
        if message.content.startswith(">"):
            if not hasattr(ctx.extension, "shells"):
                ctx.extension.shells = {}
            if message.channel.id not in ctx.extension.shells or ctx.extension.shells[message.channel.id] == None:
                ctx.loop.create_task(ctx.extension.shell(ctx, message.channel))
            await asyncio.sleep(0.5)
            code = message.content[1:].strip().replace("```py","").strip("```")+"||END||\n"
            print(code)
            ctx.extension.shells[message.channel.id].stdin.write(code.encode("UTF-8"))
            ctx.extension.shells[message.channel.id].stdin.flush()
