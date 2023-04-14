from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, UserMixin, login_required, current_user
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'secrt-kye'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://database'
database = SQLAlchemy(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'
class User(UserMixin, database.Model):
    id = database.Column(database.Integer(), primary_key=True, autoincrement=True)
    name = database.Column(database.String(25), nullable=False, unique=True)
    email = database.Column(database.String(100), nullable=False, unique=True)
    email_confirm = database.Column(database.Boolean(), default=False)
    password = database.Column(database.String(100), nullable=False)
    join_date = database.Column(database.String(20), default=datetime.today().strftime("%d/%m/%Y"))
    plan = database.Column(database.String(5), default="free")
    articles = database.Column(database.String(1000000000), default="")

    def __repr__(self):
        return '<User %r>' % self.id

class Article(database.Model):
    id = database.Column(database.Integer(), primary_key=True)
    title = database.Column(database.String(128), nullable=False)
    short = database.Column(database.String(256), nullable=False)
    text = database.Column(database.String(5096), nullable=False)
    public = database.Column(database.Boolean(), default=False)
    date = database.Column(database.DateTime(), default=datetime.utcnow)
    author = database.Column(database.Integer(), nullable=False)

    def __repr__(self):
        return '<Article %r>' % self.id
@login_manager.user_loader
def load_user(user_id):
    return database.session.get(User, int(user_id))
@app.route("/")
@app.route("/home")
def home():
    return render_template("home.html")
@app.route("/account")
@login_required
def account():
    all_articles = Article.query.order_by(Article.date.desc()).all()
    return render_template("account.html", articles=all_articles)
@app.route("/register", methods=['POST', 'GET'])
def register():
    if request.method == "POST":
        name = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm-password']
        if len(name.split()) == 0 or len(email.split()) == 0 or len(password.split()) == 0 or len(confirm_password.split()) == 0:
            return render_template("register-message.html", message_text="Усі поля повинні бути заповненні")
        if User.query.filter_by(name=name).first():
            return render_template("register-message.html", message_text="Ім'я користувача вже зайняте")
        if User.query.filter_by(email=email).first():
            return render_template("register-message.html", message_text="Електронна адреса вже зайнята")
        if password != confirm_password:
            return render_template("register-message.html", message_text="Підтвердження паролю не співпадає з паролем")
        try:
            user = User(name=name, email=email, password=password)
            database.session.add(user)
            database.session.commit()
            return redirect("/login")
        except:
            return render_template("register-message.html", message_text="Щось пішло не так")
    elif not current_user.is_authenticated:
        return render_template("register.html")
    else:
        return redirect("/account")
@app.route("/login", methods=['POST', 'GET'])
def login():
    if request.method == "POST":
        identify = request.form['id']
        password = request.form['password']
        name = User.query.filter_by(name=identify).first()
        email = User.query.filter_by(email=identify).first()
        if name and name.password == password:
            login_user(name)
        elif email and email.password == password:
            login_user(email)
        else:
            return render_template("login-message.html", message_text="Не вірні дані для входу в аккаунт")
        return redirect("/account")
    elif not current_user.is_authenticated:
        return render_template("login.html")
    else:
        return redirect("/account")
@app.route("/create", methods=['POST', 'GET'])
@login_required
def create():
    if request.method == 'POST':
        title = request.form['title']
        short = request.form['short']
        text = request.form['text']
        public = request.form.get('public')
        if len(list(title)) > 100:
            return render_template("create-message.html", message_text="Завелика назва статті/нотатки")
        if len(list(short)) > 200:
            return render_template("create-message.html", message_text="Завеликий короткий опис статті/нотатки")
        try:
            article = Article(title=title, short=short, text=text, public=public == "on", author=current_user.id)
            database.session.add(article)
            database.session.commit()
            return redirect("/account")
        except:
            return render_template("create-message.html", message_text="Щось пішло не так")
    else:
        return render_template("create.html")
@app.route("/articles")
def articles():
    all_articles = Article.query.order_by(Article.date.desc()).all()
    return render_template("articles.html", articles=all_articles, User=User)
@app.route("/article/<int:id>")
def get_article(id):
    article = Article.query.get(id)
    return render_template("article.html", article=article, author=User.query.filter_by(id=article.author).first())
@app.route("/account/<string:name>")
def user_account(name):
    try:
        all_articles = Article.query.order_by(Article.date.desc()).all()
        user = User.query.filter_by(name=name).first()
        return render_template("user_account.html", user=user, articles=all_articles)
    except NameError:
        return render_template("404.html"), 404
@app.route("/logout")
def logout():
    if current_user:
        logout_user()
    return redirect("/")

@app.errorhandler(404)
def not_found(error):
    return render_template("404.html"), 404
if __name__ == "__main__":
    app.run(debug=True)
