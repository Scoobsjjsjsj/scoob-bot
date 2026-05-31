import discord
from discord import app_commands
from discord.ext import commands
import aiohttp

from emoji_utils import CLAN_EMOJI_DEFS, create_emojis
import data
from helpers import rust_embed, RUST_COLOR, RUST_RED, RUST_ORANGE


class EmojisCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    emoji_group = app_commands.Group(name="emoji", description="Gerenciamento de emojis do servidor.")

    # ── /setupemojis ──────────────────────────────────────────────────────────

    @app_commands.command(name="setupemojis",
                          description="Gera e sobe todos os emojis do clan com gradiente e texto.")
    @app_commands.checks.has_permissions(manage_emojis=True)
    async def setupemojis(self, interaction: discord.Interaction):
        await interaction.response.defer()
        existing = {e.name for e in interaction.guild.emojis}

        try:
            created, skipped, failed = await create_emojis(interaction.guild, existing)
        except discord.Forbidden:
            await interaction.followup.send("❌ Sem permissão para criar emojis.", ephemeral=True)
            return

        embed = rust_embed("✅ Emojis do Clan Criados!", color=RUST_ORANGE)
        embed.description = (
            f"**{len(created)}** criados · "
            f"**{len(skipped)}** já existiam · "
            f"**{len(failed)}** falharam\n"
        )
        if created:
            embed.add_field(
                name="✅ Criados",
                value=" ".join(str(e) for e in created) or "—",
                inline=False,
            )
        if skipped:
            embed.add_field(
                name="⏭️ Já existiam",
                value=" ".join(f"`:{n}:`" for n in skipped),
                inline=False,
            )
        if failed:
            embed.add_field(name="❌ Falhas", value="\n".join(failed[:5]), inline=False)

        embed.set_footer(text="🦀 Use /emojitest para ver todos | Rust Clan Bot v2.0")
        await interaction.followup.send(embed=embed)

    @setupemojis.error
    async def setupemojis_error(self, interaction: discord.Interaction, error):
        await interaction.response.send_message(
            "❌ Você precisa de permissão **Gerenciar Emojis**.", ephemeral=True
        )

    # ── /emoji add ────────────────────────────────────────────────────────────

    @emoji_group.command(name="add", description="Adiciona um emoji de uma URL (máx 256 KB).")
    @app_commands.describe(name="Nome do emoji", image_url="URL da imagem PNG/JPG")
    @app_commands.checks.has_permissions(manage_emojis=True)
    async def emoji_add(self, interaction: discord.Interaction, name: str, image_url: str):
        await interaction.response.defer(ephemeral=True)
        name = name.lower().replace(" ", "_").replace("-", "_")
        try:
            async with aiohttp.ClientSession() as sess:
                async with sess.get(image_url, timeout=aiohttp.ClientTimeout(total=15)) as r:
                    if r.status != 200:
                        await interaction.followup.send(f"❌ HTTP {r.status} ao baixar imagem.", ephemeral=True)
                        return
                    raw = await r.read()
            if len(raw) > 256_000:
                await interaction.followup.send("❌ Imagem muito grande (máx 256 KB).", ephemeral=True)
                return
            emoji = await interaction.guild.create_custom_emoji(
                name=name, image=raw, reason=f"/emoji add por {interaction.user}"
            )
            await interaction.followup.send(
                embed=rust_embed("✅ Emoji Adicionado", f"{emoji} `:{name}:` criado!", color=RUST_ORANGE),
                ephemeral=True,
            )
        except discord.Forbidden:
            await interaction.followup.send("❌ Sem permissão para criar emojis.", ephemeral=True)
        except aiohttp.ClientError:
            await interaction.followup.send("❌ Falha ao baixar imagem. Verifique a URL.", ephemeral=True)

    @emoji_add.error
    async def emoji_add_error(self, interaction: discord.Interaction, error):
        await interaction.response.send_message("❌ Sem permissão **Gerenciar Emojis**.", ephemeral=True)

    # ── /emoji remove ─────────────────────────────────────────────────────────

    @emoji_group.command(name="remove", description="Remove um emoji do servidor pelo nome.")
    @app_commands.describe(name="Nome do emoji a remover")
    @app_commands.checks.has_permissions(manage_emojis=True)
    async def emoji_remove(self, interaction: discord.Interaction, name: str):
        emoji = discord.utils.get(interaction.guild.emojis, name=name)
        if not emoji:
            await interaction.response.send_message(f"❌ Emoji `:{name}:` não encontrado.", ephemeral=True)
            return
        await emoji.delete(reason=f"/emoji remove por {interaction.user}")
        await interaction.response.send_message(
            embed=rust_embed("🗑️ Emoji Removido", f"Emoji `:{name}:` removido.", color=RUST_RED),
            ephemeral=True,
        )

    @emoji_remove.error
    async def emoji_remove_error(self, interaction: discord.Interaction, error):
        await interaction.response.send_message("❌ Sem permissão **Gerenciar Emojis**.", ephemeral=True)

    # ── /emoji list ───────────────────────────────────────────────────────────

    @emoji_group.command(name="list", description="Lista todos os emojis do servidor.")
    async def emoji_list(self, interaction: discord.Interaction):
        emojis = interaction.guild.emojis
        embed  = rust_embed(
            f"😀 Emojis — {interaction.guild.name}",
            f"Total: **{len(emojis)}/{interaction.guild.emoji_limit}**",
            color=RUST_COLOR,
        )
        if not emojis:
            embed.description = "*Nenhum emoji personalizado.*"
        else:
            for i, chunk in enumerate([emojis[j:j+20] for j in range(0, min(len(emojis), 100), 20)], 1):
                embed.add_field(name=f"Emojis {i}", value=" ".join(str(e) for e in chunk), inline=False)
        await interaction.response.send_message(embed=embed)

    # ── /emojitest ────────────────────────────────────────────────────────────

    @app_commands.command(name="emojitest", description="Mostra todos os emojis do clan como referência.")
    async def emojitest(self, interaction: discord.Interaction):
        embed = rust_embed("🎨 Emojis do Clan — Referência", color=RUST_COLOR)
        lines = []
        clan_names = {d[0] for d in CLAN_EMOJI_DEFS}
        for name, label, _, _, fallback in CLAN_EMOJI_DEFS:
            server_emoji = discord.utils.get(interaction.guild.emojis, name=name)
            display = str(server_emoji) if server_emoji else fallback
            lines.append(f"{display} `:{name}:` — **{label}**")
        embed.description = "\n".join(lines)
        other = [e for e in interaction.guild.emojis if e.name not in clan_names]
        if other:
            embed.add_field(
                name="📦 Outros Emojis",
                value=" ".join(str(e) for e in other[:30]),
                inline=False,
            )
        embed.set_footer(text="🦀 Use /setupemojis para criar os emojis do clan | Rust Clan Bot v2.0")
        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(EmojisCog(bot))
