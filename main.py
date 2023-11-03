import discord
import os
# from replit import db
from Utilities.command_interpreter import CommandInterpreter
from Utilities.config import Config
from Utilities.doc_reader import DocReader
from bank import Bank
db = {}  # This is a dummy database for testing purposes. /
# When turned on in the live server, comment out db and uncomment the replit line

#######################################################################################################################
# Note, please ignore anything related to "Dungeonbot"
# Dungeonbot was a separate bot that was a text-based RPG game I made in hidden discord channels
# Dungeonbot was integrated into MewCoin to use its currency to purchase items in the Dungeonbot channels
# Dungeonbot has since been disabled and cannot be re-enabled unforunately due to Replit limitations (server hosting)
#######################################################################################################################

client = discord.Client()  # This is how the bot interacts with discord. It calls "client" and tells it to do things
bank_id = Bank.get_bank_id()  # The bot's discord ID. It's a hidden variable in the server for security reasons
dungeonbot_id = int(os.getenv('DUNGEONBOT_ID'))  # ignore, just Dungeonbot's discord ID
admin_id = int(os.getenv('ADMIN_ID'))  # MY discord ID. When an admin-level command is given, the bot references
# this ID (mine) to make sure I'm the one giving the command, or else anyone could restart/wipe the data
bot_channel_id = int(os.getenv('BOT_CHANNEL_ID'))  # An ID of a hidden discord channel where only
# bots and admin can post. This channel is used for logging purposes or for the bots to communicate data to each other
bots = {str(bank_id): "MewCoin", str(dungeonbot_id): "Dungeonbot"}  # A simple dictionary that pairs the
# bot name with its account ID for easy referencing


@client.event
async def on_ready():  # When the bot is turned on and ready, it will post this in the console
    print("Ready to make it rain MewCoin!")


@client.event
async def on_message(message: discord.Message):
    global bot_channel_id
    global admin_id
    global bots
    if message.author == client.user:
        # If the message is from the bot, ignore it
        return
    # Admin token required for certain commands
    author_id = str(message.author.id)
    if message.channel.id == int(bot_channel_id) and (str(author_id) == admin_id or str(author_id) in bots.keys()):
        # IF post was in bot channel and was by Admin or another bot...
        if CommandInterpreter.check_for_keywords(message.content):
            # IF a keyword phrase was used (command)...
            await interpret_bot_command(message)
        else:
            # If no keyword phrases or commands, ignore
            return
    elif author_id in bots.keys():
        # IF post was in a normal discord channel, but made by a bot, ignore it
        return
    else:
        # IF post was in a normal discord channel and by a user, interpret the post
        response = CommandInterpreter.interpret_message(message)
        if response:
            if response == "Leaderboard":
                leaderboard = await get_leaderboard()
                await message.channel.send(leaderboard)
            else:
                await message.channel.send(response)
        else:
            return
    await check_supply_msg()


async def check_supply_msg():
    global bots
    global bank_id
    global bot_channel_id
    if Config.get_supply_msg():
        message = ""
        for bot in bots.keys():
            if int(bot) != bank_id:
                line = bots[bot] + ":bot, "
                message += line
        message += Config.get_supply_msg()
        channel = client.get_channel(int(bot_channel_id))
        await channel.send(message, delete_after=5)
        Config.clear_supply_msg()


async def get_username(user_id: int):
    user = await client.fetch_user(user_id)
    return user.name


async def get_user(user_id: int):
    user = await client.fetch_user(user_id)
    return user


async def get_leaderboard():
    global bank_id
    global bots
    leaderboard = {}
    for i in db.keys():
        if i in bots.keys():
            continue  # Ignores bank's wallet
        username = await get_username(int(i))
        leaderboard[username] = len(db[i])
    leaderboard = {k: v for k, v in sorted(leaderboard.items(), key=lambda item: item[1], reverse=True)}
    lines = [":bank: Top MewCoin Wallets: "]
    num = 1
    for i in leaderboard.keys():
        line = str(num) + ". " + str(i) + ": " + str(leaderboard[i])
        lines.append(line)
        num += 1
        if num >= 11:
            break
    text = "\n".join(lines)
    return text


async def interpret_bot_command(message: discord.Message):
    global bots
    global bank_id
    global bot_channel_id
    # Dungeonbot Message Format:
    # Player ID: int, Amount: int, Command: str, Channel ID: int, Item: str, Item Type: str
    really_long_unmistakeable_var = message.content
    attributes = message.content.split(", ")
    bot_id = str(message.author.id)
    attr_dict = {}
    for attr in attributes:
        attr_entry = attr.split(":")
        key = attr_entry[0]
        value = attr_entry[1]
        attr_dict[key] = value
    user_id = int(attr_dict["Player ID"])
    amount = int(attr_dict["Amount"])
    command = attr_dict["Command"]
    channel_id = int(attr_dict["Channel ID"])
    response = None
    user = await get_user(user_id)
    if command == "Subtract" or command == "--":
        amount *= -1
        response = Bank.add_coin(user, amount)
    elif command == "Add" or command == "++" or command == "Refund":
        if amount > 0:
            response = Bank.add_coin(user, amount)
    elif command == "Spend":
        if str(user_id) in db.keys():
            if len(db[str(user_id)]) >= amount:
                confirmation_message = bots[bot_id] + ":Bot, "
                amount *= -1
                response = Bank.add_coin(user, amount)
                if str(bot_id) in db.keys():
                    bot = await client.fetch_user(user_id)
                    Bank.add_coin(bot, int(attr_dict["Amount"]))
                channel = client.get_channel(int(bot_channel_id))
                really_long_unmistakeable_var += ", Status:Paid"
                confirmation_message += really_long_unmistakeable_var
                await channel.send(confirmation_message, delete_after=5)
            else:
                rejection_message = bots[bot_id] + ":Bot, "
                channel = client.get_channel(int(bot_channel_id))
                really_long_unmistakeable_var += ", Status:Unpaid"
                rejection_message += really_long_unmistakeable_var
                response = DocReader.get_string("insufficient_funds_msg", {"UserName": user.name})
                await channel.send(rejection_message, delete_after=5)
        else:
            rejection_message = bots[bot_id] + ":Bot, "
            channel = client.get_channel(int(bot_channel_id))
            response = DocReader.get_string("no_wallet_msg", {"UserName": user.name})
            really_long_unmistakeable_var += ", Status:No Wallet"
            rejection_message += really_long_unmistakeable_var
            await channel.send(rejection_message, delete_after=5)
    channel = client.get_channel(channel_id)
    await channel.send(response)
    await channel.send(Bank.get_user_balance(user))


client.run(os.getenv('TOKEN'))
