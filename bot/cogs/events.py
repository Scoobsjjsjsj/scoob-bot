import asyncio
import random
from datetime import datetime, timezone
from typing import Literal
import discord
from discord import app_commands
from discord.ext import commands

import data
from helpers import rust_embed, RUST_COLOR, RUST_RED, RUST_ORANGE, RUST_GOLD, has_oficial_plus

RUST_QUOTES = [
    "A única garantia no Rust é que alguém vai te matar quando você menos esperar.",
    "Não existe amigo no Rust. Só existe... ainda não inimigo.",
    "Nakeds têm apenas rochas. E ainda assim são perigosos.",
    "O melhor momento para construir uma base boa foi ontem. O segundo melhor é agora.",
    "Nunca farm solo perto de um monumento. Aprendi da forma mais difícil.",
    "A rocha mais poderosa do Rust é aquela na sua mão no início do jogo.",
    "Rust: onde as amizades são testadas por C4.",
    "Você construiu por 6 horas. Eles raidaram em 30 minutos. É Rust.",
    "O PVP é temporário. A base de HQM é eterna. Ou até o próximo wipe.",
    "Confia no teu clan. Mas guarda sua senha do toolcupboard só pra você.",
]

RUST_TIPS = [
    "💡 Sempre coloque um **código de tela de bloqueio** nas suas portas!",
    "💡 Use **Mixing Table** para fazer pólvora mais rápido que a Campfire.",
    "💡 **Recycler** nos monumentos: transforme componentes em recursos valiosos.",
    "💡 Coloque **turrets** viradas para dentro da base também — inimigos podem entrar.",
    "💡 **Low Grade Fuel** = Animal Fat × 3 + Cloth × 1. Simples e essencial.",
    "💡 Sempre carregue **bandagens** no inventário. Cura rápida pode salvar sua vida.",
    "💡 **Sleeping bags** espalhados pelo mapa = respawn estratégico em raids.",
    "💡 Use **Jackhammer** para minerar 3× mais rápido que o pickaxe.",
    "💡 **Chinook** traz caixotes vermelhos. Vale defender o drop!",
    "💡 **Auto Turret** com HV Pistol Ammo = mais balas por recarga.",
    "💡 Nunca log off sem **comer** — você perde comida ao ficar offline.",
    "💡 **Stone walls** são mais eficientes que madeira logo no início do wipe.",
    "💡 **Tech Trash** sai do computador reciclado. Guarde para BPs de T3.",
    "💡 Coloque **landmines** nos ramps de acesso à sua base.",
]


class EventsCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ── /tags (reaction-role messages) ───────────────────────────────────────

    @app_commands.command(name="tags", description="Posta mensagem de reaction-roles no canal.")
    @app_commands.checks.has_permissions(manage_roles=True)
    async def tags(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🏷️ Role Tags",
            description=(
                "Reaja com um emoji para receber o cargo correspondente.\n"
                "Remova a reação para perder o cargo.\n\n"
                "*(Cargos devem existir com o nome igual ao emoji.)*"
            ),
            color=RUST_COLOR,
        )
        embed.set_footer(text="🦀 Rust Clan Bot v2.0")
        await interaction.response.send_message("Mensagem de tags criada abaixo.", ephemeral=True)
        msg = await interaction.channel.send(embed=embed)
        data.tag_messages.add(msg.id)

    @tags.error
    async def tags_error(self, interaction: discord.Interaction, error):
        await interaction.response.send_message("❌ Você precisa de permissão **Gerenciar Cargos**.", ephemeral=True)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        if payload.message_id not in data.tag_messages:
            return
        if payload.user_id == self.bot.user.id:
            return
        guild = self.bot.get_guild(payload.guild_id)
        if not guild:
            return
        member = guild.get_member(payload.user_id)
        if not member:
            return
        role = discord.utils.get(guild.roles, name=payload.emoji.name)
        if role:
            try:
                await member.add_roles(role, reason="Tags reaction role")
            except discord.Forbidden:
                pass

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):
        if payload.message_id not in data.tag_messages:
            return
        guild = self.bot.get_guild(payload.guild_id)
        if not guild:
            return
        member = guild.get_member(payload.user_id)
        if not member:
            return
        role = discord.utils.get(guild.roles, name=payload.emoji.name)
        if role:
            try:
                await member.remove_roles(role, reason="Tags reaction role removed")
            except discord.Forbidden:
                pass

    # ── /evento ───────────────────────────────────────────────────────────────

    @app_commands.command(name="evento", description="Cria um evento com sorteio automático de vencedor.")
    @app_commands.describe(name="Nome do evento", prize="Prêmio", duration="Duração — ex: 5m, 2h")
    @app_commands.checks.has_permissions(mention_everyone=True)
    async def evento(self, interaction: discord.Interaction, name: str, prize: str, duration: str):
        unit_map = {"m": 60, "h": 3600, "s": 1}
        try:
            secs = int(duration[:-1]) * unit_map[duration[-1].lower()]
        except (ValueError, KeyError):
            await interaction.response.send_message("❌ Duração inválida. Use `5m`, `2h`, etc.", ephemeral=True)
            return

        end_ts = int(datetime.now(timezone.utc).timestamp()) + secs
        embed = rust_embed(
            f"🎉 EVENTO — {name}",
            f"**@everyone — Participe do evento!**\n\nReaja com 🎉 para participar!",
            color=RUST_GOLD,
        )
        embed.add_field(name="🏆 Prêmio",  value=prize,               inline=True)
        embed.add_field(name="⏰ Termina", value=f"<t:{end_ts}:R>",   inline=True)
        embed.add_field(name="🎟️ Participe", value="Reaja com 🎉",  inline=True)
        embed.set_footer(text="🦀 Boa sorte a todos! | Rust Clan Bot v2.0")

        await interaction.response.send_message(
            "@everyone", embed=embed,
            allowed_mentions=discord.AllowedMentions(everyone=True),
        )
        msg = await interaction.original_response()
        await msg.add_reaction("🎉")

        entry = {
            "name": name, "prize": prize, "end_ts": end_ts,
            "msg_id": msg.id, "channel_id": interaction.channel_id, "done": False,
        }
        data.active_events.setdefault(interaction.guild_id, []).append(entry)

        # Schedule draw
        self.bot.loop.create_task(
            self._draw_winner(interaction.guild_id, interaction.channel_id, msg.id, name, prize, secs)
        )

    @evento.error
    async def evento_error(self, interaction: discord.Interaction, error):
        await interaction.response.send_message("❌ Você precisa de permissão **Mencionar @everyone**.", ephemeral=True)

    async def _draw_winner(self, guild_id, channel_id, msg_id, name, prize, delay):
        await asyncio.sleep(delay)
        guild   = self.bot.get_guild(guild_id)
        channel = guild.get_channel(channel_id) if guild else None
        if not channel:
            return
        try:
            msg = await channel.fetch_message(msg_id)
            reaction = discord.utils.get(msg.reactions, emoji="🎉")
            if not reaction:
                await channel.send("❌ Ninguém participou do evento.")
                return
            users = [u async for u in reaction.users() if not u.bot]
            if not users:
                await channel.send("❌ Nenhum participante válido.")
                return
            winner = random.choice(users)
            embed = rust_embed(
                "🏆 VENCEDOR DO EVENTO!",
                f"🎉 Parabéns, {winner.mention}!\n\n**Você ganhou: {prize}**",
                color=RUST_GOLD,
            )
            embed.add_field(name="🎰 Evento",   value=name,                         inline=True)
            embed.add_field(name="👥 Participantes", value=str(len(users)),          inline=True)
            await channel.send(content=winner.mention, embed=embed,
                               allowed_mentions=discord.AllowedMentions(users=True))
            # Mark done
            for ev in data.active_events.get(guild_id, []):
                if ev["msg_id"] == msg_id:
                    ev["done"] = True
        except (discord.NotFound, discord.Forbidden):
            pass

    # ── /quote ────────────────────────────────────────────────────────────────

    @app_commands.command(name="quote", description="Citação motivacional aleatória sobre Rust.")
    async def quote(self, interaction: discord.Interaction):
        embed = rust_embed("💬 Citação Rust", f"*\"{random.choice(RUST_QUOTES)}\"*", color=RUST_COLOR)
        await interaction.response.send_message(embed=embed)

    # ── /tip ──────────────────────────────────────────────────────────────────

    @app_commands.command(name="tip", description="Dica aleatória de Rust.")
    async def tip(self, interaction: discord.Interaction):
        embed = rust_embed("💡 Dica de Rust", random.choice(RUST_TIPS), color=RUST_ORANGE)
        await interaction.response.send_message(embed=embed)

    # ── /agenda ───────────────────────────────────────────────────────────────

    @app_commands.command(name="agenda", description="Mostra os eventos agendados do clan.")
    async def agenda(self, interaction: discord.Interaction):
        events = data.agenda_events.get(interaction.guild_id, [])
        embed = rust_embed("📅 Agenda do Clan", color=RUST_COLOR)
        if not events:
            embed.description = "*Nenhum evento agendado. Use `/addagenda` para adicionar.*"
        else:
            for i, ev in enumerate(events[-10:], 1):
                val = f"📅 `{ev['date']}` às `{ev['time']}`"
                if ev.get("note"):
                    val += f"\n📝 {ev['note']}"
                val += f"\n👤 *{ev['added_by']}*"
                embed.add_field(name=f"{i}. {ev['title']}", value=val, inline=False)
        await interaction.response.send_message(embed=embed)

    # ── /addagenda ────────────────────────────────────────────────────────────

    @app_commands.command(name="addagenda", description="Adiciona um evento à agenda (Oficial+).")
    @app_commands.describe(title="Título do evento", date="Data DD/MM/YYYY", time="Hora HH:MM", note="Observações")
    async def addagenda(self, interaction: discord.Interaction,
                        title: str, date: str, time: str, note: str = ""):
        if not has_oficial_plus(interaction.user) and not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Você precisa ser **Oficial ou superior**.", ephemeral=True)
            return
        entry = {"title": title, "date": date, "time": time, "note": note,
                 "added_by": interaction.user.display_name}
        data.agenda_events.setdefault(interaction.guild_id, []).append(entry)
        embed = rust_embed("✅ Evento Adicionado",
                           f"**{title}** — {date} às {time}", color=RUST_ORANGE)
        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(EventsCog(bot))
