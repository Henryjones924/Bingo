import logging
import os
import subprocess
import cv2
import questionary
from pytesseract import pytesseract
from tabulate import tabulate

bingo_card_path = "/workspaces/python-2/bingo_cards/"


def scan_card(path, iterations, x):
    image = cv2.imread(path)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (3, 3), 0)
    thresh = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]

    # Morph open to remove noise and invert image
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (x, x))
    opening = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel, iterations=iterations)
    invert = 255 - opening

    whitelist = "0123456789 "
    config = f"--psm 6 -c tessedit_char_whitelist={whitelist}"

    # Perform text extraction
    bingo_board_scanned = pytesseract.image_to_string(invert, lang="eng", config=config)
    return bingo_board_scanned


# Validate bingo lines and return bingo game lines
def line_validation(bingo_board_scanned):
    bingo_lines = []
    # Split data into lines
    lines = bingo_board_scanned.splitlines()
    # Remove Empty Spaces In Line
    cleaned_lines = [line.replace(" ", "") for line in lines]
    cleaned_lines = [cleaned_lines for cleaned_lines in cleaned_lines if cleaned_lines]

    # Count Number of digits in each line
    valid = 0
    for line in cleaned_lines:
        number_of_digits = len(line)

        # Validate number of digits in each line
        if (valid != 2 and number_of_digits in [9, 10]) or (
            valid == 2 and number_of_digits in [7, 8]
        ):
            valid += 1
            logging.info("Valid passed:" + str(valid))
            bingo_lines.append(line)
        else:
            logging.info(
                "Valid failed:"
                + str(valid)
                + " Number of digits="
                + str(number_of_digits)
                + " On line="
                + str(cleaned_lines)
            )
            logging.info("Error on line ranges")
            pass
    # Check total nuber of lines and number validation
    if len(bingo_lines) != 5:
        logging.info("Error all bingo lines were not detected")
        return False
    # Check Free Space Line
    if len(bingo_lines[2]) not in [7, 8]:
        logging.info("Error on Free Space Line with Length Check")
        return False

    # Check number validation of bingo card
    bingo_board = create_bingo_board(bingo_lines)
    low = 1
    high = 15
    for i in range(5):
        for number in bingo_board:
            if number[i] == -1 or (low <= int(number[i]) <= high):
                pass
            else:
                logging.info("Number out of range: " + number[i])
                return False
        low += 15
        high += 15
    logging.warn("Validation Passed")
    return bingo_lines


# Create Bingo Board grid
def create_bingo_board(bingo_lines):
    bingo_board = []
    for line in bingo_lines:
        if len(line) % 2 == 0:  # Check for Even
            # Split the line into chunks of 2 characters
            chunks = [line[i : i + 2] for i in range(0, len(line), 2)]
            bingo_board.append(chunks)

        if len(line) % 2 != 0:  # Check for odd
            first_chunk = line[0:1]  # First chunk of 1 character
            remaining_chunks = [
                line[i : i + 2] for i in range(1, len(line), 2)
            ]  # Remaining chunks of 2 characters

            # Combine the chunks
            chunks = [first_chunk] + remaining_chunks
            bingo_board.append(chunks)

    # Add free space
    bingo_board[2].insert(2, -1)
    return bingo_board


# Identified Called Numbers
def identify_called_numbers(bingo_board, call_numbers):
    x = 0
    while x <= 4:
        y = 0
        while y <= 4:
            if int(bingo_board[x][y]) in call_numbers:
                bingo_board[x][y] = -1
            y += 1
        x += 1
    return bingo_board


def game_fullcard(bingo_board):
    bingo = 0
    x = 0
    while x <= 4:
        y = 0
        while y <= 4:
            if bingo_board[x][y] == -1:
                bingo += 1
            else:
                pass
            y += 1
        x += 1
    if bingo == 25:
        return True


