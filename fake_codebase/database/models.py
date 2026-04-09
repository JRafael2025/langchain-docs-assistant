"""
Database models — SQLAlchemy ORM definitions for core entities.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import (Boolean, Column, DateTime, Enum, Float, ForeignKey,
                        Integer, String, Text)
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    """
    Represents a registered user of the platform.

    Attributes:
        id: Auto-incremented primary key.
        email: Unique email address used for login.
        password_hash: PBKDF2 hash of the user's password.
        salt: Random salt used when hashing the password.
        roles: Comma-separated list of roles (e.g. 'user,billing').
        is_active: False if the account has been deactivated.
        created_at: UTC timestamp of account creation.
        last_login: UTC timestamp of the most recent login.
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(128), nullable=False)
    salt = Column(String(64), nullable=False)
    roles = Column(String(255), default="user")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)

    orders = relationship("Order", back_populates="user", lazy="select")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "email": self.email,
            "roles": self.roles.split(",") if self.roles else [],
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Product(Base):
    """
    A product available for purchase.

    Attributes:
        id: Auto-incremented primary key.
        sku: Unique stock-keeping unit identifier.
        name: Display name of the product.
        description: Long-form product description.
        price: Price in USD (decimal).
        stock: Current available inventory count.
        is_available: Whether the product is currently for sale.
    """
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, autoincrement=True)
    sku = Column(String(64), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    price = Column(Float, nullable=False)
    stock = Column(Integer, default=0)
    is_available = Column(Boolean, default=True)

    def is_in_stock(self) -> bool:
        """Return True if product has stock available."""
        return self.is_available and self.stock > 0

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "sku": self.sku,
            "name": self.name,
            "price": self.price,
            "stock": self.stock,
            "is_available": self.is_available,
        }


class Order(Base):
    """
    Represents a customer order (may contain multiple items).

    Attributes:
        id: UUID string (not auto-increment — set at creation).
        user_id: FK to the User who placed the order.
        status: One of 'pending', 'paid', 'shipped', 'delivered', 'cancelled'.
        total_amount: Total charged amount in USD.
        currency: ISO 4217 currency code.
        created_at: UTC timestamp of order creation.
        updated_at: UTC timestamp of last status change.
    """
    __tablename__ = "orders"

    id = Column(String(36), primary_key=True)  # UUID
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    status = Column(
        Enum("pending", "paid", "shipped", "delivered", "cancelled"),
        default="pending",
    )
    total_amount = Column(Float, nullable=False)
    currency = Column(String(3), default="USD")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    transaction = relationship("Transaction", back_populates="order", uselist=False)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "status": self.status,
            "total_amount": self.total_amount,
            "currency": self.currency,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class OrderItem(Base):
    """A single line item within an Order."""
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(String(36), ForeignKey("orders.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Float, nullable=False)

    order = relationship("Order", back_populates="items")
    product = relationship("Product")


class Transaction(Base):
    """
    Records a payment transaction linked to an Order.

    Attributes:
        id: UUID string from the payment processor.
        order_id: FK to the associated Order.
        gateway: Payment gateway used ('stripe' or 'paypal').
        gateway_reference: Gateway's own transaction/charge ID.
        amount: Amount charged.
        currency: Currency code.
        status: One of 'pending', 'captured', 'failed', 'refunded'.
        created_at: UTC timestamp.
    """
    __tablename__ = "transactions"

    id = Column(String(36), primary_key=True)
    order_id = Column(String(36), ForeignKey("orders.id"), nullable=False)
    gateway = Column(String(32), default="stripe")
    gateway_reference = Column(String(128), nullable=True)
    amount = Column(Float, nullable=False)
    currency = Column(String(3), default="USD")
    status = Column(
        Enum("pending", "authorized", "captured", "failed", "refunded", "partially_refunded"),
        default="pending",
    )
    created_at = Column(DateTime, default=datetime.utcnow)

    order = relationship("Order", back_populates="transaction")
