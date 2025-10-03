from ..extensions import db, bcrypt

class AdminUser(db.Model):
    __tablename__ = "admin_users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    @classmethod
    def create(cls, username, password):
        user = cls(username=username, password_hash=bcrypt.generate_password_hash(password).decode("utf-8"))
        db.session.add(user)
        return user

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)
