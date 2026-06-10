import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import yt_dlp
from helpers import rust_embed

SCOOBY_BROWN = discord.Color(0xA0522D)
YTDL_OPTIONS = {'format':'bestaudio/best','noplaylist':True,'quiet':True,'no_warnings':True,'default_search':'ytsearch','source_address':'0.0.0.0'}
FFMPEG_OPTIONS = {'before_options':'-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5','options':'-vn'}
queues = {}

def get_queue(guild_id):
    if guild_id not in queues:
        queues[guild_id] = []
    return queues[guild_id]

async def search_ytdl(query):
    loop = asyncio.get_event_loop()
    ytdl = yt_dlp.YoutubeDL(YTDL_OPTIONS)
    if not query.startswith('http'):
        query = f'ytsearch:{query}'
    data = await loop.run_in_executor(None, lambda: ytdl.extract_info(query, download=False))
    if 'entries' in data:
        data = data['entries'][0]
    return {'url':data['url'],'title':data.get('title','Desconhecido'),'duration':data.get('duration',0),'thumbnail':data.get('thumbnail','')}

def play_next(guild_id, vc):
    queue = get_queue(guild_id)
    if queue:
        track = queue.pop(0)
        source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(track['url'], **FFMPEG_OPTIONS), volume=0.5)
        vc.play(source, after=lambda e: play_next(guild_id, vc))

class MusicCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="m", description="Toca musica do YouTube, TikTok, Spotify e mais!")
    @app_commands.describe(query="Link ou nome da musica")
    async def play(self, interaction: discord.Interaction, query: str):
        await interaction.response.defer()
        if not interaction.user.voice:
            await interaction.followup.send("🚫 Entra numa sala de voz primeiro!", ephemeral=True)
            return
        channel = interaction.user.voice.channel
        vc = interaction.guild.voice_client
        if vc is None:
            vc = await channel.connect()
        elif vc.channel != channel:
            await vc.move_to(channel)
        try:
            track = await search_ytdl(query)
        except Exception as e:
            await interaction.followup.send(f"⚠️ Erro: {e}", ephemeral=True)
            return
        queue = get_queue(interaction.guild.id)
        if vc.is_playing():
            queue.append(track)
            embed = rust_embed("🎵 Adicionado à fila", f"**{track['title']}**\nPosição: #{len(queue)}", color=SCOOBY_BROWN)
        else:
            source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(track['url'], **FFMPEG_OPTIONS), volume=0.5)
            vc.play(source, after=lambda e: play_next(interaction.guild.id, vc))
            mins, secs = divmod(track['duration'], 60)
            embed = rust_embed("🎶 Tocando agora", f"**{track['title']}**\n⏱️ `{mins:02d}:{secs:02d}`", color=SCOOBY_BROWN)
            if track['thumbnail']:
                embed.set_thumbnail(url=track['thumbnail'])
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="mpause", description="Pausa a musica")
    async def pause(self, interaction: discord.Interaction):
        vc = interaction.guild.voice_client
        if vc and vc.is_playing():
            vc.pause()
            await interaction.response.send_message("⏸️ Pausado!")
        else:
            await interaction.response.send_message("Nenhuma musica tocando.", ephemeral=True)

    @app_commands.command(name="mresume", description="Retoma a musica")
    async def resume(self, interaction: discord.Interaction):
        vc = interaction.guild.voice_client
        if vc and vc.is_paused():
            vc.resume()
            await interaction.response.send_message("▶️ Retomado!")
        else:
            await interaction.response.send_message("Nada pausado.", ephemeral=True)

    @app_commands.command(name="mskip", description="Pula para a proxima musica")
    async def skip(self, interaction: discord.Interaction):
        vc = interaction.guild.voice_client
        if vc and vc.is_playing():
            vc.stop()
            await interaction.response.send_message("⏭️ Pulado!")
        else:
            await interaction.response.send_message("Nenhuma musica tocando.", ephemeral=True)

    @app_commands.command(name="mstop", description="Para a musica e sai da sala")
    async def stop(self, interaction: discord.Interaction):
        vc = interaction.guild.voice_client
        if vc:
            queues[interaction.guild.id] = []
            await vc.disconnect()
            await interaction.response.send_message("⏹️ Parado!")
        else:
            await interaction.response.send_message("Não estou em nenhuma sala.", ephemeral=True)

    @app_commands.command(name="mfila", description="Mostra a fila de musicas")
    async def queue_cmd(self, interaction: discord.Interaction):
        queue = get_queue(interaction.guild.id)
        if not queue:
            await interaction.response.send_message("📭 Fila vazia!", ephemeral=True)
            return
        desc = "\n".join([f"`{i+1}.` {t['title']}" for i, t in enumerate(queue[:10])])
        embed = rust_embed(f"🎵 Fila ({len(queue)} musicas)", desc, color=SCOOBY_BROWN)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="mvolume", description="Ajusta o volume 0-100")
    @app_commands.describe(volume="Volume de 0 a 100")
    async def volume(self, interaction: discord.Interaction, volume: int):
        vc = interaction.guild.voice_client
        if vc and vc.source:
            vc.source.volume = max(0, min(volume, 100)) / 100
            await interaction.response.send_message(f"🔊 Volume: {volume}%")
        else:
            await interaction.response.send_message("Nenhuma musica tocando.", ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(MusicCog(bot))
