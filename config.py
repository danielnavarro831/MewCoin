

class Config:
    _supply = True  # There are still mewcoin available to distribute
    _karma_mode = True  # Allows users to ++ or -- other users to give mewcoin from the bank
    _version = "3.00"  # Latest Changes - Separated into multiple .py files. Communicates supply var to other bots
    _keywords = ["MewCoin", "mewcoin", "mewCoin", "MEWCOIN", "Mewcoin"]  # words that summon the bot
    _supply_msg = None  # Debug purposes, ignore
    _admin_mode = False  # Must enable before resetting the bank for safety purposes

    @classmethod
    def get_admin_mode(cls):  # Returns True or False
        return Config._admin_mode

    @classmethod
    def toggle_admin_mode(cls):  # Enables and disables Admin Mode. Returns debug messaging
        msg = "Admin Mode toggled "
        if Config._admin_mode:
            Config._admin_mode = False
            msg += "OFF"
        else:
            Config._admin_mode = True
            msg += "ON"
        return msg

    @classmethod
    def get_supply(cls):  # Returns True or False
        return Config._supply

    @classmethod
    def get_supply_msg(cls):
        return Config._supply_msg

    @classmethod
    def toggle_supply(cls, setting: bool):  # Used to disable mewcoin distribution from the bank
        msg = "Supply:"
        if setting:
            Config._supply = True
            msg += "True"
        else:
            Config._supply = False
            msg += "False"
        Config._supply_msg = msg

    @classmethod
    def clear_supply_msg(cls):
        Config._supply_msg = None

    @classmethod
    def get_karma_mode(cls):  # Returns True or False
        return Config._karma_mode

    @classmethod
    def toggle_karma_mode(cls, setting=None):  # Toggles Karma Mode on or off and returns debug messaging
        if setting:
            Config._karma_mode = setting
        else:
            if Config._karma_mode:
                Config._karma_mode = False
            else:
                Config._karma_mode = True
        if Config._karma_mode:
            status = "OFF"
        else:
            status = "ON"
        return "Karma mode has been toggled " + status

    @classmethod
    def get_version(cls):  # Returns the version number
        return Config._version

    @classmethod
    def get_keywords(cls):  # Returns the list of keywords used to summon the bot
        return Config._keywords
