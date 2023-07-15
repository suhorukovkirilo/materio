import os
from datetime import datetime
from random import randint

from flask import render_template, request, redirect, url_for, flash, get_flashed_messages
from flask_login import login_user, logout_user, login_required, current_user
from flask_mail import Message
from werkzeug.security import generate_password_hash, check_password_hash

from app import app, database, login_manager, mailer, recaptcha, secretcode
from models import User, Article, OTP

def get_plan(plan: str, standard_plan: str = "free"):
    if len(plan.split()) < 2 or datetime.strptime(plan.split()[1], "%Y-%m-%d") < datetime.utcnow():
        return standard_plan
    return plan

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/account", methods=['POST', 'GET'])
@login_required
def account():
    if current_user.name != "admin":
        if request.method == 'POST':
            photo = request.files['photo']
            if photo.filename != '':
                photo.save(os.path.join('mysite/static/img/user', current_user.name))
        articles = list(filter(lambda article: article.author == current_user.id or str(article.id) in current_user.reposts.split(), Article.query.order_by(Article.date.desc()).all()))
        if os.path.isfile(os.path.join('mysite/static/img/user', current_user.name)):
            profile_pic = '/static/img/user/' + current_user.name
        else:
            profile_pic = url_for('static', filename='img/user.png')
        return render_template("account.html", articles=articles, profile_pic=profile_pic)
    return redirect("/panel")

@app.route("/verify", methods=['POST', 'GET'])
@login_required
def verify():
    if request.method == 'POST':
        for otp in OTP.query.order_by().all():
            if otp.time < datetime.utcnow():
                database.session.delete(otp)
        if not recaptcha.verify():
            flash("Виконайте ReCaptcha")
            return render_template("verify.html", messages=get_flashed_messages())
        checks = OTP.query.filter_by(user=current_user.id).all()
        code = request.form['code']
        for check in checks:
            if str(check.code) == code:
                current_user.email_confirm = True
                database.session.commit()
                return redirect("/account")
            return redirect("/" + str(check.code))
    if not current_user.email_confirm:
        return render_template("verify.html", messages=get_flashed_messages())
    return render_template("404.html"), 404

@app.route("/send-mail", methods=['POST', 'GET'])
def send_mail():
    if request.method == 'POST' and not current_user.email_confirm:
        for otp in OTP.query.order_by().all():
            if otp.time < datetime.utcnow():
                database.session.delete(otp)
        checked = OTP.query.filter_by(user=current_user.id).first()
        if not checked:
            check_code = randint(10000000, 99999999)
            otp = OTP(user=current_user.id, code=check_code, type="email_verify")
            database.session.add(otp)
            database.session.commit()
        else:
            check_code = checked.code
        message = Message("Materio Підтвердження", [current_user.email], sender="noreply@demo.com",
                          html=render_template("mail.html", code=str(check_code)))
        mailer.send(message)
        flash("Код надіслано")
        return redirect(request.referrer)
    return render_template("404.html"), 404

@app.route("/send-recovery-mail", methods=['POST', 'GET'])
def send_recovery_mail():
    if request.method == 'POST':
        for otp in OTP.query.order_by().all():
            if otp.time < datetime.utcnow():
                database.session.delete(otp)
        if current_user.is_authenticated:
            checked = OTP.query.filter_by(user=current_user.id).first()
        else:
            if '@' in request.form["id"]:
                user = User.query.filter_by(email=request.form["id"]).first()
            else:
                user = User.query.filter_by(name=request.form["id"]).first()
            if not user:
                flash("Акаунт не знайдено")
                return redirect(request.referrer)
            checked = OTP.query.filter_by(user=user.id).first()
        if not checked:
            check_code = randint(10000000, 99999999)
            otp = OTP(user=current_user.id if current_user.is_authenticated else user.id, code=check_code, type="recovery-mail")
            database.session.add(otp)
            database.session.commit()
        else:
            check_code = checked.code
        message = Message("Materio Підтвердження", [current_user.email if current_user.is_authenticated else user.email], sender="noreply@demo.com",
                          html=render_template("mail.html", code=str(check_code)))
        mailer.send(message)
        flash("Код надіслано")
        return redirect(request.referrer)
    return render_template("404.html"), 404

