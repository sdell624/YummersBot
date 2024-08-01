import os
import discord
from discord.ext import commands
import youtube_dl
import ffmpeg
from dotenv import load_dotenv

# Load local .env file and access bot token
load_dotenv()
TOKEN = os.getenv('BOT_TOKEN')

# Create bot instance
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Options for youtube_dl and ffmpeg
ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0'
}

ffmpeg_options = {
    'options': '-vn'
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

# Function to download and play audio from a youtube link
def download_audio(url):
    with ytdl:
        info = ytdl.extract_info(url, download=False)
    url2 = info['formats'][0]['url']
    return url2

# Bot commands
@bot.command(name='join', help='Joins a voice channel')
async def join(ctx):
    if not ctx.message.author.voice:
        await ctx.send(f"{ctx.message.author.name} is not connected to a voice channel")
        return
    else:
        channel = ctx.message.author.voice.channel

    await channel.connect()

@bot.command(name='leave', help='Leaves the voice channel')
async def leave(ctx):
    await ctx.voice_client.disconnect()

@bot.command(name='play', help='Plays audio from a youtube link')
async def play(ctx, url):
    pass