import asyncio
import discord
from discord import app_commands
from discord.ext import commands

from emoji_utils import create_emojis, CLAN_EMOJI_DEFS
from helpers import (rust_embed, RUST_ORANGE, RUST_RED, CLAN_ROLE_DEFS,
                     OFICIAL_PLUS)


def _get(guild, name):
    return discord.utils.get(guild.roles, name=name)


async def _create_roles(guild: discord.Guild) -> tuple[int, int]:
    created = skipped = 0
    for name, color, perms_kw, hoist, _ in reversed(CLAN_ROLE_DEFS):
        if discord.utils.get(guild.roles, name=name):
            skipped += 1
            continue
        await guild.create_role(
            name=name, color=color,
            permissions=discord.Permissions(**perms_kw),
            hoist=hoist, reason="setup",
        )
        created += 1
        await asyncio.sleep(0.4)
    return created, skipped


async def _create_channels(guild: discord.Guild) -> tuple[int, int]:
    lider   = _get(guild, "👑 Lider")
    colider = _get(guild, "⚔️ Co-Lider")
    oficial = _get(guild, "🛡️ Oficial")
    raider  = _get(guild, "💣 Raider")
    pvp     = _get(guild, "🎯 PVP")
    roamer  = _get(guild, "🌿 Roamer")
    builder = _get(guild, "🏗️ Builder")
    eletric = _get(guild, "⚡ Eletricista")
    farmer  = _get(guild, "🌾 Farmer")
    botfarm = _get(guild, "🤖 BotFarmer")
    scout   = _get(guild, "🔍 Scout")
    membro  = _get(guild, "🎮 Membro")
    recruta = _get(guild, "🆕 Recruta")
    everyone = guild.default_role

    staff    = [r for r in [lider, colider, oficial] if r]
    ops      = [r for r in [raider, pvp, roamer] if r]
    build    = [r for r in [builder, eletric] if r]
    farm     = [r for r in [farmer, botfarm] if r]
    verified = [r for r in [lider, colider, oficial, raider, pvp, roamer,
                             builder, eletric, farmer, botfarm, scout, membro, recruta] if r]

    def deny() -> discord.PermissionOverwrite:
        return discord.PermissionOverwrite(view_channel=False)

    def allow() -> discord.PermissionOverwrite:
        return discord.PermissionOverwrite(view_channel=True)

    def allow_ro() -> discord.PermissionOverwrite:
        return discord.PermissionOverwrite(view_channel=True, send_messages=False)

    def ow_info() -> dict:
        ow = {everyone: deny()}
        for r in verified:
            ow[r] = allow_ro()
        return ow

    def ow_verification() -> dict:
        return {everyone: discord.PermissionOverwrite(
            view_channel=True, send_messages=False,
            add_reactions=True, read_message_history=True,
        )}

    def ow_roles(*role_lists) -> dict:
        ow = {everyone: deny()}
        for lst in role_lists:
            for r in (lst if isinstance(lst, list) else [lst]):
                if r:
                    ow[r] = allow()
        return ow

    def ow_verified_rw() -> dict:
        ow = {everyone: deny()}
        for r in verified:
            ow[r] = allow()
        return ow

    def ow_voice(*role_lists) -> dict:
        ow = {everyone: discord.PermissionOverwrite(view_channel=False, connect=False)}
        for lst in role_lists:
            for r in (lst if isinstance(lst, list) else [lst]):
                if r:
                    ow[r] = discord.PermissionOverwrite(view_channel=True, connect=True)
        return ow

    text_structure = [
        ("📋 INFORMAÇÕES", [
            ("📜-regras",      ow_info()),
            ("📢-anuncios",    ow_info()),
            ("🗓️-wipes",       ow_info()),
            ("🤖-status-bot",  ow_info()),
            ("✅-verificacao",  ow_verification()),
        ]),
        ("🔱 LIDERANÇA", [
            ("👑-lider-chat",  ow_roles(staff, [lider, colider])),
            ("📊-estrategia",  ow_roles(staff, [lider, colider])),
            ("🔒-privado",     ow_roles([lider, colider])),
        ]),
        ("⚔️ OPERAÇÕES", [
            ("💣-raid-planning-1",  ow_roles(staff, ops)),
            ("💣-raid-planning-2",  ow_roles(staff, ops)),
            ("💣-raid-planning-3",  ow_roles(staff, ops)),
            ("📡-raid-calls-1",     ow_roles(staff, ops)),
            ("📡-raid-calls-2",     ow_roles(staff, ops)),
            ("📡-raid-calls-3",     ow_roles(staff, ops)),
            ("🎯-pvp-chat-1",       ow_roles(staff, [pvp])),
            ("🎯-pvp-chat-2",       ow_roles(staff, [pvp])),
            ("🎯-pvp-chat-3",       ow_roles(staff, [pvp])),
            ("🌿-roamer-chat-1",    ow_roles(staff, [roamer])),
            ("🌿-roamer-chat-2",    ow_roles(staff, [roamer])),
            ("🌿-roamer-chat-3",    ow_roles(staff, [roamer])),
        ]),
        ("🏗️ CONSTRUÇÃO", [
            ("🏗️-builder-chat-1",    ow_roles(staff, [builder])),
            ("🏗️-builder-chat-2",    ow_roles(staff, [builder])),
            ("🏗️-builder-chat-3",    ow_roles(staff, [builder])),
            ("⚡-eletricista-chat-1", ow_roles(staff, [eletric])),
            ("⚡-eletricista-chat-2", ow_roles(staff, [eletric])),
            ("⚡-eletricista-chat-3", ow_roles(staff, [eletric])),
        ]),
        ("🌾 RECURSOS", [
            ("🌾-farmer-chat-1",  ow_roles(staff, [farmer])),
            ("🌾-farmer-chat-2",  ow_roles(staff, [farmer])),
            ("🌾-farmer-chat-3",  ow_roles(staff, [farmer])),
            ("🤖-botfarm-chat-1", ow_roles(staff, [botfarm])),
            ("🤖-botfarm-chat-2", ow_roles(staff, [botfarm])),
            ("🤖-botfarm-chat-3", ow_roles(staff, [botfarm])),
            ("📦-farm-log",       ow_verified_rw()),
            ("💎-recursos",       ow_verified_rw()),
        ]),
        ("🔍 SCOUT", [
            ("🔍-scout-chat-1",  ow_roles(staff, [scout])),
            ("🔍-scout-chat-2",  ow_roles(staff, [scout])),
            ("🔍-scout-chat-3",  ow_roles(staff, [scout])),
        ]),
        ("🎮 GERAL", [
            ("💬-geral",       ow_verified_rw()),
            ("😂-memes",       ow_verified_rw()),
            ("🎲-off-topic",   ow_verified_rw()),
            ("📸-screenshots", ow_verified_rw()),
            ("🎵-musica",      ow_verified_rw()),
        ]),
    ]

    voice_structure = [
        ("🔊 VOICE", [
            # General
            ("📢call-geral-1",        ow_voice(verified)),
            ("📢call-geral-2",        ow_voice(verified)),
            ("📢call-geral-3",        ow_voice(verified)),
            # Raid
            ("💣call-raid-1",         ow_voice(staff, ops)),
            ("💣call-raid-2",         ow_voice(staff, ops)),
            ("💣call-raid-3",         ow_voice(staff, ops)),
            # Build
            ("🏗️call-build-1",        ow_voice(staff, build)),
            ("🏗️call-build-2",        ow_voice(staff, build)),
            ("🏗️call-build-3",        ow_voice(staff, build)),
            # Farm
            ("🌾call-farm-1",         ow_voice(staff, farm)),
            ("🌾call-farm-2",         ow_voice(staff, farm)),
            ("🌾call-farm-3",         ow_voice(staff, farm)),
            # PVP
            ("🎯call-pvp-1",          ow_voice(staff, [pvp])),
            ("🎯call-pvp-2",          ow_voice(staff, [pvp])),
            ("🎯call-pvp-3",          ow_voice(staff, [pvp])),
            # Roamer
            ("🌿call-roamer-1",       ow_voice(staff, [roamer])),
            ("🌿call-roamer-2",       ow_voice(staff, [roamer])),
            ("🌿call-roamer-3",       ow_voice(staff, [roamer])),
            # Eletricista
            ("⚡call-eletricista-1",  ow_voice(staff, [eletric])),
            ("⚡call-eletricista-2",  ow_voice(staff, [eletric])),
            # Scout
            ("🔍call-scout-1",        ow_voice(staff, [scout])),
            ("🔍call-scout-2",        ow_voice(staff, [scout])),
            # Lider only
            ("👑call-lider",           ow_voice([lider, colider])),
            # AFK
            ("💤afk",                  ow_voice(verified)),
        ]),
    ]

    created_cats = created_ch = 0

    for cat_name, channels in text_structure:
        cat = discord.utils.get(guild.categories, name=cat_name)
        if not cat:
            cat = await guild.create_category(cat_name)
            created_cats += 1
            await asyncio.sleep(0.3)
        for ch_name, overwrites in channels:
            if discord.utils.get(cat.text_channels, name=ch_name.lstrip("#")):
                continue
            await cat.create_text_channel(ch_name.lstrip("#"), overwrites=overwrites)
            created_ch += 1
            await asyncio.sleep(0.3)

    for cat_name, vcs in voice_structure:
        cat = discord.utils.get(guild.categories, name=cat_name)
        if not cat:
            cat = await guild.create_category(cat_name)
            created_cats += 1
            await asyncio.sleep(0.3)
        for vc_name, ow in vcs:
            if discord.utils.get(cat.voice_channels, name=vc_name):
                continue
            await cat.create_voice_channel(vc_name, overwrites=ow)
            created_ch += 1
            await asyncio.sleep(0.3)

    return created_cats, created_ch


class SetupCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ── /setuproles ───────────────────────────────────────────────────────────

    @app_commands.command(name="setuproles", description="Cria todos os cargos do clan com cores e permissões.")
    @app_commands.checks.has_permissions(administrator=True)
    async def setuproles(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        try:
            created, skipped = await _create_roles(interaction.guild)
        except discord.Forbidden:
            await interaction.followup.send("❌ Sem permissão para criar cargos.", ephemeral=True)
            return

        embed = rust_embed("✅ Cargos Criados",
                           f"**{created}** criados · **{skipped}** já existiam",
                           color=RUST_ORANGE)
        lines = []
        for name, _, _, _, emoji in CLAN_ROLE_DEFS:
            r = discord.utils.get(interaction.guild.roles, name=name)
            lines.append(f"{emoji} {r.mention if r else f'`{name}`'}")
        embed.add_field(name="Cargos", value="\n".join(lines), inline=False)
        await interaction.followup.send(embed=embed, ephemeral=True)

    @setuproles.error
    async def setuproles_error(self, interaction: discord.Interaction, error):
        await interaction.response.send_message("❌ Precisa de permissão **Administrador**.", ephemeral=True)

    # ── /setupserver ──────────────────────────────────────────────────────────

    @app_commands.command(name="setupserver", description="Cria toda a estrutura de canais e categorias.")
    @app_commands.checks.has_permissions(administrator=True)
    async def setupserver(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        try:
            cats, channels = await _create_channels(interaction.guild)
        except discord.Forbidden:
            await interaction.followup.send("❌ Sem permissão para criar canais.", ephemeral=True)
            return
        embed = rust_embed("✅ Servidor Organizado",
                           f"**{cats}** categorias e **{channels}** canais criados.\n\n"
                           "💡 Use `/setuproles` antes se os cargos ainda não existirem.",
                           color=RUST_ORANGE)
        await interaction.followup.send(embed=embed, ephemeral=True)

    @setupserver.error
    async def setupserver_error(self, interaction: discord.Interaction, error):
        await interaction.response.send_message("❌ Precisa de permissão **Administrador**.", ephemeral=True)

    # ── /setup (all-in-one) ───────────────────────────────────────────────────

    @app_commands.command(name="setup",
                          description="Setup completo: cria cargos → emojis → canais em sequência.")
    @app_commands.checks.has_permissions(administrator=True)
    async def setup_all(self, interaction: discord.Interaction):
        await interaction.response.defer()

        progress = rust_embed("⚙️ Setup Completo — Iniciando…",
                              "Configurando o servidor do clan. Aguarde…", color=RUST_ORANGE)
        await interaction.followup.send(embed=progress)
        msg = await interaction.original_response()

        # ── Step 1: Roles ─────────────────────────────────────────────────────
        e1 = rust_embed("⚙️ Passo 1/3 — Criando Cargos…",
                        "🔄 Criando todos os cargos do clan…", color=RUST_ORANGE)
        await msg.edit(embed=e1)
        try:
            roles_created, roles_skipped = await _create_roles(interaction.guild)
        except discord.Forbidden:
            await msg.edit(embed=rust_embed("❌ Erro", "Sem permissão para criar cargos.", color=RUST_RED))
            return

        # ── Step 2: Emojis ────────────────────────────────────────────────────
        e2 = rust_embed("⚙️ Passo 2/3 — Criando Emojis…",
                        f"✅ {roles_created} cargos criados · {roles_skipped} já existiam\n"
                        "🔄 Gerando e subindo emojis gradiente…", color=RUST_ORANGE)
        await msg.edit(embed=e2)
        existing = {e.name for e in interaction.guild.emojis}
        try:
            emojis_created, emojis_skipped, emojis_failed = await create_emojis(interaction.guild, existing)
        except discord.Forbidden:
            emojis_created, emojis_skipped, emojis_failed = [], [], ["sem permissão"]

        # ── Step 3: Channels ──────────────────────────────────────────────────
        e3 = rust_embed("⚙️ Passo 3/3 — Criando Canais…",
                        f"✅ {roles_created} cargos · {len(emojis_created)} emojis\n"
                        "🔄 Criando categorias e canais…", color=RUST_ORANGE)
        await msg.edit(embed=e3)
        try:
            cats_created, ch_created = await _create_channels(interaction.guild)
        except discord.Forbidden:
            await msg.edit(embed=rust_embed("❌ Erro", "Sem permissão para criar canais.", color=RUST_RED))
            return

        # ── Final summary ─────────────────────────────────────────────────────
        final = rust_embed(
            "✅ Setup Completo!",
            "Servidor do clan configurado com sucesso! 🦀",
            color=discord.Color.green(),
        )
        final.add_field(name="🎖️ Cargos",
                        value=f"✅ {roles_created} criados · ⏭️ {roles_skipped} já existiam",
                        inline=False)
        final.add_field(name="😀 Emojis",
                        value=(f"✅ {len(emojis_created)} criados · ⏭️ {len(emojis_skipped)} já existiam"
                               + (f" · ❌ {len(emojis_failed)} falharam" if emojis_failed else "")),
                        inline=False)
        final.add_field(name="🏗️ Canais",
                        value=f"✅ {cats_created} categorias + {ch_created} canais criados",
                        inline=False)

        if emojis_created:
            final.add_field(name="Emojis",
                            value=" ".join(str(e) for e in emojis_created[:14]),
                            inline=False)

        final.add_field(
            name="📋 Próximos passos",
            value=(
                "1. Use `/setverification #✅-verificacao` para ativar verificação\n"
                "2. Use `/serverstatus` para ativar status ao vivo\n"
                "3. Use `/autoname` para ativar tags automáticas"
            ),
            inline=False,
        )
        final.set_footer(text="🦀 Rust Clan Bot v2.0")
        await msg.edit(embed=final)

    @setup_all.error
    async def setup_all_error(self, interaction: discord.Interaction, error):
        await interaction.response.send_message("❌ Precisa de permissão **Administrador**.", ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(SetupCog(bot))
