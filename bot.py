import discord
from discord.ext import commands
import yt_dlp
import asyncio
import os
from dotenv import load_dotenv

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='.', intents=intents)

# Load .env to get Discord token
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

# Class to manage music queue functionality
class MusicQueue:
    def __init__(self):
        self.queue = []
        self.current_song = None
    
    def add(self, url, title=None):
        self.queue.append({"url": url, "title": title})
    
    def get_next(self):
        if self.queue:
            self.current_song = self.queue.pop(0)
            return self.current_song
        return None
    
    def clear(self):
        self.queue.clear()
        self.current_song = None
    
    def remove(self, index):
        if 0 <= index < len(self.queue):
            return self.queue.pop(index)
        return None
    
    # Get queue info to send in a message
    def get_queue_info(self):
        queue_list = []
        if self.current_song:
            queue_list.append(f"Currently playing: {self.current_song['title']}")
        
        for i, song in enumerate(self.queue, 1):
            queue_list.append(f"{i}. {song['title']}")
        
        return "\n".join(queue_list) if queue_list else "Queue is empty"

# Initialize queue
music_queue = MusicQueue()

@bot.event
async def on_ready():
    print(f'{bot.user} connected to Discord')

#--------------------------------------
# Bot commands
#--------------------------------------

@bot.command(name='join')
async def join(ctx):
    await join_voice_channel(ctx)

@bot.command(name='leave')
async def leave(ctx):
    if ctx.voice_client:
        music_queue.clear()
        await ctx.voice_client.disconnect()
    else:
        await ctx.send("I'm not in a voice channel headass")

@bot.command(name='play', aliases=['p'])
async def play(ctx, *, query):
    try:
        # Join voice channel if not already in one
        await join_voice_channel(ctx)
        
        # Get video info
        async with ctx.typing():
            loop = asyncio.get_event_loop()
            
            # Check if query is a URL (basic check for 'youtube.com' or 'youtu.be')
            is_url = 'youtube.com' in query or 'youtu.be' in query
            
            # If not a URL, prepend 'ytsearch:'
            search_query = query if is_url else f'ytsearch:{query}'
            
            # Extract info using modified query
            data = await loop.run_in_executor(None, lambda: ytdl.extract_info(search_query, download=False))
            
            if 'entries' in data:
                data = data['entries'][0]
            
            # Add to queue
            music_queue.add(data['url'], data['title'])
            await ctx.send(f'Added to queue: {data["title"]}')
            
            # If nothing is playing, start playing
            if not ctx.voice_client.is_playing():
                await play_next(ctx)
    
    except Exception as e:
        await ctx.send(f'An error occurred: {str(e)}')

@bot.command(name='skip', aliases=['s'])
async def skip(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.stop()
        await ctx.send("Next!")
    else:
        await ctx.send("The silence of the void is already deafening")

@bot.command(name='queue', aliases=['q'])
async def show_queue(ctx):
    queue_info = music_queue.get_queue_info()
    await ctx.send(f"```\n{queue_info}\n```")

@bot.command(name='clear')
async def clear_queue(ctx):
    music_queue.clear()
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.stop()
    await ctx.send("All gone :)")

@bot.command(name='remove', aliases=['r'])
async def remove_from_queue(ctx, index: int):
    try:
        removed_song = music_queue.remove(index - 1)
        if removed_song:
            await ctx.send(f"Removed from queue: {removed_song['title']}")
        else:
            await ctx.send("Erm... that song doesn't exist!")
    except ValueError:
        await ctx.send("That's not real")

#--------------------------------------
# Support functions
#--------------------------------------

async def join_voice_channel(ctx):
    if not ctx.voice_client:
        if ctx.author.voice:
            await ctx.author.voice.channel.connect()
        else:
            await ctx.send("You need to be in a voice channel first, silly baka!")

async def play_next(ctx):
    if ctx.voice_client is None:
        return
    
    next_song = music_queue.get_next()
    if next_song:
        try:
            # Create audio source
            audio_source = discord.FFmpegPCMAudio(next_song['url'], **FFMPEG_OPTIONS)
            
            # Play the audio and set up the callback for when it finishes
            ctx.voice_client.play(audio_source, after=lambda e: asyncio.run_coroutine_threadsafe(
                play_next(ctx), bot.loop).result() if e is None else print(f'Player error: {e}'))
            
            await ctx.send(f'Now playing: {next_song["title"]}')
        
        except Exception as e:
            await ctx.send(f'An error occurred while playing {next_song["title"]}: {str(e)}')
            await play_next(ctx)  # Skip to next song if current one fails
    else:
        await ctx.send("Queue is empty!")

# Run bot with token
bot.run(TOKEN)