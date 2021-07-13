import discord, json, mysql.connector
from discord.ext import commands

with open('./config.json') as data:
   config = json.load(data)

class Announcement(commands.Cog):

   def __init__ (self, client):
      self.client = client

   @commands.command()
   async def announce (self, ctx, *message):
      if ctx.message.author.id == config['dev_id']:
         db = mysql.connector.connect(host=config['database_server'], user=config['database_user'], password=config['database_pass'], database=config['database_schema'])
         cursor = db.cursor()

         try:
            cursor.execute("SELECT general_channel FROM server_info WHERE general_channel IS NOT NULL")
            channels = cursor.fetchall()
            for channelid in channels:
               await self.client.get_channel(channelid[0]).send(f"@everyone {' '.join(message)}")
         except Exception as e:
            print(str(e))

         cursor.close()
         db.close()

def setup (client):
   client.add_cog(Announcement(client))