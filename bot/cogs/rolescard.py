import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime
import asyncio

MEMBER_ROLES = {
    "💣 Raider": "💣",
    "🎯 PVP": "🎯",
    "🌿 Roamer": "🌿",
    "🏗️ Builder": "🏗️",
    "⚡ Eletricista": "⚡",
    "🌾 Farmer": "🌾",
    "🤖 BotFarmer": "🤖",
    "🔍 Scout": "🔍"
}

NOTIFY_TYPES = {
    "raid": {"emoji": "💀", "color": 0xFF0000, "title": "🚨 RAID ALERT", "roles": ["💣 Raider", "🎯 PVP", "🌿 Roamer"]},
    "meeting": {"emoji": "📅", "color": 0x0066FF, "title": "📅 REUNIÃO", "roles": []},
    "wipe": {"emoji": "🔥", "color": 0xFF6B00, "title": "🔥 WIPE ALERT", "roles": []},
    "emergency": {"emoji": "🚨", "color": 0xFF0000, "title": "🚨 EMERGÊNCIA", "roles": []},
    "farm": {"emoji": "🌿", "color": 0x00AA00, "title": "🌾 FARM ALERT", "roles": ["🌾 Farmer", "🤖 BotFarmer"]},
    "pvp": {"emoji": "⚔️", "color": 0xFFD700, "title": "⚔️ PVP ALERT", "roles": ["🎯 PVP", "🌿 Roamer"]},
    "building": {"emoji": "🏗️", "color": 0x0066FF, "title": "🏗️ BUILD ALERT", "roles": ["🏗️ Builder", "⚡ Eletricista"]},
    "general": {"emoji": "🔔", "color": 0xFFFFFF, "title": "🔔 AVISO GERAL", "roles": []}
}

