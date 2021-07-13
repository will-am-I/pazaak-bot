import discord, json, mysql.connector
from discord.ext import commands

with open('./config.json') as data:
   config = json.load(data)

class Setup(commands.Cog):

   def __init__ (self, client):
      self.client = client

   @commands.command()
   async def setup (self, ctx, type=None, channel:discord.TextChannel=None):
      db = mysql.connector.connect(host=config['database_server'], user=config['database_user'], password=config['database_pass'], database=config['database_schema'])
      cursor = db.cursor()

      try:
         if type is None or channel is None:
            ctx.send("Use p.setup <play/general/store> <channel> to set which channel to use those commands.")
         elif type == "play":
            cursor.execute(f"UPDATE server_info SET play_channel = {channel.id} WHERE server_id = {ctx.message.guild.id}")
         elif type == "general":
            cursor.execute(f"UPDATE server_info SET general_channel = {channel.id} WHERE server_id = {ctx.message.guild.id}")
         elif type == "store":
            cursor.execute(f"UPDATE server_info SET store_channel = {channel.id} WHERE server_id = {ctx.message.guild.id}")

         await ctx.send(f"{channel.mention} is now the pazaak {type} channel.")

         db.commit()
      except Exception as e:
         db.rollback()
         print(str(e))

      cursor.close()
      db.close()

   @commands.command()
   async def unset (self, ctx, type=None):
      db = mysql.connector.connect(host=config['database_server'], user=config['database_user'], password=config['database_pass'], database=config['database_schema'])
      cursor = db.cursor()

      try:
         if type is None:
            ctx.send("Use p.unset <play/general/store> to allow use in any channel.")
         elif type == "play":
            cursor.execute(f"UPDATE server_info SET play_channel = NULL WHERE server_id = {ctx.message.guild.id}")
         elif type == "general":
            cursor.execute(f"UPDATE server_info SET general_channel = NULL WHERE server_id = {ctx.message.guild.id}")
         elif type == "store":
            cursor.execute(f"UPDATE server_info SET store_channel = NULL WHERE server_id = {ctx.message.guild.id}")

         await ctx.send(f"There is now no disignated pazaak {type} channel.")

         db.commit()
      except Exception as e:
         db.rollback()
         print(str(e))

      cursor.close()
      db.close()

   @commands.command()
   async def maxcredits (self, ctx, amount=5):
      db = mysql.connector.connect(host=config['database_server'], user=config['database_user'], password=config['database_pass'], database=config['database_schema'])
      cursor = db.cursor()

      try:
         cursor.execute(f"UPDATE server_info SET max_credits = {amount} WHERE server_id = {ctx.message.guild.id}")
         
         await ctx.send(f"The server's default max credits is now {amount}.")

         db.commit()
      except Exception as e:
         db.rollback()
         print(str(e))

      cursor.close()
      db.close()

   @commands.command()
   async def separate (self, ctx, action):
      value = 0 if action == "disable" else 1

      db = mysql.connector.connect(host=config['database_server'], user=config['database_user'], password=config['database_pass'], database=config['database_schema'])
      cursor = db.cursor()

      try:
         cursor.execute(f"UPDATE server_info SET separate_channel = {value} WHERE server_id = {ctx.message.guild.id}")

         await ctx.send(f"Separate pazaak game channels are now {action}d.")
         
         db.commit()
      except Exception as e:
         db.rollback()
         print(str(e))

      cursor.close()
      db.close()

def setup (client):
   client.add_cog(Setup(client))