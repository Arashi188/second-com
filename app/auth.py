from flask import Blueprint, render_template, redirect, url_for, flash 
from flask_login import login_user, logout_user, current_user 
from app import db 
from app.models import User 
from app.forms import LoginForm 
 
bp = Blueprint('auth', __name__) 
 
@bp.route('/login', methods=['GET', 'POST']) 
def login(): 
    form = LoginForm() 
    if form.validate_on_submit(): 
        user = User.query.filter_by(username=form.username.data).first() 
        if user and user.check_password(form.password.data): 
            login_user(user, remember=form.remember_me.data) 
            return redirect(url_for('admin.dashboard')) 
        flash('Invalid username or password', 'danger') 
    return render_template('login.html', form=form) 
 
@bp.route('/logout') 
def logout(): 
    logout_user() 
    return redirect(url_for('main.index')) 