@app.route("/register", methods=['POST', 'GET'])
def register():
    if request.method == "POST":
        name = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm-password']
        if not recaptcha.verify():
            flash("Виконайте ReCaptcha")
        elif User.query.filter_by(name=name).first():
            flash("Ім'я користувача вже зайняте")
        elif User.query.filter_by(email=email).first():
            flash("Електронна адреса вже зайнята")
        elif password != confirm_password:
            flash("Підтвердження паролю не співпадає з паролем")
        else:
            incorrect = []
            incorrect_symbols = [' ', '!', '"', "'", '£', '№', '$', ';', '%', ':', '^', '&', '?', '*', '(', ')', '+', '=',
                                 '/', '`', '¬', '₴', '\\', '#', '~', '{', '}', '[', ']', ',', '<', '.', '>', '@']
            for symbol in list(name):
                if symbol in incorrect_symbols and symbol not in incorrect:
                    incorrect.append(symbol)
            if len(incorrect) > 0:
                message = "У юзернеймі знадено некоректні символи: "
                message += " ".join(incorrect)
                flash(message)
            else:
                try:
                    password = generate_password_hash(password)
                    user = User(name=name, email=email, password=password)
                    database.session.add(user)
                    database.session.commit()
                    return redirect("/login")
                except:
                    flash("Щось пішло не так")
        return render_template("register.html", messages=get_flashed_messages())
    elif not current_user.is_authenticated:
        return render_template("register.html", messages=get_flashed_messages())
    return redirect("/account")

@app.route("/login", methods=['POST', 'GET'])
def login():
    if request.method == "POST":
        identify = request.form['id']
        password = request.form['password']
        name = User.query.filter_by(name=identify).first()
        email = User.query.filter_by(email=identify).first()
        if not recaptcha.verify():
            flash("Виконайте ReCaptcha")
        elif name and check_password_hash(name.password, password):
            login_user(name)
        elif email and check_password_hash(email.password, password):
            login_user(email)
        else:
            flash("Не вірні дані для входу в аккаунт")
            return render_template("login.html", messages=get_flashed_messages())
    elif not current_user.is_authenticated:
        return render_template("login.html", messages=get_flashed_messages())
    return redirect("/account")

@app.route("/tme/<int:code>")
def telegram(code):
    if current_user.is_authenticated:
        current_user.telegram = str(code)
        database.session.commit()
        return render_template("telegram.html")
    else:
        for user in User.query.order_by().all():
            if user.telegram != "" and user.telegram.split()[0] == str(code):
                login_user(user)
                return redirect("/account")
        flash("Невдалося увійти через телеграм")
        return redirect(request.referrer)
    return render_template("404.html"), 404

@app.route("/change_data", methods=['POST', 'GET'])
def change_data():
    if request.method == 'POST':
        for otp in OTP.query.order_by().all():
            if otp.time < datetime.utcnow():
                database.session.delete(otp)
        if current_user.is_authenticated:
            checks = OTP.query.filter_by(user=current_user.id).all()
            code = request.form['code']
            for check in checks:
                if str(check.code) == code:
                    if request.form['password'] != "":
                        current_user.password = generate_password_hash(request.form['password'])
                    if not any(sym in request.form['username'] for sym in [' ', '!', '"', "'", '£', '№', '$', ';', '%', ':', '^', '&',
                    '?', '*', '(', ')', '+', '=', '/', '`', '¬', '₴', '\\', '#', '~', '{', '}', '[', ']', ',', '<', '.', '>', '@']):
                        current_user.name = request.form['username']
                    database.session.commit()
                    flash("Дані успішно змінено")
                    return render_template("change_data.html", messages=get_flashed_messages())
            flash("Невірний код підтвердження")
        else:
            identify = request.form['id']
            if '@' in identify:
                user = User.query.filter_by(email=identify).first()
            else:
                user = User.query.filter_by(name=identify).first()
            if user:
                checks = OTP.query.filter_by(user=user.id).all()
                code = request.form['code']
                for check in checks:
                    if check.type == "recovery-mail" and user.id == check.user and str(check.code) == code and request.form['password'] != "":
                        user.password = generate_password_hash(request.form['password'])
                        return redirect("/login")
                flash("Невірний код")
            else:
                flash("Невірне ім'я користувача або електронна адреса")
    return render_template("change_data.html", messages=get_flashed_messages())

