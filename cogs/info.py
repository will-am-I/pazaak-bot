import discord, json, MySQLdb
from discord.ext import commands

with open('./config.json') as data:
   config = json.load(data)
with open('./cards.json') as data:
   cards = json.load(data)

class Info(commands.Cog):

   def __init__ (self, client):
      self.client = client

   @commands.command()
   async def rank (self, ctx):
      if generalChannel(ctx.message.guild.id, ctx.message.channel.id):
         db = MySQLdb.connect(config['database_server'], config['database_user'], config['database_pass'], config['database_schema'])
         cursor = db.cursor()

         try:
            cursor.execute(f"SELECT wins + losses AS games FROM pazaak_balance WHERE discordid = {ctx.message.author.id}")
            games = cursor.fetchone()[0]

            if games > 0:
               members = [str(member.id) async for member in ctx.message.guild.fetch_members()]
               members = ', '.join(members)

               cursor.execute(f"SELECT * FROM pazaak_balance WHERE discordid IN ({members}) ORDER BY POWER(wins, 2) / (losses + 1) DESC")
               results = cursor.fetchall()

               place = 0
               for result in results:
                  place += 1
                  if result[0] == ctx.message.author.id:
                     wins = result[1]
                     losses = result[2]
                     serverRank = str(place)
                     if serverRank.endswith("1") and not serverRank.endswith("11"):
                        serverRank += "st"
                     elif serverRank.endswith("2") and not serverRank.endswith("12"):
                        serverRank += "nd"
                     elif serverRank.endswith("3") and not serverRank.endswith("13"):
                        serverRank += "rd"
                     else:
                        serverRank += "th"
                     break
               
               cursor.execute("SELECT discordid, wins, losses FROM pazaak_balance ORDER BY POWER(wins, 2) / (losses + 1) DESC")
               results = cursor.fetchall()
               
               place = 0
               for result in results:
                  place += 1
                  if result[0] == ctx.message.author.id:
                     wins = result[1]
                     losses = result[2]
                     globalRank = str(place)
                     if globalRank.endswith("1") and not globalRank.endswith("11"):
                        globalRank += "st"
                     elif globalRank.endswith("2") and not globalRank.endswith("12"):
                        globalRank += "nd"
                     elif globalRank.endswith("3") and not globalRank.endswith("13"):
                        globalRank += "rd"
                     else:
                        globalRank += "th"
                     break

               embed = discord.Embed(title=f"{ctx.message.author.name}'s Pazaak Rank", colour=discord.Colour(0x4e7e8a), description=f"You are **{serverRank}** on {ctx.message.guild.name}'s leaderboard.\nYou are **{globalRank}** on the global leaderboard.")
               embed.set_thumbnail(url=ctx.message.author.avatar_url)
               embed.add_field(name="Wins", value=wins)
               embed.add_field(name="Losses", value=losses)
               await ctx.send(embed=embed)
            else:
               cursor.execute(f"SELECT play_channel FROM server_info WHERE server_id = {ctx.message.guild.id}")
               channel = cursor.fetchone()[0]
               if channel is not None:
                  await ctx.send(f"{ctx.message.author.mention}, you currently don't have a pazaak rank since you have never played a game. Go to {self.client.get_channel(channel).mention} and start your first game!")
               else:
                  await ctx.send(f"{ctx.message.author.mention}, you currently don't have a pazaak rank since you have never played a game. Go play your first game now!")
         except Exception as e:
            print(str(e))
         
         db.close()

   @commands.command()
   async def top (self, ctx, all=None):
      if generalChannel(ctx.message.guild.id, ctx.message.channel.id):
         db = MySQLdb.connect(config['database_server'], config['database_user'], config['database_pass'], config['database_schema'])
         cursor = db.cursor()

         try:
            if all is not None and (all == "all" or all == "global"):
               cursor.execute("SELECT discordid, wins, losses FROM pazaak_balance WHERE wins + losses > 0 ORDER BY POWER(wins, 2) / (losses + 1) DESC")
               if cursor.rowcount < 10:
                  rows = cursor.rowcount
               else:
                  rows = 10
               results = cursor.fetchall()
               
               embed = discord.Embed(title="Overall Pazaak Leaderboard", colour=discord.Colour(0x4e7e8a))
               names = []
               wins = []
               losses = []

               for i in range(rows):
                  user = await self.client.fetch_user(results[i][0])
                  names.append(f"**{i+1}.** {user.name}")
                  wins.append(str(results[i][1]))
                  losses.append(str(results[i][2]))

               names = '\n'.join(names)
               wins = '\n'.join(wins)
               losses = '\n'.join(losses)

               embed.add_field(name="Players", value=names, inline=True)
               embed.add_field(name="Wins", value=wins, inline=True)
               embed.add_field(name="Losses", value=losses, inline=True)


               await ctx.send(embed=embed)
            else:
               members = [str(member.id) async for member in ctx.message.guild.fetch_members()]
               members = ', '.join(members)

               cursor.execute(f"SELECT discordid, wins, losses FROM pazaak_balance WHERE discordid IN ({members}) AND wins + losses > 0 ORDER BY POWER(wins, 2) / (losses + 1) DESC")
               if cursor.rowcount < 10:
                  rows = cursor.rowcount
               else:
                  rows = 10
               results = cursor.fetchall()
               
               embed = discord.Embed(title=f"{ctx.message.guild.name}'s Pazaak Leaderboard", colour=discord.Colour(0x4e7e8a))
               names = []
               wins = []
               losses = []

               for i in range(rows):
                  user = await self.client.fetch_user(results[i][0])
                  names.append(f"**{i+1}.** {user.display_name}")
                  wins.append(str(results[i][1]))
                  losses.append(str(results[i][2]))

               names = '\n'.join(names)
               wins = '\n'.join(wins)
               losses = '\n'.join(losses)

               embed.add_field(name="Players", value=names, inline=True)
               embed.add_field(name="Wins", value=wins, inline=True)
               embed.add_field(name="Losses", value=losses, inline=True)

               await ctx.send(embed=embed)
         except Exception as e:
            print(str(e))

         db.close()

   @commands.command()
   async def inventory (self, ctx):
      db = MySQLdb.connect(config['database_server'], config['database_user'], config['database_pass'], config['database_schema'])
      cursor = db.cursor()

      cursor.execute(f"SELECT p1, p2, p3, p4, p5, p6, m1, m2, m3, m4, m5, m6, pm1, pm2, pm3, pm4, pm5, pm6, f24, f36, dc, tc FROM pazaak_inventory WHERE discordid = {ctx.message.author.id}")

      if cursor.rowcount > 0:
         cardAmounts = cursor.fetchone()

         embed = discord.Embed(title="Your deck", colour=discord.Colour(0x4e7e8a))
         for i in range(len(cards['cards'])):
            if any(n in cards['cards'][i]['code'] for n in ['F', 'D', 'T']):
               embed.add_field(name=f"[{cards['cards'][i]['code']}] {cards['cards'][i]['name']}", value=str(cardAmounts[i]), inline=False)
            else:
               embed.add_field(name=f"[{cards['cards'][i]['code']}]", value=str(cardAmounts[i]), inline=True)
         
         user = self.client.get_user(ctx.message.author.id)
         await user.send(embed=embed)
      else:
         await ctx.send(f"{ctx.message.author.mention}, you currently don't have a pazaak deck. Play your first game of pazaak to obtain a deck.")
      
      db.close()
      
def generalChannel (serverid, channelid):
   try:
      db = MySQLdb.connect(config['database_server'], config['database_user'], config['database_pass'], config['database_schema'])
      cursor = db.cursor()

      cursor.execute(f"SELECT general_channel FROM server_info WHERE server_id = {serverid}")
      generalChannel = cursor.fetchone()[0]

      db.close()
      return generalChannel is None or generalChannel == channelid

   except Exception as e:
      print(str(e))
      return False

def setup (client):
   client.add_cog(Info(client))