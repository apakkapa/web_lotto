from socket import gethostname
from flask import Flask, render_template, request, flash, url_for, Markup

from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import IntegerField, DateField, SubmitField, ValidationError
from wtforms.validators import InputRequired, NumberRange
from flask_bootstrap import Bootstrap
from bs4 import BeautifulSoup

import requests
import logging
import os
import random
import lxml

MSG_ERR_RANGE = 'Enter a number between 1 an 36'
MSG_ERR_PB = 'Powerball must be between 1 and 10'
MSG_ERR_NO = 'Please enter a number'
MSG_ERR_DRAW = 'Please enter a draw number'
MAX_NOS = 5
DISP_COLORS = {True: 'bg-success', False:'bg-danger'}
WINNINGS = {
    (3,False): '$5',
    (3,True): '$25',
    (4, False): '$250',
    (4,True): '$1,500',
    (5,False): '$50,000',
    (5,True): 'the LOTTO'
}

COMPANIES = {
    0 : ('Holbote Handles', 'Software solutions imagined', 'https://www.hobote_handles.com'),
    1 : ('IBM', 'We are you. We are blue', 'https://www.ibm.com'),
    2 : ('CINEMAX', 'watch me now', 'https://www.cinemax.com'),
    3 : ("Joe's Traders", 'We buy, sell and trade everything', 'https://www.traderjoe.com')
}