@app.route("/create", methods=['POST', 'GET'])
@login_required
def create():
    if request.method == 'POST':
        title = request.form['title']
        short = request.form['short']
        text = request.form['text']
        tags = request.form.get('tags')
        public = request.form.get('public')
        if not recaptcha.verify():
            flash("Виконайте ReCaptcha")
        elif len(list(title)) > 100:
            flash("Завелика назва статті/нотатки")
        elif len(list(short)) > 200:
            flash("Завеликий короткий опис статті/нотатки")
        else:
            try:
                if len(tags.split()) != 0:
                    article = Article(title=title, short=short, text=text, public=public == "on", author=current_user.id, tags=tags)
                else:
                    article = Article(title=title, short=short, text=text, public=public == "on", author=current_user.id)
                database.session.add(article)
                database.session.commit()
                flash("Нотатку/Статтю успішно створенно")
            except:
                flash("Щось пішло не так")
            if get_plan(current_user.plan) != "free":
                    picture = request.files['picture']
                    if picture.filename != "":
                        picture.save('mysite/static/img/article/' + str(article.id))
    return render_template("create.html", messages=get_flashed_messages())

@app.route("/articles")
def articles():
    articles = list(filter(lambda article: article.public, Article.query.order_by(Article.date.desc()).all()))
    return render_template("articles.html", articles=articles, User=User)

@app.route("/article/<int:id>", methods=['POST', 'GET'])
def get_article(id):
    article = Article.query.filter_by(id=id).first()
    if request.method == 'POST':
        comment = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S") + " " + current_user.name + " " + request.form['comment']
        replies = article.replies or []
        replies.append(comment)
        article.replies = replies
        database.session.commit()
    if article and (article.public or current_user.is_authenticated and article.author == current_user.id):
        if os.path.isfile(os.path.join('mysite/static/img/article', str(id))):
            article_pic = '/static/img/article/' +  str(id)
        else:
            article_pic = None
        return render_template("article.html", article=article, likes=len(article.likes.split()), replies=article.replies,
                               liked=current_user.is_authenticated and str(current_user.id) in article.likes.split(),
                               favourited=current_user.is_authenticated and str(id) in current_user.favourites.split(),
                               reposted=current_user.is_authenticated and str(id) in current_user.reposts.split(),
                               author=User.query.filter_by(id=article.author).first(), article_pic=article_pic)
    return render_template("404.html"), 404

@app.route("/article/<int:id>/<string:reply>")
def reply(id, reply):
    article = Article.query.filter_by(id=id).first()
    for repl in article.replies:
        if " ".join(repl.split()[:3]) == reply:
            return render_template("article.html", article=article, likes=len(article.likes.split()), replies=[repl],
                                   liked=current_user.is_authenticated and str(
                                       current_user.id) in article.likes.split(),
                                   author=User.query.filter_by(id=article.author).first())
    return redirect("/article/" + str(id))

@app.route("/article/<int:id>/<string:reply>/delete")
def reply_delete(id, reply):
    article = Article.query.filter_by(id=id).first()
    if article:
        replies = article.replies or []
        for repl in replies:
            if " ".join(repl.split()[:3]) == reply and repl.split()[2] == current_user.name:
                del replies[replies.index(repl)]
        database.session.commit()
        return redirect("/article/" + str(id))

@app.route("/delete/<int:id>")
def delete(id):
    article = Article.query.filter_by(id=id).first()
    if current_user.is_authenticated and article is not None and article.author == current_user.id:
        database.session.delete(article)
        database.session.commit()
        return redirect("/account")
    return render_template("404.html"), 404

@app.route("/change/<int:id>", methods=['GET', 'POST'])
def change(id):
    article = Article.query.filter_by(id=id).first()
    if current_user.is_authenticated and article is not None and article.author == current_user.id:
        if request.method == "POST":
            if not recaptcha.verify():
                flash("Виконайте ReCaptcha")
            else:
                if request.form['title'] != "":
                    article.title = request.form['title']
                if request.form['short'] != "":
                    article.short = request.form['short']
                if request.form['text'] != "":
                    article.text = request.form['text']
                if request.form['tags'] != "":
                    article.tags = request.form['tags']
                article.public = request.form.get('public') == "on"
                try:
                    database.session.commit()
                    flash("Нотатку/Статтю успішно змінено")
                except:
                    return render_template("404.html"), 404
        return render_template("change.html", messages=get_flashed_messages())
    return render_template("404.html"), 404

