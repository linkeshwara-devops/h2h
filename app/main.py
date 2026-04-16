from datetime import datetime
from pathlib import Path

from flask import Flask, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from .models import Category, Product, Review, User, db, seed_database


def create_app():
    app = Flask(__name__, instance_relative_config=True)
    default_db_path = Path(app.instance_path) / "harvest2hotel.db"
    app.config.from_mapping(
        SECRET_KEY="harvest2hotel-dev-key",
        SQLALCHEMY_DATABASE_URI=f"sqlite:///{default_db_path.as_posix()}",
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )
    app.config.from_prefixed_env()

    db.init_app(app)

    with app.app_context():
        db.create_all()
        seed_database()

    register_routes(app)
    return app


def current_user():
    user_id = session.get("user_id")
    if not user_id:
        return None
    return db.session.get(User, user_id)


def cart_snapshot():
    cart = session.get("cart", {})
    product_ids = [int(key) for key in cart.keys()]
    products = Product.query.filter(Product.id.in_(product_ids)).all() if product_ids else []

    items = []
    total = 0
    for product in products:
        quantity = int(cart.get(str(product.id), 0))
        line_total = quantity * product.price_per_kg
        total += line_total
        items.append({"product": product, "quantity": quantity, "line_total": line_total})
    return items, total


