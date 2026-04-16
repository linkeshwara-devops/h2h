from datetime import datetime

from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    company_name = db.Column(db.String(140), nullable=False)
    bio = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    products = db.relationship("Product", backref="manufacturer", lazy=True)
    reviews = db.relationship("Review", backref="user", lazy=True)


class Category(db.Model):
    __tablename__ = "categories"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    slug = db.Column(db.String(120), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=False)
    products = db.relationship("Product", backref="category", lazy=True)


class Product(db.Model):
    __tablename__ = "products"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    slug = db.Column(db.String(140), unique=True, nullable=False)
    short_description = db.Column(db.String(220), nullable=False)
    description = db.Column(db.Text, nullable=False)
    image_url = db.Column(db.String(500), nullable=False)
    price_per_kg = db.Column(db.Float, nullable=False)
    min_order_quantity = db.Column(db.Integer, nullable=False)
    stock_kg = db.Column(db.Integer, nullable=False)
    origin = db.Column(db.String(120), nullable=False)
    delivery_eta = db.Column(db.String(120), nullable=False)
    rating = db.Column(db.Float, default=4.5)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=False)
    manufacturer_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    reviews = db.relationship("Review", backref="product", lazy=True, cascade="all, delete-orphan")

    def refresh_rating(self):
        self.rating = round(sum(review.rating for review in self.reviews) / len(self.reviews), 1) if self.reviews else 0
        db.session.commit()


class Review(db.Model):
    __tablename__ = "reviews"
    id = db.Column(db.Integer, primary_key=True)
    rating = db.Column(db.Integer, nullable=False)
    title = db.Column(db.String(160), nullable=False)
    comment = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)


