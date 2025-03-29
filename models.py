from datetime import datetime
import uuid
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import db, login_manager

# Role constants
ROLE_USER = 'user'
ROLE_SUPPORT = 'support'
ROLE_ADMIN = 'admin'

# Association tables for advanced permissions
user_permissions = db.Table('user_permissions',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('permission_id', db.Integer, db.ForeignKey('permission.id'))
)

role_permissions = db.Table('role_permissions',
    db.Column('role_id', db.Integer, db.ForeignKey('role.id')),
    db.Column('permission_id', db.Integer, db.ForeignKey('permission.id'))
)

class Permission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True)  # e.g., 'create_ticket'
    description = db.Column(db.String(200))

    def __repr__(self):
        return f'<Permission {self.name}>'

class Role(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True)  # e.g., 'admin'
    permissions = db.relationship('Permission', secondary=role_permissions,
                                  backref=db.backref('roles', lazy='dynamic'))

    def __repr__(self):
        return f'<Role {self.name}>'

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True, nullable=False)
    email = db.Column(db.String(120), unique=True, index=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    full_name = db.Column(db.String(120))
    role = db.Column(db.String(20), default=ROLE_USER)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Legacy granular permission flags (for quick checks)
    can_create_ticket = db.Column(db.Boolean, default=True)
    can_view_ticket   = db.Column(db.Boolean, default=True)
    can_reply_ticket  = db.Column(db.Boolean, default=True)
    can_edit_ticket   = db.Column(db.Boolean, default=False)
    can_delete_ticket = db.Column(db.Boolean, default=False)

    # Advanced permissions via roles
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'))
    role_obj = db.relationship('Role', backref='users')

    # Additional direct permissions (optional)
    permissions = db.relationship('Permission', secondary=user_permissions,
                                  backref=db.backref('users', lazy='dynamic'))

    tickets = db.relationship('Ticket', backref='author', lazy='dynamic')
    messages_sent = db.relationship('Message', foreign_keys='Message.sender_id', backref='sender', lazy='dynamic')
    messages_received = db.relationship('Message', foreign_keys='Message.recipient_id', backref='recipient', lazy='dynamic')
    audit_logs = db.relationship('AuditLog', backref='user', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def is_admin(self):
        return self.role == ROLE_ADMIN or self.role == ROLE_SUPPORT

    def has_permission(self, perm_name):
        # Check direct permissions
        if any(p.name == perm_name for p in self.permissions):
            return True
        # Check role permissions
        if self.role_obj and any(p.name == perm_name for p in self.role_obj.permissions):
            return True
        # Fallback to legacy flags
        if perm_name == 'create_ticket' and self.can_create_ticket:
            return True
        if perm_name == 'view_ticket' and self.can_view_ticket:
            return True
        if perm_name == 'reply_ticket' and self.can_reply_ticket:
            return True
        if perm_name == 'edit_ticket' and self.can_edit_ticket:
            return True
        if perm_name == 'delete_ticket' and self.can_delete_ticket:
            return True
        return False

    def get_effective_permissions(self):
        """Return a list of permissions the user currently has (combining role and direct flags)."""
        perms = set()
        # From role permissions:
        if self.role_obj:
            perms.update([p.name for p in self.role_obj.permissions])
        # From direct permissions:
        perms.update([p.name for p in self.permissions])
        # Include legacy flags if set:
        if self.can_create_ticket:
            perms.add('create_ticket')
        if self.can_view_ticket:
            perms.add('view_ticket')
        if self.can_reply_ticket:
            perms.add('reply_ticket')
        if self.can_edit_ticket:
            perms.add('edit_ticket')
        if self.can_delete_ticket:
            perms.add('delete_ticket')
        return list(perms)

    def __repr__(self):
        return f'<User {self.username}>'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class Ticket(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    subject = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='open')
    priority = db.Column(db.String(20), default='normal')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    assigned_to = db.Column(db.Integer, db.ForeignKey('user.id'))  # For support agent assignment

    replies = db.relationship('TicketReply', backref='ticket', lazy='dynamic')

    def ticket_number(self):
        return f"Ticket# {self.created_at.strftime('%m-%y')}-{self.id:03d}"

    def __repr__(self):
        return f'<Ticket {self.ticket_number()}>'

class TicketReply(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    ticket_id = db.Column(db.Integer, db.ForeignKey('ticket.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    attachment = db.Column(db.String(200))

    def __repr__(self):
        return f'<TicketReply {self.id}>'

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    recipient_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    attachment = db.Column(db.String(200))

    def __repr__(self):
        return f'<Message {self.id}>'

class AuditLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    action = db.Column(db.String(200))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<AuditLog {self.action} by User {self.user_id}>'