def game_lines(bingo_board):
    rows = bingo_board
    cols = [[bingo_board[j][i] for j in range(5)] for i in range(5)]
    diags = [
        [bingo_board[i][i] for i in range(5)],
        [bingo_board[i][4 - i] for i in range(5)],
    ]
    lines = rows + cols + diags
    for line in lines:
        if len(set(line)) == 1 and line[0] != 0:
            return True
    return False


def game_fourcorners(bingo_board):
    if (
        bingo_board[0][0] == -1
        and bingo_board[0][4] == -1
        and bingo_board[4][0] == -1
        and bingo_board[4][4] == -1
    ):
        return True
    else:
        return False


def import_card(bingo_card_file_name):
    bingo_card_file_name = bingo_card_path + bingo_card_file_name
    # Scan Bingo Cards
    validation_passed = False
    for interaction in range(1, 7):
        for x in range(1, 6):
            bingo_board_scanned = scan_card(bingo_card_file_name, interaction, x)
            validation_check = line_validation(bingo_board_scanned)
            if validation_check is False:
                logging.warning(
                    "Validation Failed on: Interaction="
                    + str(interaction)
                    + " and x="
                    + str(x)
                )
            else:
                validation_passed = True
                break
        if validation_passed:
            logging.warning(
                "Validation Passed on: Interaction="
                + str(interaction)
                + " and x="
                + str(x)
            )
            break

    # CreateCard
    if validation_passed:
        bingo_board = create_bingo_board(validation_check)
    else:
        logging.warning("Bingo Card could not be read / validated")
        exit()
    return bingo_board


def display_bingo_win(bingo_board, call_numbers):
    os.system("clear")
    print(tabulate(bingo_board, tablefmt="grid"))
    print("Called Numbers: " + str(call_numbers))
    print("BINGO!!!!")


def bingo_check_for_win(bingo_board, game_mode, call_numbers):
    play_bingo_board = identify_called_numbers(bingo_board, call_numbers)
    print(tabulate(play_bingo_board, tablefmt="grid"))

    # Game modes win conidtions
    if game_mode == "Full Card":
        bingo = game_fullcard(play_bingo_board)
        if bingo is True:
            return display_bingo_win(bingo_board, call_numbers)
        else:
            return False
    elif game_mode == "Corners":
        bingo = game_fourcorners(play_bingo_board)
        if bingo is True:
            return display_bingo_win(bingo_board, call_numbers)
        else:
            return False
    elif game_mode == "Lines":
        bingo = game_lines(play_bingo_board)
        if bingo is True:
            return display_bingo_win(bingo_board, call_numbers)
        else:
            return False


def called_numbers(call_numbers):
    called = input("Enter called number or type stop:")
    if called.lower() == "stop":
        exit()
    try:
        os.system("clear")
        call_numbers.append(int(called))
    except ValueError:
        print("Invalid input. Please enter a valid number.")
    return call_numbers


def play_bingo():
    bingo_boards = []
    # Get Bingo Cards from directory
    list_bingo_cards = subprocess.check_output("ls " + bingo_card_path, shell=True)
    bingo_cards_array = list_bingo_cards.splitlines()
    bingo_cards_array = [filename.decode("utf-8") for filename in bingo_cards_array]

    # Question about what cards to play
    selected_cards = questionary.checkbox(
        "Select Cards:", choices=bingo_cards_array
    ).ask()

    # Add selected bingo cards into bingo_baords vairable
    for selected_card in selected_cards:
        bingo_boards.append(import_card(selected_card))

    # Question on game mode selection
    game_mode = questionary.select(
        "Select Game Mode", choices=["Full Card", "Corners", "Lines"]
    ).ask()

    numbers_called = []
    # Game Play Start
    while True:
        # Record Called Numbers
        numbers_called = called_numbers(numbers_called)

        # Iterate through each bingo board
        for i in range(len(bingo_boards)):
            if (
                bingo_check_for_win(bingo_boards[i], game_mode, numbers_called)
            ) is False:
                pass
            else:
                bingo_check_for_win(bingo_boards[i], game_mode, numbers_called)
                exit()

        # Display called numbers
        print("Game Mode: " + game_mode)
        print("Numbers Called:" + str(numbers_called))


play_bingo()
