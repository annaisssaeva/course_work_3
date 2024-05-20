from flask import Flask, render_template, request, redirect, url_for, send_file
import sqlite3
from flask_cors import cross_origin
import random
from datetime import datetime
from datetime import timedelta
import timeit
import numpy as np
import pyttsx3
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import ForeignKey, PrimaryKeyConstraint
from sqlalchemy.orm import relationship
from flask_login import LoginManager, UserMixin, current_user, login_user, logout_user, AnonymousUserMixin
import time
import simpleaudio as sa
import simpleaudio.functionchecks as fc
import soundfile
import datetime
import wave
from backend import words_sorted, sents

#print(sents)

engine = pyttsx3.init()
engine.setProperty('rate', 130)
#engine.save_to_file('Задания с предложениями. Поместите руки на клавиатуру так, чтобы мизинец левой руки был на клавише фэ. Безымянный палец — на клавише ыы. Средний – на вэ. Указательный на а. Мизинец правой руки на клавише жэ. Безымянный на клавише дэ. Средний на эл. Указательный на оо.', 'sent_instr.wav')
#engine.runAndWait()
#engine.save_to_file('Отлично! Ответ правильный.', "static/audio/good_result1.wav")
#engine.save_to_file('Вы ответили правильно, супер!', "static/audio/good_result2.wav")
#engine.save_to_file('Ответ правильный, молодец!', "static/audio/good_result3.wav")
#engine.save_to_file('К сожалению, ответ неверный. Попробуйте еще раз.', "static/audio/bad_result1.wav")
#engine.save_to_file('Ой! Ответ неправильный. Не отчаивайтесь и попробуйте еще раз.', "static/audio/bad_result2.wav")


#engine.runAndWait()


near_stims = 'фывапролджэё'
ex_types = ['Задания с буквами', "Задания со слогами", "Задания со словами", "Задания спредложениями"]
away_stims = 'йцукенгшщзхъячсмитьбю'
good_words = ['Отлично! Ответ правильный.', "Вы ответили правильно, супер!", "Ответ правильный, молодец!"]
all_stims = 'фывапролджэёйцукенгшщзхъячсмитьбю'
wovels = 'уеыаоэёяию'
consonants = 'йцкнгшщзхфвпрлджчсмтб'
stim = random.choice(all_stims)
stim2 = random.choice(consonants) + random.choice(wovels)



app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///small11111111111.db"
app.config["SECRET_KEY"] = "ENTER YOUR SECRET KEY"
db = SQLAlchemy()


login_manager = LoginManager()
login_manager.init_app(app)
db.init_app(app)


#модели
class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column("id", db.Integer, primary_key=True)
    username = db.Column(db.String(250), unique=True, nullable=False)
    password = db.Column(db.String(250), nullable=False)
    words_to_go = db.Column("words_to_go", db.Text)
    sents_to_go = db.Column("sents_to_go", db.Text)


#class Words(db.Model):
   # __tablename__ = "words"

    #words_id = db.Column("words_id", db.Integer, primary_key=True)
    #words_to_go = db.Column("words_to_go", db.Text)

    #user_id = db.Column('user', db.Integer, ForeignKey('users.id'))
    #user = db.relationship('User')





class Answer(db.Model):
    __tablename__ = "answers"
    answer_id = db.Column("answer_id", db.Integer, primary_key=True)

    time = db.Column("time", db.Float)
    type_of_exercise = db.Column("type_of_exercise", db.Text)
    exercise = db.Column("exercise", db.Text)
    answer = db.Column("answer", db.Text)
    mistake = db.Column("mistake", db.Boolean)


    user_id = db.Column('user', db.Integer, ForeignKey('users.id'))
    user = db.relationship('User')


with app.app_context():
    db.create_all()
    db.session.commit()

# Initialize app with extension

# Create database within app context

# Creates a user loader callback that returns the user object given an id
@login_manager.user_loader
def loader_user(user_id):
    return User.query.get(user_id)



