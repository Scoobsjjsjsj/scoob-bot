import asyncio
from datetime import datetime, timezone
import discord
from discord import app_commands
from discord.ext import commands

import data
from helpers import rust_embed, RUST_COLOR, RUST_ORANGE, RUST_RED


class MeetingCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    meeting = app_commands.Group(name="meeting", description="Sistema de reuniões do clan.")

    @meeting.command(name="schedule", description="Agenda uma reunião com @everyone ping.")
    @app_commands.describe(topic="Assunto da reunião", time="Horário — ex: Sábado 20:00 BRT")
    @app_commands.checks.has_permissions(mention_everyone=True)
    async def schedule(self, interaction: discord.Interaction, topic: str, time: str):
        embed = rust_embed(
            "📅 REUNIÃO AGENDADA",
            f"@everyone — Uma reunião foi marcada!\n\n**Reaja ✅ para confirmar presença ou ❌ para recusar.**",
            color=RUST_ORANGE,
        )
        embed.add_field(name="📌 Assunto",       value=topic, inline=False)
        embed.add_field(name="🕐 Horário",        value=f"`{time}`", inline=True)
        embed.add_field(name="👤 Convocado por",  value=interaction.user.mention, inline=True)
        embed.set_footer(text="🦀 Rust Clan Bot v2.0 — Reaja para confirmar presença")

        await interaction.response.send_message(
            "@everyone", embed=embed,
            allowed_mentions=discord.AllowedMentions(everyone=True),
        )
        msg = await interaction.original_response()
        await msg.add_reaction("✅")
        await msg.add_reaction("❌")

        entry = {
            "topic": topic, "time_str": time,
            "msg_id": msg.id, "channel_id": interaction.channel_id,
            "confirmed": [], "declined": [],
            "status": "scheduled",
            "created_by": interaction.user.id,
            "created_at": datetime.now(timezone.utc),
        }
        data.meetings.setdefault(interaction.guild_id, []).append(entry)

    @schedule.error
    async def schedule_error(self, interaction: discord.Interaction, error):
        await interaction.response.send_message("❌ Você precisa de permissão **Mencionar @everyone**.", ephemeral=True)

    @meeting.command(name="start", description="Inicia a reunião e pinga os confirmados via DM + canal.")
    @app_commands.checks.has_permissions(mention_everyone=True)
    async def start(self, interaction: discord.Interaction):
        guild_meetings = data.meetings.get(interaction.guild_id, [])
        scheduled = [m for m in guild_meetings if m["status"] == "scheduled"]
        if not scheduled:
            await interaction.response.send_message("❌ Nenhuma reunião agendada.", ephemeral=True)
            return

        meeting = scheduled[0]
        meeting["status"] = "active"
        meeting["started_at"] = datetime.now(timezone.utc)

        confirmed_members = []
        for mid in meeting["confirmed"]:
            member = interaction.guild.get_member(mid)
            if member:
                confirmed_members.append(member)

        embed = rust_embed(
            "🚨 REUNIÃO INICIANDO AGORA!",
            f"**{meeting['topic']}**\n\nTodos na call imediatamente!",
            color=RUST_RED,
        )
        embed.add_field(name="✅ Confirmados", value=str(len(confirmed_members)), inline=True)

        await interaction.response.send_message(
            "@everyone", embed=embed,
            allowed_mentions=discord.AllowedMentions(everyone=True),
        )

        # DM confirmed members
        for member in confirmed_members:
            try:
                await member.send(embed=embed)
            except discord.Forbidden:
                pass
            await asyncio.sleep(0.3)

    @meeting.command(name="end", description="Encerra a reunião ativa e posta um resumo.")
    @app_commands.checks.has_permissions(mention_everyone=True)
    async def end(self, interaction: discord.Interaction):
        guild_meetings = data.meetings.get(interaction.guild_id, [])
        active = [m for m in guild_meetings if m["status"] == "active"]
        if not active:
            await interaction.response.send_message("❌ Nenhuma reunião ativa.", ephemeral=True)
            return

        meeting = active[0]
        meeting["status"] = "ended"
        meeting["ended_at"] = datetime.now(timezone.utc)

        started = meeting.get("started_at", meeting["created_at"])
        duration = int((meeting["ended_at"] - started).total_seconds() // 60)

        confirmed_names = []
        for mid in meeting["confirmed"]:
            member = interaction.guild.get_member(mid)
            confirmed_names.append(member.display_name if member else f"ID:{mid}")

        embed = rust_embed(
            "✅ Reunião Encerrada",
            f"**{meeting['topic']}** foi encerrada.",
            color=RUST_ORANGE,
        )
        embed.add_field(name="⏱️ Duração",       value=f"{duration} minutos",               inline=True)
        embed.add_field(name="✅ Presentes",       value=str(len(confirmed_names)) or "0",    inline=True)
        if confirmed_names:
            embed.add_field(name="👥 Lista",
                            value="\n".join(f"• {n}" for n in confirmed_names[:20]),
                            inline=False)
        await interaction.response.send_message(embed=embed)

    @meeting.command(name="list", description="Lista todas as reuniões agendadas e ativas.")
    async def list_meetings(self, interaction: discord.Interaction):
        guild_meetings = [m for m in data.meetings.get(interaction.guild_id, [])
                          if m["status"] in ("scheduled", "active")]
        embed = rust_embed("📅 Reuniões", color=RUST_COLOR)
        if not guild_meetings:
            embed.description = "*Nenhuma reunião agendada.*"
        else:
            for m in guild_meetings:
                status_icon = "🟢 Ativa" if m["status"] == "active" else "🕐 Agendada"
                embed.add_field(
                    name=f"{status_icon} — {m['topic']}",
                    value=f"⏰ `{m['time_str']}` · ✅ {len(m['confirmed'])} confirmados",
                    inline=False,
                )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @meeting.command(name="cancel", description="Cancela a próxima reunião e notifica confirmados.")
    @app_commands.checks.has_permissions(mention_everyone=True)
    async def cancel(self, interaction: discord.Interaction):
        guild_meetings = data.meetings.get(interaction.guild_id, [])
        scheduled = [m for m in guild_meetings if m["status"] == "scheduled"]
        if not scheduled:
            await interaction.response.send_message("❌ Nenhuma reunião agendada.", ephemeral=True)
            return

        meeting = scheduled[0]
        meeting["status"] = "cancelled"

        embed = rust_embed(
            "❌ Reunião Cancelada",
            f"A reunião **{meeting['topic']}** foi cancelada.",
            color=RUST_RED,
        )
        await interaction.response.send_message(embed=embed)

        for mid in meeting["confirmed"]:
            member = interaction.guild.get_member(mid)
            if member:
                try:
                    await member.send(embed=embed)
                except discord.Forbidden:
                    pass
                await asyncio.sleep(0.3)

    # ── Track reactions for meetings ──────────────────────────────────────────

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        if payload.user_id == self.bot.user.id:
            return
        guild_meetings = data.meetings.get(payload.guild_id, [])
        for m in guild_meetings:
            if m["msg_id"] != payload.message_id or m["status"] != "scheduled":
                continue
            uid = payload.user_id
            if str(payload.emoji) == "✅":
                if uid not in m["confirmed"]:
                    m["confirmed"].append(uid)
                if uid in m["declined"]:
                    m["declined"].remove(uid)
            elif str(payload.emoji) == "❌":
                if uid not in m["declined"]:
                    m["declined"].append(uid)
                if uid in m["confirmed"]:
                    m["confirmed"].remove(uid)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):
        guild_meetings = data.meetings.get(payload.guild_id, [])
        for m in guild_meetings:
            if m["msg_id"] != payload.message_id:
                continue
            uid = payload.user_id
            if str(payload.emoji) == "✅" and uid in m["confirmed"]:
                m["confirmed"].remove(uid)
            elif str(payload.emoji) == "❌" and uid in m["declined"]:
                m["declined"].remove(uid)


async def setup(bot: commands.Bot):
    await bot.add_cog(MeetingCog(bot))
