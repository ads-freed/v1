from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, jsonify, send_from_directory
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.urls import url_parse

from app import db, socketio
from models import User, Ticket, TicketReply, Message
from forms import LoginForm, RegistrationForm, ProfileForm, TicketForm, TicketReplyForm, PrivateMessageForm
from utils import save_file

main = Blueprint('routes', __name__)

@main.route('/uploads/<filename>')
@login_required
def uploaded_file(filename):
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename)

@main.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('routes.dashboard'))
    return redirect(url_for('routes.login'))

@main.route('/login', methods=['GET','POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('routes.login'))
        login_user(user)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('routes.dashboard')
        return redirect(next_page)
    return render_template('login.html', form=form)

@main.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('routes.login'))

@main.route('/register', methods=['GET','POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('routes.dashboard'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data, full_name=form.full_name.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Registration successful. You can now log in.')
        return redirect(url_for('routes.login'))
    return render_template('register.html', form=form)

@main.route('/profile', methods=['GET','POST'])
@login_required
def profile():
    form = ProfileForm(obj=current_user)
    if form.validate_on_submit():
        current_user.email = form.email.data
        current_user.full_name = form.full_name.data
        if form.password.data:
            current_user.set_password(form.password.data)
        db.session.commit()
        flash('Profile updated successfully.')
        return redirect(url_for('routes.profile'))
    # Pass the effective permissions to the template
    effective_perms = current_user.get_effective_permissions()
    return render_template('profile.html', form=form, permissions=effective_perms)

@main.route('/dashboard')
@login_required
def dashboard():
    if current_user.is_admin():
        tickets = Ticket.query.order_by(Ticket.created_at.desc()).all()
    else:
        tickets = Ticket.query.filter_by(user_id=current_user.id).order_by(Ticket.created_at.desc()).all()
    return render_template('dashboard.html', tickets=tickets)

@main.route('/ticket/create', methods=['GET','POST'])
@login_required
def ticket_create():
    if not current_user.has_permission('create_ticket'):
        flash("You do not have permission to create a ticket.")
        return redirect(url_for('routes.dashboard'))
    form = TicketForm()
    if form.validate_on_submit():
        ticket = Ticket(subject=form.subject.data, description=form.description.data, user_id=current_user.id)
        db.session.add(ticket)
        db.session.commit()
        if form.attachment.data:
            filename = save_file(form.attachment.data)
            reply = TicketReply(message="Initial attachment", ticket_id=ticket.id, user_id=current_user.id, attachment=filename)
            db.session.add(reply)
            db.session.commit()
        socketio.emit('ticket_event', {'action': 'created', 'ticket_id': ticket.id}, broadcast=True)
        flash('Ticket created successfully.')
        return redirect(url_for('routes.dashboard'))
    return render_template('ticket_create.html', form=form)

@main.route('/ticket/<int:ticket_id>', methods=['GET','POST'])
@login_required
def ticket_detail(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    if not current_user.is_admin() and ticket.user_id != current_user.id:
        flash('Access denied.')
        return redirect(url_for('routes.dashboard'))
    form = TicketReplyForm()
    if form.validate_on_submit():
        if not current_user.has_permission('reply_ticket'):
            flash("You do not have permission to reply to tickets.")
            return redirect(url_for('routes.ticket_detail', ticket_id=ticket.id))
        filename = None
        if form.attachment.data:
            filename = save_file(form.attachment.data)
        reply = TicketReply(message=form.message.data, ticket_id=ticket.id, user_id=current_user.id, attachment=filename)
        db.session.add(reply)
        db.session.commit()
        socketio.emit('ticket_event', {'action': 'replied', 'ticket_id': ticket.id}, broadcast=True)
        flash('Reply submitted.')
        return redirect(url_for('routes.ticket_detail', ticket_id=ticket.id))
    return render_template('ticket_detail.html', ticket=ticket, form=form)

@main.route('/tickets_partial')
@login_required
def tickets_partial():
    if current_user.is_admin():
        tickets = Ticket.query.order_by(Ticket.created_at.desc()).all()
    else:
        tickets = Ticket.query.filter_by(user_id=current_user.id).order_by(Ticket.created_at.desc()).all()
    return render_template('tickets_partial.html', tickets=tickets)

@main.route('/messages', methods=['GET','POST'])
@login_required
def private_messages():
    form = PrivateMessageForm()
    form.recipient.choices = [(u.id, u.username) for u in User.query.filter(User.id != current_user.id).all()]
    if form.validate_on_submit():
        filename = None
        if form.attachment.data:
            filename = save_file(form.attachment.data)
        message = Message(body=form.body.data, sender_id=current_user.id,
                          recipient_id=form.recipient.data, attachment=filename)
        db.session.add(message)
        db.session.commit()
        socketio.emit('private_message', {
            'sender': current_user.username,
            'recipient_id': form.recipient.data,
            'preview': form.body.data[:50]
        }, broadcast=True)
        flash('Message sent.')
        return redirect(url_for('routes.private_messages'))
    return render_template('private_chat.html', form=form)
