from datetime import datetime
from flask import render_template, flash, redirect, url_for, request, current_app
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.urls import url_parse

from app import app, db
from app.forms import LoginForm, RegistrationForm, EditProfileForm, \
    EmptyForm, PostForm, ResetPasswordRequestForm, ResetPasswordForm, EditPostForm, CommentForm, EditCommentForm, \
    SearchForm
from app.models import User, Post, Comment
from app.email import send_password_reset_email


@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()


@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
@app.route('/home', methods=['GET', 'POST'])
@login_required
def index():
    # form = PostForm()
    # if form.validate_on_submit():
    #     post = Post(body=form.body.data, anonymous=form.anonymous.data,
    #                 author=current_user)
    #     db.session.add(post)
    #     db.session.commit()
    #     flash('Your post is now live!')
    #     return redirect(url_for('index'))
    username = user
    print(user)
    page = request.args.get('page', 1, type=int)
    posts = current_user.followed_posts().paginate(page, app.config['POSTS_PER_PAGE'], False)
    users = current_user.followed_users()
    next_url = url_for('index', page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('index', page=posts.prev_num) \
        if posts.has_prev else None
    return render_template('home.html', title='Home',
                           # form=form,
                           posts=posts.items, users=users, next_url=next_url,
                           prev_url=prev_url)


@app.route('/explore')
@login_required
def explore():
    page = request.args.get('page', 1, type=int)
    anonymous = Post.query.filter_by(anonymous=True).paginate(page, app.config['POSTS_PER_PAGE'], False).items
    not_anonymous = Post.query.filter_by(anonymous=False).paginate(page, app.config['POSTS_PER_PAGE'], False).items
    # posts = Post.query.order_by(Post.timestamp.desc()).paginate(
    #     page, app.config['POSTS_PER_PAGE'], False)
    # next_url = url_for('explore', page=posts.next_num) \
    #     if posts.has_next else None
    # prev_url = url_for('explore', page=posts.prev_num) \
    #     if posts.has_prev else None
    return render_template('explore.html', title='Explore', anonymous=anonymous, not_anonymous=not_anonymous)
                           # next_url=next_url, prev_url=prev_url


@app.route('/search', methods=['GET', 'POST'])
@login_required
def search():
    form = SearchForm()
    if form.validate_on_submit():
        anonymous = form.anonymous.data
        print(anonymous)
        print(type(anonymous))
        flash('Here are your search results!')
        return redirect(url_for('search_results', anonymous=anonymous))
    return render_template('search.html', title='Search', form=form)


@app.route('/search_results/', methods=['GET', 'POST'])
@login_required
def search_results():
    page = request.args.get('page', 1, type=int)
    anonymous = request.args.get('anonymous')
    print(anonymous)
    print(type(anonymous))
    if anonymous == 'True':
        anonymous = bool(1)
    else:
        anonymous = bool(0)
    print(anonymous)
    print(type(anonymous))
    posts = Post.query.filter_by(anonymous=anonymous).paginate(page, app.config['POSTS_PER_PAGE'], False).items
    print(posts)
    return render_template('search_results.html', title='Search Results', posts=posts
                           )


@app.route('/user/<username>', methods=['GET', 'POST'])
@login_required
def user(username):
    form = PostForm()
    if form.validate_on_submit():
        post = Post(body=form.post.data, image=form.image.data.filename, author=current_user)
        db.session.add(post)
        db.session.commit()
        flash('Your post is now live!')
        return redirect(url_for('index'))
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    posts = user.posts.order_by(Post.timestamp.desc()).paginate(
        page, app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('user', username=user.username, page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('user', username=user.username, page=posts.prev_num) \
        if posts.has_prev else None
    return render_template('user.html', user=user, posts=posts.items,
                           next_url=next_url, prev_url=prev_url, form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)


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


@app.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_password_reset_email(user)
        flash('Check your email for the instructions to reset your password')
        return redirect(url_for('login'))
    return render_template('reset_password_request.html',
                           title='Reset Password', form=form)


@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    user = User.verify_reset_password_token(token)
    if not user:
        return redirect(url_for('index'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('Your password has been reset.')
        return redirect(url_for('login'))
    return render_template('reset_password.html', form=form)


@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('edit_profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', title='Edit Profile',
                           form=form)

@app.route('/upload/<username>', methods=['GET', 'POST'])
@login_required
def upload(username):
    form = PostForm()
    if form.validate_on_submit():
        post = Post(body=form.body.data, anonymous=form.anonymous.data,
                    author=current_user)
        db.session.add(post)
        db.session.commit()
        flash('Your post is now live!')
        return redirect(url_for('user', username=username))
    return render_template('upload.html', title='Upload', form=form)

# @app.route('/login', methods=['GET', 'POST'])
# def login():
#     if current_user.is_authenticated:
#         return redirect(url_for('index'))
#     form = LoginForm()
#     if form.validate_on_submit():
#         user = User.query.filter_by(username=form.username.data).first()
#         if user is None or not user.check_password(form.password.data):
#             flash('Invalid username or password')
#             return redirect(url_for('login'))
#         login_user(user, remember=form.remember_me.data)
#         next_page = request.args.get('next')
#         if not next_page or url_parse(next_page).netloc != '':
#             next_page = url_for('index')
#         return redirect(next_page)
#     return render_template('login.html', title='Sign In', form=form)


@app.route('/post/<int:id>', methods=['GET', 'POST'])
@login_required
def post(id):
    username = request.args.get('username')
    user = User.query.filter_by(username=username).first_or_404()
    post = Post.query.filter_by(id=id).first_or_404()
    form = CommentForm()
    print(post.anonymous)
    if form.validate_on_submit():
        comment = Comment(body=form.body.data, post=post,
                          author=current_user)
        db.session.add(comment)
        db.session.commit()
        flash('Your comment has been posted.')
        return redirect(url_for('post', id=id, username=username))
    page = request.args.get('page', 1, type=int)
    if page == -1:
        page = (post.comments.count() - 1) // \
            current_app.config['COMMENTS_PER_PAGE'] + 1
    pagination = post.comments.order_by(Comment.timestamp.asc()).paginate(page,
        per_page=current_app.config['COMMENTS_PER_PAGE'], error_out=False)
    comments = pagination.items
    return render_template('post.html', post=post, user=user, username=username,
                           form=form, comments=comments, pagination=pagination)


@app.route('/edit_post/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_post(id):
    username = request.args.get('username')
    post = Post.query.get_or_404(id)
    print(id)
    form = EditPostForm()
    if form.validate_on_submit():
        post.body = form.body.data
        post.anonymous = form.anonymous.data
        post.author = current_user
        db.session.add(post)
        db.session.commit()
        flash('Your post has been updated.')
        return redirect(url_for('post', id=id, username=current_user.username))
    if request.method == 'GET':
        post = Post.query.get_or_404(id)
        # form.id.data = post.id
        form.body.data = post.body
        form.image.data = post.image
        form.anonymous.data = post.anonymous
    return render_template('edit_post.html', title='Edit Post', post=post, user=user, username=username,
                           form=form)


@app.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete(id):
    form = EmptyForm()
    if form.validate_on_submit():
        post = Post.query.filter_by(id=id).first()
        db.session.delete(post)
        db.session.commit()
        flash('Your post has been deleted!')
        return redirect(url_for('index'))
    return redirect(url_for('index'))


@app.route('/edit_comment/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_comment(id):
    comment = Comment.query.get_or_404(id)
    form = EditCommentForm()
    post_id = request.args.get('post_id')
    if form.validate_on_submit():
        comment.body = form.body.data
        db.session.add(comment)
        db.session.commit()
        flash('Your comment for Post #{} has been updated.'.format(post_id))
        return redirect(url_for('post', id=post_id, username=current_user.username))
        # return redirect(url_for('user', username=username.username))
    if request.method == 'GET':
        # form.id.data = post.id
        form.body.data = comment.body
    return render_template('edit_comment.html', title='Edit Comment', form=form, comment_id=id,
                           post_id=post_id)


@app.route('/delete_comment/<int:id>', methods=['POST'])
@login_required
def delete_comment(id):
    form = EmptyForm()
    if form.validate_on_submit():
        comment = Comment.query.filter_by(id=id).first()
        db.session.delete(comment)
        db.session.commit()
        flash('Your comment has been deleted!')
        return redirect(url_for('index'))
    return redirect(url_for('index'))


@app.route('/follow/<username>', methods=['POST'])
@login_required
def follow(username):
    form = EmptyForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=username).first()
        if user is None:
            flash('User {} not found.'.format(username))
            return redirect(url_for('index'))
        if user == current_user:
            flash('You cannot follow yourself!')
            return redirect(url_for('user', username=username))
        current_user.follow(user)
        db.session.commit()
        flash('You are following {}!'.format(username))
        return redirect(url_for('user', username=username))
    else:
        return redirect(url_for('index'))


@app.route('/unfollow/<username>', methods=['POST'])
@login_required
def unfollow(username):
    form = EmptyForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=username).first()
        if user is None:
            flash('User {} not found.'.format(username))
            return redirect(url_for('index'))
        if user == current_user:
            flash('You cannot unfollow yourself!')
            return redirect(url_for('user', username=username))
        current_user.unfollow(user)
        db.session.commit()
        flash('You are not following {}.'.format(username))
        return redirect(url_for('user', username=username))
    else:
        return redirect(url_for('index'))