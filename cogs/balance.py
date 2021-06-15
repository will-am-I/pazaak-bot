import discord, json, MySQLdb
from discord.ext import commands, tasks

with open('../config.json') as data:
   config = json.load(data)
with open('./cards.json') as data:
   cards = json.load(data)

class Balance(commands.Cog):

   def __init__ (self, client):
      self.client = client

   @commands.command()
   async def balance (self, ctx):
      pass

   @commands.Cog.listener()
   async def on_message (self, message):
      pass

def setup (client):
   client.add_cog(Balance(client))