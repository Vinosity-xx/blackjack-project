Hello! This is my submission for the Blackjack assignment implemented in Python and Django. The application is UI-Based and should feature all of the requirements mentioned in the PDF file. 

Overview: 

- Standard Blackjack rules
	- Card dealing
	- Standard win conditions
- Betting system with mock currency
	- Ability to bet any size within given bankroll
	- Winnings/losses calculated and given correctly
	- Standard "Double Down" feature that is commonly found at most Blackjack tables
	- Ability to split hands if player gets a pair of the same card. 
- Web-based Django UI
	- Adjusted CSS to make it seem more "casino-like".  
	- Simple but sleek UI that allows for fast games. 
	- Saves game state based on user session.

Prerequisites (What I used):

- Python 3.10.2 (or higher)
- Django 5.2.7 (or higher)
- Git

How to use:

Step 1: Clone the repo

- Install Git
- In terminal, run: git clone https://github.com/Vinosity-xx/blackjack-project

Step 2: Setup Virtual Environment

- python -m venv blackjack
- blackjack\Scripts\activate

Step 3: Install Dependencies

- pip install -r requirements.txt

Step 4: Start Django server and run application

- python manage.py runserver
- Navigate to webpage: http://127.0.0.1:8000/

Step 5: Enjoy blackjack!