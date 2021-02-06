import discord, asyncio, json, math
from discord.ext import commands
from PostFinder import PostFinder

#objects
client = commands.Bot(command_prefix = '!')
boton = False
config = None
activechannel = None
checkdelay = 5 #Number of seconds between sending an update

#functions
def channelSet() -> bool:
    if activechannel == None:
        return False
    else:
        return True

def updateConfig():
    with open("config.json", 'w') as f:
        json.dump(config, f, indent=4)

async def sendPrices():
    with PostFinder() as pf:
        while True:
            if channelSet() and boton:
                newposts = pf.get_posts()
                if newposts:
                    matched, unmatched = newposts
                    if matched:
                        print("Relevant offers found:")
                        for post in matched:
                            if len(post["body"]) <= 1500:
                                description = post["body"]
                            else:
                                description = post["body"][:1500]+"... (More)"
                            if len(post["title"]) <= 200:
                                title = post["title"]
                            else:
                                title = post["title"][:200]+"... (More)"
                            print("\tPost ID: "+post['id'])
                            pf.log(f"Found post: Matched (ID: {post['id']})")
                            embed = discord.Embed(title=title, description=description, url=post["link"])
                            await activechannel.send(embed=embed)
                    if unmatched:
                        print("Nonrelevant offers found:")
                        for post in unmatched:
                            print("\tPost ID: "+post['id'])
                            pf.log(f"Found post: Unmatched (ID: {post['id']})")

            await asyncio.sleep(checkdelay)

@client.event
async def on_ready():
    global config, activechannel, boton
    print("Started.")
    boton = True
    await client.change_presence(status=discord.Status.online)
    with open("config.json") as f:
        config = json.load(f)
        try:
            activechannel = client.get_channel(config["active_channel_id"])
            print("Loaded active channel.")
        except:
            print("Error loading active channel.")
            activechannel = None

@client.command()
async def setchannel(ctx):
    global config, activechannel
    if activechannel != ctx.message.channel:
        print("Setting active channel.")
        activechannel = ctx.message.channel
        config["active_channel_id"] = activechannel.id
        updateConfig()
        await ctx.send("Active channel set to #"+activechannel.name+".")
    else:
        await ctx.send("No change was made.")

@client.command()
async def want(ctx, *, details=None):
    global config
    if details == None:
        wantlist = ""
        for wantkey in config["want"]:
            wantlist += wantkey+"\n"
        embed = discord.Embed(title=f'Want list ({str(len(config["want"]))})', description=wantlist)
        await ctx.send(embed=embed)
        return
    args = details.split()
    if config["want"] == ["*"]:
        config["want"] = []
    if args[0].lower() == "add":
        if len(args) < 2:
            await ctx.send("Missing argument! Syntax: want add <keyword(s)>")
            return
        else:
            for wantkey in args[1:]:
                if wantkey == "*":
                    await ctx.send("* cannot be added to the want list. Use want clear to empty the want list.")
                elif wantkey in config["want"]:
                    await ctx.send(f'"{wantkey}" is already in the want list.')
                else:
                    config["want"].append(wantkey)
                    await ctx.send(f'Added "{wantkey}" to the want list.')
    elif args[0].lower() == "remove":
        if len(args) < 2:
            await ctx.send("Missing argument! Syntax: want remove <keyword(s)>")
            return
        else:
            for wantkey in args[1:]:
                if wantkey in config["want"]:
                    config["want"].remove(wantkey)
                    await ctx.send(f'Removed "{wantkey}" from the want list.')
                else:
                    await ctx.send(f'"{wantkey}" is not in the want list.')
    elif args[0].lower() == "clear":
        config["want"] = ["*"]
        await ctx.send("Cleared the want list.")
    else:
        await ctx.send("Invalid argument! Syntax: want <add/remove/clear>")
    if config["want"] == []:
        config["want"] = ["*"]
    updateConfig()

@client.command()
async def have(ctx, *, details=None):
    global config
    if details == None:
        havelist = ""
        for havekey in config["have"]:
            havelist += havekey+"\n"
        embed = discord.Embed(title=f'Have list ({str(len(config["have"]))})', description=havelist)
        await ctx.send(embed=embed)
        return
    args = details.split()
    if config["have"] == ["*"]:
        config["have"] = []
    if args[0].lower() == "add":
        if len(args) < 2:
            await ctx.send("Missing argument! Syntax: have add <keyword(s)>")
            return
        else:
            for havekey in args[1:]:
                if havekey == "*":
                    await ctx.send("* cannot be added to the have list. Use have clear to empty the have list.")
                elif havekey in config["have"]:
                    await ctx.send(f'"{havekey}" is already in the have list.')
                else:
                    config["have"].append(havekey)
                    await ctx.send(f'Added "{havekey}" to the have list.')
    elif args[0].lower() == "remove":
        if len(args) < 2:
            await ctx.send("Missing argument! Syntax: have remove <keyword(s)>")
            return
        else:
            for havekey in args[1:]:
                if havekey in config["have"]:
                    config["have"].remove(havekey)
                    await ctx.send(f'Removed "{havekey}" from the have list.')
                else:
                    await ctx.send(f'"{havekey}" is not in the have list.')
    elif args[0].lower() == "clear":
        config["have"] = ["*"]
        await ctx.send("Cleared the have list.")
    else:
        await ctx.send("Invalid argument! Syntax: have <add/remove/clear>")
    if config["have"] == []:
        config["have"] = ["*"]
    updateConfig()

@client.command()
async def shutdown(ctx):
    print("Exiting...")
    await ctx.send("Shutting down.")
    await client.change_presence(status=discord.Status.offline)
    exit()
    
#run
client.loop.create_task(sendPrices())
client.run("MjM1NTU2MDU2MzU5NTAxODI0.V_2ArA.vCt9X5a397y9fRiEpZnTUNypXSA")