@app.route('/register', methods=["GET", "POST"])
def register():
    if request.method == "POST":
        user = User(username=request.form.get("username"),
                     password=request.form.get("password"),
                    words_to_go=str(words_sorted)[2:-2],
                    sents_to_go=str(sents)[2:-2])
        db.session.add(user)
        db.session.commit()

        #words = Words(user_id=user.id,
        #              words_to_go=str(words_sorted)[2:-1])
        #db.session.add(words)
        #db.session.commit()
        return redirect(url_for("login"))
    return render_template("sign_up.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    try:
        if request.method == "POST":
            user = User.query.filter_by(
                username=request.form.get("username")).first()
            if user.password == request.form.get("password"):
                login_user(user)
                return redirect(url_for("main"))
        return render_template("login.html")
    except AttributeError:
        return render_template("login_error.html")


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("main"))




@app.route('/')
def index():
    return render_template('main.html')

@app.route('/main')
def main():
    if isinstance(current_user, AnonymousUserMixin):
        return render_template('main.html')
    else:
        return render_template('main.html', username=current_user.username)

@app.route('/main')
def play_audio():
    audio_path = 'static/audio/sent_instr.wav'  # Replace with the path to your audio file
    return send_file(audio_path, mimetype='audio/mp3', as_attachment=True)



###############################
#буквы
###############################
start = datetime.datetime.now()
previous_difference = []
previous_difference.append(timedelta(hours=0, minutes=0, seconds=0))
num_mists = 0
@app.route('/exercise', methods=['POST', "GET"])
def exercise():
    #задаем значения стимула и похвалу
    global num_mists
    global stim
    global good_words
    global all_stims
    message = ''
    print(stim)
    print(num_mists)


    if request.method == 'POST':
        #получаем ответ
        ans = request.form.get('exercise')
        #находим время, за которе ввели ответ
        diff = datetime.datetime.now() - start
        time_diff = diff - previous_difference[-1]
        previous_difference.append(diff)
        print(time_diff)

        #если ответ правильный
        if ans == stim:
            num_mists = 0

            #выбираем похвалу, которая выведется на экран, и следующий стимул
            message = random.choice(good_words)
            stim = random.choice(all_stims)


            #выбираем какую похвалу озвучиваем
            file_path = random.choice(["static/audio/good_result1.wav", "static/audio/good_result2.wav", "static/audio/good_result3.wav"])
            data, samplerate = soundfile.read(file_path)
            soundfile.write(file_path, data, samplerate)

            #проигрываем похвалу
            wave_obj = sa.WaveObject.from_wave_file(file_path)
            play = wave_obj.play()
            play.wait_done()
            play.stop()

            if isinstance(current_user, AnonymousUserMixin):
                return render_template('exercise.html', stim=stim, message=message)
            else:
                # заносим информацию в базу данных
                answer = Answer(time=float(time_diff.total_seconds()),
                                type_of_exercise=ex_types[0],
                                exercise=stim,
                                answer=ans,
                                mistake=False,
                                user_id=current_user.id)
                db.session.add(answer)
                db.session.commit()

                return render_template('exercise.html', stim=stim, message=message)

        #если ответ неправильный
        else:
            num_mists += 1
            message = "К сожалению, неверно."

            # выбираем какую похвалу ощвучиваем
            file_path = random.choice(
                ["static/audio/bad_result1.wav", "static/audio/bad_result2.wav"])
            data, samplerate = soundfile.read(file_path)
            soundfile.write(file_path, data, samplerate)

            # проигрываем похвалу
            wave_obj = sa.WaveObject.from_wave_file(file_path)
            play = wave_obj.play()
            play.wait_done()
            play.stop()

            if isinstance(current_user, AnonymousUserMixin):

                return render_template('exercise.html', stim=stim, message=message)
            else:
                answer = Answer(time=float(time_diff.total_seconds()),
                                type_of_exercise=ex_types[0],
                                exercise=stim,
                                answer=ans,
                                mistake=True,
                                user_id=current_user.id)
                db.session.add(answer)
                db.session.commit()
                if num_mists <= 2:
                    return render_template('exercise.html', stim=stim, message=message)
                else:
                    stim = random.choice(all_stims)
                    num_mists = 0
                    return render_template('exercise.html', stim=stim, message=message)


    return render_template('exercise.html', stim=stim, message=message)