def register_routes(app):
    @app.context_processor
    def inject_globals():
        return {"current_user": current_user(), "now": datetime.utcnow()}

    @app.get("/")
    def home():
        featured_products = Product.query.order_by(Product.rating.desc()).limit(8).all()
        categories = Category.query.order_by(Category.name).all()
        top_reviews = Review.query.order_by(Review.created_at.desc()).limit(6).all()
        stats = {
            "manufacturers": User.query.filter_by(role="manufacturer").count(),
            "products": Product.query.count(),
            "orders": 1248,
            "hotels": 312,
        }
        return render_template(
            "index.html",
            featured_products=featured_products,
            categories=categories,
            top_reviews=top_reviews,
            stats=stats,
        )

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            email = request.form["email"].strip().lower()
            password = request.form["password"]
            user = User.query.filter_by(email=email).first()
            if user and check_password_hash(user.password, password):
                session["user_id"] = user.id
                flash("Welcome back to Harvest2Hotel.", "success")
                destination = "manufacturer_dashboard" if user.role == "manufacturer" else "catalog"
                return redirect(url_for(destination))
            flash("Invalid email or password.", "danger")
        return render_template("login.html")

    @app.route("/register", methods=["GET", "POST"])
    def register():
        if request.method == "POST":
            email = request.form["email"].strip().lower()
            existing = User.query.filter_by(email=email).first()
            if existing:
                flash("That email is already registered.", "warning")
                return redirect(url_for("register"))

            user = User(
                name=request.form["name"].strip(),
                email=email,
                password=generate_password_hash(request.form["password"]),
                role=request.form["role"],
                company_name=request.form["company_name"].strip(),
                bio=request.form["bio"].strip(),
            )
            db.session.add(user)
            db.session.commit()
            flash("Account created successfully. Please sign in.", "success")
            return redirect(url_for("login"))
        return render_template("register.html")

    @app.get("/logout")
    def logout():
        session.clear()
        flash("You have been logged out.", "info")
        return redirect(url_for("home"))

    @app.get("/catalog")
    def catalog():
        query = request.args.get("q", "").strip()
        category_slug = request.args.get("category", "").strip()

        products_query = Product.query
        if query:
            products_query = products_query.filter(Product.name.ilike(f"%{query}%"))
        if category_slug:
            products_query = products_query.join(Category).filter(Category.slug == category_slug)

        products = products_query.order_by(Product.created_at.desc()).all()
        categories = Category.query.order_by(Category.name).all()
        return render_template(
            "catalog.html",
            products=products,
            categories=categories,
            query=query,
            active_category=category_slug,
        )

    @app.route("/product/<int:product_id>", methods=["GET", "POST"])
    def product_detail(product_id):
        product = Product.query.get_or_404(product_id)
        if request.method == "POST":
            user = current_user()
            if not user:
                flash("Please sign in to leave a review.", "warning")
                return redirect(url_for("login"))

            review = Review(
                product_id=product.id,
                user_id=user.id,
                rating=int(request.form["rating"]),
                title=request.form["title"].strip(),
                comment=request.form["comment"].strip(),
            )
            db.session.add(review)
            db.session.commit()
            product.refresh_rating()
            flash("Your review was added.", "success")
            return redirect(url_for("product_detail", product_id=product.id))

        return render_template("product_detail.html", product=product)

    @app.post("/cart/add/<int:product_id>")
    def add_to_cart(product_id):
        quantity = max(int(request.form.get("quantity", 1)), 1)
        cart = session.get("cart", {})
        cart[str(product_id)] = cart.get(str(product_id), 0) + quantity
        session["cart"] = cart
        flash("Product added to cart.", "success")
        return redirect(request.referrer or url_for("catalog"))

    @app.get("/cart")
    def cart():
        items, total = cart_snapshot()
        return render_template("cart.html", items=items, total=total)

    @app.route("/payment", methods=["GET", "POST"])
    def payment():
        items, total = cart_snapshot()
        if not items:
            flash("Add products to your cart before payment.", "warning")
            return redirect(url_for("catalog"))

        if request.method == "POST":
            payment_data = {
                "business_name": request.form["business_name"].strip(),
                "contact_name": request.form["contact_name"].strip(),
                "payment_method": request.form["payment_method"].strip(),
                "delivery_address": request.form["delivery_address"].strip(),
                "notes": request.form["notes"].strip(),
            }
            session["payment_details"] = payment_data
            return redirect(url_for("checkout"))

        return render_template("payment.html", items=items, total=total)

    @app.post("/cart/update/<int:product_id>")
    def update_cart(product_id):
        quantity = max(int(request.form.get("quantity", 1)), 0)
        cart = session.get("cart", {})
        if quantity == 0:
            cart.pop(str(product_id), None)
        else:
            cart[str(product_id)] = quantity
        session["cart"] = cart
        flash("Cart updated.", "info")
        return redirect(url_for("cart"))

    @app.get("/checkout")
    def checkout():
        items, total = cart_snapshot()
        payment_details = session.get("payment_details")
        if not items or not payment_details:
            flash("Complete your cart and payment details first.", "warning")
            return redirect(url_for("cart"))

        session["cart"] = {}
        session.pop("payment_details", None)
        flash("Order request placed. Suppliers will confirm logistics shortly.", "success")
        return render_template("order_success.html", total=total, payment_details=payment_details)

    @app.get("/manufacturer/dashboard")
    def manufacturer_dashboard():
        user = current_user()
        if not user or user.role != "manufacturer":
            flash("Manufacturer access only.", "danger")
            return redirect(url_for("login"))
        products = Product.query.filter_by(manufacturer_id=user.id).order_by(Product.created_at.desc()).all()
        return render_template("manufacturer_dashboard.html", products=products)

    @app.route("/manufacturer/products/new", methods=["GET", "POST"])
    def new_product():
        user = current_user()
        if not user or user.role != "manufacturer":
            flash("Please sign in as a manufacturer.", "danger")
            return redirect(url_for("login"))

        if request.method == "POST":
            category = Category.query.filter_by(id=int(request.form["category_id"])).first()
            product = Product(
                name=request.form["name"].strip(),
                slug=request.form["name"].strip().lower().replace(" ", "-"),
                short_description=request.form["short_description"].strip(),
                description=request.form["description"].strip(),
                image_url=request.form["image_url"].strip(),
                price_per_kg=float(request.form["price_per_kg"]),
                min_order_quantity=int(request.form["min_order_quantity"]),
                stock_kg=int(request.form["stock_kg"]),
                origin=request.form["origin"].strip(),
                delivery_eta=request.form["delivery_eta"].strip(),
                category_id=category.id,
                manufacturer_id=user.id,
            )
            db.session.add(product)
            db.session.commit()
            flash("Product published successfully.", "success")
            return redirect(url_for("manufacturer_dashboard"))

        categories = Category.query.order_by(Category.name).all()
        return render_template("manufacturer_product_form.html", categories=categories)

    @app.get("/manufacturer/store/<int:manufacturer_id>")
    def manufacturer_store(manufacturer_id):
        manufacturer = User.query.get_or_404(manufacturer_id)
        products = Product.query.filter_by(manufacturer_id=manufacturer.id).all()
        return render_template("manufacturer_store.html", manufacturer=manufacturer, products=products)
