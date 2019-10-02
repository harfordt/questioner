from flask import render_template, request, flash, redirect, url_for
from werkzeug.urls import url_parse

from app import app, db  # db maybe shouldn't be here
from app.models import User, Post, Board  # this maybe shouldn't be here
from app.forms import LoginForm, RegistrationForm, EditProfileForm, PostForm, CreateBoardForm

from flask_login import current_user, login_user, logout_user, login_required

from datetime import datetime

from flask_babel import _, get_locale
from flask import g, jsonify
from guess_language import guess_language
from app.translate import translate


@app.route('/', methods=['POST', 'GET'])
@app.route('/home', methods=['POST', 'GET'])
@app.route('/index', methods=['POST', 'GET'])
@login_required
def index():
    form = PostForm()
    if form.validate_on_submit():
        language = guess_language(form.post.data)
        if language == "UNKNOWN" or len(language) > 5:
            language = ""
        post = Post(body=form.post.data, author=current_user, language=language)
        db.session.add(post)
        db.session.commit()
        flash('Success!')
        return redirect(url_for('index'))

    page = request.args.get('page', 1, type=int)
    posts = current_user.followed_posts().paginate(page, app.config['POSTS_PER_PAGE'], False)
    prev_url = url_for('index', page=posts.prev_num) if posts.has_prev else None
    next_url = url_for('index', page=posts.next_num) if posts.has_next else None

    return render_template('index.html', title="welcome", form=form, posts=posts.items, prev_url=prev_url,
                           next_url=next_url)


@app.route('/explore')
@login_required
def explore():
    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.timestamp.desc()).paginate(page, app.config['POSTS_PER_PAGE'], False)
    prev_url = url_for('explore', page=posts.prev_num) if posts.has_prev else None
    next_url = url_for('explore', page=posts.next_num) if posts.has_next else None
    return render_template("index.html", posts=posts.items, title="Explore", prev_url=prev_url, next_url=next_url)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()

        if user is None or not user.check_password(form.password.data):
            flash("Invalid username or password")
            return redirect(url_for('login'))

        login_user(user, remember=form.remember_me.data)

        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')

        return redirect(url_for('index'))

    return render_template('login.html', title='Sign in', form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


@app.route('/user/<username>')
@login_required
def profile(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    posts = user.posts.order_by(Post.timestamp.desc()).paginate(page, app.config['POSTS_PER_PAGE'], False)
    prev_url = url_for('profile', username=username, page=posts.prev_num) if posts.has_prev else None
    next_url = url_for('profile', username=username, page=posts.next_num) if posts.has_next else None
    return render_template("profile.html", title="profile", user=user, posts=posts.items, prev_url=prev_url,
                           next_url=next_url)


@app.route('/edit_profile', methods=['POST', 'GET'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash("Profile updated!")
        return redirect(url_for("profile", username=current_user.username))
    elif request.method == "GET":
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me

    return render_template("edit_profile.html", title='Edit Profile', form=form)


@app.route('/follow/<username>')
@login_required
def follow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('User {} not found.'.format(username))
        return redirect(url_for('index'))
    if user == current_user:
        flash('You cannot follow yourself!')
        return redirect(url_for('profile', username=username))
    current_user.follow(user)
    db.session.commit()
    flash('You are following {}!'.format(username))
    return redirect(url_for('profile', username=username))


@app.route('/unfollow/<username>')
@login_required
def unfollow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('User {} not found.'.format(username))
        return redirect(url_for('index'))
    if user == current_user:
        flash('You cannot unfollow yourself!')
        return redirect(url_for('profile', username=username))
    current_user.unfollow(user)
    db.session.commit()
    flash('You are not following {}.'.format(username))
    return redirect(url_for('profile', username=username))


@app.route('/translate', methods=["GET", "POST"])
def translate_text():
    print("\n\n{}\n\n".format(request.form))
    print("""
    text: {}
    src:  {}
    dest: {}""".format(request.form['text'],
                       request.form['source_language'],
                       request.form['dest_language']))
    return jsonify({
        'text': translate(request.form['text'],
                          request.form['source_language'],
                          request.form['dest_language'])
    })


@app.route('/create-board', methods=['POST', 'GET'])
@login_required
def create_board():
    form = CreateBoardForm()
    if form.validate_on_submit():
        board = Board(boardname=form.boardname.data, boardowner=current_user)
        db.session.add(board)
        db.session.commit()
        return redirect(url_for('create_board'))
    return render_template("create-board.html", title="create board", form=form)


@app.route('/boards')
def boards():
    boards = Board.query.filter_by(teacherid=current_user.id).all()
    print(boards)
    return render_template('boards.html',title="Boards",boards=boards)

@app.route('/board/<boardid>')
def board(boardid):
    return render_template('board.html',title='BOARD TITLE')


@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()
    g.locale = str(get_locale())


# not sure if this should be here or somewhere else
@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Post': Post}
