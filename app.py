from flask import (Flask, render_template, redirect, url_for, request, flash)
from config import Config
from models import db, Car, User, CarAccess, MaintenanceEvent
from flask_login import UserMixin
from flask_login import (
    LoginManager,
    login_user,
    logout_user,
    login_required,
    current_user
)

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

from datetime import datetime
from decimal import Decimal, InvalidOperation
from models import MaintenanceEvent
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError

app = Flask(__name__)

app.config.from_object(Config)

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

with app.app_context():
    
    db.create_all()
    """
    car = Car(
        make = "Peugeot",
        model = "206 cc",
        current_mileage = 307000,
        vin = "00000000000000000",
        license_plate = "NGV392")

    db.session.add(car)
    db.session.commit()
    

    user = User(
        username = "NeodyLead",
        email = "neodylead@gmail.com"
    )
    """



@app.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("garage"))

    return redirect(url_for("login"))


@login_manager.user_loader
def load_user(user_id):
    try:
        return db.session.get(User, int(user_id))
    except (TypeError, ValueError):
        return None


@app.route("/car/<int:car_id>")
@login_required
def car_detail(car_id):
    # Check whether the current user has access to this car.
    access = CarAccess.query.filter_by(
        user_id=current_user.user_id,
        car_id=car_id
    ).first_or_404()

    # Retrieve this car's maintenance history, newest first.
    events = MaintenanceEvent.query.filter_by(
        car_id=car_id
    ).order_by(
        MaintenanceEvent.event_date.desc(),
        MaintenanceEvent.event_id.desc()
    ).all()

    return render_template(
        "car_detail.html",
        car=access.car,
        access=access,
        events=events
    )

@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("garage"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        if not username or not email or not password:
            flash("Please fill in every field.")
            return redirect(url_for("register"))

        if len(password) < 8:
            flash("Your password must contain at least 8 characters.")
            return redirect(url_for("register"))

        existing_user = User.query.filter(
            (User.username == username) |
            (User.email == email)
        ).first()

        if existing_user:
            flash("That username or email address is already registered.")
            return redirect(url_for("register"))

        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password)
        )

        db.session.add(user)
        db.session.commit()

        flash("Account created! You can now log in.")
        return redirect(url_for("login"))

    return render_template("register.html")



@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("garage"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for("garage"))

        flash("Invalid username or password.")

    return render_template("login.html")


@app.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    flash("You have been logged out.")
    return redirect(url_for("login"))


@app.route("/garage")
@login_required
def garage():
    user_cars = current_user.car_accesses

    return render_template(
        "garage.html",
        user=current_user,
        user_cars=user_cars,
        current_year=datetime.now().year

    )


