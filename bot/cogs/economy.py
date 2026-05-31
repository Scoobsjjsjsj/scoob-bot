import discord
from discord import app_commands
from discord.ext import commands

import data
from helpers import rust_embed, RUST_COLOR, RUST_RED, RUST_ORANGE, RUST_GOLD, has_oficial_plus


class EconomyCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    scrap = app_commands.Group(name="scrap", description="Sistema de economia de scrap do clan.")

    @scrap.command(name="give", description="Dá scrap points a um membro (Oficial+).")
    @app_commands.describe(user="Membro", amount="Quantidade de scrap")
    async def give(self, interaction: discord.Interaction, user: discord.Member, amount: int):
        if not has_oficial_plus(interaction.user) and not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Você precisa ser **Oficial ou superior**.", ephemeral=True)
            return
        if amount <= 0:
            await interaction.response.send_message("❌ Quantidade deve ser > 0.", ephemeral=True)
            return
        gid = interaction.guild_id
        data.scrap_balances.setdefault(gid, {})[user.id] = \
            data.scrap_balances.get(gid, {}).get(user.id, 0) + amount
        bal = data.scrap_balances[gid][user.id]
        embed = rust_embed(
            "⚙️ Scrap Adicionado",
            f"{user.mention} recebeu **{amount:,} scrap**!\nSaldo atual: `{bal:,}`",
            color=RUST_ORANGE,
        )
        await interaction.response.send_message(embed=embed)
        try:
            await user.send(embed=rust_embed(
                "⚙️ Você recebeu Scrap!",
                f"**{amount:,} scrap** foram adicionados à sua conta.\nSaldo: `{bal:,}`",
                color=RUST_ORANGE,
            ))
        except discord.Forbidden:
            pass

    @scrap.command(name="balance", description="Mostra o saldo de scrap de um membro.")
    @app_commands.describe(user="Membro (deixe vazio para ver o seu)")
    async def balance(self, interaction: discord.Interaction, user: discord.Member = None):
        target = user or interaction.user
        bal = data.scrap_balances.get(interaction.guild_id, {}).get(target.id, 0)
        embed = rust_embed(
            f"⚙️ Saldo de Scrap — {target.display_name}",
            f"💰 Saldo: **`{bal:,}` scrap**",
            color=RUST_COLOR,
        )
        embed.set_thumbnail(url=target.display_avatar.url)
        await interaction.response.send_message(embed=embed)

    @scrap.command(name="leaderboard", description="Top 10 membros com mais scrap.")
    async def leaderboard(self, interaction: discord.Interaction):
        bal = data.scrap_balances.get(interaction.guild_id, {})
        if not bal:
            await interaction.response.send_message(
                embed=rust_embed("⚙️ Leaderboard Scrap", "*Nenhum dado ainda.*", color=RUST_COLOR)
            )
            return
        top = sorted(bal.items(), key=lambda x: x[1], reverse=True)[:10]
        embed = rust_embed("⚙️ Top Scrap — Leaderboard", color=RUST_GOLD)
        medals = ["🥇", "🥈", "🥉"] + [f"**{i}.**" for i in range(4, 11)]
        lines = []
        for i, (mid, amount) in enumerate(top):
            member = interaction.guild.get_member(mid)
            name = member.display_name if member else f"ID:{mid}"
            lines.append(f"{medals[i]} **{name}** — `{amount:,}` scrap")
        embed.description = "\n".join(lines)
        await interaction.response.send_message(embed=embed)

    @scrap.command(name="spend", description="Deduz scrap do seu saldo.")
    @app_commands.describe(amount="Quantidade a gastar", reason="Para que serve")
    async def spend(self, interaction: discord.Interaction, amount: int, reason: str):
        if amount <= 0:
            await interaction.response.send_message("❌ Quantidade deve ser > 0.", ephemeral=True)
            return
        gid = interaction.guild_id
        bal = data.scrap_balances.get(gid, {}).get(interaction.user.id, 0)
        if amount > bal:
            await interaction.response.send_message(
                f"❌ Saldo insuficiente. Você tem `{bal:,}` scrap.", ephemeral=True
            )
            return
        data.scrap_balances.setdefault(gid, {})[interaction.user.id] = bal - amount
        new_bal = data.scrap_balances[gid][interaction.user.id]
        embed = rust_embed(
            "⚙️ Scrap Gasto",
            f"**{amount:,} scrap** gastos.\n**Motivo:** {reason}\n**Novo saldo:** `{new_bal:,}`",
            color=RUST_RED,
        )
        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(EconomyCog(bot))
