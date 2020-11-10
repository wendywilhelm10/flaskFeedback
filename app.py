from flask import Flask, render_template, redirect, session, flash
from flask_debugtoolbar import DebugToolbarExtension
from models import db, connect_db, User, Feedback
from forms import UserForm, LoginForm, FeedbackForm
from sqlalchemy.exc import IntegrityError

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgres:///user_feedback'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = True
app.config['SECRET_KEY'] = 'feedbackexercise1234'
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False

connect_db(app)

toolbar = DebugToolbarExtension(app)

@app.route('/')
def show_register():
    return redirect('/register')

@app.route('/register', methods=['GET', 'POST'])
def register_user():
    form = UserForm()

    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        email = form.email.data
        first_name = form.first_name.data
        last_name = form.last_name.data
        new_user = User.register(username, password, email, first_name, last_name)

        db.session.add(new_user)
        try:
            db.session.commit()
        except IntegrityError:
            form.username.errors.append('Username taken.  Please pick another one.')
            return render_template('register.html', form=form)

        session['username'] = new_user.username
        return redirect(f'/users/{new_user.username}')
    else:
        return render_template('register.html', form=form)
    
@app.route('/login', methods=['GET', 'POST'])
def login_form():
    form = LoginForm()

    if form.validate_on_submit():
        username = form.username.data   
        password = form.password.data   
        user = User.authenticate(username, password)

        if user:
            session['username'] = user.username
            return redirect(f'/users/{user.username}')
        else:
            form.username.errors.append('Invalid username/password')

    return render_template('login.html', form=form)

@app.route('/users/<username>')
def show_user(username):
    if 'username' not in session:
        flash('Please login first!')
        return redirect('/login')

    if (username != session['username']):
        flash("You cannot view another user's information!")
        username = session['username']
        return redirect(f'/users/{username}')

    user = User.query.get_or_404(username)
    feedback = Feedback.query.filter_by(username=username)
    return render_template('userinfo.html', user=user, feedback=feedback)

@app.route('/users/<username>/feedback/add', methods=['GET', 'POST'])
def add_feedback(username):
    if 'username' not in session:
        flash('Please login first!')
        return redirect('/login')

    if (username != session['username']):
        flash('You cannot add feedback for another user')
        username = session['username']
        return redirect(f'/users/{username}')

    form = FeedbackForm()

    if form.validate_on_submit():
        title = form.title.data
        content = form.content.data
        new_feedback = Feedback(title=title, content=content, username=username)

        db.session.add(new_feedback)
        db.session.commit()
        return redirect(f'/users/{username}')
    else:
        return render_template('feedback.html', form=form)

@app.route('/feedback/<int:id>/update', methods=['GET', 'POST'])
def update_feedback(id):
    feedback = Feedback.query.get_or_404(id)

    if 'username' not in session:
        flash('Please login first!')
        return redirect('/login')

    if (feedback.username != session['username']):
        flash('You cannot update feedback for another user')
        return redirect(f"/users/{session['username']}")

    form = FeedbackForm(obj=feedback)

    if form.validate_on_submit():
        feedback.title = form.title.data   
        feedback.content = form.content.data
        db.session.commit()
        return redirect(f"/users/{session['username']}")
    else:
        return render_template('feedback.html', form=form)

@app.route('/feedback/<int:id>/delete', methods=['POST'])
def delete_feedback(id):
    if 'username' not in session:
        flash('Please login first!')
        return redirect('/login')

    feedback = Feedback.query.get_or_404(id)

    if (feedback.username != session['username']):
        flash('You cannot delete feedback for another user')
        return redirect(f"/users/{session['username']}")

    db.session.delete(feedback)
    db.session.commit()
    return redirect(f"/users/{session['username']}")

@app.route('/users/<username>/delete', methods=['POST'])
def delete_user(username):
    if 'username' not in session:
        flash('Please login first!')
        return redirect('/login')

    if (username != session['username']):
        flash('You cannot delete another user')
        return redirect(f"/users/{session['username']}")

    Feedback.query.filter_by(username=username).delete()
    user = User.query.get_or_404(username)
    db.session.delete(user)
    db.session.commit()

    session.pop('username')
    return redirect('/')

@app.route('/logout')
def logout_user():
    session.pop('username')
    flash('Goodbye!')
    return redirect('/')