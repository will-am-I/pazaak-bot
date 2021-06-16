import discord, json, MySQLdb
from discord.ext import commands

with open('../config.json') as data:
   config = json.load(data)
with open('./cards.json') as data:
   cards = json.load(data)

class Store(commands.Cog):

   def __init__ (self, client):
      self.client = client

   @commands.command()
   async def store (self, ctx, page=1):
      startAt = ((page - 1) * 6)
      if page == 4:
         endAt = startAt + 5
      else:
         endAt = startAt + 7
      
      description = "Use p.buy <card> to purchase a card."
      if page == 4:
         description += "\nOnly one of each of these cards per person."

      embed = discord.Embed(title="Card Store", colour=discord.Colour(0x4e7e8a), description=description)
      embed.set_footer(text=f"Page {page}/4 | Use !pazaakstore <page> to select another page.")
      
      for i in range(startAt, endAt):
         if page < 4:
            embed.add_field(name=f"[{cards['cards'][i]['code']}]", value=f"{cards['cards'][i]['cost']} credits", inline=True)
         else:
            embed.add_field(name=f"[{cards['cards'][i]['code']}] {cards['cards'][i]['name']}", value=f"{cards['cards'][i]['cost']} credits\n{cards['prestige'][cards['cards'][i]['code']]['requirement']}", inline=False)

      await ctx.send(embed=embed)

   @commands.command()
   async def buy (self, ctx, card):
      card = card.translate({ord(i): None for i in '[]'})
      dbcard = next(item['db_name'] for item in cards['cards'] if item['code'] == card)
      cost = next(item['cost'] for item in cards['cards'] if item['code'] == card)

      db = MySQLdb.connect(config['database_server'], config['database_user'], config['database_pass'], config['database_schema'])
      cursor = db.cursor()

      try:
         cursor.execute(f"SELECT * FROM pazaak WHERE discordid = {ctx.message.author.id}")

         if cursor.rowcount == 0:
            await ctx.send("You don't currently have a deck of your own. Play your first game of pazaak to obtain a deck.")
         else:
            cursor.execute(f"SELECT coins FROM member_rank WHERE discordid = {ctx.message.author.id}")
            credits = cursor.fetchone()[0]

            if credits >= cost:
               if any(i in card for i in ['F', 'D', 'T']):
                  cursor.execute(f"SELECT {dbcard} FROM pazaak WHERE discordid = {ctx.message.author.id}")
                  amount = cursor.fetchone()[0]

                  if amount >= 1:
                     if amount > 1:
                        cursor.execute(f"UPDATE pazaak SET {dbcard} = 1 WHERE discordid = {ctx.message.author.id}")
                     await ctx.send("You may only own 1 of these cards.")
                  else:
                     cursor.execute(f"SELECT wins, wins + losses AS games FROM pazaak WHERE discordid = {ctx.message.author.id}")
                     results = cursor.fetchone()
                     
                     if results[1] < cards['prestige'][card]['games']:
                        await ctx.send("You have not played enough games to buy this card.")
                     elif results[0] < cards['prestige'][card]['wins']:
                        await ctx.send("You have not won enough games to buy this card.")
                     else:
                        cursor.execute(f"UPDATE member_rank SET coins = coins - {cost} WHERE discordid = {ctx.message.author.id}")
                        db.commit()
                        cursor.execute(f"UPDATE pazaak SET {dbcard} = {dbcard} + 1 WHERE discordid = {ctx.message.author.id}")
                        db.commit()
                        await ctx.send(f"[{card}] has been added to your deck.")
               else:
                  cursor.execute(f"UPDATE member_rank SET coins = coins - {cost} WHERE discordid = {ctx.message.author.id}")
                  db.commit()
                  cursor.execute(f"UPDATE pazaak SET {dbcard} = {dbcard} + 1 WHERE discordid = {ctx.message.author.id}")
                  db.commit()
                  await ctx.send(f"[{card}] has been added to your deck.")
            else:
               await ctx.send("You don't have enough credits for this card.")
      except Exception as e:
         db.rollback()
         print(str(e))

      db.close()
      
def setup (client):
   client.add_cog(Store(client))