class RolesCard(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.rolescard_messages = {}
        self.notify_history = []
        self.scheduled_notify = None

    @app_commands.command(name="rolescard", description="Cria mensagem para membros escolherem cargos")
    @app_commands.checks.has_permissions(manage_roles=True)
    async def rolescard(self, interaction: discord.Interaction):
        await interaction.response.defer()
        embed = discord.Embed(
            title="🎭 Escolha seu Cargo",
            description="Reaja com o emoji do cargo que deseja!\nRetire a reação para remover o cargo.",
            color=0xFF4500
        )
        lines = "\n".join([f"{emoji} → **{role}**" for role, emoji in MEMBER_ROLES.items()])
        embed.add_field(name="Cargos disponíveis", value=lines, inline=False)
        embed.set_footer(text="Apenas cargos de membro • Cargos altos são atribuídos pela liderança")
        embed.timestamp = datetime.utcnow()
        msg = await interaction.channel.send(embed=embed)
        for emoji in MEMBER_ROLES.values():
            await msg.add_reaction(emoji)
            await asyncio.sleep(0.3)
        self.rolescard_messages[msg.id] = MEMBER_ROLES
        await interaction.followup.send("✅ Mensagem de cargos criada!", ephemeral=True)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if payload.user_id == self.bot.user.id:
            return
        if payload.message_id not in self.rolescard_messages:
            return
        emoji_str = str(payload.emoji)
        role_map = self.rolescard_messages[payload.message_id]
        guild = self.bot.get_guild(payload.guild_id)
        if not guild:
            return
        member = guild.get_member(payload.user_id)
        for role_name, emoji in role_map.items():
            if emoji == emoji_str:
                role = discord.utils.get(guild.roles, name=role_name)
                if role and member:
                    await member.add_roles(role)
                break

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        if payload.message_id not in self.rolescard_messages:
            return
        emoji_str = str(payload.emoji)
        role_map = self.rolescard_messages[payload.message_id]
        guild = self.bot.get_guild(payload.guild_id)
        if not guild:
            return
        member = guild.get_member(payload.user_id)
        for role_name, emoji in role_map.items():
            if emoji == emoji_str:
                role = discord.utils.get(guild.roles, name=role_name)
                if role and member:
                    await member.remove_roles(role)
                break

    @app_commands.command(name="notify", description="Envia notificação avançada para todos os membros")
    @app_commands.describe(
        tipo="Tipo: raid, meeting, wipe, emergency, farm, pvp, building, general",
        mensagem="Mensagem a enviar"
    )
    @app_commands.checks.has_permissions(manage_guild=True)
    async def notify(self, interaction: discord.Interaction, tipo: str, mensagem: str):
        await interaction.response.defer()
        tipo = tipo.lower()
        if tipo not in NOTIFY_TYPES:
            await interaction.followup.send(f"❌ Tipo inválido! Use: {', '.join(NOTIFY_TYPES.keys())}", ephemeral=True)
            return
        config = NOTIFY_TYPES[tipo]
        embed = discord.Embed(
            title=config["title"],
            description=f"**{mensagem}**",
            color=config["color"]
        )
        embed.add_field(name="📢 Enviado por", value=interaction.user.mention, inline=True)
        embed.add_field(name="🕐 Horário", value=datetime.now().strftime("%d/%m/%Y %H:%M"), inline=True)
        embed.add_field(name="🏠 Servidor", value=interaction.guild.name, inline=True)
        embed.set_footer(text=f"{config['emoji']} {tipo.upper()} • {interaction.guild.name}")
        embed.timestamp = datetime.utcnow()
        sent = 0
        failed = 0
        start = datetime.now()
        for member in interaction.guild.members:
            if not member.bot:
                try:
                    await member.send(embed=embed)
                    sent += 1
                except:
                    failed += 1
        role_pings = ""
        for role_name in config["roles"]:
            role = discord.utils.get(interaction.guild.roles, name=role_name)
            if role:
                role_pings += f"{role.mention} "
        elapsed = (datetime.now() - start).seconds
        await interaction.channel.send(f"@everyone {role_pings}", embed=embed)
        self.notify_history.append({
            "tipo": tipo, "mensagem": mensagem,
            "enviado_por": str(interaction.user),
            "horario": datetime.now().strftime("%d/%m/%Y %H:%M")
        })
        if len(self.notify_history) > 10:
            self.notify_history.pop(0)
        report = discord.Embed(title="📊 Relatório de Envio", color=0x00FF00)
        report.add_field(name="✅ Enviados", value=str(sent), inline=True)
        report.add_field(name="❌ Falhou", value=str(failed), inline=True)
        report.add_field(name="⏱️ Tempo", value=f"{elapsed}s", inline=True)
        await interaction.followup.send(embed=report, ephemeral=True)

    @app_commands.command(name="notifyhistory", description="Mostra últimas 10 notificações enviadas")
    async def notifyhistory(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        if not self.notify_history:
            await interaction.followup.send("Nenhuma notificação enviada ainda.", ephemeral=True)
            return
        embed = discord.Embed(title="📋 Histórico de Notificações", color=0xFF4500)
        for i, n in enumerate(reversed(self.notify_history), 1):
            embed.add_field(
                name=f"{i}. {n['tipo'].upper()} — {n['horario']}",
                value=f"**{n['mensagem']}**\nPor: {n['enviado_por']}",
                inline=False
            )
        await interaction.followup.send(embed=embed, ephemeral=True)
@app_commands.command(name="notifyschedule", description="Agenda notificação")
    @app_commands.describe(tipo="Tipo de notificação", mensagem="Mensagem", tempo="Minutos para enviar")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def notifyschedule(self, interaction: discord.Interaction, tipo: str, mensagem: str, tempo: int):
        await interaction.response.defer(ephemeral=True)
        if tipo not in NOTIFY_TYPES:
            await interaction.followup.send("❌ Tipo inválido!", ephemeral=True)
            return
        if self.scheduled_notify:
            await interaction.followup.send("❌ Já existe uma agendada! Use /notifycancel primeiro.", ephemeral=True)
            return
        await interaction.followup.send(f"✅ Notificação agendada para {tempo} minutos!", ephemeral=True)
        async def send_later():
            await asyncio.sleep(tempo * 60)
            config = NOTIFY_TYPES[tipo]
            embed = discord.Embed(title=config["title"], description=f"**{mensagem}**", color=config["color"])
            embed.add_field(name="📢 Agendado por", value=interaction.user.mention)
            embed.add_field(name="🕐 Horário", value=datetime.now().strftime("%d/%m/%Y %H:%M"))
            for member in interaction.guild.members:
                if not member.bot:
                    try:
                        await member.send(embed=embed)
                    except:
                        pass
            role_pings = ""
            for role_name in config["roles"]:
                role = discord.utils.get(interaction.guild.roles, name=role_name)
                if role:
                    role_pings += f"{role.mention} "
            await interaction.channel.send(f"@everyone {role_pings}", embed=embed)
            self.scheduled_notify = None
        self.scheduled_notify = asyncio.create_task(send_later())

    @app_commands.command(name="notifycancel", description="Cancela notificação agendada")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def notifycancel(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        if not self.scheduled_notify:
            await interaction.followup.send("❌ Nenhuma notificação agendada!", ephemeral=True)
            return
        self.scheduled_notify.cancel()
        self.scheduled_notify = None
        await interaction.followup.send("✅ Notificação cancelada!", ephemeral=True)
async def setup(bot):
    await bot.add_cog(RolesCard(bot))