def seed_database():
    if Category.query.first():
        return

    categories = [
        Category(name="Pulses", slug="pulses", description="Protein-rich lentils and dal for hotel kitchens."),
        Category(name="Tomato", slug="tomato", description="Fresh and processed tomato supply for bulk buyers."),
        Category(name="Potato", slug="potato", description="Table and processing grade potatoes."),
        Category(name="Rice", slug="rice", description="Premium rice varieties for restaurants and banquets."),
        Category(name="Wheat", slug="wheat", description="Bulk wheat grains and flour-ready lots."),
        Category(name="Spices", slug="spices", description="Aromatic whole spices and blended options."),
    ]
    db.session.add_all(categories)
    db.session.flush()

    users = [
        User(name="Raghav Sharma", email="raghav@greenpulse.com", password=generate_password_hash("demo123"), role="manufacturer", company_name="GreenPulse Foods", bio="Supplying sorted pulses and grains with strict moisture control and hotel-ready packaging."),
        User(name="Anita Rao", email="anita@freshfields.in", password=generate_password_hash("demo123"), role="manufacturer", company_name="FreshFields Produce", bio="Farm-linked vegetable network with rapid dispatch for hospitality kitchens."),
        User(name="Hotel Buyer", email="buyer@demo.com", password=generate_password_hash("demo123"), role="buyer", company_name="Skyline Hotel Group", bio="Procurement team for multi-city hotel kitchens."),
    ]
    db.session.add_all(users)
    db.session.flush()

    category_lookup = {category.slug: category.id for category in categories}
    manufacturer_lookup = {user.company_name: user.id for user in users}
    products = [
        Product(name="Premium Toor Dal", slug="premium-toor-dal", short_description="Machine-cleaned toor dal with uniform split size for large kitchens.", description="Consistent texture, low impurity level, and food-service grade packing for hotels, caterers, and cloud kitchens.", image_url="https://images.unsplash.com/photo-1515543904379-3d757afe72e4?auto=format&fit=crop&w=900&q=80", price_per_kg=98, min_order_quantity=25, stock_kg=1400, origin="Maharashtra", delivery_eta="2-3 business days", category_id=category_lookup["pulses"], manufacturer_id=manufacturer_lookup["GreenPulse Foods"], rating=4.8),
        Product(name="Hotel Red Tomatoes", slug="hotel-red-tomatoes", short_description="Firm red tomatoes for gravies, salads, and buffet prep.", description="Selected for consistency, shine, and transport stability with bulk-crate dispatch for hotel kitchens.", image_url="https://images.unsplash.com/photo-1546094096-0df4bcaaa337?auto=format&fit=crop&w=900&q=80", price_per_kg=34, min_order_quantity=40, stock_kg=2200, origin="Kolar", delivery_eta="Next-day dispatch", category_id=category_lookup["tomato"], manufacturer_id=manufacturer_lookup["FreshFields Produce"], rating=4.6),
        Product(name="Processing Grade Potatoes", slug="processing-grade-potatoes", short_description="Bulk potatoes ideal for fries, curries, and breakfast service.", description="Low bruising, uniform size, and dependable shelf life for high-volume food operations.", image_url="https://images.unsplash.com/photo-1518977676601-b53f82aba655?auto=format&fit=crop&w=900&q=80", price_per_kg=28, min_order_quantity=50, stock_kg=3600, origin="Agra", delivery_eta="48 hours", category_id=category_lookup["potato"], manufacturer_id=manufacturer_lookup["FreshFields Produce"], rating=4.4),
        Product(name="Aged Basmati Rice", slug="aged-basmati-rice", short_description="Long-grain basmati for premium dining and banquet menus.", description="Naturally aged grains with high elongation, aromatic finish, and export-style quality sorting.", image_url="https://images.unsplash.com/photo-1586201375761-83865001e31c?auto=format&fit=crop&w=900&q=80", price_per_kg=122, min_order_quantity=30, stock_kg=1800, origin="Haryana", delivery_eta="3-4 business days", category_id=category_lookup["rice"], manufacturer_id=manufacturer_lookup["GreenPulse Foods"], rating=4.9),
        Product(name="Sharbati Wheat", slug="sharbati-wheat", short_description="High-quality wheat for atta mills and hotel bakery units.", description="Golden grain finish, clean lots, and dependable milling yield for chapati and bakery programs.", image_url="https://images.unsplash.com/photo-1574323347407-f5e1ad6d020b?auto=format&fit=crop&w=900&q=80", price_per_kg=42, min_order_quantity=60, stock_kg=2600, origin="Madhya Pradesh", delivery_eta="3 business days", category_id=category_lookup["wheat"], manufacturer_id=manufacturer_lookup["GreenPulse Foods"], rating=4.5),
        Product(name="Whole Dry Red Chillies", slug="whole-dry-red-chillies", short_description="Color-rich chillies for hotel kitchens and masala units.", description="Cleaned, sun-dried, and packed in bulk lots with heat consistency and strong aroma retention.", image_url="https://images.unsplash.com/photo-1583224995223-2a82b2f6c1f4?auto=format&fit=crop&w=900&q=80", price_per_kg=160, min_order_quantity=15, stock_kg=700, origin="Guntur", delivery_eta="2 business days", category_id=category_lookup["spices"], manufacturer_id=manufacturer_lookup["GreenPulse Foods"], rating=4.7),
    ]
    db.session.add_all(products)
    db.session.flush()

    buyer = next(user for user in users if user.role == "buyer")
    db.session.add_all([
        Review(rating=5, title="Reliable hotel-grade quality", comment="The basmati rice had strong aroma and excellent grain length after cooking. Repeat order approved.", product_id=products[3].id, user_id=buyer.id),
        Review(rating=4, title="Fresh stock and neat packing", comment="Tomatoes arrived firm and bright. Ideal for our breakfast and curry sections.", product_id=products[1].id, user_id=buyer.id),
        Review(rating=5, title="Consistent dal for bulk kitchen use", comment="Very low wastage after washing. The split size stayed even across the batch.", product_id=products[0].id, user_id=buyer.id),
    ])
    db.session.commit()
