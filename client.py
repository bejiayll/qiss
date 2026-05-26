import discord
from discord import slash_command

from datetime import datetime
from datetime import timezone

from enum import Enum

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = discord.Bot(intents=intents)

TARGET_CHANNEL: int = 1508810502313349251

obserless_roles = []
obserless_users = []
obserless_channels = []

required_roles = [1508796704885833789]

class Ordering(Enum):
    count_down = "По кол-ву сообщений М -> Б"
    count_up = "По кол-ву сообщений Б -> М"
    date_elder = "По дате C -> Н"
    date_newer = "По дате Н -> С"

class Respondent:
    def __init__(
            self,
            member: discord.User, 
            message_count: int, 
            last_message: datetime | None
            ):
        self.member: discord.User = member
        self.message_count: int = message_count
        self.last_message: datetime = last_message

def rolepare(
    roles: list[discord.Role],
    role_check: list[int]
):
    for role in roles:
        if role.id in role_check:
            return True
    return False

@bot.event
async def on_message(message: discord.Message):
    if message.author.bot: return
    if message.channel.id == TARGET_CHANNEL and type(message.channel) is not discord.Thread:
        await message.add_reaction("✅")
        await message.add_reaction("⏳")
        await message.add_reaction("❌")
    return

@bot.slash_command(name="by_role", description="Отображает список пользователей, имеющих комбинацию заданных ролей")
async def by_role(ctx: discord.ApplicationContext, role1: discord.Role, role2: discord.Role = None, role3: discord.Role = None, role4: discord.Role = None, offset: int = 0):
    members = ctx.guild.members
    users: list[discord.Member] = []

    for member in members:

        if member.bot: continue
        
        if not rolepare(member.roles, [role1.id]): continue

        if role2 is not None:
            if not rolepare(member.roles, [role2.id]): continue
        
        if role3 is not None:
            if not rolepare(member.roles, [role3.id]): continue
        
        if role4 is not None:
            if not rolepare(member.roles, [role4.id]): continue

        users.append(member)
    if len(users) < 1:
        result = "❌ Не нашлось никого с подходящими ролями" 
    else: result = "".join(f"{users.index(user) + offset + 1}. {user.mention}\n" for user in users[offset:offset+21])
    string_builder = "" + role1.mention + role2.mention if role2 is not None else "" + role3.mention if role3 is not None else "" + role4.mention if role4 is not None else ""
    await ctx.respond(embed=discord.Embed(description=f"Нашлось {len(users)} участников с ролями {string_builder} \n {result}"))

    


@bot.slash_command(name="timedump", description="Формат даты ДД-ММ-ГГГГ")
async def timedump(
    ctx: discord.ApplicationContext,
    after: str = "01-01-2020",
    before: str = "31-12-2039",
    order: Ordering = Ordering.date_newer,
    count: int = 20,
    offset: int = 0
):

    await ctx.defer()

    after_date = datetime.strptime(after, "%d-%m-%Y")
    before_date = datetime.strptime(before, "%d-%m-%Y")

    users: dict[int, Respondent] = {}

    members = ctx.guild.members

    for member in members:

        if member.bot:
            continue

        if required_roles:
            if not rolepare(member.roles, required_roles):
                continue

        if obserless_roles:
            if rolepare(member.roles, obserless_roles):
                continue

        users[member.id] = Respondent(
            member=member,
            message_count=0,
            last_message=None
        )
    for channel in ctx.guild.text_channels:
        if channel.id in obserless_channels: continue

        try:
            async for message in channel.history(
                after=after_date,
                before=before_date,
                limit=None
            ):

                if message.author.bot: continue
                if message.author.id not in users: continue

                respondent = users[message.author.id]
                respondent.message_count += 1

                if (
                    respondent.last_message is None
                    or message.created_at > respondent.last_message
                ):
                    respondent.last_message = message.created_at

        except discord.Forbidden:
            print("403")

    respondents = list(users.values())

    if order == Ordering.count_down:
        respondents.sort(
            key=lambda x: x.message_count,
            reverse=True
        )
    elif order == Ordering.count_up:
        respondents.sort(
            key=lambda x: x.message_count
        )
    elif order == Ordering.date_newer:
        respondents.sort(
            key=lambda x: (
                x.last_message
                or datetime.max.replace(tzinfo=timezone.utc)
            ),
            reverse=True
        )

    elif order == Ordering.date_elder:
        respondents.sort(
        key=lambda x: (
            x.last_message
            or datetime.min.replace(tzinfo=timezone.utc)
        )
    )
    respondents = respondents[offset:offset + count]
    lines = []
    for resp in respondents:
        last_msg = (
            resp.last_message.strftime("%d-%m-%Y %H:%M")
            if resp.last_message
            else "Нет сообщений"
        )
        lines.append(
            f"""{resp.member.mention} Сообщений: {resp.message_count} Последнее: {last_msg}
            ---------------------"""
        )
    if not lines:
        await ctx.followup.send("Ничего не найдено")
        return
    result = "\n".join(lines)
    await ctx.respond(embed=discord.Embed(description=f"{result}"))
        