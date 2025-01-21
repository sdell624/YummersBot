import discord
from discord.ext import commands
import yt_dlp
import asyncio
import os
from dotenv import load_dotenv

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Load .env to get Discord token (should be in format "DISCORD_TOKEN=[token here]")
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# YouTube DL options
YTDL_OPTIONS = {
    'format': 'bestaudio/best',
    'extractaudio': True,
    'audioformat': 'mp3',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0',
}

# FFmpeg options
FFMPEG_OPTIONS = {
    'options': '-vn',
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5'
}

# Create YT DLP client
ytdl = yt_dlp.YoutubeDL(YTDL_OPTIONS)

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')

@bot.command(name='join')
async def join(ctx):
    """Join the user's voice channel"""
    if ctx.author.voice:
        channel = ctx.author.voice.channel
        await channel.connect()
    else:
        await ctx.send("You need to be in a voice channel first!")

@bot.command(name='leave')
async def leave(ctx):
    """Leave the voice channel"""
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
    else:
        await ctx.send("I'm not in a voice channel!")

@bot.command(name='play')
async def play(ctx, *, url):
    """Play audio from a YouTube URL"""
    try:
        # Join voice channel if not already in one
        if not ctx.voice_client:
            if ctx.author.voice:
                await ctx.author.voice.channel.connect()
            else:
                await ctx.send("You need to be in a voice channel first!")
                return

        async with ctx.typing():
            # Get video info and extract URL
            loop = asyncio.get_event_loop()
            data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=False))
            
            if 'entries' in data:
                # Take first item from a playlist
                data = data['entries'][0]

            audio_url = data['url']
            
            # Create audio source
            audio_source = discord.FFmpegPCMAudio(audio_url, **FFMPEG_OPTIONS)
            
            # Play the audio
            ctx.voice_client.play(audio_source)
            
            await ctx.send(f'Now playing: {data["title"]}')

    except Exception as e:
        await ctx.send(f'An error occurred: {str(e)}')

# Replace 'YOUR_TOKEN_HERE' with your bot's token
bot.run(TOKEN)