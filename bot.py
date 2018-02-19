import discord, asyncio, sqlite3, random
from pathlib import Path

tokenID = '#Your Bot Token Goes here!'
serverID = '#Your Server ID Number here!'
channelID = '#Your Channel ID Number here!'

# All the necessary data goes to Data class objects
class Data:
    def __init__(self, serverID, channelID):
        self._answer = ''
        self._serverID = serverID
        self._channelID = channelID
        self._correct_answers = []

    @property
    def answer(self):
        return self._answer

    @answer.setter
    def answer(self, value):
        self._answer = value

    @property
    def serverID(self):
        return self._serverID
    
    @serverID.setter
    def serverID(self, value):
        self._serverID = value

    @property
    def channelID(self):
        return self._channelID

    @channelID.setter
    def channelID(self, value):
        self._channelID = value
    
    def add_correct_answer(self, user):
        self._correct_answers.append(user)

    def get_correct_answers(self):
        return self._correct_answers

    def reset_correct_answers(self):
        self._correct_answers = []

# Object od the Data class
data = Data(serverID, channelID)

client = discord.Client()

@client.event
async def on_ready():
    print('on_ready')
    populate_quiz_database()
    populate_contenders_database()
    await ask_question()

def populate_contenders_database():
    if Path("./contenders.db").exists():
        conn_contenders = sqlite3.connect('contenders.db')
        cursor_contenders = conn_contenders.cursor()
        cursor_contenders.execute('DROP TABLE contenders')
        conn_contenders.commit()
        conn_contenders.close()
    conn_contenders = sqlite3.connect('contenders.db')
    cursor_contenders = conn_contenders.cursor()
    cursor_contenders.execute('CREATE TABLE contenders (id integer primary key, username text, points integer)')
    conn_contenders.commit()
    conn_contenders.close()
    print("finished populating contenders")

def populate_quiz_database():
    if Path("./quiz.db").exists():
        conn_quiz = sqlite3.connect('quiz.db')
        cursor_quiz = conn_quiz.cursor()
        cursor_quiz.execute('DROP TABLE quiz')
        conn_quiz.commit()
        conn_quiz.close()
    conn_quiz = sqlite3.connect('quiz.db')
    cursor_quiz = conn_quiz.cursor()
    cursor_quiz.execute('CREATE TABLE quiz (id integer primary key, question text, answer text)')
    conn_quiz.commit()
    conn_quiz.close()
    # add the questions to the newly formed database here
    conn_quiz = sqlite3.connect('quiz.db')
    cursor_quiz = conn_quiz.cursor()
    with open('questions.txt', 'r') as f:
        for id, line in enumerate(f):
            line = line.strip('\n')
            question = line.split('#')
            cursor_quiz.execute('INSERT INTO quiz VALUES ("%d", "%s","%s")' % (id, question[0], question[1]))
            conn_quiz.commit()
    conn_quiz.close()
    print("finished populating quiz")

async def ask_question():
    conn_quiz = sqlite3.connect('quiz.db')
    cursor_quiz = conn_quiz.cursor()
    max_num = 0
    for row in cursor_quiz.execute("SELECT MAX(id) FROM quiz"):
        max_num = row[0]
    num = random.randint(1, max_num)
    result = cursor_quiz.execute('SELECT question, answer FROM quiz WHERE id={0}'.format(num))
    question = str()
    for row in result:
        question = row[0]
        data.answer = row[1]
    conn_quiz.close()
    wanted_channel = client.get_server(data.serverID).get_channel(data.channelID)
    await client.send_message(wanted_channel, question)
    await asyncio.sleep(15)
    data.reset_correct_answers()
    await ask_question()

@client.event
async def on_message(message):
    if message.content.upper() == data.answer.upper() and message.author not in data.get_correct_answers():
        try:
            # if it is correct answer for the first time on this question by this user
            data.add_correct_answer(message.author)
            conn_contenders = sqlite3.connect('contenders.db')
            cursor_contenders = conn_contenders.cursor()
            user_infos = str(message.author).split('#')
            cursor_contenders.execute('SELECT username, points FROM contenders WHERE id = ?', (int(user_infos[1]),))
            result = cursor_contenders.fetchone()
            if result is None:
                cursor_contenders.execute('INSERT INTO contenders VALUES ("%d", "%s", "%d")' % (int(user_infos[1]), user_infos[0], 1))
                conn_contenders.commit()
            else:
                cursor_contenders.execute('UPDATE contenders SET points = points + 1, username = "%s" WHERE id = "%d"' %(user_infos[0], int(user_infos[1])))
                conn_contenders.commit()
        except Exception:
            print("EXCEPTION on_message!")
            exit()
        finally:
            conn_contenders.close()
    elif str(message.content) == 'show ranking':
        await show_rankings()

async def show_rankings():
    conn_contenders = sqlite3.connect('contenders.db')
    cursor_contenders = conn_contenders.cursor()
    wanted_channel = client.get_server(data.serverID).get_channel(data.channelID)
    try:
        cursor_contenders.execute('SELECT * FROM contenders ORDER BY points DESC')
        result = cursor_contenders.fetchone()
        exit_msg = str()
        if result is None:
            exit_msg = 'Empty rankings\n'
        else:
            cursor_contenders.execute('SELECT * FROM contenders ORDER BY points DESC')
            top_contenders = cursor_contenders.fetchall()
            for item in top_contenders[:4]:
                exit_msg += '{0} points: {1}\n'.format(item[1], item[2])
        await client.send_message(wanted_channel, exit_msg)
    except Exception:
        print("EXCEPTION show_rankings!")
        exit()
    finally:
        conn_contenders.close()

client.run(tokenID)