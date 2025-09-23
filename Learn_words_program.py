import sys
import json
from PyQt5.QtWidgets import (QApplication, QWidget, QPushButton, QLabel, QButtonGroup, QTabWidget, QHBoxLayout,
                             QVBoxLayout, QRadioButton, QLineEdit, QComboBox, QListWidget)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPixmap
import requests
import random

class LearnApp(QWidget):
    def __init__(self):
        super().__init__()
        #add word widgets
        self.english_input = QLineEdit(self)
        self.translate_word = QLineEdit(self)
        self.word_info_label = QLabel('Выберете сложность', self)
        self.radio_level_hard = QRadioButton('Hard', self)
        self.radio_level_middle = QRadioButton('Middle', self)
        self.radio_level_easy = QRadioButton('Easy', self)
        self.learned_label = QLabel('Вы слышали это слово?', self)
        self.radio_learned_yes = QRadioButton('Yes', self)
        self.radio_learned_no = QRadioButton('No', self)
        self.category_label = QLabel('Выберете категорию')
        self.category_combo = QComboBox()
        self.add_word_button = QPushButton('Add', self)
        self.level_group_radio = QButtonGroup()
        self.learned_group_radio = QButtonGroup()

        #cards widgets
        self.prev_page_button = QPushButton('<', self)
        self.next_page_button = QPushButton('>', self)
        self.card_label = QLabel(self)
        self.english_word_label = QLabel(self)
        self.translated_word_label = QLabel(self)

        #tests widgets
        self.image_label = QLabel('image', self)
        self.button1 = QPushButton(self)
        self.button2 = QPushButton(self)
        self.button3 = QPushButton(self)
        self.button4 = QPushButton(self)

        #stats widgets
        self.static_title_label = QLabel('|Your Statistic|')
        self.total_words_label = QLabel(self)
        self.learned_words_label = QLabel(self)
        self.message_label = QLabel(self)

        #dictionary widgets
        self.title_label = QLabel('Your Dictionary', self)
        self.dictionary_words_list = QListWidget(self)
        self.delete_button = QPushButton('Delete', self)

        #tabs
        self.tabs = QTabWidget()
        self.add_word_tab = QWidget()
        self.cards_tab = QWidget()
        self.tests_tab = QWidget()
        self.stats_tab = QWidget()
        self.dictionary_tab = QWidget()

        #other
        self.current_index = -1
        self.initUI()
        self.show_words_and_image()
        self.show_dictionary()
        self.show_test()
        self.show_stats()

    def initUI(self):
        #css for items
        self.english_input.setObjectName('english_input')
        self.translate_word.setObjectName('translate_word')
        self.add_word_button.setObjectName('add_word_button')
        self.word_info_label.setObjectName('word_info_label')
        self.radio_level_hard.setObjectName('radio_level_hard')
        self.radio_level_middle.setObjectName('radio_level_middle')
        self.radio_level_easy.setObjectName('radio_level_easy')
        self.learned_label.setObjectName('learned_label')
        self.radio_learned_yes.setObjectName('radio_learned_yes')
        self.radio_learned_no.setObjectName('radio_learned_no')
        self.category_label.setObjectName('category_label')
        self.category_combo.setObjectName('category_combo')
        self.prev_page_button.setObjectName('prev_page_button')
        self.next_page_button.setObjectName('next_page_button')
        self.card_label.setObjectName('card_label')
        self.english_word_label.setObjectName('english_word_label')
        self.translated_word_label.setObjectName('translated_word_label')
        self.title_label.setObjectName('title_label')
        self.dictionary_words_list.setObjectName('dictionary_words_list')
        self.delete_button.setObjectName('delete_button')
        self.image_label.setObjectName('image_label')
        self.button1.setObjectName('button1')
        self.button2.setObjectName('button2')
        self.button3.setObjectName('button3')
        self.button4.setObjectName('button4')
        self.static_title_label.setObjectName('static_title_label')
        self.total_words_label.setObjectName('total_words_label')
        self.learned_words_label.setObjectName('learned_words_label')
        self.message_label.setObjectName('message_label')

        self.setStyleSheet("""
            QLineEdit#english_input,QLineEdit#translate_word{
                font-size: 30px;
                font-family: Calibri;
                color: hsl(360, 83%, 9%);
            }
            QPushButton#add_word_button, QPushButton#prev_page_button, QPushButton#next_page_button,
            QPushButton#button1,QPushButton#button2, QPushButton#button3, QPushButton#button4{
                font-size: 30px;
                font-family: Calibri;
                background-color: hsl(110, 80%, 45%);
                color: white;
                font-style: bold;
            }
            QLabel#word_info_label,QLabel#category_label,QLabel#learned_label, QLabel#card_label,
            QLabel#english_word_label, QLabel#translated_word_label, QLabel#image_label,
            QLabel#static_title_label, QLabel#total_words_label, QLabel#learned_words_label, QLabel#message_label{
                font-size: 25px;
                font-style: italic;
                font-family: Arial;
                font-weight: bold;
            }
            QRadioButton#radio_level_hard,QRadioButton#radio_level_middle,
            QRadioButton#radio_level_easy,QRadioButton#radio_learned_yes,QRadioButton#radio_learned_no{
                font-size: 20px;
            }
            QComboBox#category_combo{
                font-size:20x;
                font-family: Arial;
            }
            QLabel#title_label{
                font-size: 40px;
                font-style: italic;
                font-family: Arial;
                color: purple;
            }
            QListWidget#dictionary_words_list {
                font-size: 18px;
                font-family: 'Calibri';
                background-color: #f5f5f5;
                alternate-background-color: #e9e9e9;
                border-radius: 6px;
                border: 1px solid #c0c0c0;
                padding: 5px;
            }
            
            QListWidget#dictionary_words_list::item {
                padding: 8px;
                border-bottom: 1px solid #e0e0e0;
            }
            
            QListWidget#dictionary_words_list::item:selected {
                background-color: #5cb85c;
                color: hsl(354, 67%, 17%);
            }
            
            QListWidget#dictionary_words_list::item:hover {
                background-color: #d4edda;
            }
            QPushButton#delete_button{
                font-size: 30px;
                color: white;
                background-color: red;
                border: 2px solid hsl(354, 100%, 31%);
                border-radius: 10px
            }
        """)

        # загальнні зміни
        self.setWindowTitle('English Words Learning Program')
        self.english_input.setPlaceholderText('Введите слово:')
        self.translate_word.setPlaceholderText('Введите перевод:')
        self.category_combo.addItem('', 'none')
        self.category_combo.addItem('Food', 'food')
        self.category_combo.addItem('Transport', 'transport')
        self.category_combo.addItem('Feelings', 'feelings')
        self.category_combo.addItem('Medicine', 'medicine')
        self.category_combo.addItem('Clothes', 'clothes')
        self.category_combo.addItem('Technique', 'technique')
        self.category_combo.addItem('Nature', 'nature')
        self.category_combo.addItem('Animals', 'animals')
        self.category_combo.addItem('Travel', 'travel')
        self.category_combo.addItem('Home', 'home')
        self.category_combo.addItem('Funds', 'funds')
        self.learned_label.setAlignment(Qt.AlignCenter)
        self.word_info_label.setAlignment(Qt.AlignCenter)
        self.category_label.setAlignment(Qt.AlignCenter)
        self.card_label.setAlignment(Qt.AlignCenter)
        self.english_word_label.setAlignment(Qt.AlignCenter)
        self.translated_word_label.setAlignment(Qt.AlignCenter)
        self.title_label.setAlignment(Qt.AlignTop)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.static_title_label.setAlignment(Qt.AlignCenter)
        self.total_words_label.setAlignment(Qt.AlignCenter)
        self.learned_words_label.setAlignment(Qt.AlignCenter)
        self.message_label.setAlignment(Qt.AlignCenter)

        # розділив радіо на 2 групи
        self.level_group_radio.addButton(self.radio_level_hard)
        self.level_group_radio.addButton(self.radio_level_middle)
        self.level_group_radio.addButton(self.radio_level_easy)

        self.learned_group_radio.addButton(self.radio_learned_yes)
        self.learned_group_radio.addButton(self.radio_learned_no)

        #додаю таб на екран
        self.tabs.addTab(self.add_word_tab, 'Add Word')
        self.tabs.addTab(self.cards_tab, 'Cards')
        self.tabs.addTab(self.tests_tab, 'Tests')
        self.tabs.addTab(self.stats_tab, 'Statistics')
        self.tabs.addTab(self.dictionary_tab, 'Dictionary')

        #add_word_layout
        add_word_layout = QVBoxLayout(self.add_word_tab)

        add_word_layout.addWidget(self.english_input)
        add_word_layout.addWidget(self.translate_word)
        add_word_layout.addWidget(self.word_info_label)
        add_word_layout.addWidget(self.radio_level_hard)
        add_word_layout.addWidget(self.radio_level_middle)
        add_word_layout.addWidget(self.radio_level_easy)
        add_word_layout.addWidget(self.learned_label)
        add_word_layout.addWidget(self.radio_learned_yes)
        add_word_layout.addWidget(self.radio_learned_no)
        add_word_layout.addWidget(self.category_label)
        add_word_layout.addWidget(self.category_combo)
        add_word_layout.addWidget(self.add_word_button)

        #cards_layout
        cards_layout = QVBoxLayout(self.cards_tab)
        buttons_layout = QHBoxLayout()
        words_layout = QHBoxLayout()
        cards_layout.addWidget(self.card_label)

        buttons_layout.addWidget(self.prev_page_button)
        buttons_layout.addWidget(self.next_page_button)

        words_layout.addWidget(self.english_word_label)
        words_layout.addWidget(self.translated_word_label)

        cards_layout.addLayout(buttons_layout)
        cards_layout.addLayout(words_layout)

        #tests_layout
        tests_layout = QVBoxLayout(self.tests_tab)
        tests_layout.addWidget(self.image_label)
        buttons_layout1 = QHBoxLayout()
        tests_layout.addLayout(buttons_layout1)

        buttons_layout1.addWidget(self.button1)
        buttons_layout1.addWidget(self.button2)
        buttons_layout1.addWidget(self.button3)
        buttons_layout1.addWidget(self.button4)

        #stats_layout
        stats_layout = QVBoxLayout(self.stats_tab)
        stats_layout.addWidget(self.static_title_label)
        stats_layout.addWidget(self.total_words_label)
        stats_layout.addWidget(self.learned_words_label)
        stats_layout.addWidget(self.message_label)

        #dictionary_layout
        dictionary_layout = QVBoxLayout(self.dictionary_tab)
        dictionary_layout.addWidget(self.title_label)
        dictionary_layout.addWidget(self.dictionary_words_list)
        dictionary_layout.addWidget(self.delete_button)

        #main_layout
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(self.tabs)

        self.setLayout(main_layout)

        #дав команду для кнопки
        self.add_word_button.clicked.connect(self.save_data)
        self.prev_page_button.clicked.connect(self.prev_page)
        self.next_page_button.clicked.connect(self.next_page)
        self.delete_button.clicked.connect(self.delete)
        self.button1.clicked.connect(self.button1_clicked)
        self.button2.clicked.connect(self.button2_clicked)
        self.button3.clicked.connect(self.button3_clicked)
        self.button4.clicked.connect(self.button4_clicked)

    def get_data(self):
        word = self.english_input.text()
        translate = self.translate_word.text()
        if self.radio_level_hard.isChecked():
            level = 'hard'
        elif self.radio_level_middle.isChecked():
            level = 'middle'
        elif self.radio_level_easy.isChecked():
            level = 'easy'
        else:
            level = 'none'
        learned = self.radio_learned_yes.isChecked()
        category = self.category_combo.currentData()
        image_url = self.get_image(word)
        self.word_data = {
            'word': word,
            'translate': translate,
            'level': level,
            'learned': learned,
            'category': category,
            'image_url': image_url
        }
        return self.word_data

    def save_data(self):
        data = self.get_data()
        if data['word'] and data['translate']:
            try:
                try:
                    with open('words_data.json', 'r', encoding='utf-8') as file:
                        content = file.read().strip()
                        if content:
                            existing_data = json.loads(content)
                            if not isinstance(existing_data, list):
                                existing_data = [existing_data]
                        else:
                            existing_data = []
                except (FileNotFoundError, json.JSONDecodeError):
                    existing_data = []

                if any(data['word'] == self.english_input.text() or data['translate'] == self.translate_word.text() for data in existing_data):
                    print('This word is already exist')
                    return

                existing_data.append(data)
                with open('words_data.json', 'w', encoding='utf-8') as file:
                    json.dump(existing_data, file, indent=4, ensure_ascii=False)
            except Exception as e:
                print(f'Error saving data {str(e)}')

                with open('words_data.json', 'w', encoding='utf-8') as file:
                    json.dump([data], file, indent=4, ensure_ascii=False)

        else:
            print('Fill both inputs')
            return
        self.show_stats()
        self.show_test()
        self.show_words_and_image()
        self.show_dictionary()

        self.english_input.clear()
        self.translate_word.clear()
        self.level_group_radio.setExclusive(False)
        self.radio_level_hard.setChecked(False)
        self.radio_level_middle.setChecked(False)
        self.radio_level_easy.setChecked(False)
        self.level_group_radio.setExclusive(True)
        self.learned_group_radio.setExclusive(False)
        self.radio_learned_yes.setChecked(False)
        self.radio_learned_no.setChecked(False)
        self.learned_group_radio.setExclusive(True)
        self.category_combo.setCurrentIndex(0)

    def get_image(self, name):
        if not name:
            self.card_label.setText('Enter some text -_0')
            return
        try:
            access_key = 'jTNq1BAH2K-ob6PfdHb2n-D69nLmLf9Ebw86Frt6RcA'
            url = f'https://api.unsplash.com/photos/random?query={name}&client_id={access_key}'
            response = requests.get(url)
            response.raise_for_status()

            image_data = response.json()
            #print(image_data)
            url_data = image_data['urls']['regular']

            img_response = requests.get(url_data)
            img_response.raise_for_status()

            image = QPixmap()
            image.loadFromData(img_response.content)

            if not image.isNull():
                self.card_label.setPixmap(image.scaled(300,300, Qt.KeepAspectRatio))
                return url_data
            else:
                self.card_label.setText(f'Picture for {name} does not found')
                return
        except requests.RequestException:
            print(f'Error: {requests.RequestException}')
            self.card_label.setText(f'Error')
            return

    def show_words_and_image(self):
        try:
            with open('words_data.json', 'r', encoding='utf-8') as file:
                words_data = json.load(file)

            if words_data:
                last_word = words_data[-1]

                self.english_word_label.setText(last_word.get('word', ''))
                self.translated_word_label.setText(last_word.get('translate', ''))

                image_url = last_word.get('image_url', '')
                if image_url:
                    image_response = requests.get(image_url)
                    if image_response.status_code == 200:
                        image = QPixmap()
                        image.loadFromData(image_response.content)
                        self.card_label.setPixmap((image.scaled(300,300, Qt.KeepAspectRatio)))
                    else:
                        self.card_label.setText('Picture not found')
                else:
                    self.card_label.setText('Picture not found')
            else:
                self.card_label.setText('Data is empty')
        except (FileNotFoundError, json.JSONDecodeError):
            self.card_label.setText('File does not exist')
        except Exception as error:
            print(f'{error}')
            self.card_label.setText('Error')

    def prev_page(self):
        try:
            with open('words_data.json', 'r', encoding='utf-8') as file:
                words_data = json.load(file)
            if words_data:
                self.current_index -= 1

                if self.current_index < 0:
                    self.current_index = len(words_data) - 1

                word = words_data[self.current_index]['word']
                translate = words_data[self.current_index]['translate']

                self.english_word_label.setText(word)
                self.translated_word_label.setText(translate)

                image_url = words_data[self.current_index].get('image_url')
                if image_url:
                    response = requests.get(image_url)
                    image = QPixmap()
                    image.loadFromData(response.content)
                    self.card_label.setPixmap(image.scaled(300,300, Qt.KeepAspectRatio))
                else:
                    self.card_label.setText('Picture not found')
        except Exception:
            self.english_word_label.setText('Error')
            self.translated_word_label.setText('Error')
            self.card_label.setText('Error')

    def next_page(self):
        try:
            with open('words_data.json', 'r', encoding='utf-8') as file:
                words_data = json.load(file)

            if words_data:
                self.current_index += 1

                if self.current_index > len(words_data)-1:
                    self.current_index = 0

                word = words_data[self.current_index]['word']
                translate = words_data[self.current_index]['translate']

                self.english_word_label.setText(word)
                self.translated_word_label.setText(translate)

                image_url = words_data[self.current_index].get('image_url')
                if image_url:
                    response = requests.get(image_url)
                    image = QPixmap()
                    image.loadFromData(response.content)
                    self.card_label.setPixmap(image.scaled(300,300, Qt.KeepAspectRatio))
                else:
                    self.card_label.setText('Picture not found')
        except Exception:
            self.english_word_label.setText('Error')
            self.translated_word_label.setText('Error')
            self.card_label.setText('Error')

    def delete(self):
        row = self.dictionary_words_list.currentRow()
        if row >= 0 :
            self.dictionary_words_list.takeItem(row)
        try:
            with open('words_data.json', 'r', encoding='utf-8') as file:
                data = json.load(file)
                data.pop(row)
            with open('words_data.json', 'w', encoding='utf-8') as file:
                json.dump(data, file, indent=4, ensure_ascii=False)

            if data:
                self.show_words_and_image()
            else:
                self.card_label.setText('No words are saved')
                self.english_word_label.setText('')
                self.translated_word_label.setText('')
            self.show_test()
            self.show_stats()

        except Exception as error:
            print(f'{error}')

    def show_test(self):
        #list of buttons and words if data does not exist
        buttons = [self.button1, self.button2, self.button3, self.button4]
        data_not_exist_words = ['word', 'word', 'word', 'word']
        try:
            with open('words_data.json', 'r', encoding='utf-8') as file:
                #get data from file
                data = json.load(file)
                #check if data exist
                if not data:
                    self.image_label.setText('Your dictionary is empty')
                    for i in range(4):
                        buttons[i].setText(data_not_exist_words[i])
                    return

                #check if index less than length of data
                if self.current_index >= len(data):
                    self.current_index = 0

                #get image url for image label
                image_url = data[self.current_index]['image_url']

                #get word from data by index
                word = data[self.current_index]['word']

                #list of random words for other buttons
                random_words = ['apple', 'river', 'cloud', 'music', 'python',
                    'forest', 'dream', 'light', 'coffee', 'mirror',
                    'flower', 'rocket', 'sunset', 'island', 'mountain',
                    'shadow', 'keyboard', 'window', 'storm', 'feather',
                    'castle', 'banana', 'planet', 'ocean', 'whisper',
                    'desert', 'camera', 'candle', 'dragon', 'pencil',
                    'butterfly', 'guitar', 'moonlight', 'treasure', 'glacier',
                    'squirrel', 'volcano', 'raindrop', 'tunnel', 'lantern',
                    'notebook', 'pyramid', 'journey', 'horizon', 'compass',
                    'jungle', 'firework', 'crystal', 'valley', 'rainbow'
                                ]
                #set image on image label
                if image_url:
                    response = requests.get(image_url)
                    image = QPixmap()
                    image.loadFromData(response.content)
                    self.image_label.setPixmap(image.scaled(300, 300, Qt.KeepAspectRatio))

                #pick randomly index for correct button
                correct_button = random.randint(0, 3)

                #save that index in variable
                self.correct_button_index = correct_button

                #list of 3 random words
                words = []

                #loop for getting 3 random words
                for _ in range(3):
                    random_word = random.choice(random_words)
                    while random_word == word or random_word in words:
                        random_word = random.choice(random_words)
                    words.append(random_word)

                #loop for setting text on buttons
                for i in range(4):
                    if i == correct_button:
                        buttons[i].setText(word)
                    else:
                        buttons[i].setText(words.pop())
        except FileNotFoundError:
            self.image_label.setText('Data does not exist')
            for i in range(4):
                buttons[i].setText(data_not_exist_words[i])
        except Exception as error:
            print(f'{error}')

    #checking answer
    def check_answer(self, index):
        try:
            with open('words_data.json', 'r', encoding='utf-8') as file:
                #get data from file
                data = json.load(file)

                #get index
                curr_index = self.current_index
                if index == self.correct_button_index:
                    if not data[curr_index]['learned']:
                        data[curr_index]['learned'] = True

                    with open('words_data.json', 'w', encoding='utf-8') as file:
                        json.dump(data, file, indent=4, ensure_ascii=False)

        except Exception as error:
            print(f'{error}')
        if index == self.correct_button_index:
            self.image_label.setText('Correct!')
            self.current_index += 1
            QTimer.singleShot(1000, self.show_test)

        else:
            self.image_label.setText('Incorrect!')
            QTimer.singleShot(1000, self.show_test)

    def button1_clicked(self):
        self.check_answer(0)

    def button2_clicked(self):
        self.check_answer(1)

    def button3_clicked(self):
        self.check_answer(2)

    def button4_clicked(self):
        self.check_answer(3)

    def show_stats(self):
        try:
            with open('words_data.json', 'r', encoding='utf-8') as file:
                # get data from file
                data = json.load(file)
                total_words = len(data)
                learned_words = 0
                for word in data:
                    if word['learned'] == True:
                        learned_words += 1
                self.total_words_label.setText(f'Total words: {total_words}')
                self.learned_words_label.setText(f'Learned words: {learned_words}')
                if learned_words >= (total_words / 2):
                    self.message_label.setText('You doing well!')
                else:
                    self.message_label.setText('You should work harder!')

        except Exception as error:
            self.total_words_label.setText('Your list is empty')
            print(f'{error}')

    def show_dictionary(self):
        try:
            self.dictionary_words_list.clear()

            with open('words_data.json', 'r', encoding='utf-8') as file:
                data = json.load(file)
                for i in range(len(data)):
                    word = data[i]['word']
                    translate = data[i]['translate']
                    self.dictionary_words_list.addItem(f'{word} - {translate}')
        except Exception as error:
            self.dictionary_words_list.addItem('Your list is empty')
            print(f'{error}')


if __name__ == '__main__':
    app = QApplication(sys.argv)
    lear_words_app = LearnApp()
    lear_words_app.show()
    sys.exit(app.exec_())