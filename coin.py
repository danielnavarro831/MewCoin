from Utilities.doc_reader import DocReader
# from replit import db
db = {}
# db is used for testing locally. It's a dummy database. When on the live server, use the replit db


class Coin:
    _coin_id = int(DocReader.get_variable_data("Coin ID"))  # Grabs the latest coin ID that will be used next
    # Every mewcoin has a unique ID that can be used for tracking purposes. Think of it as baby's first crypto

    def __init__(self, owner_id: int):
        ID = Coin.get_coin_id()  # Get the latest coin ID to use
        self.info = {"ID": ID,  # Create a dictionary called info for the coin and assigns it an ID, an Owner, a
                     # previous owner. A previous owner of 0 means it has never been distributed. Otherwise it's an ID
                     "Owner": owner_id,
                     "PrevOwner": 0}  # 0=bank, otherwise will be discord ID of previous owner
        Coin.update_coin_id()  # Increase the coin ID variable so the next coin doesn't use the same ID

    @classmethod
    def get_coin_id(cls):  # Returns the coin ID
        Coin._coin_id = DocReader.get_variable_data("Coin ID")
        return Coin._coin_id

    @classmethod
    def update_coin_id(cls):  # Increases the coin ID by 1 so the next created coin doesn't use the same ID
        num = Coin._coin_id
        num += 1
        DocReader.set_variable_data("Coin ID", num)

    @classmethod
    def update_coins(cls, amount: int, owner_id: int, prev_id: int):
        # Updates an amount of coins to have a new owner and list the previous owner
        for a in range(amount):
            # Wallet, Coin, PrevOwner Tag
            db[str(prev_id)][a]["PrevOwner"] = prev_id
            db[str(prev_id)][a]["Owner"] = owner_id
