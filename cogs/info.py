import discord, json, MySQLdb
from discord.ext import commands, tasks

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
   async def top (self, ctx):
      pass

   @commands.command()
   async def sidedeck (self, ctx):
      pass
      
def setup (client):
   client.add_cog(Info(client))