###############################
#слоги
###############################
start = datetime.datetime.now()
previous_difference = []
previous_difference.append(timedelta(hours=0, minutes=0, seconds=0))
num_mists2 = 0
@app.route('/exercise2', methods=['POST', "GET"])
def exercise2():
    #задаем значения стимула и похвалу
    global stim2
    global good_words
    global wovels
    global consonants
    global num_mists2
    message = ''
    print(stim2)

    if request.method == 'POST':
        #получаем ответ
        ans = request.form.get('exercise')
        #находим время, за которе ввели ответ
        diff = datetime.datetime.now() - start
        time_diff = diff - previous_difference[-1]
        previous_difference.append(diff)
        print(time_diff)

        #если ответ правильный
        if ans == stim2:
            num_mists2 = 0

            #выбираем похвалу, которая выведется на экран, и следующий стимул
            message = random.choice(good_words)
            stim2 = random.choice(consonants) + random.choice(wovels)


            #выбираем какую похвалу озвучиваем
            file_path = random.choice(["static/audio/good_result1.wav", "static/audio/good_result2.wav", "static/audio/good_result3.wav"])
            data, samplerate = soundfile.read(file_path)
            soundfile.write(file_path, data, samplerate)

            #проигрываем похвалу
            wave_obj = sa.WaveObject.from_wave_file(file_path)
            play = wave_obj.play()
            play.wait_done()
            play.stop()

            if isinstance(current_user, AnonymousUserMixin):
                return render_template('exercise2.html', stim=stim2, message=message)
            else:
                # заносим информацию в базу данных
                answer = Answer(time=float(time_diff.total_seconds()),
                                type_of_exercise=ex_types[1],
                                exercise=stim2,
                                answer=ans,
                                mistake=False,
                                user_id=current_user.id)
                db.session.add(answer)
                db.session.commit()

                return render_template('exercise2.html', stim=stim2, message=message)

        #если ответ неправильный
        else:
            num_mists2 += 1
            message = "К сожалению, неверно."

            # выбираем какую похвалу ощвучиваем
            file_path = random.choice(
                ["static/audio/bad_result1.wav", "static/audio/bad_result2.wav"])
            data, samplerate = soundfile.read(file_path)
            soundfile.write(file_path, data, samplerate)

            # проигрываем похвалу
            wave_obj = sa.WaveObject.from_wave_file(file_path)
            play = wave_obj.play()
            play.wait_done()
            play.stop()


            if isinstance(current_user, AnonymousUserMixin):
                return render_template('exercise2.html', stim=stim2, message=message)
            else:
                answer = Answer(time=float(time_diff.total_seconds()),
                                type_of_exercise=ex_types[1],
                                exercise=stim2,
                                answer=ans,
                                mistake=True,
                                user_id=current_user.id)
                db.session.add(answer)
                db.session.commit()

                if num_mists2 <= 2:
                    return render_template('exercise2.html', stim=stim2, message=message)
                else:
                    num_mists2 = 0
                    stim2 = random.choice(consonants) + random.choice(wovels)
                    return render_template('exercise2.html', stim=stim2, message=message)
    return render_template('exercise2.html', stim=stim2, message=message)



