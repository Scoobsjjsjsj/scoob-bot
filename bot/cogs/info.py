import discord
from discord import app_commands
from discord.ext import commands

from helpers import rust_embed, RUST_COLOR, RUST_RED, RUST_ORANGE


CLAN_RULES = [
    ("1️⃣ Respeito",       "Trate todos com respeito. Zero tolerância para toxicidade, racismo ou assédio."),
    ("2️⃣ Comunicação",    "Sempre avise antes de sair por mais de 2 dias. Use os canais corretos."),
    ("3️⃣ Atividade",      "Mínimo 3 sessões/semana. Inatividade +7 dias sem aviso = kick automático."),
    ("4️⃣ Farm em equipe", "Recursos farmados são do clan. Não esconda materiais sem autorização do Lider."),
    ("5️⃣ Raids",          "Raids apenas com autorização do Lider/Co-Lider. Nunca solo sem avisar."),
    ("6️⃣ Bases",          "Registre SEMPRE novas bases com `/base`. Informe localização no canal #recursos."),
    ("7️⃣ Discord",        "Obrigatório estar no Discord durante o jogo. Use o canal de voz correto."),
    ("8️⃣ Aliados",        "Não traga pessoas externas à base sem aprovação. Alianças = Lider decide."),
    ("9️⃣ Traição",        "Roubar, griefar ou vazar info do clan = **ban permanente** sem apelação."),
    ("🔟 Hierarquia",     "Respeite os cargos. Decisões do Lider e Co-Lider são finais e irrevogáveis."),
]

COMMANDS_HELP = {
    "🔐 Verificação": [
        "`/setverification` — Define canal de verificação",
        "`/unverify @user` — Remove verificação de um membro",
    ],
    "🏷️ Autoname": [
        "`/autoname` — Ativa/desativa tag automática",
        "`/nameall` — Aplica tag a TODOS os membros",
    ],
    "🗓️ Wipes": [
        "`/wipe [server] [date] [time] [ip]` — Anuncia wipe",
        "`/wipes` — Lista wipes registrados",
        "`/delwipe [server]` — Remove wipe",
    ],
    "🎖️ Cargos": [
        "`/setuproles` — Cria todos os cargos do clan",
        "`/giverole @user [role]` — Dá cargo (Oficial+)",
        "`/removerole @user [role]` — Remove cargo (Oficial+)",
        "`/roster` — Lista membros por cargo",
        "`/roles [theme]` — Cria cargo temático",
    ],
    "🏗️ Servidor": [
        "`/setupserver` — Cria toda estrutura de canais",
        "`/serverstatus` — Status ao vivo em #status-bot",
    ],
    "📅 Reuniões": [
        "`/meeting schedule [topic] [time]` — Agenda reunião",
        "`/meeting start` — Inicia reunião ativa",
        "`/meeting end` — Encerra reunião",
        "`/meeting list` — Lista reuniões",
        "`/meeting cancel` — Cancela próxima reunião",
    ],
    "⚔️ Moderação": [
        "`/warn @user [reason]` — Avisa membro (kick ao 3°)",
        "`/warnings @user` — Ver avisos",
        "`/clearwarns @user` — Limpar avisos (Oficial+)",
        "`/mute @user [time] [reason]` — Muta membro",
        "`/unmute @user` — Desmuta",
        "`/kick @user [reason]` — Kicka",
        "`/ban @user [reason]` — Bane",
        "`/slowmode [s]` — Slowmode do canal",
        "`/lock` / `/unlock` — Bloqueia/desbloqueia canal",
        "`!limpar [N]` — Deleta N mensagens (qualquer idade)",
    ],
    "🎖️ Squad & Ops": [
        "`/squad @user [role]` — Define função no squad",
        "`/raid [target] [grid]` — Anuncia raid @everyone",
        "`/notify [msg]` — DM a todos + @everyone",
        "`/stats @user` — Ver estatísticas do membro",
        "`/placar` — Leaderboard do clan",
        "`/roster` — Membros por função",
    ],
    "🌾 Recursos": [
        "`/calc [walls] [type]` — Calc explosivos",
        "`/farm [resource] [amount]` — Registra farm",
        "`/base [name] [grid]` — Registra base",
        "`/kit` — Lista de kits",
        "`/bp [item]` — Blueprint e custo",
        "`/decay [structure]` — Tempo de decay",
        "`/upkeep [s] [m] [h]` — Custo de upkeep",
        "`/crafting [item]` — Receita de craft",
    ],
    "⚙️ Economia": [
        "`/scrap give @user [amount]` — Dá scrap (Oficial+)",
        "`/scrap balance [@user]` — Ver saldo",
        "`/scrap leaderboard` — Top 10 scrap",
        "`/scrap spend [amount] [reason]` — Gastar scrap",
    ],
    "🎉 Eventos & Fun": [
        "`/evento [name] [prize] [duration]` — Cria evento sorteio",
        "`/quote` — Citação aleatória de Rust",
        "`/tip` — Dica aleatória de Rust",
        "`/agenda` — Ver agenda do clan",
        "`/addagenda [title] [date] [time]` — Adicionar à agenda",
        "`/tags` — Mensagem de reaction-roles",
    ],
}


class InfoCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ── /regras ───────────────────────────────────────────────────────────────

    @app_commands.command(name="regras", description="Mostra as regras do clan.")
    async def regras(self, interaction: discord.Interaction):
        embed = rust_embed(
            "📜 Regras do Clan",
            "Leia e respeite todas as regras. O descumprimento resulta em kick ou ban permanente.",
            color=RUST_RED,
        )
        for name, value in CLAN_RULES:
            embed.add_field(name=name, value=value, inline=False)
        embed.set_footer(text="🦀 Ao entrar no clan, você concorda com todas as regras | Rust Clan Bot v2.0")
        await interaction.response.send_message(embed=embed)

    # ── /ajuda ────────────────────────────────────────────────────────────────

    @app_commands.command(name="ajuda", description="Mostra todos os comandos organizados por categoria.")
    async def ajuda(self, interaction: discord.Interaction):
        # Send multiple embeds (one overview + one per category page)
        overview = rust_embed(
            "📖 Ajuda — Rust Clan Bot v2.0",
            f"Bot completo para gerenciamento de clan no Rust.\n\n"
            f"**{sum(len(v) for v in COMMANDS_HELP.values())}** comandos disponíveis em "
            f"**{len(COMMANDS_HELP)}** categorias.\n\n"
            f"Use os embeds abaixo para navegar pelos comandos.",
            color=RUST_COLOR,
        )
        overview.add_field(
            name="📋 Categorias",
            value="\n".join(f"• {cat}" for cat in COMMANDS_HELP.keys()),
            inline=False,
        )
        await interaction.response.send_message(embed=overview, ephemeral=True)

        # Send category embeds
        for category, cmds in COMMANDS_HELP.items():
            embed = rust_embed(category, "\n".join(cmds), color=RUST_ORANGE)
            await interaction.followup.send(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(InfoCog(bot))