@app.route("/search/<string:tags>")
def search(tags):
    if "?" != request.full_path[-1]:
        return redirect(request.path)
    articles = Article.query.order_by(Article.date.desc()).all()
    tags = tags.split("..")
    search_articles = []
    for article in articles:
        if all(tag in article.tags.split("..") for tag in tags):
            search_articles.append(article)
    return render_template("search.html", articles=search_articles, tags=tags, User=User)

@app.route("/like/<int:id>", methods=['GET', 'POST'])
def liked(id):
    if current_user.is_authenticated:
        article = Article.query.filter_by(id=id).first()
        if request.method == 'POST' and article is not None:
            if str(current_user.id) not in article.likes.split():
                article.likes += str(current_user.id) + " "
            else:
                article.likes = article.likes.replace(str(current_user.id), "")
            database.session.commit()
            return redirect(request.referrer)
        return render_template("404.html"), 404
    return redirect("/login")

@app.route("/favourite/<int:id>", methods=['GET', 'POST'])
@login_required
def favourited(id):
    if request.method == 'POST' and Article.query.filter_by(id=id).first():
        if str(id) not in current_user.favourites.split():
            current_user.favourites += str(id) + " "
        else:
            current_user.favourites = current_user.favourites.replace(str(id) + " ", "")
        database.session.commit()
        return redirect(request.referrer)
    return redirect("/favourites")

@app.route("/repost/<int:id>", methods=['GET', 'POST'])
@login_required
def repost(id):
    if request.method == 'POST' and Article.query.filter_by(id=id).first():
        if str(id) not in current_user.reposts.split():
            current_user.reposts += str(id) + " "
        else:
            current_user.reposts = current_user.reposts.replace(str(id), "")
        database.session.commit()
        return redirect(request.referrer)
    return render_template("404.html"), 404

@app.route("/favourites")
@login_required
def favourites():
    articles = list(filter(lambda article: str(article.id) in current_user.favourites.split(), Article.query.order_by(Article.date.desc()).all()))
    return render_template("favourites.html", articles=articles, User=User)

@app.route("/account/<string:name>")
def user_account(name):
    user = User.query.filter_by(name=name).first()
    if current_user.is_authenticated and current_user == user:
        return redirect("/account")
    if user:
        articles = list(filter(lambda article: article.author == user.id or str(article.id) in user.reposts.split(), Article.query.order_by(Article.date.desc()).all()))
        if os.path.isfile(os.path.join('mysite/static/img/user', user.name)):
            profile_pic = '/static/img/user/' + user.name
        else:
            profile_pic = None
        return render_template("user_account.html", user=user, User=User, articles=articles, followers=len(user.followers.split()), profile_pic=profile_pic,
                               followed=current_user.is_authenticated and str(current_user.id) in user.followers.split())
    return render_template("404.html"), 404

@app.route("/follow/<string:name>", methods=['POST', 'GET'])
@login_required
def follow(name):
    if request.method == 'POST':
        author = User.query.filter_by(name=name).first()
        if author:
            followers = author.followers.split()
            if str(current_user.id) in followers:
                del followers[followers.index(str(current_user.id))]
            else:
                followers.append(str(current_user.id))
            author.followers = " ".join(followers)
            database.session.commit()
        return redirect(request.referrer)
    return render_template("404.html"), 404

@app.route("/foryou")
@login_required
def foryou():
    foryou_articles = []
    for article in Article.query.order_by().all():
        author = User.query.filter_by(id=article.author).first()
        if author and str(current_user.id) in author.followers.split():
            foryou_articles.append(article)
    return render_template("articles.html", articles=foryou_articles, User=User)

@app.route("/upgrade/<string:plan>")
@login_required
def upgrade(plan):
    if plan in ["pro місяць за 5$", "pro рік за 50$", "vip місяць за 15$", "vip рік за 150$"]:
        return render_template("upgrade.html", plan=plan, plan_type="pro" if plan.split()[0] == "pro" else "vip",
                               plan_time="month" if plan.split()[1] == "місяць" else "year")
    return render_template("404.html"), 404

@app.route("/help")
def help():
    return render_template("help.html")

@app.route("/page", methods=["POST", "GET"])
@login_required
def page():
    if request.method == 'POST':
        html = request.form["html"]
        if len(list(html)) > 1000:
            html = html[:1000]
        current_user.page = html
        database.session.commit()
        return redirect("/page/" + current_user.name)
    return render_template("page.html")

