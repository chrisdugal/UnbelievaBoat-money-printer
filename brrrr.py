import time
import schedule
from random import randint
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
import os, shutil

email = os.environ.get("DISCORD_EMAIL")
password = os.environ.get("DISCORD_PWD")
username = os.environ.get("DISCORD_USERNAME")
channelURL = os.environ.get("DISCORD_URL")

# parameters
work_cooldown = 5

race_cooldown = 1
race_animal = "horse"
race_bet = "1000"

blackjack_cooldown = 3
decks = 1
blackjack_base_bet = 100
blackjack_bet_step = 20
blackjack_min_bet = 20
# must have at least 4x this in the bank (split && double down)
blackjack_max_bet = 2000


# init
race_wins = 0
race_losses = 0

balance = 0
running_count = 0
true_count = 0


def work():

    msg_input.send_keys("!work")
    msg_input.send_keys(Keys.ENTER)
    time.sleep(1)

    msg_input.send_keys("!deposit all")
    msg_input.send_keys(Keys.ENTER)
    time.sleep(1)


def race():

    global races
    global race_wins
    global race_losses

    msg_input.send_keys("!withdraw " + race_bet)
    msg_input.send_keys(Keys.ENTER)
    time.sleep(1)

    msg_input.send_keys("!animal-race " + race_bet + " " + race_animal)
    msg_input.send_keys(Keys.ENTER)
    time.sleep(1)

    msg_input.send_keys("!animal-race start " + race_animal)
    msg_input.send_keys(Keys.ENTER)
    time.sleep(1)

    # track win-loss ratio
    time.sleep(10)
    try:
        embeds = driver.find_elements_by_class_name("grid-1nZz7S")
        embeds.reverse()

        # assumes race is the first embed
        result = (
            embeds[0]
            .find_element_by_class_name("embedDescription-1Cuq9a")
            .text.lower()
            .split("\n")[-1]
        )

        if any(char.isdigit() for char in result):
            race_wins += 1
        else:
            race_losses += 1
    except:
        print("race results not found")

    print("race win-loss: ", race_wins, "-", race_losses)

    msg_input.send_keys("!deposit all")
    msg_input.send_keys(Keys.ENTER)
    time.sleep(1)


def add_to_count(card, cards_remaining):

    global running_count
    global true_count

    if card.__contains__("cardBack"):
        return

    card = card[1:-2]

    if "2" <= card <= "6":
        running_count += 1
    elif "7" <= card <= "9":
        pass
    else:
        running_count -= 1

    true_count = running_count / (cards_remaining / 52)


def normal_decision(hand, d_hand):

    normal_lookup = [
        ["s", "s", "s", "s", "s", "s", "s", "s", "s", "s"],  # 17+
        ["s", "s", "s", "s", "s", "h", "h", "h", "h", "h"],  # 16
        ["s", "s", "s", "s", "s", "h", "h", "h", "h", "h"],  # 15
        ["s", "s", "s", "s", "s", "h", "h", "h", "h", "h"],  # 14
        ["s", "s", "s", "s", "s", "h", "h", "h", "h", "h"],  # 13
        ["h", "h", "s", "s", "s", "h", "h", "h", "h", "h"],  # 12
        ["d", "d", "d", "d", "d", "d", "d", "d", "d", "h"],  # 11
        ["d", "d", "d", "d", "d", "d", "d", "d", "h", "h"],  # 10
        ["h", "d", "d", "d", "d", "h", "h", "h", "h", "h"],  # 9
        ["h", "h", "h", "h", "h", "h", "h", "h", "h", "h"],  # 5-8
    ]

    hand = int(hand)
    d_hand = int(d_hand) - 2

    if hand >= 17:
        return normal_lookup[0][d_hand]
    elif hand == 16:
        return normal_lookup[1][d_hand]
    elif hand == 15:
        return normal_lookup[2][d_hand]
    elif hand == 14:
        return normal_lookup[3][d_hand]
    elif hand == 13:
        return normal_lookup[4][d_hand]
    elif hand == 12:
        return normal_lookup[5][d_hand]
    elif hand == 11:
        return normal_lookup[6][d_hand]
    elif hand == 10:
        return normal_lookup[7][d_hand]
    elif hand == 9:
        return normal_lookup[8][d_hand]
    elif 5 <= hand <= 8:
        return normal_lookup[9][d_hand]
    else:
        print("error in normal lookup", hand, d_hand)