@app.route("/car/add", methods=["POST"])
@login_required
def add_car():
    print("DEBUG: add_car route reached")

    make = request.form.get("make", "").strip()
    # Keep the rest of your existing code unchanged.
    # Read and clean the submitted form values.
    model = request.form.get("model", "").strip()
    vin = request.form.get("vin", "").strip().upper()
    license_plate = request.form.get("license_plate", "").strip().upper()

    mileage_text = request.form.get("current_mileage", "0").strip()
    year_text = request.form.get("production_year", "").strip()
    registration_text = request.form.get("first_registration", "").strip()

    fuel_type = request.form.get("fuel_type", "").strip()
    engine = request.form.get("engine", "").strip()
    power_text = request.form.get("power", "").strip()
    color = request.form.get("color", "").strip()

    print(f"DEBUG: make={make!r}, model={model!r}")
    print(f"DEBUG: VIN={vin!r}, plate={license_plate!r}")
    print(f"DEBUG: mileage={mileage_text!r}, year={year_text!r}")

    print("DEBUG: Starting validation")
    # Validate required fields.

    print("DEBUG: Starting validation")
    print(f"DEBUG: make={make!r}, model={model!r}")
    print(f"DEBUG: VIN={vin!r}, plate={license_plate!r}")
    print(f"DEBUG: mileage={mileage_text!r}, year={year_text!r}")

    if not make or not model or not vin or not license_plate:
        print("DEBUG: Failed required-fields validation")

        flash("Please fill in the make, model, VIN, and registration plate.")
        return redirect(url_for("garage"))

    if len(vin) != 17:
        print("DEBUG: Failed required-fields validation")
        flash("The VIN must contain exactly 17 characters.")
        return redirect(url_for("garage"))

    if len(license_plate) > 7:
        print("DEBUG: Failed required-fields validation")
        flash("The registration plate must not exceed 7 characters.")
        return redirect(url_for("garage"))

    # Check whether the VIN or registration plate is already registered.
    duplicate = Car.query.filter(
        or_(
            Car.vin == vin,
            Car.license_plate == license_plate
        )
    ).first()

    if duplicate:
        print("DEBUG: Failed required-fields validation")
        flash("A car with that VIN or registration plate already exists.")
        return redirect(url_for("garage"))

    # Validate numerical fields.
    try:
        mileage = int(mileage_text)
        if mileage < 0:
            raise ValueError
    except ValueError:
        flash("Mileage must be a non-negative whole number.")
        return redirect(url_for("garage"))

    production_year = None
    if year_text:
        try:
            production_year = int(year_text)
            if not 1886 <= production_year <= datetime.now().year + 1:
                raise ValueError
        except ValueError:
            flash("Please enter a valid production year.")
            return redirect(url_for("garage"))

    power = None
    if power_text:
        try:
            power = int(power_text)
            if power <= 0:
                raise ValueError
        except ValueError:
            flash("Power must be a positive whole number.")
            return redirect(url_for("garage"))

    # Parse the optional first-registration date.
    first_registration = None
    if registration_text:
        try:
            first_registration = datetime.strptime(
                registration_text, "%Y-%m-%d"
            ).date()
        except ValueError:
            flash("Please enter a valid first-registration date.")
            return redirect(url_for("garage"))

    # Create the car record.
    car = Car(
        make=make,
        model=model,
        vin=vin,
        license_plate=license_plate,
        current_mileage=mileage,
        production_year=production_year,
        first_registration=first_registration,
        fuel_type=fuel_type or None,
        engine=engine or None,
        power=power,
        color=color or None,
        created_at=datetime.utcnow(),
        baseline_mileage=mileage,
    )

    try:
        print("DEBUG: Adding car to session")
        db.session.add(car)

        print("DEBUG: Flushing car")
        db.session.flush()

        print(f"DEBUG: Car ID assigned: {car.car_id}")

        access = CarAccess(
            user_id=current_user.user_id,
            car_id=car.car_id,
            role="owner"
        )
        db.session.add(access)

        print("DEBUG: Committing transaction")
        db.session.commit()
        print("DEBUG: Commit successful")

    except IntegrityError as e:
        db.session.rollback()
        print(f"DEBUG: IntegrityError: {e}")
        flash("The car could not be saved. Check its VIN and registration plate.")
        return redirect(url_for("garage"))

    flash(f"{make} {model} was added to your garage!")
    return redirect(url_for("garage"))


