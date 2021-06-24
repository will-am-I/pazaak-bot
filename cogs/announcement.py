import discord, json, MySQLdb
from discord.ext import commands

with open('./config.json') as data:
   config = json.load(data)

class Announcement(commands.Cog):

   def __init__ (self, client):
      self.client = client

   @commands.command()
   async def announce (self, ctx, *message):
      if ctx.message.author.id == config['dev_id']:
         db = MySQLdb.connect(config['database_server'], config['database_user'], config['database_pass'], config['database_schema'])
         cursor = db.cursor()

         try:
            cursor.execute("SELECT general_channel FROM server_info WHERE general_channel IS NOT NULL")
            channels = cursor.fetchall()
            for channelid in channels:
               await self.client.get_channel(channelid[0]).send(f"@everyone {' '.join(message)}")
         except Exception as e:
            print(str(e))

         db.close()

def setup (client):
   client.add_cog(Announcement(client))