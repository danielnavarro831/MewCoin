import os
import random
from Utilities.config import Config
from Utilities.doc_reader import DocReader
from coin import Coin
# from replit import db
db = {}
# db is a dummy database for testing locally. Use the replit db when on the live server


class Bank:
    _bank_id = int(os.getenv('BANK_ID'))  # The discord ID of the bot account
    _replenish_amount = 1000  # When admin commands to add new coins, this is how many are added at a time
    _expected_count = int(os.getenv('EXPECTED_COUNT'))  # The amount to expect in reserve/circulation (total)

    @classmethod
    def check_for_user(cls, user: object):  # Checks if the user has a mewcoin wallet in the database
        user_id = user.id
        if user_id in db.keys():
            return True
        return False

    @classmethod
    def get_bank_id(cls):  # Gets the bank account ID
        return Bank._bank_id

    @classmethod
    def get_bank_reserves(cls, message=False):  # Returns how many mewcoin are in the bank (not in circulation)
        amount = len(db[str(Bank._bank_id)])
        if not message:
            return amount
        return DocReader.get_string("amount_in_reserves_msg", {"Amount": amount})

    @classmethod
    def setup(cls, user: object):  # Sets up a new mewcoin wallet for a user
        name_id = str(user.id)
        if name_id in db.keys():
            # This person already has a wallet
            return DocReader.get_string("dupe_wallet_msg", {"UserName": user.name})
        else:
            # New MewCoin wallet created
            db[name_id] = []
            return DocReader.get_string("new_wallet_msg", {"UserName": user.name})

    @classmethod
    def add_coin(cls, user: object, amount: int):  # adds or subtracts an amount in bulk from a user's wallet
        bank = Bank._bank_id  # Bank's discord account ID
        name_id = str(user.id)  # user's account ID
        subtracting = False  # initially assumes adding
        if name_id in db.keys():  # Checks to see if the user has a wallet first
            if amount < 0:  # If the amount is less than 0, then we're subtracting
                subtracting = True
                amount = abs(amount)  # makes the amount an absolute amount instead of a negative
                if amount > len(db[name_id]):  # If the amount being subtracted exceeds the user's wallet, then it
                    # becomes the amount the user has so there isn't a negative balance
                    amount = len(db[name_id])
                # Update Coins
                Coin.update_coins(amount, bank, user.id)  # Updates coin owners and previous owners
                db[str(bank)] += db[name_id][:amount]  # the coins are copied to the bank's wallet
                del db[name_id][:amount]  # the coins are removed from the user's wallet
            else:  # Positive amount, we're adding!
                if Config.get_supply():  # make sure there's enough supply in the bank
                    if amount > len(db[str(bank)]):  # If the amount exceeds the bank's supply...
                        amount = len(db[str(bank)])  # The amount becomes what's left
                    # Owners and PrevOwners
                    Coin.update_coins(amount, user.id, bank)  # Update coin owners and previous owners
                    db[name_id] += db[str(bank)][:amount]  # The coins are copied to the user's wallet
                    del db[str(bank)][:amount]  # and removed from the bank's wallet
                else:
                    return DocReader.get_string("reserves_error_msg", {})  # If there's no supply, return this error
            Bank.check_supply()  # After taking from the bank, check the supply and update boolean if necessary
            if not subtracting:  # Return appropriate messaging
                # MewCoin successfully added
                return DocReader.get_string("add_coin_msg", {"Amount": amount,
                                                             "UserName": user.name})
            else:
                # MewCoin successfully subtracted
                return DocReader.get_string("subtract_coin_msg", {"Amount": amount,
                                                                  "UserName": user.name})
        else:
            # Target has no wallet. Cannot add or subtract
            return DocReader.get_string("no_wallet_msg", {"UserName": user.name})

    @classmethod
    def gift_amount(cls, user1: object, user2: object, amount: int):
        name1_id = str(user1.id)
        name2_id = str(user2.id)
        if name1_id in db.keys():
            if name2_id in db.keys():
                if len(db[name1_id]) >= amount:  # Verifies gifter has enough
                    if amount >= 0:  # Verifies nothing funny going on
                        # Update Owners and PrevOwners
                        Coin.update_coins(amount, user2.id, user1.id)
                        db[name2_id] += db[name1_id][:amount]
                        del db[name1_id][:amount]
                        Bank.check_supply()
                        return DocReader.get_string("gift_msg", {"UserName1": user1.name,
                                                                 "UserName2": user2.name,
                                                                 "Amount": amount})
                    else:
                        # Tried to gift a negative amount
                        return DocReader.get_string("robbery_msg", {"UserName1": user1.name,
                                                                    "UserName2": user2.name})
                else:
                    # Gifter doesn't have enough money
                    return DocReader.get_string("insufficient_funds_msg", {"UserName": user1.name})
            else:
                # Recipient doesn't have a wallet
                return DocReader.get_string("no_wallet_msg", {"UserName": user2.name})
        else:
            # Gifter doesn't have a wallet
            return DocReader.get_string("no_wallet_msg", {"UserName": user1.name})

    @classmethod
    def empty_wallet(cls, user: object):
        name_id = str(user.id)  # user's discord ID
        if name_id in db.keys():  # If the user has a wallet...
            # Update Owners and PrevOwners
            Coin.update_coins(len(db[name_id]), Bank._bank_id, user.id)
            db[str(Bank._bank_id)] += db[name_id]  # Return all coins to the bank
            db[name_id] = []  # Empty the user's wallet
            Bank.check_supply()  # Update the bank supply boolean if it was empty
            # Return appropriate messaging
            return DocReader.get_string("empty_wallet_msg", {"UserName": user.name})
        else:
            # Target has no wallet. Cannot empty
            return DocReader.get_string("no_wallet_msg", {"UserName": user.name})

    @classmethod
    def get_user_balance(cls, user: object):
        name_id = str(user.id)  # User discord ID
        if name_id in db.keys():  # If user has a wallet...
            amount = len(db[name_id])  # get the amount they have in their wallet
            # Return appropriate messaging
            return DocReader.get_string("balance_msg", {"UserName": user.name,
                                                        "Amount": amount})
        else:
            # Target has no wallet. Cannot get balance
            return DocReader.get_string("no_wallet_msg", {"UserName": user.name})

    @classmethod
    def get_circulation(cls):
        num = 0
        for i in db.keys():  # For each existing user wallet...
            if db[i] == db[str(Bank._bank_id)]:
                continue  # Skips bank's wallet amount
            else:
                # Increase "num" with the amount in the user's wallet
                num += len(db[i])
        # Return the amount of mewcoin in circulation
        return DocReader.get_string("circulation_msg", {"Amount": num})

    @classmethod
    def delete_user(cls, user: object):
        if user.id == Bank._bank_id:
            # You can't delete the bank's wallet
            return DocReader.get_string("bank_deletion_error", {})
        name_id = str(user.id)  # Get discord account ID
        if name_id in db.keys():  # If the user has a wallet...
            # Update coin logs
            Coin.update_coins(len(db[name_id]), int(Bank._bank_id), user.id)
            db[str(Bank._bank_id)] += db[name_id]  # Return all coins to the bank
            del db[name_id]  # Remove the user from the database
            Bank.check_supply()  # Update bank supply if previously empty
            # Return appropriate messaging
            return DocReader.get_string("del_wallet_msg", {"UserName": user.name})
        else:
            # Wallet does not exist. Cannot delete
            return DocReader.get_string("no_wallet_msg", {"UserName": user.name})

    @classmethod
    def reset_bank(cls):
        for i in db.keys():
            if db[i] == db[str(Bank._bank_id)]:
                # Skip bank's wallet
                continue
            else:
                # All MewCoin returned to bank's wallet
                Coin.update_coins(len(db[i]), Bank._bank_id, i)
                db[str(Bank._bank_id)] += db[i]
                db[i] = []
        Bank.check_supply()  # update bank's supply if previously empty
        # Return debug messaging
        return DocReader.get_string("bank_reset_msg", {})

    @classmethod
    def nuclear_option(cls):
        # Completely delete all wallets, including the bank
        # ONLY USE IF DATA/COIN INFO IS CORRUPTED!
        for i in db.keys():
            del db[i]
        return "Server wiped"

    @classmethod
    def replenish_reserves(cls):
        wallet = Bank.make_coins(Bank._replenish_amount)  # has the bank make a new batch of mewcoin
        db[str(Bank._bank_id)] += wallet  # Adds the newly created coins to the bank's wallet
        Bank.check_supply()  # Updates the bank's supply if previously empty
        print("Bank Replenished")  # Debug messaging in console
        return DocReader.get_string("reserves_replenished_msg", {"Amount": Bank._replenish_amount})

    @classmethod
    def make_coins(cls, amount: int):  # Amount = how many new mewcoin to make
        wallet = []  # holds newly created mewcoin
        for i in range(amount):
            mewcoin = Coin(Bank._bank_id)  # makes the coin listing the bank as the owner
            wallet.append(mewcoin.info)  # adds it to the wallet list
        return wallet

    @classmethod
    def validate_coins(cls):  # Checks the count, the IDs and which wallets they belong to
        EC = Bank._expected_count  # The amount expected in the bank/circulation
        COUNT_CHECK = True  # assumes everything is okie dokie
        ID_CHECK = True  # assumes everything is okie dokie
        WALLET_CHECK = True  # assumes everything is okie dokie
        num = 0  # counts all coins
        sum_a = 0  # Adds all the IDs together to verify the total
        sum_b = 0  # Creates a sum = the number of coins excpected (1+2+3..) sum a and sum b will be compared
        problem_wallet = 0  # used to identify which wallet (ID) has a problem
        for a in db.keys():  # for each user in the database...
            wallet_size = 0
            num += len(db[a])  # increases "num" by the wallet size of the user
            wallet_check = len(db[a])  # wallet check = the user's wallet size
            for b in range(len(db[a])):  # for each coin in the user's wallet...
                sum_a += int(db[a][b]["ID"])
                if int(db[a][b]["Owner"] == int(a)):  # verifies the current owner and matches it to the wallet it's in
                    wallet_size += 1
                    # Don't keep this, rewrite
                    hacked_pls_delete = [100, 500, 1000, 2000, 3000, 4000, 5000, 6000, 7000, 8000, 9000, 9900]
                    if wallet_size in hacked_pls_delete:  # ignore, debug messaging for progress tracking
                        print("Checked " + str(wallet_size) + " coins so far...")
            if wallet_size != wallet_check:  # If the size of the wallet is not verified
                WALLET_CHECK = False  # an error will be raised at the end
                problem_wallet = a  # displays the user ID of the problematic wallet
        for c in range(1, EC + 1):  # adds the number of coins together (1+2+3+..)
            sum_b += c
        if num != EC:  # if the counted number of coins does not match the expected amount, raise an error
            COUNT_CHECK = False
        if sum_a != sum_b:  # If the ID sum does not match the expected amount sum, raise an error
            ID_CHECK = False
        if COUNT_CHECK:  # If ther isn't an issue with the amount counted...
            COUNT_REPORT = "Count Verified"
        else:  # Report an error for the count
            COUNT_REPORT = "Count Error: " + str(num) + " counted. " + str(EC) + " expected."
        if ID_CHECK:  # If no issue with IDs...
            ID_REPORT = "ID Sum Verified"
        else:  # Report an error for IDs
            ID_REPORT = "ID Error: " + str(sum_a) + " counted. " + str(sum_b) + " expected."
        if WALLET_CHECK:  # If no issue with the user wallets...
            WALLET_REPORT = "Wallet Sizes Verified"
        else:  # Report a problematic wallet
            WALLET_REPORT = "Wallet Size Error: " + problem_wallet + "'s wallet has an incorrect count"
        VALIDATION_REPORT = COUNT_REPORT + "/" + ID_REPORT + "/" + WALLET_REPORT
        return VALIDATION_REPORT

    @classmethod
    def get_coin_log(cls, user=None, index=None):  # grabs a coin log of a specified user/coin
        if not user:  # if no user was provided, check the bank
            user = Bank._bank_id
        if not index:  # if no specific coin was given, pick a random coin
            index = random.randint(0, len(db[str(user)]) - 1)
        print(db[str(user)][index])
        return "Log printed to console"

    @classmethod
    def check_supply(cls):
        if Bank.get_bank_reserves() > 0:  # If the bank has coins to distribute...
            if not Config.get_supply():  # Set the supply to True
                Config.toggle_supply(True)
        else:  # The bank has no more coins
            if Config.get_supply():  # Set the supply to False
                Config.toggle_supply(False)

    @classmethod
    def get_all_accounts(cls):  # Gets all wallets and prints the amount each one has
        accounts = {}  # {AccountID: Balance}
        for account in db.keys():  # For each wallet in the database...
            balance = len(db[account])  # The balance = number of coins in the wallet
            accounts[account] = balance  # add the account ID to the dictionary keys and the value is the balance
        return accounts
