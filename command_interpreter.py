import discord
import os
from Utilities.config import Config
from Utilities.doc_reader import DocReader
from bank import Bank


class CommandInterpreter:
    _bank_id = Bank.get_bank_id()  # Bot's discord ID
    _dungeonbot_id = int(os.getenv('DUNGEONBOT_ID'))  # Ignore
    _admin_id = int(os.getenv('ADMIN_ID'))  # MY discord ID for admin commands
    _bot_channel_id = int(os.getenv('BOT_CHANNEL_ID'))  # Bot discord channel ID
    _bots = {str(_bank_id): "MewCoin", str(_dungeonbot_id): "Dungeonbot"}  # Dictionary for referencing
    _commands = DocReader.get_commands()  # A tool used to read the excel file where we store our
    # approved commands and stores them in a dictionary
    _admin_commands = DocReader.get_admin_commands()  # A tool used to read the admin-level commands in excel
    # and store them in a dictionary

    @classmethod
    def strip_text(cls, message: str):  # Message is the entire text in the post
        message = message.title()  # Makes every word in name casing "Like This For Example"
        words = message.split(" ")  # Splits every word up by spaces. If there's a space, it's considered a new word.
        # words is a list of each "word" separated by spaces
        punct = ["!", ".", ",", "?", "/", "\\", "&", "%", "$", "#", "@",
                 "_", "*", "^", "=", ":", ";", "(", ")", "[", "]", "{", "}", "~", "<", ">", "|"]
        # punct contains all possible punctuation or non-alpha characters (except numbers)
        for word in words:  # for each word in the list of words...
            while word[-1] in punct:  # while the last character in the current word is in the list of punctuation...
                for sym in punct:  # for each symbol in punctuation...
                    word = word.strip(sym)  # remove the symbol from the word
        return words  # returns a list of words in the post without any punctuation

    @classmethod
    def check_for_keywords(cls, message: str):  # message is the raw text from the post
        words = CommandInterpreter.strip_text(message)  # words ends up being a
        # list of each word used without punctuation
        for word in words:  # for each word in the list of words...
            if word in Config.get_keywords():  # if the keyword used to activate the bot (mewcoin) is used...
                return True  # Confirm that the bot was called
        return False  # The bot was not called

    @classmethod
    def check_for_commands(cls, message: str):  # message is the raw post text
        commands = CommandInterpreter._commands  # A dictionary of possible commands
        message = message.title()  # Capitalizes The First Letter In Each Word
        keywords = []  # Creates a list of all keywords detected in the message
        for command in commands.keys():  # for each command in our command dictionary...
            if command in message:  # if the command is in the message...
                keywords.append(command)  # add the command to the list of keywords
            elif commands[command]["Aliases"]:  # OR if a command alias (e.g. ++ instead of add) is in the message...
                for alias in commands[command]["Aliases"]:
                    if alias in message:
                        keywords.append(command)  # Add the command (not alias) to the keyword list
        return keywords  # return the list of keywords found in the message

    @classmethod
    def interpret_message(cls, message: discord.Message):  # discord.Message contains all attributes of the message like
        # who wrote it (ID), what time, the raw text, where it was posted, etc.
        author_id = int(message.author.id)  # The discord account ID of the person who wrote the message
        admin_id = CommandInterpreter._admin_id  # MY discord ID (admin) for referencing
        karma_mode = Config.get_karma_mode()  # Gets the current state of 'Karma Mode' (True or False)
        texts = []  # This will hold the message the bot will post in response to the command given
        keywords = CommandInterpreter.check_for_keywords(message.content)  # Checks to see if the bot was called
        commands = CommandInterpreter.check_for_commands(message.content)  # Checks to see if a command was given
        admin_commands = CommandInterpreter._admin_commands  # Dictionary of admin commands
        if not keywords:
            return  # If bot was not called, ignore
        if not commands:
            return  # If no command was given, ignore
        if keywords and commands:  # If the bot was called AND a command was given...
            command = commands[0]  # Only checks for the FIRST command given in the message so something like
            # "mewcoin add subtract" doesn't happen
            if message.mentions:  # If another user was mentioned, check these commands
                #########################################################
                # Initialize an account
                #########################################################
                if command == "Setup":
                    # mewcoin init @username
                    texts.append(Bank.setup(message.mentions[0]))
                ########################################################
                # Increase MewCoin by 1
                ########################################################
                elif command == "++":
                    if author_id == admin_id or karma_mode:
                        # mewcoin @username ++
                        if karma_mode and message.author in message.mentions and author_id != admin_id:
                            texts.append(DocReader.get_string("karma_error_msg", {}))
                        else:
                            texts.append(Bank.add_coin(message.mentions[0], 1))
                            texts.append(Bank.get_user_balance(message.mentions[0]))
                        if Bank.get_bank_reserves() == 0:
                            texts.append(DocReader.get_string("reserves_error_msg", {}))
                    else:
                        texts.append(DocReader.get_string("permission_error_msg", {}))
                ########################################################
                # Decrease MewCoin by 1
                ########################################################
                elif command == "--":
                    if author_id == admin_id or karma_mode:
                        # mewcoin @username --
                        if karma_mode and message.author in message.mentions and author_id != admin_id:
                            texts.append(DocReader.get_string("karma_error_msg", {}))
                        else:
                            texts.append(Bank.add_coin(message.mentions[0], -1))
                            texts.append(Bank.get_user_balance(message.mentions[0]))
                    else:
                        texts.append(DocReader.get_string("permission_error_msg", {}))
                #######################################################
                # Gift MewCoin
                #######################################################
                elif command == "Gift":
                    # mewcoin gift @username x
                    gifter = message.author
                    giftee = message.mentions[0]
                    num = CommandInterpreter.get_num(message.content)
                    if num:
                        texts.append(Bank.gift_amount(gifter, giftee, num))
                        texts.append(Bank.get_user_balance(gifter))
                        texts.append(Bank.get_user_balance(giftee))
                    else:
                        texts.append(DocReader.get_string("gift_error_msg", {}))
                ######################################################
                # Check wallet ballance
                ######################################################
                elif command == "Check":
                    # mewcoin check @username
                    texts.append(Bank.get_user_balance(message.mentions[0]))
                ######################################################
                # Add a specific amount of MewCoin
                ######################################################
                elif command == "Add":
                    if author_id == admin_id:
                        # mewcoin @username add X
                        num = CommandInterpreter.get_num(message.content)
                        if num:
                            texts.append(Bank.add_coin(message.mentions[0], num))
                            texts.append(Bank.get_user_balance(message.mentions[0]))
                        else:
                            texts.append(DocReader.get_string("amount_required_msg", {}))
                    else:
                        texts.append(DocReader.get_string("permission_error_msg", {}))
                ######################################################
                # Subtract a specific amount of MewCoin
                ######################################################
                elif command == "Subtract":
                    if author_id == admin_id:
                        # mewcoin @username subtract x
                        num = CommandInterpreter.get_num(message.content)
                        if num:
                            if num > 0:
                                num = 0 - num
                            texts.append(Bank.add_coin(message.mentions[0], num))
                            texts.append(Bank.get_user_balance(message.mentions[0]))
                        else:
                            texts.append(DocReader.get_string("amount_required_msg", {}))
                    else:
                        texts.append(DocReader.get_string("permission_error_msg", {}))
                ######################################################
                # Admin Command
                ######################################################
                elif command in admin_commands:
                    if command == "Admin":
                        if admin_id == author_id:
                            message = "Admin Mode toggled "
                            if Config.get_admin_mode():
                                Config.toggle_admin_mode()
                                message += "OFF"
                            else:
                                Config.toggle_admin_mode()
                                message += "ON"
                            texts.append(message)
                        else:
                            texts.append(DocReader.get_string("permission_error_msg", {}))
                    else:
                        if Config.get_admin_mode():
                            texts.append(CommandInterpreter.interpret_admin_command(message))
                        else:
                            texts.append(DocReader.get_string("unknown_command_msg", {}))
                #####################################################
                # Unknown command given
                #####################################################
                else:
                    texts.append(DocReader.get_string("unknown_command_msg", {}))
            #####################################################
            # No user mentioned
            #####################################################
            else:
                #####################################################
                # Displays possible commands
                #####################################################
                if command == "Help":
                    texts.append(CommandInterpreter.get_help_texts(message))
                #####################################################
                # Check number of MewCoin in circulation
                #####################################################
                elif command == "Circulation":
                    texts.append(Bank.get_circulation())
                #####################################################
                # Check MewCoin balance
                #####################################################
                elif command == "Check":
                    texts.append(Bank.get_user_balance(message.author))
                #####################################################
                # Generate a top 10 leaderboard
                #####################################################
                elif command == "Leaderboard":
                    texts.append("Leaderboard")
                elif command in admin_commands:
                    if command == "Admin":
                        if admin_id == author_id:
                            message = "Admin Mode toggled "
                            if Config.get_admin_mode():
                                Config.toggle_admin_mode()
                                message += "OFF"
                            else:
                                Config.toggle_admin_mode()
                                message += "ON"
                            texts.append(message)
                        else:
                            texts.append(DocReader.get_string("permission_error_msg", {}))
                    else:
                        if Config.get_admin_mode():
                            texts.append(CommandInterpreter.interpret_admin_command(message))
                        else:
                            texts.append(DocReader.get_string("unknown_command_msg", {}))
                else:
                    return
            response = "\n".join(texts)  # After command was found and action was taken, create this response from the
            # texts stored in the "texts" list
            return response
        #####################################################
        # Keyword not mentioned
        #####################################################
        else:
            return DocReader.get_string("unknown_command_msg", {})

    @classmethod
    def interpret_admin_command(cls, message: discord.Message):
        author_id = message.author.id
        admin_id = CommandInterpreter._admin_id
        texts = []
        if author_id == admin_id:
            mentioned_commands = CommandInterpreter.check_for_commands(message.content)
            admin_commands = CommandInterpreter._admin_commands
            if mentioned_commands:
                command = mentioned_commands[0]
            else:
                return DocReader.get_string("unknown_command_msg", {})
            if admin_commands[command]["Requires Mention"]:
                if not message.mentions:
                    return DocReader.get_string("mention_required", {})
            if command == "Delete":
                texts.append(Bank.delete_user(message.mentions[0]))
            elif command == "Empty":
                texts.append(Bank.empty_wallet(message.mentions[0]))
                texts.append(Bank.get_user_balance(message.mentions[0]))
            elif command == "Karma":
                texts.append(Config.toggle_karma_mode())
            elif command == "Replenish":
                texts.append(Bank.replenish_reserves())
            elif command == "Reset":
                texts.append(Bank.reset_bank())
            elif command == "Wipe":
                texts.append(Bank.nuclear_option())
            elif command == "Validate":
                texts.append(Bank.validate_coins())
            elif command == "Log":
                num = CommandInterpreter.get_num(message.content)
                if message.mentions:
                    if num:
                        texts.append(Bank.get_coin_log(message.mentions[0].id, num))
                    else:
                        texts.append(Bank.get_coin_log(message.mentions[0].id))
                else:
                    texts.append(Bank.get_coin_log())
            elif command == "Version":
                texts.append(DocReader.get_string("version_msg", {"Number": Config.get_version()}))
            elif command == "Export":
                accounts = Bank.get_all_accounts()
                DocReader.export_mewcoin_data(accounts)
                texts.append("Data Exported")
            response = "\n".join(texts)
            return response
        else:
            return DocReader.get_string("permission_error_msg", {})

    @classmethod
    def get_num(cls, message: str):  # Check for a number used in the text
        text = message.split(" ")  # Split the words up by spaces used
        for i in range(len(text)):  # For each "word" in the list...
            try:  # Try seeing if it's a number
                num = int(text[i])
                return num  # If so, return the number
            except ValueError:
                pass  # If not, continue checking
        num = None  # If no number found, return a None value
        return num

    @classmethod
    def get_help_texts(cls, message: discord.Message):  # discord.Message contains all post attributes
        author_id = message.author.id  # Who wrote the post
        admin_id = CommandInterpreter._admin_id  # MY discord ID for admin reference
        commands = CommandInterpreter._commands  # Dictionary of available commands
        texts = []  # Stores lines of texts that will be composed into the bot's response
        for command in commands.keys():  # For each possible command in our list of commands
            help_text = commands[command]["Help Text"]  # Get the help texts for each command
            admin_command = commands[command]["Admin Command"]  # Determin if the command is an Admin command
            command_name = commands[command]["Command"]  # Get the command name
            if help_text:  # If help text exists for the command...
                if admin_command:  # If it's an admin command...
                    if author_id == admin_id:  # If admin wrote the message...
                        line = command_name + ": " + help_text  # Add the help text for the admin command
                        texts.append(line)
                else:  # If admin DIDN'T write the command, only add non-admin help text
                    line = command_name + ": " + help_text
                    texts.append(line)
        response = "\n".join(texts)  # Compose a response
        return response  # Return the response to post