@app.route("/page/<string:user>")
def user_page(user):
    user = User.query.filter_by(name=user).first()
    if user:
        return render_template("user_page.html", user=user)
    return render_template("404.html"), 404

@app.route("/logout")
def logout():
    if current_user:
        logout_user()
    return redirect("/")

@app.route("/delete", methods=["POST", "GET"])
@login_required
def account_delete():
    if request.method == "POST":
        database.session.delete(current_user)
        return redirect("/")
    return render_template("account_delete.html")
@app.route("/panel")
def admin_panel():
    if current_user.is_authenticated and current_user.name == "admin":
        return render_template("admin_panel.html")
    return render_template("404.html"), 404

@app.route("/panel/<string:do>/<string:table>/<string:id>", methods=["POST", "GET"])
def panel_do(do, table, id):
    if current_user.is_authenticated and current_user.name == "admin":
        if request.method == "POST":
            if do == "d" and table == "User":
                user_id = User.query.filter_by(id=id).first()
                user_name = User.query.filter_by(name=id).first()
                user_email = User.query.filter_by(email=id).first()
                if any((user_id, user_name, user_email)):
                    for article in Article.query.order_by().all():
                        if article.author == (user_id if user_id else user_name if user_name else user_email).id:
                            database.session.delete(article)
                    database.session.delete(user_id if user_id else user_name if user_name else user_email)
                    flash("Користувача успішно видалено")
                else:
                    flash("Користувача не знайдено")
            elif do == "d" and table == "Article":
                article = Article.query.filter_by(id=id).first()
                if article:
                    database.session.delete(article)
                    flash("артикль успішно видалено")
                else:
                    flash("Артикль не знайдено")
            elif do == "c" and table == "User":
                user_id = User.query.filter_by(id=id).first()
                user_name = User.query.filter_by(name=id).first()
                user_email = User.query.filter_by(email=id).first()
                user = user_id if user_id else user_name if user_name else user_email
                user.name = request.form["name"]
                user.email = request.form["email"]
                user.email_confirm = request.form["confirm"] == "on"
                if request.form["password"] != "":
                    user.password = generate_password_hash(request.form["password"])
                flash("Дані користувача успішно змінено")
            elif do == "c" and table == "Article":
                article = Article.query.filter_by(id=id).first()
                article.title = request.form['title']
                article.short = request.form['short']
                article.text = request.form['text']
                article.tags = request.form.get('tags')
                article.public = request.form.get('public') == "on"
                picture = request.files['picture']
                if picture.filename != "":
                    picture.save(os.path.join('static/img/article', str(Article.query.order_by(Article.date.desc()).all()[0].id)))
                flash("Дані артикля успішно змінено")
            database.session.commit()
            return redirect("/panel")
        else:
            if table == "User":
                user_id = User.query.filter_by(id=id).first()
                user_name = User.query.filter_by(name=id).first()
                user_email = User.query.filter_by(email=id).first()
                if any((user_id, user_name, user_email)):
                    response = user_id if user_id else user_name if user_name else user_email
                else:
                    flash("Користувача не знайдено")
                    return redirect("/panel")
            elif table == "Article":
                article = User.query.filter_by(id=id).first()
                if article:
                    response = article
                else:
                    flash("Артикль не знайдено")
                    return redirect("/panel")
            else:
                flash("Таблицю не знайдено")
                return redirect("/panel")
            if do == "d":
                return render_template("panel_delete.html")
            elif do == "c":
                return render_template("panel_change.html", response=response, table=table, id=id)
            else:
                flash("Дію не знайдено")
                return redirect("/panel")
    return render_template("404.html"), 404

@app.errorhandler(404)
def not_found(error):
    return render_template("404.html"), 404

@app.errorhandler(400)
def bad_request(error):
    return render_template("400.html"), 400

@app.errorhandler(500)
def server_error(error):
    return render_template("500.html"), 500

@app.template_filter("str")
def to_str(integer):
    return str(integer)

with open("mysite/secret.txt", "w", encoding="utf-8") as file:
    file.write("Site Secret Code: " + secretcode)

with app.app_context():
    admin = User.query.filter_by(name="admin").first()
    if admin:
        admin.password = generate_password_hash(secretcode)
    else:
        admin = User(name="admin", password=generate_password_hash(secretcode), email="admid@gmail.com", email_confirm=True)
        database.session.add(admin)
    database.session.commit()

if __name__ == "__main__":
    app.run(debug=True)
