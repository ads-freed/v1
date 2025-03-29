from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app import db
from models import User, Ticket, AuditLog
from forms import ProfileForm, UserPermissionsForm
from functools import wraps

admin = Blueprint('admin', __name__)

def admin_required(func):
    @wraps(func)
    def decorated_view(*args, **kwargs):
        if not current_user.is_admin():
            flash('Admin access required.')
            return redirect(url_for('routes.dashboard'))
        return func(*args, **kwargs)
    return decorated_view

@admin.route('/dashboard')
@login_required
@admin_required
def dashboard():
    tickets = Ticket.query.order_by(Ticket.created_at.desc()).all()
    return render_template('admin_dashboard.html', tickets=tickets)

@admin.route('/ticket/<int:ticket_id>/edit', methods=['GET','POST'])
@login_required
@admin_required
def edit_ticket(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    if request.method == 'POST':
        ticket.status = request.form.get('status', ticket.status)
        ticket.priority = request.form.get('priority', ticket.priority)
        ticket.assigned_to = request.form.get('assigned_to', ticket.assigned_to)
        db.session.commit()
        flash('Ticket updated successfully.')
        return redirect(url_for('admin.dashboard'))
    return render_template('ticket_edit.html', ticket=ticket)

@admin.route('/users')
@login_required
@admin_required
def user_management():
    users = User.query.all()
    return render_template('user_management.html', users=users)

@admin.route('/user/<int:user_id>/edit', methods=['GET','POST'])
@login_required
@admin_required
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    form = ProfileForm(obj=user)
    if form.validate_on_submit():
        user.email = form.email.data
        user.full_name = form.full_name.data
        if form.password.data:
            user.set_password(form.password.data)
        db.session.commit()
        flash('User updated successfully.')
        return redirect(url_for('admin.user_management'))
    return render_template('profile.html', form=form, edit_mode=True, user=user)

@admin.route('/user/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('Cannot delete yourself.')
        return redirect(url_for('admin.user_management'))
    db.session.delete(user)
    db.session.commit()
    flash('User deleted.')
    return redirect(url_for('admin.user_management'))

@admin.route('/user/<int:user_id>/permissions', methods=['GET', 'POST'])
@login_required
@admin_required
def update_permissions(user_id):
    user = User.query.get_or_404(user_id)
    form = UserPermissionsForm(obj=user)
    if form.validate_on_submit():
        user.can_create_ticket = form.can_create_ticket.data
        user.can_view_ticket = form.can_view_ticket.data
        user.can_reply_ticket = form.can_reply_ticket.data
        user.can_edit_ticket = form.can_edit_ticket.data
        user.can_delete_ticket = form.can_delete_ticket.data
        db.session.commit()
        from models import AuditLog
        audit = AuditLog(user_id=current_user.id, action=f"Updated permissions for user {user.username}")
        db.session.add(audit)
        db.session.commit()
        flash('User permissions updated successfully.')
        return redirect(url_for('admin.user_management'))
    return render_template('update_permissions.html', form=form, user=user)

@admin.route('/audit_logs')
@login_required
@admin_required
def audit_logs():
    logs = AuditLog.query.order_by(AuditLog.timestamp.desc()).all()
    return render_template('audit_logs.html', logs=logs)

@admin.route('/analytics_data')
@login_required
@admin_required
def analytics_data():
    data = {
        'open': Ticket.query.filter_by(status='open').count(),
        'in_progress': Ticket.query.filter_by(status='in progress').count(),
        'closed': Ticket.query.filter_by(status='closed').count(),
    }
    return jsonify(data)
