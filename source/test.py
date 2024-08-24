#from PIL import Image 
from pytesseract import pytesseract 
import cv2
from tabulate import tabulate
import os
import logging


def scan_card(path,iterations,x):
    image = cv2.imread(path)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (3,3), 0)
    thresh = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]

    # Morph open to remove noise and invert image
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (x,x))
    opening = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel, iterations=iterations)
    invert = 255 - opening

    whitelist = "0123456789 "
    config = f"--psm 6 -c tessedit_char_whitelist={whitelist}"


    # Perform text extraction
    scan = pytesseract.image_to_string(invert, lang='eng', config=config)
    return (scan)
    #Data formating 
    #cv2.imwrite('/workspaces/python-2/output/output1.png', kernel)
    #cv2.imwrite('/workspaces/python-2/output/output2.png', invert)




#Validate bingo lines and return bingo game lines
def line_validation(scan):
    bingo_lines = []
    #Split data into lines
    lines = scan.splitlines()
    #Remove Empty Spaces In Line
    cleaned_lines = [line.replace(" ", "") for line in lines]
    cleaned_lines = [cleaned_lines for cleaned_lines in cleaned_lines if cleaned_lines]

    #Count Number of digits in each line
    valid = 0
    for line in cleaned_lines:
        number_of_digits = len(line)
    
        
        #Validate number of digits in each line
        if (valid != 2 and number_of_digits in [9,10]) or (valid == 2 and number_of_digits in [7,8]) :
            valid +=1
            logging.info("Valid passed:"+str(valid))
            bingo_lines.append(line)
        else:
            logging.info ("Valid failed:"+str(valid)+" Number of digits="+str(number_of_digits)+ " On line="+str(cleaned_lines))
            logging.info ("Error on line ranges")
            pass
    #Check total nuber of lines and number validation
    if len(bingo_lines) != 5:
        logging.info("Error all bingo lines were not detected")
        return False
    #Check Free Space Line
    if len(bingo_lines[2]) not in [7,8]:
        logging.info ("Error on Free Space Line with Length Check")
        return False
    
    #Check number validation of bingo card
    bingo_board = create_bingo_board(bingo_lines)
    low = 1
    high = 15
    for i in range(5):
        for number in bingo_board:
            #print (number[i])
            if number[i] == -1 or (low <= int(number[i]) <= high):
                #print ("pass")
                pass
            else:
                print("Number out of range: "+number[i])
                return False
        low+=15
        high+=15
    logging.warn("Validation Passed")
    return (bingo_lines)
        



#Create Bingo Board grid
def create_bingo_board(bingo_lines):
    bingo_board = []
    for line in bingo_lines:
        if len(line) % 2 == 0: #Check for Even
            # Split the line into chunks of 2 characters
            chunks = [line[i:i+2] for i in range(0, len(line), 2)]
            bingo_board.append(chunks)
            
        if len(line) % 2 != 0: #Check for odd
           
            first_chunk = line[0:1]  # First chunk of 1 character
            remaining_chunks = [line[i:i+2] for i in range(1, len(line), 2)]  # Remaining chunks of 2 characters

            # Combine the chunks
            chunks = [first_chunk] + remaining_chunks
            bingo_board.append(chunks)

         
    #Add free space
    bingo_board[2].insert(2,-1)
    return (bingo_board)

#Identified Called Numbers
def identify_called_numbers(bingo_board, call_numbers):
    x=0
    while x<=4:
        y=0
        while y<=4:
            if int(bingo_board[x][y]) in call_numbers:
                bingo_board[x][y] = -1
                #print (bingo_board[x][y]) #List found numbers    
            y+=1
        x+=1
    return (bingo_board)
         
def game_fullcard(bingo_board):
    bingo= 0
    x=0
    while x<=4:
        y=0
        while y<=4:
            if bingo_board[x][y] == -1:
                bingo+=1  
            else:
                pass
            y+=1
        x+=1
    if bingo==25:
        return True

def game_lines(bingo_board): 
    rows = bingo_board 
    cols = [[bingo_board[j][i] for j in range(5)] for i in range(5)] 
    diags = [[bingo_board[i][i] for i in range(5)], [bingo_board[i][4-i] for i in range(5)]] 
    lines = rows + cols + diags
    for line in lines: 
        if len(set(line)) == 1 and line[0] != 0: 
            return True
    return False

    

def game_fourcorners(bingo_board):
    
    if bingo_board[0][0] == -1 and bingo_board[0][4] == -1 and bingo_board[4][0] == -1 and bingo_board[4][4] == -1:
        return True
    else:
        return False


def import_card():
    #ScanCard
    validation_passed = False
    path = input("Enter Game Card Path: ")
    for interaction in range(1,7):
        for x in range (1,6):
            scan = scan_card(path, interaction, x)
            validation_check = line_validation(scan)
            if validation_check is False:
                logging.warning("Validation Failed on: Interaction="+str(interaction)+" and x="+str(x))
            else:
                validation_passed = True
                break
        if validation_passed:
            logging.warning("Validation Passed on: Interaction="+str(interaction)+" and x="+str(x))
            break
  

    
    #CreateCard
    if validation_passed:
        bingo_board = create_bingo_board(validation_check)
    else:
        logging.warning("Bingo Card could not be read / validated")
        exit ()
    return (bingo_board)
    



def play_bingo(bingo_board):
    
    play_bingo_board = []
    #Select Game mode
    try:
        mode = int(input("Game mode Selection (1)Full card, (2)Corners, (3)Lines: "))    
    except ValueError:
        print("Invalid input. Please enter a valid number.")
        exit()
    #Enter Called Numbers
    call_numbers = []
    while True:
        play_bingo_board = []
        
        #Display
        os.system('clear')
        print (tabulate(bingo_board,tablefmt="grid"))
        print ("Called Numbers (Below)")
        print (call_numbers)
        
        call = input("Enter called number or type stop:")
        if call.lower() == 'stop':
            break
        try:
            call_numbers.append(int(call)) 
            #Display called numbers
            print("Numbers Called:" + str(call_numbers))
            play_bingo_board = identify_called_numbers(bingo_board,call_numbers)
        except ValueError:
            print("Invalid input. Please enter a valid number.")
            continue
        
        
        #Game modes win conidtions
        if int(mode) == 1:
            bingo = game_fullcard(play_bingo_board)
            if bingo is True:
                 #Display
                os.system('clear')
                print (tabulate(bingo_board,tablefmt="grid"))
                print ("Called Numbers (Below)")
                print (call_numbers)
                print ("BINGO!!!!")
                break
        elif int(mode) == 2:
            bingo = game_fourcorners(play_bingo_board)
            if bingo is True:
                os.system('clear')
                print (tabulate(bingo_board,tablefmt="grid"))
                print ("Called Numbers (Below)")
                print (call_numbers)
                print ("BINGO!!!!")                
                break
        elif int(mode) == 3:
            bingo = game_lines(play_bingo_board)
            if bingo is True:
                os.system('clear')
                print (tabulate(bingo_board,tablefmt="grid"))
                print ("Called Numbers (Below)")
                print (call_numbers)
                print ("BINGO!!!!")
                break
    return (bingo)

play_bingo(import_card())
