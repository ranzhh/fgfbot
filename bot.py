import discord
import logging
import feedparser
import json
from datetime import datetime
from urllib.parse import quote

from discord.ext import commands, tasks

# Set up logging
logging.basicConfig(level=logging.INFO)

# Load configuration file
with open('config.json', 'r') as f:
    c: dict = json.load(f)

# Define intents
intents = discord.Intents.default()
intents.message_content = True

# Set up bot
bot = commands.Bot(command_prefix=c.get('RIN_BOT_PREFIX'), intents=intents)

def create_game_embed(title: str, link: str, store: str):
    embed = discord.Embed(title=title, url=link, description=f'New free game on {store}')
    return embed

@tasks.loop(minutes=30)
async def check_free_games():
    free_games = await get_free_games()

    for channel in c.get('RIN_BOT_CHANNELS'):
        c_id, c_deb = channel.get('id'), channel.get('debug')
        ctx = await bot.fetch_channel(c_id)

        if c_deb and len(free_games) < 1:
            await ctx.send('No new free games found since the last check on ' + last_checked.strftime('%Y-%m-%d %H:%M:%S'))
            continue

        for game in free_games:
            embed = create_game_embed(game.get('title'), game.get('link'), game.get('store'))
            await ctx.send(embed=embed)

async def get_free_games():
    global last_checked

    logging.info('Getting free games at time: ' + str(last_checked))

    stores = c.get('STORES')

    new_entries = [check_feed(store, last_checked) for store in stores]
    new_entries = [entry for entries in new_entries for entry in entries]

    # overwrite last checked
    last_checked = datetime.now()

    return new_entries

def check_feed(store: str, last_checked: datetime):
    logging.info(f'Checking feed for {store}')
    feed_url = 'https://www.reddit.com/r/FreeGameFindings/new.rss'
    store_url = quote(store)
    feed_url = f'https://www.reddit.com/r/FreeGameFindings/search.rss?q=title%3A{store_url}&restrict_sr=1&sr_nsfw=&sort=new&include_over_18=1'
    feed: dict = feedparser.parse(feed_url)

    entries = feed.get('entries')
    new_entries = [entry for entry in entries if datetime.strptime(entry.get('published'), '%Y-%m-%dT%H:%M:%S+00:00') > last_checked]

    return new_entries

@bot.event
async def on_ready():
    logging.info(f'{bot.user} has connected to Discord!')
    check_free_games.start()
        
last_checked = datetime.now()

# Launch bot
bot.run(c.get('RIN_BOT_TOKEN'))