###############################
#слова
###############################
start = datetime.datetime.now()
previous_difference = []
previous_difference.append(timedelta(hours=0, minutes=0, seconds=0))
num_mists3 = 0
stim3 = random.choice(words_sorted)
@app.route('/exercise3', methods=['POST', "GET"])
def exercise3():
    # задаем значения стимула и похвалу
    global good_words
    #global wovels
    #global consonants
    global num_mists3
    global stim3

    if not isinstance(current_user, AnonymousUserMixin):
        #stim3 = random.choice(words_sorted)
    #else:
        #w_t_g = Words.query.filter_by(user_id=current_user.id).first()
        w_t_g = current_user.words_to_go
        stim3 = w_t_g.split("', '")[0]

    message = ''
    print(stim3)
    #print(current_user.words_to_go)


    if request.method == 'POST':
        # получаем ответ
        ans = request.form.get('exercise')
        # находим время, за которе ввели ответ
        diff = datetime.datetime.now() - start
        time_diff = diff - previous_difference[-1]
        previous_difference.append(diff)
        print(time_diff)

        # если ответ правильный
        if ans == stim3:
            num_mists3 = 0

            # выбираем похвалу, которая выведется на экран, и следующий стимул
            message = random.choice(good_words)



            #stim3 = current_user.words_to_go.split("\', \'")[0]

            # выбираем какую похвалу озвучиваем
            file_path = random.choice(
                ["static/audio/good_result1.wav", "static/audio/good_result2.wav", "static/audio/good_result3.wav"])
            data, samplerate = soundfile.read(file_path)
            soundfile.write(file_path, data, samplerate)

            # проигрываем похвалу
            wave_obj = sa.WaveObject.from_wave_file(file_path)
            play = wave_obj.play()
            play.wait_done()
            play.stop()

            if isinstance(current_user, AnonymousUserMixin):
                stim3 = random.choice(words_sorted)
                return render_template('exercise3.html', stim=stim3, message=message)
            else:

                current_user.words_to_go = str(current_user.words_to_go.split("', '")[1:])[2:-2]
                print("heyyy")
                db.session.commit()

                # заносим информацию в базу данных
                answer = Answer(time=float(time_diff.total_seconds()),
                                type_of_exercise=ex_types[2],
                                exercise=stim3,
                                answer=ans,
                                mistake=False,
                                user_id=current_user.id)
                db.session.add(answer)
                db.session.commit()

                w_t_g = current_user.words_to_go
                stim3 = w_t_g.split("', '")[0]
                print(stim3)

                return render_template('exercise3.html', stim=stim3, message=message)

        # если ответ неправильный
        else:
            num_mists3 += 1
            message = "К сожалению, неверно."

            # выбираем какую похвалу ощвучиваем
            file_path = random.choice(
                ["static/audio/bad_result1.wav", "static/audio/bad_result2.wav"])
            data, samplerate = soundfile.read(file_path)
            soundfile.write(file_path, data, samplerate)

            # проигрываем похвалу
            wave_obj = sa.WaveObject.from_wave_file(file_path)
            play = wave_obj.play()
            play.wait_done()
            play.stop()

            if isinstance(current_user, AnonymousUserMixin):
                stim3 = random.choice(words_sorted)
                return render_template('exercise3.html', stim=stim3, message=message)
            else:
                answer = Answer(time=float(time_diff.total_seconds()),
                                type_of_exercise=ex_types[2],
                                exercise=stim3,
                                answer=ans,
                                mistake=True,
                                user_id=current_user.id)
                db.session.add(answer)
                db.session.commit()

                if num_mists3 <= 2:
                    return render_template('exercise3.html', stim=stim3, message=message)
                else:
                    num_mists3 = 0

                    left_words = current_user.words_to_go.split("', '")[1:]
                    print(left_words)
                    left_words.append(stim3)

                    current_user.words_to_go = str(left_words)[2:-2]
                    print("heyyy")
                    db.session.commit()

                    w_t_g = current_user.words_to_go
                    stim3 = w_t_g.split("', '")[0]


                    return render_template('exercise3.html', stim=stim3, message=message)
    return render_template('exercise3.html', stim=stim3, message=message)



