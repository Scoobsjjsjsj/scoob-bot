import os
import asyncio
import discord
from discord.ext import commands

BOT_TOKEN = os.getenv("BOT_TOKEN")

COGS = [
    "cogs.verification",
    "cogs.autoname",
    "cogs.wipe",
    "cogs.roles",
    "cogs.setup",
    "cogs.status",
    "cogs.meeting",
    "cogs.moderation",
    "cogs.squad",
    "cogs.resources",
    "cogs.economy",
    "cogs.events",
    "cogs.emojis",
    "cogs.info",
    "cogs.rolescard",
    "cogs.divulgar",
]


class Bot(commands.Bot):
    async def setup_hook(self):
        for cog in COGS:
            try:
                await self.load_extension(cog)
                print(f"  ✓ {cog}")
            except Exception as e:
                print(f"  ✗ {cog}: {e}")
        await self.tree.sync()
        print("Slash commands synced.")


intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.reactions = True

bot = Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    print(f"v2.0 — {len(bot.cogs)} cogs loaded")
    print("─" * 40)


async def main():
    while True:
        try:
            await bot.start(BOT_TOKEN)
        except Exception as e:
            print(f"Bot crashed: {e}. Restarting in 5 seconds...")
        finally:
            if not bot.is_closed():
                await bot.close()
        await asyncio.sleep(5)
        bot.clear()


asyncio.run(main())
