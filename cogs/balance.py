import discord, json, MySQLdb
from discord.ext import commands
from datetime import datetime, timedelta
from random import randint

with open('./config.json') as data:
   config = json.load(data)
with open('./cards.json') as data:
   cards = json.load(data)

class Balance(commands.Cog):

   def __init__ (self, client):
      self.client = client

   @commands.command()
   async def balance (self, ctx):
      db = MySQLdb.connect(config['database_server'], config['database_user'], config['database_pass'], config['database_schema'])
      cursor = db.cursor()

      try:
         cursor.execute(f"SELECT credits FROM pazaak_balance WHERE discordid = {ctx.message.author.id}")
         if cursor.rowcount > 0:
            credits = cursor.fetchone()[0]

            file = discord.File("./images/credits.png", filename="credits.png")
            embed = discord.Embed(title=f"{ctx.message.author.name}'s credit balance", colour=discord.Colour(0x4e7e8a), description=f"You currently have **{credits}** credits.")
            embed.set_thumbnail(url="attachment://credits.png")
         else:
            embed = discord.Embed(title=f"{ctx.message.author.name}'s credit balance", colour=discord.Colour(0x4e7e8a), description=f"You currently have **0** credits.")
         await ctx.send(file=file, embed=embed)
      except Exception as e:
         print(str(e))
      
      db.close()

   @commands.Cog.listener()
   async def on_message (self, message):
      if message.author.id != config['bot_id'] and (not message.content.startswith("p.")):
         db = MySQLdb.connect("localhost", config['database_user'], config['database_pass'], config['database_schema'])
         cursor = db.cursor()

         try:
            cursor.execute(f"INSERT IGNORE INTO pazaak_balance (discordid) VALUES ({message.author.id})")
            db.commit()

            cursor.execute(f"SELECT DATE_FORMAT(creditlock, '%Y-%m-%d %T') FROM pazaak_balance WHERE discordid = {message.author.id}")
            stamp = cursor.fetchone()[0]
            if datetime.strptime(stamp, "%Y-%m-%d %H:%M:%S") < datetime.utcnow():
               coinlock = (datetime.utcnow() + timedelta(seconds=30)).strftime("%Y-%m-%d %H:%M:%S")
               cursor.execute(f"SELECT max_credits FROM server_info WHERE server_id = {message.guild.id}")
               maxcredits = cursor.fetchone()[0]
               cursor.execute(f"UPDATE pazaak_balance SET credits = credits + {randint(1, maxcredits)}, creditlock = STR_TO_DATE('{coinlock}', '%Y-%m-%d %T') WHERE discordid = {message.author.id}")
            db.commit()
         except Exception as e:
            db.rollback()
            print(str(e))

         db.close()

def setup (client):
   client.add_cog(Balance(client))