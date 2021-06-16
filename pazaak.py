import discord, MySQLdb, os, json
from discord.ext import commands

client = commands.Bot(command_prefix = 'p.')
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
   db = MySQLdb.connect(config['database_server'], config['database_user'], config['database_pass'], config['database_schema'])
   cursor = db.cursor()

   try:
      cursor.execute(f"INSERT IGNORE INTO server_info (server_id) VALUES ({guild.id})")
      db.commit()
   except Exception as e:
      db.rollback()
      print(str(e))

   db.close()
   
for filename in os.listdir('./cogs'):
   if filename.endswith('.py'):
      client.load_extension(f'cogs.{filename[:-3]}')

client.run(config['discord_token'])