def ace_decision(hand, d_hand):

    ace_lookup = [
        ["s", "s", "s", "s", "s", "s", "s", "s", "s", "s"],  # A, 8-10
        ["s", "d", "d", "d", "d", "s", "s", "h", "h", "h"],  # A, 7
        ["h", "d", "d", "d", "d", "h", "h", "h", "h", "h"],  # A, 6
        ["h", "h", "d", "d", "d", "h", "h", "h", "h", "h"],  # A, 5
        ["h", "h", "d", "d", "d", "h", "h", "h", "h", "h"],  # A, 4
        ["h", "h", "h", "d", "d", "h", "h", "h", "h", "h"],  # A, 3
        ["h", "h", "h", "d", "d", "h", "h", "h", "h", "h"],  # A, 2
    ]

    hand = int(hand) - 11
    d_hand = int(d_hand) - 2

    if 8 <= hand <= 11:
        return ace_lookup[0][d_hand]
    elif hand == 7:
        return ace_lookup[1][d_hand]
    elif hand == 6:
        return ace_lookup[2][d_hand]
    elif hand == 5:
        return ace_lookup[3][d_hand]
    elif hand == 4:
        return ace_lookup[4][d_hand]
    elif hand == 3:
        return ace_lookup[5][d_hand]
    elif hand == 2:
        return ace_lookup[6][d_hand]
    else:
        print("error in ace lookup", hand, d_hand)


def split_decision(hand, d_hand):

    split_lookup = [
        ["p", "p", "p", "p", "p", "p", "p", "p", "p", "p"],  # A, 8
        ["s", "s", "s", "s", "s", "s", "s", "s", "s", "s"],  # 10
        ["p", "p", "p", "p", "p", "s", "p", "p", "s", "s"],  # 9
        ["p", "p", "p", "p", "p", "p", "h", "h", "h", "h"],  # 7
        ["p", "p", "p", "p", "p", "h", "h", "h", "h", "h"],  # 6
        ["d", "d", "d", "d", "d", "d", "d", "d", "h", "h"],  # 5
        ["h", "h", "h", "p", "p", "h", "h", "h", "h", "h"],  # 4
        ["p", "p", "p", "p", "p", "p", "h", "h", "h", "h"],  # 3
        ["p", "p", "p", "p", "p", "p", "h", "h", "h", "h"],  # 2
    ]

    hand = int(hand) / 2
    d_hand = int(d_hand) - 2

    if hand == 1 or hand == 8:
        return split_lookup[0][d_hand]
    elif hand == 10:
        return split_lookup[1][d_hand]
    elif hand == 9:
        return split_lookup[2][d_hand]
    elif hand == 7:
        return split_lookup[3][d_hand]
    elif hand == 6:
        return split_lookup[4][d_hand]
    elif hand == 5:
        return split_lookup[5][d_hand]
    elif hand == 4:
        return split_lookup[6][d_hand]
    elif hand == 3:
        return split_lookup[7][d_hand]
    elif hand == 2:
        return split_lookup[8][d_hand]
    else:
        print("error in split lookup", hand, d_hand)


