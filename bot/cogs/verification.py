import asyncio
import discord
from discord import app_commands
from discord.ext import commands

import data
from helpers import rust_embed, RUST_ORANGE, RUST_RED, build_nick


class VerificationCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ── on_member_join ────────────────────────────────────────────────────────

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        channel_id = data.verification_channels.get(member.guild.id)
        channel = member.guild.get_channel(channel_id) if channel_id else None

        # DM the new member
        dm_embed = rust_embed(
            f"👋 Bem-vindo ao {member.guild.name}!",
            f"Para acessar o servidor, vá até o canal de verificação e reaja com ✅ na sua mensagem.\n\n"
            f"Você receberá o cargo **🆕 Recruta** e ganhará acesso ao servidor.",
            color=RUST_ORANGE,
        )
        dm_embed.set_thumbnail(url=member.guild.icon.url if member.guild.icon else None)
        try:
            await member.send(embed=dm_embed)
        except discord.Forbidden:
            pass

        # Post in verification channel
        if channel:
            embed = rust_embed(
                "🔐 Verificação Necessária",
                f"{member.mention} entrou no servidor!\n\n"
                f"**Reaja com ✅ abaixo** para se verificar e ganhar acesso ao servidor.",
                color=RUST_ORANGE,
            )
            embed.add_field(
                name="📋 Instruções",
                value="1️⃣ Reaja com ✅ nesta mensagem\n"
                      "2️⃣ Você receberá o cargo **🆕 Recruta**\n"
                      "3️⃣ Leia as regras em `#regras`",
                inline=False,
            )
            embed.set_thumbnail(url=member.display_avatar.url)
            embed.set_footer(text=f"ID: {member.id} | Rust Clan Bot v2.0")
            msg = await channel.send(embed=embed)
            await msg.add_reaction("✅")
            data.pending_verifications.setdefault(member.guild.id, {})[msg.id] = member.id

    # ── Reaction handler ──────────────────────────────────────────────────────

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        if str(payload.emoji) != "✅":
            return
        guild_verifications = data.pending_verifications.get(payload.guild_id, {})
        if payload.message_id not in guild_verifications:
            return
        expected_member_id = guild_verifications[payload.message_id]
        if payload.user_id != expected_member_id:
            return

        guild = self.bot.get_guild(payload.guild_id)
        if not guild:
            return
        member = guild.get_member(payload.user_id)
        if not member:
            return

        recruta = discord.utils.get(guild.roles, name="🆕 Recruta")
        if recruta:
            try:
                await member.add_roles(recruta, reason="Verificação ✅")
            except discord.Forbidden:
                pass

        # Update nickname if autoname is enabled
        if guild.id in data.autoname_guilds:
            try:
                await member.edit(nick=build_nick(member))
            except discord.Forbidden:
                pass

        # Remove from pending and clean up message
        guild_verifications.pop(payload.message_id, None)

        channel = guild.get_channel(payload.channel_id)
        if channel:
            try:
                msg = await channel.fetch_message(payload.message_id)
                success_embed = rust_embed(
                    "✅ Verificado!",
                    f"{member.mention} foi verificado e recebeu o cargo **🆕 Recruta**!",
                    color=discord.Color.green(),
                )
                await msg.edit(embed=success_embed)
                await msg.clear_reactions()
            except (discord.NotFound, discord.Forbidden):
                pass

        try:
            welcome_embed = rust_embed(
                "✅ Verificação Concluída!",
                f"Bem-vindo, {member.mention}! Você agora tem acesso ao servidor.\n\n"
                f"Leia as regras e aproveite! 🦀",
                color=discord.Color.green(),
            )
            await member.send(embed=welcome_embed)
        except discord.Forbidden:
            pass

    # ── /setverification ──────────────────────────────────────────────────────

    @app_commands.command(name="setverification", description="Define o canal de verificação para novos membros.")
    @app_commands.describe(channel="Canal onde a mensagem de verificação será enviada")
    @app_commands.checks.has_permissions(administrator=True)
    async def setverification(self, interaction: discord.Interaction, channel: discord.TextChannel):
        data.verification_channels[interaction.guild_id] = channel.id
        embed = rust_embed(
            "✅ Canal de Verificação Definido",
            f"Novos membros receberão mensagem de verificação em {channel.mention}.",
            color=RUST_ORANGE,
        )
        await interaction.response.send_message(embed=embed)

    @setverification.error
    async def setverification_error(self, interaction: discord.Interaction, error):
        await interaction.response.send_message("❌ Você precisa de permissão de **Administrador**.", ephemeral=True)

    # ── /unverify ─────────────────────────────────────────────────────────────

    @app_commands.command(name="unverify", description="Remove a verificação de um membro.")
    @app_commands.describe(user="Membro a desverificar")
    @app_commands.checks.has_permissions(administrator=True)
    async def unverify(self, interaction: discord.Interaction, user: discord.Member):
        recruta = discord.utils.get(interaction.guild.roles, name="🆕 Recruta")
        removed = []
        if recruta and recruta in user.roles:
            await user.remove_roles(recruta, reason=f"Unverify por {interaction.user}")
            removed.append(recruta.name)

        embed = rust_embed(
            "🔒 Membro Desverificado",
            f"{user.mention} perdeu o acesso ao servidor." if removed else f"{user.mention} não estava verificado.",
            color=RUST_RED,
        )
        await interaction.response.send_message(embed=embed)

    @unverify.error
    async def unverify_error(self, interaction: discord.Interaction, error):
        await interaction.response.send_message("❌ Você precisa de permissão de **Administrador**.", ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(VerificationCog(bot))
