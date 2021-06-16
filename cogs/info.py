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
      db = MySQLdb.connect(config['database_server'], config['database_user'], config['database_pass'], config['database_schema'])
      cursor = db.cursor()

      try:
         cursor.execute(f"SELECT wins + losses AS games FROM pazaak_balance WHERE discordid = {ctx.message.author.id}")
         games = cursor.fetchone()[0]

         if games > 0:
            cursor.execute("SELECT discordid, wins, losses FROM pazaak_balance ORDER BY wins DESC, losses ASC")
            results = cursor.fetchall()
            
            i = 0
            for result in results:
               i += 1
               if result[0] == ctx.message.author.id:
                  place = str(i)
                  if place.endswith("1") and not place.endswith("11"):
                     place += "st"
                  elif place.endswith("2") and not place.endswith("12"):
                     place += "nd"
                  elif place.endswith("3") and not place.endswith("13"):
                     place += "rd"
                  else:
                     place += "th"

                  embed = discord.Embed(title=f"{ctx.message.author.name}'s Pazaak Rank", colour=discord.Colour(0x4e7e8a), description=f"You are {place} place on the leaderboard.")
                  embed.set_thumbnail(url=ctx.message.author.avatar_url)
                  embed.add_field(name="Wins", value=result[1])
                  embed.add_field(name="Losses", value=result[2])
                  await ctx.send(embed=embed)
         else:
            cursor.execute(f"SELECT play_channel FROM server_info WHERE server_id = {ctx.message.guild.id}")
            channel = cursor.fetchone()[0]
            await ctx.send(f"{ctx.message.author.mention}, you currently don't have a pazaak rank since you have never played a game. Go to {self.client.get_channel(channel).mention} and start your first game!")
      except Exception as e:
         print(str(e))
      
      db.close()

   @commands.command()
   async def top (self, ctx, all=None):
      db = MySQLdb.connect(config['database_server'], config['database_user'], config['database_pass'], config['database_schema'])
      cursor = db.cursor()

      try:
         if all is None:
            members = [member.id for member in ctx.message.guild.fetch_members()]
            members = ', '.join(members)

            cursor.execute(f"SELECT discordid, wins, losses FROM pazaak_balance WHERE discordid IN ({members}) ORDER BY wins DESC, losses ASC")
            if cursor.rowcount < 10:
               rows = cursor.rowcount
            else:
               rows = 10
            results = cursor.fetchall()

            leaderboard = ""
            for i in range(rows):
               user = self.client.fetch_user(results[i][0])
               leaderboard += f"**{i+1}.**\t{user.name}\t{results[i][1]}/{results[i][2]}\n"

            await ctx.send(embed=discord.Embed(title=f"{ctx.message.guild.name}'s Pazaak Leaderboard", colour=discord.Colour(0x4e7e8a), description=leaderboard))
         if all == "all":
            cursor.execute("SELECT discordid, wins, losses FROM pazaak_balance ORDER BY wins DESC, losses ASC")
            if cursor.rowcount < 10:
               rows = cursor.rowcount
            else:
               rows = 10
            results = cursor.fetchall()

            leaderboard = ""
            for i in range(rows):
               user = self.client.fetch_user(results[i][0])
               leaderboard += f"**{i+1}.**\t{user.name}\t{results[i][1]}/{results[i][2]}\n"

            await ctx.send(embed=discord.Embed(title="Pazaak Leaderboard", colour=discord.Colour(0x4e7e8a), description=leaderboard))
      except Exception as e:
         print(str(e))

      db.close()

   @commands.command()
   async def sidedeck (self, ctx):
      db = MySQLdb.connect(config['database_server'], config['database_user'], config['database_pass'], config['database_schema'])
      cursor = db.cursor()

      cursor.execute(f"SELECT p1, p2, p3, p4, p5, p6, m1, m2, m3, m4, m5, m6, pm1, pm2, pm3, pm4, pm5, pm6, f24, f36, dc, tc FROM pazaak_inventory WHERE discordid = {ctx.message.author.id}")

      if cursor.rowcount > 0:
         cardAmounts = cursor.fetchone()

         embed = discord.Embed(title="Your deck", colour=discord.Colour(0x4e7e8a))
         for card in cards['cards']:
            if any(i in card['code'] for i in ['F', 'D', 'T']):
               embed.add_field(name=f"[{card['code']}] {card['name']}", value=str(card['cost']), inline=False)
            else:
               embed.add_field(name=f"[{card['code']}]", value=str(card['cost']), inline=True)
         
         user = self.client.get_user(ctx.message.author.id)
         await user.send(embed=embed)
      else:
         await ctx.send("You currently don't have a pazaak deck. Play your first game of pazaak to obtain a deck.")
      
      db.close()
      
def setup (client):
   client.add_cog(Info(client))