TITBITS = {
    0: 'select draw_date, draw_winners, max(draw_estimate) from lotto_numbers',
    1: """
        SELECT
            sum(draw_winners),
            sum(draw_estimate)
        FROM
            lotto_numbers
        where
            draw_winners>0 order by  draw_estimate desc
        """,
    2: """
        select ball, count(ball) from (select ball_1 as ball from lotto_numbers
        UNION ALL
        select ball_2 as ball from lotto_numbers
        UNION ALL
        select ball_3 as ball from lotto_numbers
        UNION ALL
        select ball_4 as ball from lotto_numbers
        UNION ALL
        select ball_5 as ball from lotto_numbers) as balls
        GROUP BY ball
        order by  count(ball)
        """,
    3: 'You won',
    4: 'We even'
}


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///lotto_number.db'
app.config['SECRET_KEY'] = '124&secret@l%1**10!@#floatsia((7&5^'
Bootstrap(app)
db = SQLAlchemy(app)
logging.basicConfig(
    filename='lotto.log',
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s %(name)s %(threadName)s : %(message)s')


class LottoNumbers(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    draw_no = db.Column(db.Integer, unique=True)
    draw_date = db.Column(db.Text, unique=True)
    draw_estimate = db.Column(db.Float)
    draw_winners = db.Column(db.Integer)
    ball_1 = db.Column(db.Integer)
    ball_2 = db.Column(db.Integer)
    ball_3 = db.Column(db.Integer)
    ball_4 = db.Column(db.Integer)
    ball_5 = db.Column(db.Integer)
    ball_6 = db.Column(db.Integer)  #powerball

    def __repr__(self):
        pass

    @classmethod
    def titbit(cls, no):
        pass

    @classmethod
    def get_draw_numbers(cls, draw_no):
        pass

    @classmethod
    def scrape_data_from_url(cls, url, draw_no):
        draw_date, balls, power_ball, jackpot, no_of_winners = None,  [], None, 0, 0

        response = requests.get(f'{url}/?drawnumber={draw_no}')
        if response.status_code != 200:
            return (None, draw_date, balls, power_ball, jackpot, no_of_winners)

        html = response.text
        soup = BeautifulSoup(html, 'lxml')
        balls = [ball.text for ball in soup.find_all('div', {'class':'lotto-balls'})]

        if not balls:
            return (None, draw_date, balls, power_ball, jackpot, no_of_winners)

        power_ball_div = soup.find('div', {'class':'yellow-ball'})

        if not power_ball_div:
            return (None, draw_date, balls, power_ball, jackpot, no_of_winners)

        power_ball = power_ball_div.text
        draw_date = soup.find('div', {'class': 'drawDetails'}).div.strong.text

        power_ball_parent = power_ball_div.parent
        nnnn = power_ball_parent.next_sibling
        jackpot_div = nnnn.next_sibling

        # jackpot and no_of_winner do not always exist
        jackpot, no_of_winners = 0, 0
        if jackpot_div is not None:
            jackpot =  jackpot_div.text
            jackpot_pos = jackpot.find('Jackpot')
            if jackpot_pos > -1:
                jackpot = jackpot[len('Jackpot')+1:]
                jackpot = jackpot.replace('$','').replace(',','').replace(' ','')
                no_of_winners_div = jackpot_div.next_sibling
                no_of_winners = no_of_winners_div.text
            else:
                jackpot = 0

        return (draw_no, draw_date, balls, power_ball, jackpot, no_of_winners)

    @classmethod
    def add_data_to_db(cls, draw_no, draw_date, balls, power_ball, jackpot, no_of_winners):
        pass


class UsersPick(FlaskForm):
    draw_no = IntegerField('Draw #', [InputRequired(MSG_ERR_DRAW)])
    n1 = IntegerField('i', [InputRequired(MSG_ERR_NO), NumberRange(1,36,MSG_ERR_RANGE)])
    n2 = IntegerField('ii', [InputRequired(MSG_ERR_NO), NumberRange(1,36,MSG_ERR_RANGE)])
    n3 = IntegerField('iii', [InputRequired(MSG_ERR_NO), NumberRange(1,36,MSG_ERR_RANGE)])
    n4 = IntegerField('iv', [InputRequired(MSG_ERR_NO), NumberRange(1,36,MSG_ERR_RANGE)])
    n5 = IntegerField('v', [InputRequired(MSG_ERR_NO), NumberRange(1,36,MSG_ERR_RANGE)])
    power_ball = IntegerField('pb', [InputRequired(MSG_ERR_NO), NumberRange(1,10,MSG_ERR_PB)])
    submit = SubmitField('Check Numbers')

    def validate_on_submit(self):
        if not super().validate_on_submit():
            return False
        s = {self.n1.data, self.n2.data, self.n3.data, self.n4.data, self.n5.data}
        if len(s) == MAX_NOS:
            return True
        else:
            self.draw_no.errors.append("Numbers cannot be duplicated")
            return False


    def numbers_match(self, db_nos, numbers_entered):
        return db_nos.intersection(numbers_entered)

    def check_nos(self, db_nos):
        db_nos_set = {x for x in db_nos}
        return db_nos_set.intersection({self.n1.data, self.n2.data, self.n3.data, self.n4.data, self.n5.data })


@app.route('/', methods=['GET', 'POST'])
def main_menu():
    def pluralize(word, number):
        if (number == 0) or (number>1):
            return f'{word}s'
        else:
            return word
    def and_or_but(n):
        if n!=0:
            return 'and'
        return 'but'

    form = UsersPick()
    class_colors = ['', '', '', '', '', '']
    if form.validate_on_submit():
        # check draw for numbers in database
        # if not found check for number on web and add numbers to database
        # if not found on web then display draw not available
        # display nos
        #
        #
        #db_nos = LottoNumbers.get_draw_numbers(form.draw_no.data)
        s = LottoNumbers.query.filter_by(draw_no=form.draw_no.data).first()
        if not s: #try scaping the web
            url = 'http://www.nlcbplaywhelotto.com/nlcb-lotto-plus-results'
            draw_no, draw_date, balls, power_ball, jackpot, no_of_winners = LottoNumbers.scrape_data_from_url(url, form.draw_no.data)
            if draw_no is not None:
                s = LottoNumbers(
                    draw_no=draw_no,
                    draw_date=draw_date,
                    ball_1=balls[0],
                    ball_2=balls[1],
                    ball_3=balls[2],
                    ball_4=balls[3],
                    ball_5=balls[4],
                    ball_6= power_ball,
                    draw_estimate=jackpot,
                    draw_winners=no_of_winners
                    )
                db.session.add(s)
                db.session.commit()

        if s:
            db_nos = (s.ball_1, s.ball_2, s.ball_3, s.ball_4, s.ball_5)
            #now look at the set intersection of db_nos &  nos_entered

            nos = form.check_nos(db_nos)
            l_nos = len(nos)
            class_colors[0] = DISP_COLORS[form.n1.data in db_nos]
            class_colors[1] = DISP_COLORS[form.n2.data in db_nos]
            class_colors[2] = DISP_COLORS[form.n3.data in db_nos]
            class_colors[3] = DISP_COLORS[form.n4.data in db_nos]
            class_colors[4] = DISP_COLORS[form.n5.data in db_nos]
            class_colors[5] = DISP_COLORS[form.power_ball.data == s.ball_6]

            msg = ''
            winning_key = (l_nos, form.power_ball.data == s.ball_6)
            if winning_key in WINNINGS.keys():
                msg = f'You won {WINNINGS[winning_key]}!'
                if winning_key == (5, True):
                    msg = f'{msg}, estimated at ${s.draw_estimate:,.2f}'

            msg = f'{msg}<br>You got <b>{l_nos}</b> {pluralize("number", l_nos)}'
            if form.power_ball.data == s.ball_6:
                msg = f'{msg} <i>{and_or_but(l_nos)}</i> you got the <b>powerball</b>'
            msg = f'{msg}.<br>The numbers for draw #<b>{form.draw_no.data}</b> are <b>{db_nos}</b><br>The powerball is <b>{s.ball_6}</b>'
            msg = f'{msg}. The jackpot was {s.draw_estimate}. There were {s.draw_winners} winners'
        else:
            msg = f'Draw #<b>{form.draw_no.data}</b> not found!'

        flash(Markup(msg))

    if request.method == 'POST':
        app.logger.info(f'{request.remote_addr} {request.headers["X-Real-IP"]} - Draw #:{form.draw_no.data} {form.n1.data} {form.n2.data} {form.n3.data} {form.n4.data} {form.n5.data} P{form.power_ball.data}')

    ad_no = random.randint(0, len(COMPANIES)-1)
    tit_no = random.randint(0, len(TITBITS)-1)

    advertiser = COMPANIES[ad_no][0]
    titbit = TITBITS[tit_no]
    return render_template(
        'main_menu.html',
        form=form,
        coloring=class_colors,
        advertiser=advertiser,
        adv_link = COMPANIES[ad_no][2],
        adv_slogan = COMPANIES[ad_no][1],
        titbit=titbit,
        no_errors=(request.method == 'POST'))


if __name__ == '__main__':
    db.create_all()
    if 'liveconsole' not in gethostname():
        app.run()
