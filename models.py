from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
from sqlalchemy import Numeric

db = SQLAlchemy()

class Car(db.Model):
    car_id = db.Column(db.Integer, primary_key=True)
    make = db.Column(db.String(50), nullable=False)
    model = db.Column(db.String(50), nullable=False)
    current_mileage = db.Column(db.Integer, default=0)
    vin = db.Column(db.String(17), nullable=False, unique=True)
    license_plate = db.Column(db.String(7), nullable=False, unique=True)
    production_year = db.Column(db.Integer)
    first_registration = db.Column(db.Date)
    fuel_type = db.Column(db.String(10))
    engine = db.Column(db.String(10))
    power = db.Column(db.Integer)
    color = db.Column(db.String(20))
    created_at = db.Column(db.DateTime)
    accesses = db.relationship("CarAccess", backref="car")
    maintenance_events = db.relationship("MaintenanceEvent", backref="car")
    baseline_mileage = db.Column(db.Integer, nullable=False, default=0)


class User(UserMixin, db.Model):
    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime)
    car_accesses = db.relationship("CarAccess", backref="user")

    def get_id(self):
        return str(self.user_id)


class CarAccess(db.Model):
    access_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.user_id"))
    car_id = db.Column(db.Integer, db.ForeignKey("car.car_id"))
    role = db.Column(db.String(20))
    created_at = db.Column(db.DateTime)


class MaintenanceEvent(db.Model):
    event_id = db.Column(db.Integer, primary_key=True)

    car_id = db.Column(
        db.Integer,
        db.ForeignKey("car.car_id"),
        nullable=False
    )

    title = db.Column(db.String(100), nullable=False)
    event_date = db.Column(db.Date, nullable=False)
    mileage = db.Column(db.Integer, nullable=False)

    description = db.Column(db.Text)
    cost = db.Column(Numeric(10, 2))

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    currency = db.Column(
        db.String(3),
        nullable=False,
        default="HUF"
    )