@app.route("/car/<int:car_id>/maintenance/add", methods=["POST"])
@login_required
def add_maintenance_event(car_id):
    # Check whether the current user has access to this car.
    access = CarAccess.query.filter_by(
        user_id=current_user.user_id,
        car_id=car_id
    ).first_or_404()

    # Read the submitted form fields.
    title = request.form.get("title", "").strip()
    event_date_text = request.form.get("event_date", "")
    mileage_text = request.form.get("mileage", "")
    description = request.form.get("description", "").strip()
    cost_text = request.form.get("cost", "").strip()
    currency = request.form.get("currency", "HUF").strip().upper()

    # Validate the required text fields.
    if not title or not event_date_text or not mileage_text:
        flash("Please fill in the title, date, and mileage.")
        return redirect(url_for("car_detail", car_id=car_id))

    # Convert the date from the HTML form into a Python date.
    try:
        event_date = datetime.strptime(
            event_date_text, "%Y-%m-%d"
        ).date()
    except ValueError:
        flash("Please enter a valid maintenance date.")
        return redirect(url_for("car_detail", car_id=car_id))

    # Convert mileage to an integer.
    try:
        mileage = int(mileage_text)

        if mileage < 0:
            raise ValueError

    except ValueError:
        flash("Mileage must be a non-negative whole number.")
        return redirect(url_for("car_detail", car_id=car_id))

    if currency not in {"HUF", "EUR", "USD"}:
        flash("Please select a supported currency.")
        return redirect(url_for("car_detail", car_id=car_id))

    cost = None

    if cost_text:
        try:
            cost = Decimal(cost_text)

            if not cost.is_finite() or cost < 0:
                raise InvalidOperation

            # HUF costs must be whole numbers.
            if currency == "HUF" and cost != cost.to_integral_value():
                raise InvalidOperation

            # EUR and USD may have at most two decimal places.
            if cost.as_tuple().exponent < -2:
                raise InvalidOperation

            # Numeric(10, 2) allows up to eight integer digits.
            if cost >= Decimal("100000000"):
                raise InvalidOperation

        except InvalidOperation:
            flash(
                "Enter a valid cost: whole numbers for HUF, "
                "or up to two decimal places for EUR and USD."
            )
            return redirect(url_for("car_detail", car_id=car_id))

    # Create the new maintenance event.
    event = MaintenanceEvent(
        car_id=access.car.car_id,
        title=title,
        event_date=event_date,
        mileage=mileage,
        description=description or None,
        cost=cost,
        currency=currency
    )

    # Add the maintenance event.
    db.session.add(event)

    # Update the car's mileage if the event records a higher value.
    if (
        access.car.current_mileage is None
        or mileage > access.car.current_mileage
    ):
        access.car.current_mileage = mileage

    # Save both changes in one transaction.
    db.session.commit()
    flash("Maintenance event added successfully!")

    return redirect(url_for("car_detail", car_id=car_id))



@app.route(
    "/car/<int:car_id>/maintenance/<int:event_id>/delete",
    methods=["POST"]
)
@login_required
def delete_maintenance_event(car_id, event_id):
    # Verify that the user has access to this car.
    access = CarAccess.query.filter_by(
        user_id=current_user.user_id,
        car_id=car_id
    ).first_or_404()

    if access.role != "owner":
        flash("Only the car owner can delete maintenance events.")
        return redirect(url_for("car_detail", car_id=car_id))

    # Find the event belonging to this specific car.
    event = MaintenanceEvent.query.filter_by(
        event_id=event_id,
        car_id=access.car.car_id
    ).first_or_404()

    # Remove the maintenance event.
    db.session.delete(event)
    db.session.flush()

    # Find the highest mileage among the remaining maintenance events.
    highest_event = MaintenanceEvent.query.filter_by(
        car_id=car_id
    ).order_by(
        MaintenanceEvent.mileage.desc()
    ).first()

    # Recalculate the car's mileage without losing its baseline.
    car = access.car

    car.current_mileage = max(
        car.baseline_mileage,
        highest_event.mileage if highest_event else 0
    )

    db.session.commit()

    flash("Maintenance event deleted successfully.")

    return redirect(url_for("car_detail", car_id=car_id))


@app.route("/car/<int:car_id>/delete", methods=["POST"])
@login_required
def delete_car(car_id):
    # Find the current user's access to this car.
    access = CarAccess.query.filter_by(
        user_id=current_user.user_id,
        car_id=car_id
    ).first_or_404()

    # Only the owner can delete the entire car.
    if access.role != "owner":
        flash("Only the car's owner can delete it.")
        return redirect(url_for("garage"))

    car = access.car

    # Remove the car's maintenance history first.
    MaintenanceEvent.query.filter_by(
        car_id=car.car_id
    ).delete(synchronize_session=False)

    # Remove all users' access records for this car.
    CarAccess.query.filter_by(
        car_id=car.car_id
    ).delete(synchronize_session=False)

    # Finally, remove the car itself.
    db.session.delete(car)
    db.session.commit()

    flash(f"{car.make} {car.model} was deleted.")

    return redirect(url_for("garage"))



