import discord
from discord.ext import commands

class Help(commands.Cog):

   def __init__ (self, client):
      self.client = client
      
   @commands.command()
   async def help (self, ctx, command=None, dmcommand=None):
      if command is None:
         embed = discord.Embed(title="Pazaak Commands", colour=discord.Colour(0x4e7e8a), description="Type **p.help <page>** to get command information in each section.")
         embed.add_field(name="1. Playing pazaak", value="These are commands used in pazaak play.", inline=False)
         embed.add_field(name="2. Side deck selection", value="These are commands used to select the side deck at the beginning of the game.", inline=False)
         embed.add_field(name="3. Server settings", value="These are commands used to set text channels used for pazaak.", inline=False)
         await ctx.send(embed=embed)
      elif command.isdigit():
         if command == "1":
            embed = discord.Embed(title="How to play pazaak", colour=discord.Colour(0x4e7e8a), description="Pazaak is a card game in Star Wars that is similar to BlackJack.\nPlayers will be dealt a card each turn and have the option to end, stand, or play a card.\nPlayers may not pass 20 in total at the end of their turn.\nType **p.help <command>** for more information about each one.")
            embed.add_field(name="**p.duel <member> [wager]**", value="Use this to challenge another member to a game of pazaak.", inline=False)
            embed.add_field(name="**p.accept**", value="Use this to accept the pazaak challenge.", inline=False)
            embed.add_field(name="**p.decline**", value="Use this to delcine the pazaak challenge.", inline=False)
            embed.add_field(name="**p.heads**", value="Use this to choose heads for the coin flip to start the game.", inline=False)
            embed.add_field(name="**p.tails**", value="Use this to choose tails for the coin flip to start the game.", inline=False)
            embed.add_field(name="**p.end**", value="Use this to end your turn.", inline=False)
            embed.add_field(name="**p.stand**", value="Use this to stand on your hand.", inline=False)
            embed.add_field(name="**p.play <card> [sign]**", value="Use this to play one of your side deck cards.", inline=False)
            embed.set_footer(text="Arguments with '<>' are required; arguments with '[]' are optional.")
            await ctx.send(embed=embed)
         elif command == "2":
            embed = discord.Embed(title="Side deck selection", colour=discord.Colour(0x4e7e8a), description="The side deck is used to get your hand to 20 or as close as possible.\nYou first select 10 cards, and, out of those 10, 4 are randomly selected to be playable.\n\nThe following are commands to use in your DM with the bot.\nType **p.help <command>** for help with these particular commands.")
            embed.add_field(name="p.add <card> [amount]", value="Use this to add one or more of a specific card to your side deck.", inline=False)
            embed.add_field(name="p.remove <card> [amount]", value="Use this to remove one or more of a specific card from your side deck.", inline=False)
            embed.add_field(name="p.last", value="Use this to bring up the last side deck you used.", inline=False)
            embed.add_field(name="p.done", value="Use this to finish your side deck selection and receive your playable cards.", inline=False)
            embed.set_footer(text="Arguments with '<>' are required; arguments with '[]' are optional.")
            await ctx.send(embed=embed)
         elif command == "3" and ctx.message.author.server_permissions.administrator:
            embed = discord.Embed(title="Server settings", colour=discord.Colour(0x4e7e8a), description="These are settings you may set up for ease of strain on text channels.\nType **p.help <command>** For more information on each one.")
            embed.add_field(name="**p.setup <type> <channel>**", value="Use this to determine which channels to play, send info, and/or use the store.\nOnly members with admin privileges can use this.", inline=False)
            embed.add_field(name="**p.unset <channel>**", value="Use this to allow members to use any channel to play, send info, and/or use the store.\nOnly members with admin privileges can use this.", inline=False)
            embed.add_field(name="**p.maxcredits [amount]**", value="Use this command to set the maximum number of credits members can earn by talking in chat.\nOnly members with admin privileges can use this.", inline=False)
            embed.set_footer(text="Arguments with '<>' are required; arguments with '[]' are optional.")
            await ctx.send(embed=embed)
         else:
            await ctx.send("That is not one of the 3 pages on the help menu.")
      else:
         if command == "add":
            embed = discord.Embed(title="add <card> [amount]", colour=discord.Colour(0x4e7e8a), description="This is used to add one or more of a specific card to your side deck.")
            embed.add_field(name="<card>", value="This is the specific card you wish to add.\nAll cards must be typed inside '[]'.\n_(For example '[+4]' or '[F3/6]' or '[+/-3]'.)_", inline=False)
            embed.add_field(name="[amount]", value="This is the amount of cards you wish to add.\nIf no amount is entered, 1 will be added.\nYou man not add more cards than what you currently own.", inline=False)
            embed.set_footer(text="Arguments with '<>' are required; arguments with '[]' are optional.")
            await ctx.send(embed=embed)
         elif command == "remove":
            embed = discord.Embed(title="remove <card> [amount]", colour=discord.Colour(0x4e7e8a), description="This is used to add one or more of a specific card to your side deck.")
            embed.add_field(name="<card>", value="This is the specific card you wish to remove.\nAll cards must be typed inside '[]'.\n_(For example '[+4]' or '[F3/6]' or '[+/-3]'.)_", inline=False)
            embed.add_field(name="[amount]", value="This is the amount of cards you wish to remove.\nIf no amount is entered, 1 will be removed.\nYou man not remove more cards than what you currently have selected.", inline=False)
            embed.set_footer(text="Arguments with '<>' are required; arguments with '[]' are optional.")
            await ctx.send(embed=embed)
         elif command == "last":
            await ctx.send(embed=discord.Embed(title="last", colour=discord.Colour(0x4e7e8a), description="This is used to pull the last side deck you used.\nYou will still be free to remove and add cards, and you must still type done to confirm the side deck.\n\nIf you have not played a game before, you will not have a previously used side deck, and this command will not work."))
         elif command == "done":
            await ctx.send(embed=discord.Embed(title="done", colour=discord.Colour(0x4e7e8a), description="This is used to confirm your side deck.\nIf you have fewer than 10 cards, this will not work.\nAfter typing 'done', you will receive your 4 playable cards.\n\nOnce both players have confirmed their respective side decks, play will continue in the main pazaak play channel."))
         elif command == "pazaak":
            embed = discord.Embed(title="p.pazaak <member> [wager]", colour=discord.Colour(0x4e7e8a), description=f"This command is used to challenge another member to pazaak.\nThe challenge will expire after 3 minutes.\nBe sure to keep all pazaak play in {self.client.get_channel(847627259275116554).mention}.")
            embed.add_field(name="<member>", value="Tag another server member using @.", inline=False)
            embed.add_field(name="[wager]", value="Enter a numerical wager amount.\nThe amount must be more than 50 and both players must have the amount on hand.", inline=False)
            embed.set_footer(text="Arguments with '<>' are required; arguments with '[]' are optional.")
            await ctx.send(embed=embed)
         elif command == "accept":
            await ctx.send(embed=discord.Embed(title="p.accept", colour=discord.Colour(0x4e7e8a), description="This command is used to accept the pazaak challenge.\nYou will have 3 minutes from when the challenge was first made.\nOnce accepted both players will receive DM's to start the side deck selection."))
         elif command == "decline":
            await ctx.send(embed=discord.Embed(title="p.decline", colour=discord.Colour(0x4e7e8a), description="This command is used to delcline the pazaak challenge.\nIf nothing happens after 3 minutes the challenge expires and is treated as if it was declined anyway."))
         elif command == "heads":
            await ctx.send(embed=discord.Embed(title="p.heads", colour=discord.Colour(0x4e7e8a), description="This command is used to select heads for the initial coin flip.\nYou will get a prompt to do so when both players have selected their repective side decks."))
         elif command == "tails":
            await ctx.send(embed=discord.Embed(title="p.tails", colour=discord.Colour(0x4e7e8a), description="This command is used to select tails for the initial coin flip.\nYou will get a prompt to do so when both players have selected their repective side decks."))
         elif command == "end":
            await ctx.send(embed=discord.Embed(title="p.end", colour=discord.Colour(0x4e7e8a), description="This command is used to end your turn.\nThis will allow the next player to proceed with his turn unless he has typed !stand, in which case it will be your turn again.\nAfterwards play will return to you for your turn.\nIf your total reaches 20 at any time your turn will automatically end and acts as if you already typed !stand."))
         elif command == "stand":
            await ctx.send(embed=discord.Embed(title="p.stand", colour=discord.Colour(0x4e7e8a), description="This command is used to stand on your hand.\nThis will allow the next player to play his turn unless he as also typed !stand.\nIf your total reaches 20 at any time your turn will automatically end and acts as if you already typed !stand."))
         elif command == "play":
            embed = discord.Embed(title="p.play <card> [sign]", colour=discord.Colour(0x4e7e8a), description="This command is used to play a card from your side deck.\nCheck your DM's for your playable side deck.\nAfterwards you must still type !end or !stand for play to continue\nIf your total reaches 20 at any time your turn will automatically end and acts as if you already typed !stand.")
            embed.add_field(name="<card>", value="Type the card you wish to play surrounded by '[]'.\n_(For example, a '+4' card would be typed as '[+4]' and a '-1' card would be typed as '[-1]'.)_\nOther specialty cards will just take the first letter.\n_(For example, a Double card would be typed as '[D]' and a Flip 2/4 card would be typed as '[F2/4]'.)_", inline=False)
            embed.add_field(name="[sign]", value="Type '+' (plus) or '-' (minus) to determine if the played card will be plus or minus.\nThis is only used for +/- cards and the Tiebreaker card.\n_(For example, a '+/- 2' card to be negative will be typed as '[+/-2] -' and a tiebreaker card to be positive will be typed as '[T] +'.)_")
            embed.set_footer(text="Arguments with '<>' are required; arguments with '[]' are optional.")
            await ctx.send(embed=embed)
         elif command == "setup" and ctx.message.author.server_permissions.administrator:
            embed = discord.Embed(title="p.setup <type> <channel>", colour=discord.Colour(0x4e7e8a), description="This command is used to set which channels to play, send info, and/or shop.\nBy default members may use any channel.")
            embed.add_field(name="<type>", value="Type 'play', 'store', or 'general' to determine which type of information should be displayed in the specified channel.")
            embed.add_field(name="<channel>", value="Tag the channel you wish to set the information to go to.")
            embed.set_footer(text="Arguments with '<>' are required; arguments with '[]' are optional.")
            await ctx.send(embed=embed)
         elif command == "unset" and ctx.message.author.server_permissions.administrator:
            embed = discord.Embed(title="p.unset <type>", colour=discord.Colour(0x4e7e8a), description="This command is used to allow members to use any channel to play, send info, and/or shop.\nBy default members may use any channel.")
            embed.add_field(name="<type>", value="Type 'play', 'store', or 'general' to determine which type of information is allowed anywhere.")
            embed.set_footer(text="Arguments with '<>' are required; arguments with '[]' are optional.")
            await ctx.send(embed=embed)
         elif command == "maxcredits" and ctx.message.author.server_permissions.administrator:
            embed = discord.Embed(title="p.maxcredits [amount]", colour=discord.Colour(0x4e7e8a), description="This command is used to set the maximum number of credits members can earn at a time.\nMembers may earn credits every 30 seconds by talking in any text channel.\nThe minimum will always be 1.")
            embed.add_field(name="[amount]", value="Type the maximum amount members can earn.\nIf nothing is entered the maximum reverts to its default at 5 credits.", inline=False)
            embed.set_footer(text="Arguments with '<>' are required; arguments with '[]' are optional.")
            await ctx.send(embed=embed)
         elif command == "separate" and ctx.message.author.server_permissions.adminstrator:
            embed = discord.Embed(title="p.separate <enable/disable>", colour=discord.Colour(0x4e7e8a), description="This command is used if you'd like the bot to create a separate channel for each game of pazaak.\nOnce the game is done the channel is automatically deleted.")
            embed.add_field(name="<enable/disable>", value="Type 'enable' or 'disable' to choose whether separate channels are used.\nThis is disabled by default.", inline=False)
            embed.set_footer(text="Arguments with '<>' are required; arguments with '[]' are optional.")
            await ctx.send(embed=embed)
         else:
            await ctx.send(f"{command} is not a pazaak command.")

def setup (client):
   client.add_cog(Help(client))