###############################
#предложения
###############################
start = datetime.datetime.now()
previous_difference = []
previous_difference.append(timedelta(hours=0, minutes=0, seconds=0))
num_mists4 = 0
stim4 = random.choice(sents)
@app.route('/exercise4', methods=['POST', "GET"])
def exercise4():
    # задаем значения стимула и похвалу
    global good_words
    global num_mists4
    global stim4

    if not isinstance(current_user, AnonymousUserMixin):
        #stim4 = random.choice(sents)
    #else:
        # w_t_g = Words.query.filter_by(user_id=current_user.id).first()
        s_t_g = current_user.sents_to_go
        stim4 = s_t_g.split("', '")[0]

    message = ''
    print(stim4)
    #print(current_user.sents_to_go)

    if request.method == 'POST':
        # получаем ответ
        ans = request.form.get('exercise')
        # находим время, за которе ввели ответ
        diff = datetime.datetime.now() - start
        time_diff = diff - previous_difference[-1]
        previous_difference.append(diff)
        print(time_diff)

        # если ответ правильный
        if ans == stim4:
            num_mists4 = 0

            # выбираем похвалу, которая выведется на экран, и следующий стимул
            message = random.choice(good_words)

            # stim3 = current_user.words_to_go.split("\', \'")[0]

            # выбираем какую похвалу озвучиваем
            file_path = random.choice(
                ["static/audio/good_result1.wav", "static/audio/good_result2.wav", "static/audio/good_result3.wav"])
            data, samplerate = soundfile.read(file_path)
            soundfile.write(file_path, data, samplerate)

            # проигрываем похвалу
            wave_obj = sa.WaveObject.from_wave_file(file_path)
            play = wave_obj.play()
            play.wait_done()
            play.stop()

            if isinstance(current_user, AnonymousUserMixin):
                stim4 = random.choice(sents)
                return render_template('exercise4.html', stim=stim4, message=message)
            else:


                current_user.sents_to_go = str(current_user.sents_to_go.split("', '")[1:])[2:-2]
                print("heyyy")
                db.session.commit()

                # заносим информацию в базу данных
                answer = Answer(time=float(time_diff.total_seconds()),
                                type_of_exercise=ex_types[3],
                                exercise=stim4,
                                answer=ans,
                                mistake=False,
                                user_id=current_user.id)
                db.session.add(answer)
                db.session.commit()

                s_t_g = current_user.sents_to_go
                stim4 = s_t_g.split("', '")[0]
                print(stim4)

                return render_template('exercise4.html', stim=stim4, message=message)

        # если ответ неправильный
        else:
            num_mists4 += 1
            message = "К сожалению, неверно."

            # выбираем какую похвалу ощвучиваем
            file_path = random.choice(
                ["static/audio/bad_result1.wav", "static/audio/bad_result2.wav"])
            data, samplerate = soundfile.read(file_path)
            soundfile.write(file_path, data, samplerate)

            # проигрываем похвалу
            wave_obj = sa.WaveObject.from_wave_file(file_path)
            play = wave_obj.play()
            play.wait_done()
            play.stop()

            if isinstance(current_user, AnonymousUserMixin):
                stim4 = random.choice(sents)
                return render_template('exercise4.html', stim=stim4, message=message)
            else:
                answer = Answer(time=float(time_diff.total_seconds()),
                                type_of_exercise=ex_types[3],
                                exercise=stim4,
                                answer=ans,
                                mistake=True,
                                user_id=current_user.id)
                db.session.add(answer)
                db.session.commit()

                if num_mists4 <= 2:
                    return render_template('exercise4.html', stim=stim4, message=message)
                else:
                    num_mists4 = 0

                    left_sents = current_user.sents_to_go.split("', '")[1:]
                    print(left_sents)
                    left_sents.append(stim4)

                    current_user.sents_to_go = str(left_sents)[2:-2]
                    print("heyyy")
                    db.session.commit()

                    s_t_g = current_user.sents_to_go
                    stim4 = s_t_g.split("', '")[0]

                    return render_template('exercise4.html', stim=stim4, message=message)
    return render_template('exercise4.html', stim=stim4, message=message)


#return render_template('exercise4.html')




@app.route('/progress')
def progress():
    if isinstance(current_user, AnonymousUserMixin):
        return render_template('no_progress.html')


    users_answers = Answer.query.filter_by(user_id = current_user.id).all()
    time_all = 0
    time1 = 0
    time2 = 0
    time3 = 0
    time4 = 0
    for answ in users_answers:
        time_all += float(answ.time)
        if answ.type_of_exercise == ex_types[0]:
            print('bukvi')
            time1 += float(answ.time)
        elif answ.type_of_exercise == ex_types[1]:
            print('slogi')
            time2 += float(answ.time)
        elif answ.type_of_exercise == ex_types[2]:
            print('slogi')
            time3 += float(answ.time)
        elif answ.type_of_exercise == ex_types[3]:
            print('slogi')
            time4 += float(answ.time)





    return render_template('progress.html',
                           username=current_user.username,
                           id=current_user.id,
                           time_all=int(time_all/60),
                           time1=int(time1/60),
                           time2=int(time2/60),
                           time3=int(time3/60),
                           time4=int(time4/60))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=15555, debug=True)
