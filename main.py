from contextlib import contextmanager
import discord
from discord.ext import commands
from discord import app_commands
import env
import webuntis as wu
import datetime
import typing
import json

bot = commands.Bot(command_prefix="!!", intents=None)

s = wu.Session(
    server=env.WEBUNTIS_SERVER,
    school=env.WEBUNTIS_SCHOOL,
    username=env.WEBUNTIS_USERNAME,
    password=env.WEBUNTIS_PASSWORD,
    useragent="Webuntis Discord Bot",
)


def validate_date(date_str: str, date_format: str = "%Y-%m-%d") -> bool:
    try:
        date = datetime.datetime.strptime(date_str, date_format)
        return date.date()
    except ValueError:
        return False


@contextmanager
def get_session():
    try:
        s.login()
        yield s
    finally:
        s.logout()


def fetch_classes() -> typing.List[str]:
    with get_session() as s:
        return [klassen.name for klassen in s.klassen()]


def fetch_time_blocks(date: datetime.date, class_: str):
    with get_session() as s:
        start_date = date  # Start date for timetable
        end_date = date  # End date for timetable

        # Ensure that you get the actual class object
        target_class = s.klassen().filter(name=class_)[0]
        print(target_class)
        if not target_class:
            raise ValueError(f"Class '{class_}' not found.")

        # Fetch the timetable data
        data = s.timetable_extended(
            klasse=target_class, start=start_date, end=end_date
        ).combine()
        data_list = []
        previous_day = None

        # Iterate through each time block in the timetable data
        for timeblock in data:
            current_day = timeblock.start.date()

            # Print the date if it's the first block of the day
            if previous_day != current_day:
                previous_day = current_day
                print(f"\nDate: {current_day}")
            # Append the time block data to the data_list
            data_list.append(
                {
                    "start_time": timeblock.start.time().strftime("%H:%M"),
                    "end_time": timeblock.end.time().strftime("%H:%M"),
                    "subject": " | ".join(
                        [subject.long_name for subject in timeblock.subjects]
                    ),
                    "room": " | ".join([str(room) for room in timeblock.rooms]),
                    "classes": ", ".join(
                        [str(class_) for class_ in timeblock.klassen][:3]
                    )
                    + ("..." if len(timeblock.klassen) > 3 else ""),
                    "type": timeblock.lstext,
                }
            )

        return data_list  # Return the collected data


async def class_autocompletion(
    interaction: discord.Interaction, current: str
) -> typing.List[app_commands.Choice[str]]:
    data = [
        app_commands.Choice(name=class_, value=class_)
        for class_ in classes
        if current.lower() in class_.lower()
    ][:25]
    return data


@bot.event
async def on_ready():
    print("Bot is up and ready!")
    try:
        synced = await bot.tree.sync()
        for i in synced:
            print(f"SYNCING {i}")
    except Exception as e:
        print(e)


@bot.tree.command(name="get_class_schedule")
@app_commands.autocomplete(class_=class_autocompletion)
async def get_class_schedule(
    interaction: discord.Interaction, class_: str, date: str = None
):
    allowed_classes = classes

    # Validate the class
    if class_ not in allowed_classes:
        await interaction.response.send_message(
            f"❌ Invalid class: `{class_}`. Please choose a class from the list.",
            ephemeral=True,
        )
        return

    # Validate the date
    if date:
        target_date = validate_date(date)
        if not target_date:
            await interaction.response.send_message(
                f"❌ Invalid date format: `{date}`. Please use the format `YYYY-MM-DD`.",
                ephemeral=True,
            )
    else:
        target_date = datetime.date.today()
    data = fetch_time_blocks(target_date, class_)

    if not data:
        if not date:
            await interaction.response.send_message("you have no courses today!")
        else:
            await interaction.response.send_message(f"you have no courses on {date}")
    else:
        embed = discord.Embed(title=date, color=discord.Colour.blue())
        for block in data:
            embed.add_field(
                name=block["subject"],
                value=f"{block['start_time']} - {block['end_time']}"
                + "\n"
                + block["room"]
                + "\n"
                + block["type"]
                + "\n"
                + block["classes"],
                inline=False,
            )
        await interaction.response.send_message(content="", embed=embed)


@bot.tree.command(name="get_class")
@app_commands.autocomplete(class_=class_autocompletion)
async def get_classes(
    interaction: discord.Interaction,
    class_: str,
):
    allowed_classes = fetch_classes()

    if class_ not in allowed_classes:
        await interaction.response.send_message(
            f"❌ Invalid class: `{class_}`. Please choose a class from the list.",
            ephemeral=True,
        )
    else:
        await interaction.response.send_message(
            f"✅ You selected the class: `{class_}`."
        )


classes = fetch_classes()
bot.run(env.DISCORD_TOKEN)
