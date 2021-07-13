import discord, mysql.connector, os, json
from discord import integrations
from discord.ext import commands

intents = discord.Intents.default()
intents.members = True
client = commands.Bot(command_prefix = 'p.', intents=intents)
client.remove_command('help')

with open('./config.json') as data:
   config = json.load(data)

@client.event
async def on_ready ():
   await client.change_presence(activity=discord.Activity(type=discord.ActivityType.playing, name="Pazaak, type p.help for info"))
   print('Pure Pazaak!')

@client.command()
async def load (ctx, extension):
   if ctx.message.author.id == config['dev_id']:
      client.load_extension(f'cogs.{extension}')
      await ctx.send(f'{extension} has been loaded in')
   
@client.command()
async def unload (ctx, extension):
   if ctx.message.author.id == config['dev_id']:
      client.unload_extension(f'cogs.{extension}')
      await ctx.send(f'{extension} has been unloaded out')
   
@client.command()
async def reload (ctx, extension):
   if ctx.message.author.id == config['dev_id']:
      client.unload_extension(f'cogs.{extension}')
      client.load_extension(f'cogs.{extension}')
      await ctx.send(f'{extension} has been reloaded')

@client.event
async def on_guild_join (guild):
   db = mysql.connector.connect(host=config['database_server'], user=config['database_user'], password=config['database_pass'], database=config['database_schema'])
   cursor = db.cursor()

   try:
      cursor.execute(f"INSERT IGNORE INTO server_info (server_id) VALUES ({guild.id})")
      db.commit()
   except Exception as e:
      db.rollback()
      print(str(e))

   cursor.close()
   db.close()

@client.event
async def on_guild_remove (guild):
   db = mysql.connector.connect(host=config['database_server'], user=config['database_user'], password=config['database_pass'], database=config['database_schema'])
   cursor = db.cursor()

   try:
      cursor.execute(f"DELETE FROM server_info WHERE server_id = {guild.id}")
      db.commit()
   except Exception as e:
      db.rollback()
      print(str(e))

   cursor.close()
   db.close()
   
for filename in os.listdir('./cogs'):
   if filename.endswith('.py'):
      client.load_extension(f'cogs.{filename[:-3]}')

client.run(config['discord_token'])