@app.route("/car/<int:car_id>/edit", methods=["GET", "POST"])
@login_required
def edit_car(car_id):
    access = CarAccess.query.filter_by(
        user_id=current_user.user_id,
        car_id=car_id
    ).first_or_404()

    if access.role != "owner":
        flash("Only the car owner can modify vehicle details.")
        return redirect(url_for("car_detail", car_id=car_id))

    car = access.car

    if request.method == "POST":
        make = request.form.get("make", "").strip()
        model = request.form.get("model", "").strip()
        vin = request.form.get("vin", "").strip().upper()
        license_plate = request.form.get("license_plate", "").strip().upper()

        mileage_text = request.form.get("current_mileage", "").strip()
        year_text = request.form.get("production_year", "").strip()
        registration_text = request.form.get("first_registration", "").strip()

        fuel_type = request.form.get("fuel_type", "").strip()
        engine = request.form.get("engine", "").strip()
        power_text = request.form.get("power", "").strip()
        color = request.form.get("color", "").strip()

        # Validate required fields.
        if not make or not model or not vin or not license_plate:
            flash("Make, model, VIN, and registration plate are required.")
            return redirect(url_for("edit_car", car_id=car_id))

        if len(vin) != 17:
            flash("The VIN must contain exactly 17 characters.")
            return redirect(url_for("edit_car", car_id=car_id))

        if len(license_plate) > 7:
            flash("The registration plate must not exceed 7 characters.")
            return redirect(url_for("edit_car", car_id=car_id))

        # Check whether another car already uses this VIN or plate.
        duplicate = Car.query.filter(
            Car.car_id != car_id,
            or_(
                Car.vin == vin,
                Car.license_plate == license_plate
            )
        ).first()

        if duplicate:
            flash("Another car already uses that VIN or registration plate.")
            return redirect(url_for("edit_car", car_id=car_id))

        # Validate mileage.
        try:
            mileage = int(mileage_text)
            if mileage < 0:
                raise ValueError
        except ValueError:
            flash("Mileage must be a non-negative whole number.")
            return redirect(url_for("edit_car", car_id=car_id))

        # Validate production year.
        production_year = None

        if year_text:
            try:
                production_year = int(year_text)

                if not 1886 <= production_year <= datetime.now().year + 1:
                    raise ValueError

            except ValueError:
                flash("Please enter a valid production year.")
                return redirect(url_for("edit_car", car_id=car_id))

        # Validate engine power.
        power = None

        if power_text:
            try:
                power = int(power_text)

                if power <= 0:
                    raise ValueError

            except ValueError:
                flash("Power must be a positive whole number.")
                return redirect(url_for("edit_car", car_id=car_id))

        # Validate first-registration date.
        first_registration = None

        if registration_text:
            try:
                first_registration = datetime.strptime(
                    registration_text,
                    "%Y-%m-%d"
                ).date()

            except ValueError:
                flash("Please enter a valid first-registration date.")
                return redirect(url_for("edit_car", car_id=car_id))

        # Update the existing database record.
        car.make = make
        car.model = model
        car.vin = vin
        car.license_plate = license_plate
        car.current_mileage = mileage
        car.production_year = production_year
        car.first_registration = first_registration
        car.fuel_type = fuel_type or None
        car.engine = engine or None
        car.power = power
        car.color = color or None

        try:
            db.session.commit()

        except IntegrityError:
            db.session.rollback()
            flash("The changes could not be saved. Check the VIN and registration plate.")
            return redirect(url_for("edit_car", car_id=car_id))

        flash(f"{car.make} {car.model} was updated successfully!")
        return redirect(url_for("car_detail", car_id=car_id))

    return render_template(
        "edit_car.html",
        car=car,
        current_year=datetime.now().year
    )