def blackjack():

    global balance
    global running_count
    global true_count

    # calculate bet size
    calculated_bet = blackjack_base_bet + blackjack_bet_step * true_count

    if true_count < 0:
        bet_size = blackjack_min_bet
    elif calculated_bet > blackjack_max_bet:
        bet_size = blackjack_max_bet
    else:
        bet_size = int(calculated_bet)

    # start game
    msg_input.send_keys("!withdraw " + str(4 * bet_size))
    msg_input.send_keys(Keys.ENTER)
    time.sleep(1)
    msg_input.send_keys("!bj " + str(bet_size))
    msg_input.send_keys(Keys.ENTER)
    time.sleep(1)

    # play game
    meta = ["type"]
    cards_remaining = decks * 52
    while "type" in meta:
        try:
            embeds = driver.find_elements_by_class_name("grid-1nZz7S")
            embeds.reverse()

            for embed in embeds:
                author = embed.find_element_by_class_name("embedAuthor-3l5luH").text
                if author == username:
                    meta = (
                        embed.find_element_by_class_name("embedDescription-1Cuq9a")
                        .text.lower()
                        .split(" ")
                    )

                    # if this fails, game's over
                    try:
                        cards_remaining_line = embed.find_element_by_class_name(
                            "embedFooter-3yVop-"
                        ).text.lower()
                        if cards_remaining_line.__contains__("shuffling"):
                            running_count = 0
                            true_count = 0
                        else:
                            try:
                                int(cards_remaining_line.split(" ")[-1])
                                cards_remaining = int(
                                    cards_remaining_line.split(" ")[-1]
                                )
                            except:
                                pass
                    except:
                        # get cards
                        card_groups = embed.find_element_by_class_name(
                            "embedFields-2IPs5Z"
                        ).find_elements_by_class_name("embedField-1v-Pnh")
                        for group in card_groups:
                            cards = group.find_element_by_class_name(
                                "embedFieldValue-nELq2s"
                            ).find_elements_by_class_name("emojiContainer-3X8SvE")
                            for card in cards:
                                add_to_count(
                                    card.find_element_by_tag_name("img").get_attribute(
                                        "alt"
                                    ),
                                    cards_remaining,
                                )
                        break

                    game_info = (
                        embed.find_element_by_class_name("embedFields-2IPs5Z")
                        .text.lower()
                        .split("\n")
                    )

                    hand = game_info[1].lower().split(" ")
                    d_hand = game_info[3].lower().split(" ")

                    # make a move
                    move = ""
                    if "soft" in hand:
                        move = ace_decision(hand[-1], d_hand[-1])
                    elif "split" in meta:
                        move = split_decision(hand[-1], d_hand[-1])
                    else:
                        move = normal_decision(hand[-1], d_hand[-1])

                    if move == "s":
                        move = "stand"
                    elif move == "h":
                        move = "hit"
                    elif move == "d":
                        move = "double down"
                    elif move == "p":
                        move = "split"
                    else:
                        print("error when making move")

                    msg_input.send_keys(move)
                    msg_input.send_keys(Keys.ENTER)
                    time.sleep(1)

                    break
        except:
            pass

    # check outcome
    # note: will miss hand 1 when split occurs
    result = meta[len(meta) - 1]

    # update balance
    if result == "back":
        balance += 0
    else:
        balance += int(result.replace(",", ""))

    print("balance: ", balance)

    # deposit
    msg_input.send_keys("!deposit all")
    msg_input.send_keys(Keys.ENTER)
    time.sleep(1)


def setup():

    global driver
    global msg_input

    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")

    driver = webdriver.Chrome(options=chrome_options)

    driver.get("https://discord.com/login")
    time.sleep(5)

    email_input = driver.find_element_by_name("email")
    email_input.send_keys(email)

    password_input = driver.find_element_by_name("password")
    password_input.send_keys(password)

    try:
        login_button = driver.find_element_by_xpath(
            '//*[@id="app-mount"]/div[2]/div/div[2]/div/div/form/div/div/div[1]/div[3]/button[2]'
        )
        login_button.click()
        time.sleep(10)
    except:
        print("Error: login failed")

    try:
        driver.get(channelURL)
        time.sleep(5)
    except:
        print("Error: channel URL failed")

    try:
        continue_button = driver.find_element_by_xpath(
            '//*[@id="app-mount"]/div[2]/div/div[2]/div/div/div/div[2]/div[2]/div[2]/div[1]/div[1]/div/div[4]/button[2]'
        )
        continue_button.click()
        time.sleep(1)
    except:
        pass

    msg_input = driver.find_element_by_xpath(
        '//*[@id="app-mount"]/div[2]/div/div[2]/div/div/div/div/div[2]/div[2]/main/form/div/div/div/div[1]/div/div[3]/div[2]'
    )

    print("setup successful")


setup()

# tasks
schedule.every(work_cooldown).minutes.do(work)
schedule.every(race_cooldown).minutes.do(race)
schedule.every(blackjack_cooldown).minutes.do(blackjack)

while True:
    schedule.run_pending()
    time.sleep(1)
