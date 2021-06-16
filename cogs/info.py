import discord, json, MySQLdb
from discord.ext import commands

with open('../config.json') as data:
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
         cursor.execute(f"SELECT * FROM pazaak WHERE discordid = {ctx.message.author.id}")
         if cursor.rowcount > 0:
            cursor.execute("SELECT discordid, wins, losses FROM pazaak ORDER BY wins DESC, losses ASC")
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
                  break
         else:
            cursor.execute(f"SELECT play_channel FROM server_info WHERE server_id = {ctx.message.guild.id}")
            await ctx.send(f"{ctx.message.author.mention}, you currently don't have a pazaak rank since you have never played a game. Go to {self.client.get_channel(847627259275116554).mention} and start your first game!")
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
      db = MySQLdb.connect("localhost", config['database_user'], config['database_pass'], config['database_schema'])
      cursor = db.cursor()

      cursor.execute(f"SELECT plus_one, plus_two, plus_three, plus_four, plus_five, plus_six, minus_one, minus_two, minus_three, minus_four, minus_five, minus_six, plus_minus_one, plus_minus_two, plus_minus_three, plus_minus_four, plus_minus_five, plus_minus_six, flip_two_four, flip_three_six, double_card, tiebreaker_card FROM pazaak WHERE discordid = {ctx.message.author.id}")

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
         ctx.send("You currently don't have a pazaak deck. Play your first game of pazaak to obtain a deck.")
      
      db.close()
      
def setup (client):
   client.add_cog(Info(client))