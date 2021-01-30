import config
import telebot
import sqlite3
from datetime import date, timedelta
from telegram_bot_calendar import DetailedTelegramCalendar, LSTEP
import pandas as pd
import os
import logging
import matplotlib.pyplot as plt


try:
    os.system('python SendEmailLogs.py 1')
    os.remove('Bot.log')
    logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s',
                        level=logging.INFO,
                        filename='Bot.log'
                        )
    # токен бота
    bot = telebot.TeleBot(config.token)

    # список видов настроения
    mood_list = ['awfull', 'bad', 'okey', 'good', 'joyful']
    mood_dict = {'awfull': 1, 'bad': 2, 'okey': 3, 'good': 4, 'joyful': 5}
    mood_emoji_dict = {'1': '☹', '2': '🙁', '3': '😐', '4': '🙂', '5': '😀', '-':'-'}


    #клавиатуры
    back_button = 'menu'

    #меню
    menu_keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    menu_keyboard.row('check', 'analytics', 'check old')

    #вид настроения
    mood_keyboard = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    mood_keyboard.row(*mood_list).add(back_button)

    #вид аналитики
    analyse_keyboard = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    analyse_keyboard.row('Simple row', 'AI analyse', 'Chart', 'Pie Chart').add(back_button)

    # клавиатура интервалов
    interval_keyboard = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    interval_keyboard.row('за 10 дней', 'за 30 дней', 'за 90 дней', 'за все время').add(back_button)

    #клавиатура добавитть коммент
    comment_keyboard = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    comment_keyboard.row('Без комментариев')

    # клавиатура пользоователей с отзывами
    feedback_keyboard = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    feedback_keyboard.row('Аноним 1, 22 года, юрист').add(back_button)


    # создаем таблицу для данных, если ее нету
    conn = sqlite3.connect('mood.db')
    cur = conn.cursor()
    cur.execute('''
    CREATE TABLE IF NOT EXISTS mood_status (
       userid INT,
       date TEXT,
       status TEXT,
       commentary TEXT,
       primary key (userid, date)
        )
    ''')
    conn.commit()


    # ответ на системные сообщения через \слово
    #информация по боту
    @bot.message_handler(commands=['start', 'help'])
    def start_message(message):
        bot.send_message(message.chat.id,
                         '''
                         MoodCheckingBot v1.1
                         Это бот для мониторинга настроения.
                         Суть довольно проста: каждый день надо записывать какое у тебя настроение.
                         Потом можно посмотреть аналитику по этим статусам.
                         Очевидно, что если неделю плохое настроение, то надо брать отпуск, а если 3 недели - уволняться с работы.
                         Эту инструкцию можно всегда вызвать через команды /start или /help
                         Кнопки меню:
                         - check - записать/переписать статус настроения за текущий день;
                         - analytics - посмотреть аналитику;
                         - check old - изменить/добавить статус настроения за прошлые дни.
                         Также можно выгрузитьд данные в CSV через команду /export_csv.
                         Отзывы реальных пользователей - /feedbacks
                         ''', reply_markup=menu_keyboard)

    #рестарт
    @bot.message_handler(commands=['restart', 'rs'])
    def start_message(message):
        bot.send_message(message.chat.id, 'Choose action', reply_markup=menu_keyboard)

    #экспорт данных
    @bot.message_handler(commands=['export_csv'])
    def export_data(message):
        user_id = message.from_user.id

        conn = sqlite3.connect('mood.db')
        df = pd.read_sql_query(f'''
                        SELECT 
                        date, 
                        status, 
                        case when commentary = '' then null else commentary end commentary
                        FROM mood_status
                        where userid = {user_id}
                        ''', conn)
        df.to_csv('MyMoodTracker.csv', sep=';', index=False, encoding='utf-8')
        file = open('MyMoodTracker.csv', encoding='utf8')
        bot.send_document(message.chat.id, file, reply_markup=menu_keyboard)

    #отзывы
    @bot.message_handler(commands=['feedbacks'])
    def choose_feedbacker(message):
        msg = bot.send_message(message.chat.id, 'Выбери реалаьного пользователя из рандомного списка юзеров',
                               reply_markup=feedback_keyboard)
        bot.register_next_step_handler(msg, send_text)



    # реакци бота на сообщения
    @bot.message_handler(content_types=['text'])
    def send_text(message):
        if message.text.lower() == 'check':
            msg = bot.send_message(message.chat.id, 'Выбери настроение, которые у тебя в целом за сегодня',
                                   reply_markup=mood_keyboard)
            bot.register_next_step_handler(msg, check_today_mood)
        elif message.text.lower() == 'analytics':
            msg = bot.send_message(message.chat.id, 'Выбери интервал, за который AI будет анализировать данные',
                                   reply_markup=interval_keyboard)
            bot.register_next_step_handler(msg, get_interval)
        elif message.text.lower() == 'check old':
            calendar, step = DetailedTelegramCalendar(max_date=date.today()).build()
            bot.send_message(message.chat.id, f"Select {LSTEP[step]}", reply_markup=calendar)
            msg = bot.send_message(message.chat.id, 'Выбери СНАЧАЛА ДАТУ, потом настроение, которые было в тот день',
                                   reply_markup=mood_keyboard)
            bot.register_next_step_handler(msg, check_old_mood)

        elif message.text.lower() == 'menu':
            bot.send_message(message.chat.id, 'Choose action', reply_markup=menu_keyboard)

        elif message.text == 'Гюнель, 22 года, юрист':
            bot.send_message(message.chat.id,
                             '''
                             Гюнель:
                             Привет, меня зовут Гюнель, я юрист, закончила бакалавр МГЮА без 4... и 3 и 2 тоже не было. 
                             Сейчас я работаю в юридическое конторе и учусь на магистратуре. Еще я учу английский. В общем, обычная жизнь молодой, красивой, современной и успешной леди.
                             Но все же раньше я думала, что моя жизнь не очень веселая, но в какой-то момент мне попался билборд с рекламой бота MoodCheckingBot, я подумала: 
                             - А че, можно попробовать.
                             Вы знаете, после того, как я начала пользоваться ботом, моя жизнь поделилась на "до" и "после".
                             Я наконец-то поняла, что моя жизнь очень веселая. 
                             Когда же у меня неделю плохое настроение, при помощи бота я сразу это понимаю и тут же беру отпуск и улетаю на Бали.
                             А когда настроение не очень 3 недели, я просто меняю работу, все просто! Все просто с ботом MoodCheckingBot!
                             ''', reply_markup=menu_keyboard)

    #записывааем настроение в базу

    #опередляем insert или update
    def check_recording(user_id, dt):
        conn = sqlite3.connect('mood.db')
        cur = conn.cursor()
        cur.execute(f'''
                    SELECT count(*)
                    FROM mood_status
                    where userid = {user_id}
                    and date = '{dt}'
                    ''')
        recording_cnt = cur.fetchall()[0][0]
        if recording_cnt == 0:
            return 'insert'
        #else:
            #action_type = 'update'

    def check_today_mood(message):
        print('check_today_mood')
        if message.text in mood_list:
            user_id = message.from_user.id
            global dt
            dt = date.today()
            status = mood_dict[message.text.lower()]

            conn = sqlite3.connect('mood.db')
            cur = conn.cursor()
            #insert new
            if check_recording(user_id, dt) == 'insert':

                cur.execute(f'''
                        INSERT INTO mood_status(userid, date, status) 
                           VALUES({user_id}, '{dt}', '{status}')
                           ''')
                conn.commit()
                msg = bot.send_message(message.chat.id, 'Напиши комментарий', reply_markup=comment_keyboard)
                bot.register_next_step_handler(msg, get_analyse)
            #update old
            else:
                cur.execute(f'''
                        update mood_status
                        set status = '{status}'
                        where userid = {user_id}
                        and date = '{dt}'
                        ''')
                conn.commit()
                msg = bot.send_message(message.chat.id, 'Напиши комментарий', reply_markup=comment_keyboard)
                bot.register_next_step_handler(msg, add_commentary)

    def check_old_mood(message):
        print('check_old_mood')
        if message.text.lower() in mood_list:
            #выбрана дата, потом статус
            try:
                user_id = message.from_user.id
                global dt
                dt = update_dt
                status = mood_dict[message.text.lower()]

                conn = sqlite3.connect('mood.db')
                cur = conn.cursor()

                if check_recording(user_id, dt) == 'insert':
                    cur.execute(f'''
                            INSERT INTO mood_status(userid, date, status) 
                               VALUES({user_id}, '{dt}', '{status}')
                               ''')
                    conn.commit()
                    msg = bot.send_message(message.chat.id, 'Напиши комментарий', reply_markup=comment_keyboard)
                    bot.register_next_step_handler(msg, add_commentary)
                else:
                    cur.execute(f'''
                            update mood_status
                            set status = '{status}'
                            where userid = {user_id}
                            and date = '{dt}'
                            ''')
                    conn.commit()
                    msg = bot.send_message(message.chat.id, 'Напиши комментарий', reply_markup=comment_keyboard)
                    bot.register_next_step_handler(msg, add_commentary)
            except:
                calendar, step = DetailedTelegramCalendar(max_date=date.today()).build()
                bot.send_message(message.chat.id, f"Select {LSTEP[step]}", reply_markup=calendar)
                msg = bot.send_message(message.chat.id,
                                       '''Не так, выбери СНАЧАЛА ДАТУ, потом настроение, которое было в тот день, ван мо трай''',
                                       reply_markup=mood_keyboard)
                bot.register_next_step_handler(msg, check_old_mood)


    #добавляем комментарии
    def add_commentary(message):
        if message.text == 'Без комментариев':
            bot.send_message(message.chat.id, 'Ну ладно. Все записал', reply_markup=menu_keyboard)
        else:
            user_id = message.from_user.id
            commentary = message.text
            conn = sqlite3.connect('mood.db')
            cur = conn.cursor()
            cur.execute(f'''
                update mood_status
                set commentary = '{commentary}'
                where userid = {user_id}
                and date = '{dt}'
                        ''')
            conn.commit()
            bot.send_message(message.chat.id, 'Все записал', reply_markup=menu_keyboard)


    def get_interval(message):
        global interval_cnt
        if message.text == 'за 10 дней':
            interval_cnt = 10
            msg = bot.send_message(message.chat.id, 'Выбери вид анализа', reply_markup=analyse_keyboard)
            bot.register_next_step_handler(msg, get_analyse)
        elif message.text == 'за 30 дней':
            interval_cnt = 30
            msg = bot.send_message(message.chat.id, 'Выбери вид анализа', reply_markup=analyse_keyboard)
            bot.register_next_step_handler(msg, get_analyse)
        elif message.text == 'за 90 дней':
            interval_cnt = 90
            msg = bot.send_message(message.chat.id, 'Выбери вид анализа', reply_markup=analyse_keyboard)
            bot.register_next_step_handler(msg, get_analyse)
        elif message.text == 'за все время':
            interval_cnt = 9999
            msg = bot.send_message(message.chat.id, 'Выбери вид анализа', reply_markup=analyse_keyboard)
            bot.register_next_step_handler(msg, get_analyse)


    def get_analyse(message):
        if message.text == 'Simple row':
            user_id = message.from_user.id
            simple_output = ''
            end_dt = date.today()
            start_dt = date.today() + timedelta(days=-interval_cnt+1)
            print(start_dt)

            conn = sqlite3.connect('mood.db')
            cur = conn.cursor()
            cur.execute(f'''
                with 
                t0 as (
                select 
                start_dt, 
                cast(julianday('{end_dt}') - julianday(start_dt) as integer) nn
                from (
                    select 
                    case 
                        when {interval_cnt} > 100 and min(date) > '{start_dt}' then '{start_dt}'
                        when {interval_cnt} > 100 and min(date) <= '{start_dt}' then min(date) 
                        when {interval_cnt} < 100 and min(date) > '{start_dt}' then min(date)
                        else '{start_dt}'
                        end start_dt
                    from mood_status
                    where userid = {user_id}
                    and date!='-' 
                )),
    
                series(n) as (
                select 1 
                    union all
                select n+1 
                from series, t0 
                where n < nn
                ),
                
                t1 as (
                select n, '{end_dt}' dt, '-'|| (n-1) ||' day' param
                from series
                ), 
    
                t2 as (
                select date('{end_dt}', param) ndt
                from t1
                ),
    
                t3 as (
                select ndt,
                case when status is null then '-' else status end status
                from t2
                left join (select 
                            date, 
                            status 
                            from mood_status
                            where userid = {user_id}) tt on t2.ndt=tt.date
                )
    
                select status
                from t3 
                where ndt>= (select min(ndt) mdt from t3 where status != '-')
                order by ndt
                    ''')
            all_data = cur.fetchall()
            for i in all_data:
                for j in i:
                    emoji = mood_emoji_dict[j]
                    simple_output += emoji
            bot.send_message(message.chat.id, simple_output, reply_markup=menu_keyboard)

        elif message.text == 'AI analyse':
            user_id = message.from_user.id
            simple_output = ''
            end_dt = date.today()
            start_dt = date.today() + timedelta(days=-interval_cnt + 1)

            conn = sqlite3.connect('mood.db')
            cur = conn.cursor()
            cur.execute(f'''
                with 
                t0 as (
                select 
                start_dt, 
                cast(julianday('{end_dt}') - julianday(start_dt) as integer) nn
                from (
                    select 
                    case 
                        when {interval_cnt} > 100 and min(date) > '{start_dt}' then '{start_dt}'
                        when {interval_cnt} > 100 and min(date) <= '{start_dt}' then min(date) 
                        when {interval_cnt} < 100 and min(date) > '{start_dt}' then min(date)
                        else '{start_dt}'
                        end start_dt
                    from mood_status
                    where userid = {user_id}
                    and date!='-'
                )),
    
                series(n) as (
                select 1 
                    union all
                select n+1 
                from series, t0 
                where n < nn
                ),
    
                t1 as (
                select n, '{end_dt}' dt, '-'|| (n-1) ||' day' param
                from series
                ), 
    
                t2 as (
                select date('{end_dt}', param) ndt
                from t1
                ),
    
                t3 as (
                select ndt,
                case when status is null then '-' else status end status
                from t2
                left join (select 
                            date, 
                            status 
                            from mood_status
                            where userid = {user_id}) tt on t2.ndt=tt.date
                )
    
                select avg(status) avg_status
                from t3 
                where ndt>= (select min(ndt) mdt from t3 where status != '-')
                and status !='-'
                    ''')
            AI_result = int(cur.fetchall()[0][0])
            if AI_result <= 1:
                #bot.send_sticker(message.chat.id, 'You need help')
                bot.send_sticker(message.chat.id, 'CAACAgIAAxkBAAIJUWADCE4YHpTTfFqttc-ggUruZSYlAAL4AwACierlByp3dvbJG_twHgQ',
                                 reply_markup=menu_keyboard)
            elif AI_result <= 2:
                #bot.send_sticker(message.chat.id, 'You are not okey')
                bot.send_sticker(message.chat.id, 'CAACAgIAAxkBAAIJUGADCCIB5XTa4bJSjAlMoqcE5i-AAAJ0AQACD8emDmYg1q0EQ_rpHgQ',
                                 reply_markup=menu_keyboard)
            elif AI_result <= 3:
                #bot.send_sticker(message.chat.id, 'You are okey')
                bot.send_sticker(message.chat.id, 'CAACAgIAAxkBAAIJT2ADB_u2RoLMvUZHi-eBrPuFu00vAAI8AQACD8emDlUQHmOieHlHHgQ',
                                 reply_markup=menu_keyboard)
            elif AI_result <= 4:
                #bot.send_sticker(message.chat.id, 'You are better than okey')
                bot.send_sticker(message.chat.id, 'CAACAgEAAxkBAAIJTWADBxZ61c23FVnXVbG9FHyctiI1AAIMAAOhBQwN78Ogo7d0iDEeBA',
                                 reply_markup=menu_keyboard)
            else:
                #bot.send_sticker(message.chat.id, 'You are super okey')
                bot.send_sticker(message.chat.id, 'CAACAgIAAxkBAAIJTmADB9_CxJ3ymZ89OKC8IAJTOjdCAAJ-CAACXAJlA-ncQYpBipakHgQ',
                                 reply_markup=menu_keyboard)

        elif message.text == 'Chart':
            user_id = message.from_user.id
            end_dt = date.today()
            start_dt = date.today() + timedelta(days=-interval_cnt + 1)

            conn = sqlite3.connect('mood.db')
            df = pd.read_sql_query(f'''
                with 
                t0 as (
                select 
                start_dt, 
                cast(julianday('{end_dt}') - julianday(start_dt) as integer) nn
                from (
                    select 
                    case 
                        when {interval_cnt} > 100 and min(date) > '{start_dt}' then '{start_dt}'
                        when {interval_cnt} > 100 and min(date) <= '{start_dt}' then min(date) 
                        when {interval_cnt} < 100 and min(date) > '{start_dt}' then min(date)
                        else '{start_dt}'
                        end start_dt
                    from mood_status
                    where userid = {user_id}
                    and date!='-'
                )),
    
                series(n) as (
                select 1 
                    union all
                select n+1 
                from series, t0 
                where n < nn
                ),
    
                t1 as (
                select n, '{end_dt}' dt, '-'|| (n-1) ||' day' param
                from series
                ), 
    
                t2 as (
                select date('{end_dt}', param) ndt
                from t1
                ),
    
                t3 as (
                select ndt,
                case when status is null then null else status end status
                from t2
                left join (select 
                            date, 
                            status 
                            from mood_status
                            where userid = {user_id}) tt on t2.ndt=tt.date
                )
    
                select ndt Dates, cast(status as integer) Moods
                from t3 
                where ndt>= (select min(ndt) mdt from t3 where status != '-')
                order by ndt
                ''', conn)
            df.plot('Dates','Moods', kind='bar')
            plt.savefig('MoodDiagram.jpeg', dpi=100, bbox_inches='tight')
            bot.send_photo(message.chat.id, open('MoodDiagram.jpeg', 'rb'), reply_markup=menu_keyboard)

        elif message.text == 'Pie Chart':
            user_id = message.from_user.id
            end_dt = date.today()
            start_dt = date.today() + timedelta(days=-interval_cnt + 1)

            conn = sqlite3.connect('mood.db')
            df = pd.read_sql_query(f'''
                    with 
                    t0 as (
                    select 
                    start_dt, 
                    cast(julianday('{end_dt}') - julianday(start_dt) as integer) nn
                    from (
                        select 
                        case 
                            when {interval_cnt} > 100 and min(date) > '{start_dt}' then '{start_dt}'
                            when {interval_cnt} > 100 and min(date) <= '{start_dt}' then min(date) 
                            when {interval_cnt} < 100 and min(date) > '{start_dt}' then min(date)
                            else '{start_dt}'
                            end start_dt
                        from mood_status
                        where userid = {user_id}
                        and date!='-'
                    )),
        
                    series(n) as (
                    select 1 
                        union all
                    select n+1 
                    from series, t0 
                    where n < nn
                    ),
        
                    t1 as (
                    select n, '{end_dt}' dt, '-'|| (n-1) ||' day' param
                    from series
                    ), 
        
                    t2 as (
                    select date('{end_dt}', param) ndt
                    from t1
                    ),
        
                    t3 as (
                    select ndt,
                    case when status is null then null else status end status
                    from t2
                    left join (select 
                                date, 
                                status 
                                from mood_status
                                where userid = {user_id}) tt on t2.ndt=tt.date
                    )
        
                    select 
                    case 
                    when status = '1' then 'awful' 
                    when status = '2' then 'bad'
                    when status = '3' then 'okay'
                    when status = '4' then 'good'
                    else 'joyful'
                    end Moods, 
                    count(status) Percentage
                    from t3 
                    where status is not null
                    and ndt >= (select min(ndt) mdt from t3 where status != '-')
                    group by status
                    order by count(status)
                    ''', conn)
            status = df.Moods
            df.plot('Moods', 'Percentage', kind='pie', autopct='%1.1f%%', labels=None, title='Наглядый график-кружок', ylabel='').legend(status, loc='best')
            plt.savefig('MoodDiagram.jpeg', dpi=100, bbox_inches='tight')
            bot.send_photo(message.chat.id, open('MoodDiagram.jpeg', 'rb'), reply_markup=menu_keyboard)


    # для календаря, выбор даты
    @bot.callback_query_handler(func=DetailedTelegramCalendar.func())
    def cal(c):
        result, key, step = DetailedTelegramCalendar(max_date=date.today()).process(c.data)
        if not result and key:
            bot.edit_message_text(f"Select {LSTEP[step]}",
                                  c.message.chat.id,
                                  c.message.message_id,
                                  reply_markup=key)
        elif result:
            global update_dt
            update_dt = result


    @bot.message_handler(content_types=['document'])
    def handle_file(message):
        bot.send_message(message.chat.id, 'Ты отправил файл, поздравляю')

    bot.polling()
except Exception as e:
    print(e)
    print('restart')
    #os.system('python MoodCheckingBot_4.py 1')
