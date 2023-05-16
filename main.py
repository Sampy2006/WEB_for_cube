from flask import Flask, render_template, request
from werkzeug.utils import redirect
from data import db_session, news_resources, quests_resource
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from forms.LoginForm import LoginForm

from werkzeug.utils import redirect

import data.users_resource as us_re

from data.users import User
from data.news import News

from forms.news import NewsForm
from forms.user import RegisterForm

from flask_restful import reqparse, abort, Api, Resource

app = Flask(__name__)

app.config['MAX_CONTENT_LENGTH'] = 16 * 1000 * 1000

api = Api(app)

app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'

login_manager = LoginManager()
login_manager.init_app(app)

from data.quests import Quest

from forms.questsForm import QuestsForm
import datetime


@app.route('/')
def index():
    return render_template("index.html")


@app.route('/register', methods=['GET', 'POST'])
def reqister():
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Пароли не совпадают")
        db_sess = db_session.create_session()
        if db_sess.query(User).filter(User.email == form.email.data).first():
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Такой пользователь уже есть")
        user = User(
            name=form.name.data,
            email=form.email.data,
            about=form.about.data
        )
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()
        return redirect('/login')
    return render_template('register.html', title='Регистрация', form=form)


@app.route('/admin', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect("/")
        return render_template('login.html',
                               message="Неправильный логин или пароль",
                               form=form)
    return render_template('login.html', title='Авторизация', form=form)


@app.route('/news', methods=['GET', 'POST'])
@login_required
def add_news():
    form = NewsForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        news = News()
        news.title = form.title.data
        news.content = form.content.data
        news.is_private = form.is_private.data
        current_user.news.append(news)
        db_sess.merge(current_user)
        db_sess.commit()
        return redirect('/tasks')
    return render_template('news.html', title='Добавление новости',
                           form=form)


@app.route('/news/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_news(id):
    form_news = NewsForm()
    form_quest = QuestsForm()
    if request.method == "GET":
        db_sess = db_session.create_session()
        news = db_sess.query(News).filter(News.id == id
                                          ).first()

        quest = db_sess.query(Quest).filter(Quest.news_id == id)

        if news:
            form_news.title.data = news.title
            form_news.content.data = news.content
            form_news.is_private.data = news.is_private

        else:
            abort(404)

        #  if quest:
        #      form_quest.content.data = quest.content

    if form_news.validate_on_submit():
        print('Зашёл в валидатор у News')
        db_sess = db_session.create_session()
        news = db_sess.query(News).filter(News.id == id
                                          ).first()
        if news:
            news.title = form_news.title.data
            news.content = form_news.content.data
            news.is_private = form_news.is_private.data
            db_sess.commit()
            return redirect('/tasks')
        else:
            abort(404)
    return render_template('news.html',
                           title='Редактирование новости',
                           form=form_news
                           )


@app.route('/news_delete/<int:id>', methods=['GET', 'POST'])
@login_required
def news_delete(id):
    db_sess = db_session.create_session()
    news = db_sess.query(News).filter(News.id == id
                                      ).first()
    if news:
        db_sess.delete(news)
        db_sess.commit()
    else:
        abort(404)
    return redirect('/tasks')


@app.route("/tasks")
def tasks():
    db_sess = db_session.create_session()
    news = db_sess.query(News).filter(News.is_private != True)
    quest = db_sess.query(Quest)
    return render_template("tasks.html", news=news, quest=quest)


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    user = db_sess.query(User).all()
    return db_sess.query(User).get(user_id)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


if __name__ == '__main__':
    db_session.global_init("db/blogs.db")

    app.run(debug=True)
