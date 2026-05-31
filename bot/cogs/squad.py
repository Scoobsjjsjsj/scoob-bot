import asyncio
from datetime import datetime, timezone
from typing import Literal
import discord
from discord import app_commands
from discord.ext import commands

import data
from helpers import (rust_embed, RUST_COLOR, RUST_RED, RUST_ORANGE, RUST_GOLD,
                     has_oficial_plus, CLAN_ROLE_DEFS)

SQUAD_ROLE_EMOJIS = {
    "Raider": "💣", "Farmer": "🌾", "Builder": "🏗️",
    "Scout": "🔍", "Lider": "👑", "Roamer": "🌿",
    "PVP": "🎯", "Eletricista": "⚡", "BotFarmer": "🤖",
}
SQUAD_LITERAL = Literal["Raider", "Farmer", "Builder", "Scout", "Lider",
                         "Roamer", "PVP", "Eletricista", "BotFarmer"]


class SquadCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ── /squad ────────────────────────────────────────────────────────────────

    @app_commands.command(name="squad", description="Atribui uma função de squad a um membro.")
    @app_commands.describe(user="Membro", role="Função no squad")
    async def squad(self, interaction: discord.Interaction,
                    user: discord.Member, role: SQUAD_LITERAL):
        if not has_oficial_plus(interaction.user) and not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Você precisa ser **Oficial ou superior**.", ephemeral=True)
            return
        data.squad_assignments.setdefault(interaction.guild_id, {})[user.id] = role
        emoji = SQUAD_ROLE_EMOJIS.get(role, "🎖️")
        embed = rust_embed("🎖️ Squad Atualizado",
                           f"{user.mention} → **{emoji} {role}**", color=RUST_ORANGE)
        await interaction.response.send_message(embed=embed)

    # ── /raid ─────────────────────────────────────────────────────────────────

    @app_commands.command(name="raid", description="Anuncia um raid com @everyone ping.")
    @app_commands.describe(target="Nome/clan alvo", grid="Grid no mapa — ex: E12")
    @app_commands.checks.has_permissions(mention_everyone=True)
    async def raid(self, interaction: discord.Interaction, target: str, grid: str):
        now_ts = int(datetime.now(timezone.utc).timestamp())
        embed = rust_embed(
            "🚨 RAID INICIADO — @everyone",
            "**Todos na call AGORA! Prepara os foguetes!** 💣🚀",
            color=RUST_RED,
        )
        embed.add_field(name="🎯 Alvo",          value=f"`{target}`",           inline=True)
        embed.add_field(name="📍 Grid",           value=f"`{grid.upper()}`",    inline=True)
        embed.add_field(name="👤 Iniciado por",   value=interaction.user.mention, inline=True)
        embed.add_field(name="⏰ Horário",         value=f"<t:{now_ts}:T>",      inline=True)
        embed.set_footer(text="💣 Bora raidar! | Rust Clan Bot v2.0")

        await interaction.response.send_message(
            "@everyone", embed=embed,
            allowed_mentions=discord.AllowedMentions(everyone=True),
        )
        data.raid_log.setdefault(interaction.guild_id, []).append({
            "target": target, "grid": grid.upper(),
            "caller_id": interaction.user.id,
            "ts": datetime.now(timezone.utc),
        })

    @raid.error
    async def raid_error(self, interaction: discord.Interaction, error):
        await interaction.response.send_message("❌ Você precisa de permissão **Mencionar @everyone**.", ephemeral=True)

    # ── /notify ───────────────────────────────────────────────────────────────

    @app_commands.command(name="notify", description="Envia DM para TODOS os membros + @everyone no canal.")
    @app_commands.describe(message="Mensagem urgente")
    @app_commands.checks.has_permissions(administrator=True)
    async def notify(self, interaction: discord.Interaction, message: str):
        await interaction.response.defer()
        embed = rust_embed(
            "🚨 NOTIFICAÇÃO URGENTE",
            f"**{message}**",
            color=RUST_RED,
        )
        embed.add_field(name="📢 De",   value=interaction.user.mention,                              inline=True)
        embed.add_field(name="⏰ Hora", value=f"<t:{int(datetime.now(timezone.utc).timestamp())}:T>", inline=True)
        embed.set_footer(text="🚨 Mensagem urgente do clan | Rust Clan Bot v2.0")

        sent = failed = 0
        for member in interaction.guild.members:
            if member.bot:
                continue
            try:
                await member.send(embed=embed)
                sent += 1
            except (discord.Forbidden, discord.HTTPException):
                failed += 1
            await asyncio.sleep(0.5)

        await interaction.channel.send(
            "@everyone", embed=embed,
            allowed_mentions=discord.AllowedMentions(everyone=True),
        )
        await interaction.followup.send(
            f"✅ DMs enviadas: **{sent}** · Falhas: **{failed}** (DMs fechadas).", ephemeral=True
        )

    @notify.error
    async def notify_error(self, interaction: discord.Interaction, error):
        await interaction.response.send_message("❌ Você precisa de permissão de **Administrador**.", ephemeral=True)

    # ── /stats ────────────────────────────────────────────────────────────────

    @app_commands.command(name="stats", description="Mostra as estatísticas de um membro.")
    @app_commands.describe(user="Membro a consultar")
    async def stats(self, interaction: discord.Interaction, user: discord.Member):
        gid = interaction.guild_id
        squad_role = data.squad_assignments.get(gid, {}).get(user.id, "Não atribuído")
        emoji = SQUAD_ROLE_EMOJIS.get(squad_role, "❓")

        # Farm totals
        farm_entries = [e for e in data.farm_log.get(gid, []) if e["member_id"] == user.id]
        totals: dict[str, int] = {}
        for e in farm_entries:
            totals[e["resource"]] = totals.get(e["resource"], 0) + e["amount"]

        # Raid count
        raids = [r for r in data.raid_log.get(gid, []) if r["caller_id"] == user.id]

        # Bases
        bases = [b for b in data.base_locations.get(gid, []) if b.get("added_by_id") == user.id]

        # Warnings
        warns = len(data.warnings.get(gid, {}).get(user.id, []))

        # Scrap
        scrap = data.scrap_balances.get(gid, {}).get(user.id, 0)

        embed = rust_embed(f"📊 Stats — {user.display_name}", color=RUST_COLOR)
        embed.set_thumbnail(url=user.display_avatar.url)

        # Highest clan role
        clan_role = "Sem cargo"
        for rname, _, _, _, rem in CLAN_ROLE_DEFS:
            if discord.utils.get(user.roles, name=rname):
                clan_role = f"{rem} {rname}"
                break

        embed.add_field(name="🏷️ Cargo Clan",    value=clan_role,       inline=True)
        embed.add_field(name="🎖️ Função Squad",  value=f"{emoji} {squad_role}", inline=True)
        embed.add_field(name="📅 Entrou",         value=f"<t:{int(user.joined_at.timestamp())}:D>" if user.joined_at else "?", inline=True)
        embed.add_field(name="💣 Raids lançados", value=str(len(raids)), inline=True)
        embed.add_field(name="🏠 Bases registradas", value=str(len(bases)), inline=True)
        embed.add_field(name="⚠️ Avisos",         value=str(warns),      inline=True)
        embed.add_field(name="⚙️ Scrap",          value=f"`{scrap:,}`",  inline=True)

        if totals:
            res_emojis = {"sulfur":"🟡","wood":"🪵","metal":"🔩","hqm":"💎","scrap":"⚙️","stone":"🪨","charcoal":"⬛"}
            farm_lines = "\n".join(
                f"{res_emojis.get(r, '📦')} **{r.title()}**: `{a:,}`" for r, a in totals.items()
            )
            embed.add_field(name="🌾 Farm Total (sessão)", value=farm_lines, inline=False)

        await interaction.response.send_message(embed=embed)

    # ── /placar ───────────────────────────────────────────────────────────────

    @app_commands.command(name="placar", description="Leaderboard de raids, farm e atividade do clan.")
    async def placar(self, interaction: discord.Interaction):
        gid = interaction.guild_id
        embed = rust_embed("🏆 Placar do Clan", color=RUST_GOLD)

        # Top raiders
        raid_counts: dict[int, int] = {}
        for r in data.raid_log.get(gid, []):
            raid_counts[r["caller_id"]] = raid_counts.get(r["caller_id"], 0) + 1

        if raid_counts:
            top_raiders = sorted(raid_counts.items(), key=lambda x: x[1], reverse=True)[:5]
            lines = []
            medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]
            for i, (mid, count) in enumerate(top_raiders):
                member = interaction.guild.get_member(mid)
                name = member.display_name if member else f"ID:{mid}"
                lines.append(f"{medals[i]} **{name}** — {count} raids")
            embed.add_field(name="💣 Top Raiders", value="\n".join(lines), inline=False)

        # Top farmers (sulfur)
        farm_totals: dict[int, int] = {}
        for e in data.farm_log.get(gid, []):
            if e["resource"] == "sulfur":
                farm_totals[e["member_id"]] = farm_totals.get(e["member_id"], 0) + e["amount"]

        if farm_totals:
            top_farmers = sorted(farm_totals.items(), key=lambda x: x[1], reverse=True)[:5]
            lines = []
            for i, (mid, total) in enumerate(top_farmers):
                member = interaction.guild.get_member(mid)
                name = member.display_name if member else f"ID:{mid}"
                lines.append(f"{'🥇🥈🥉4️⃣5️⃣'[i*2:i*2+2]} **{name}** — `{total:,}` sulfur")
            embed.add_field(name="🟡 Top Farmers (Sulfur)", value="\n".join(lines), inline=False)

        # Scrap leaderboard
        scrap_bal = data.scrap_balances.get(gid, {})
        if scrap_bal:
            top_scrap = sorted(scrap_bal.items(), key=lambda x: x[1], reverse=True)[:5]
            lines = []
            medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]
            for i, (mid, bal) in enumerate(top_scrap):
                member = interaction.guild.get_member(mid)
                name = member.display_name if member else f"ID:{mid}"
                lines.append(f"{medals[i]} **{name}** — `{bal:,}` scrap")
            embed.add_field(name="⚙️ Top Scrap", value="\n".join(lines), inline=False)

        if not embed.fields:
            embed.description = "*Nenhum dado registrado ainda. Jogue mais!*"

        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(SquadCog(bot))
