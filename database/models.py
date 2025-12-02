from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Date, Float
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), default='agent') # admin, agent

class Location(Base):
    __tablename__ = 'locations'
    id = Column(Integer, primary_key=True)
    label = Column(String(10), unique=True, nullable=False) # e.g., A1
    barcode = Column(String(20), unique=True, nullable=False) # 000XXYY

    products = relationship("Product", back_populates="location")

class Nomenclature(Base):
    __tablename__ = 'nomenclature'
    id = Column(Integer, primary_key=True)
    code = Column(String(50), unique=True, nullable=False, index=True)
    designation = Column(String(255), nullable=False)
    last_supply_date = Column(DateTime, nullable=True)
    last_search_date = Column(DateTime, nullable=True)
    last_edit_date = Column(DateTime, nullable=True)

    products = relationship("Product", back_populates="nomenclature", foreign_keys="Product.code", primaryjoin="Product.code==Nomenclature.code")

class Product(Base):
    __tablename__ = 'products'
    id = Column(Integer, primary_key=True)
    code = Column(String(50), ForeignKey('nomenclature.code'), nullable=False) # Code Produit (from XpertPharm)
    barcode = Column(String(50), nullable=False) # Code Barre Lot
    expiry_date = Column(Date, nullable=True)
    location_id = Column(Integer, ForeignKey('locations.id'))
    cleaning = Column(Boolean, default=False)
    
    location = relationship("Location", back_populates="products")
    nomenclature = relationship("Nomenclature", back_populates="products", foreign_keys=[code])

class SupplyList(Base):
    __tablename__ = 'supply_lists'
    id = Column(Integer, primary_key=True)
    title = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    status = Column(String(20), default='draft') # draft, validated, closed

    items = relationship("SupplyListItem", back_populates="supply_list", cascade="all, delete-orphan")

class SupplyListItem(Base):
    __tablename__ = 'supply_list_items'
    id = Column(Integer, primary_key=True)
    supply_list_id = Column(Integer, ForeignKey('supply_lists.id'))
    
    # Item 1 (Selected)
    product_code_1 = Column(String(50))
    designation_1 = Column(String(255))
    location_1 = Column(String(50))
    barcode_1 = Column(String(50))
    expiry_date_1 = Column(Date)

    # Item 2 (Next in list)
    product_code_2 = Column(String(50), nullable=True)
    designation_2 = Column(String(255), nullable=True)
    location_2 = Column(String(50), nullable=True)
    barcode_2 = Column(String(50), nullable=True)
    expiry_date_2 = Column(Date, nullable=True)

    quantity = Column(Integer, default=1)
    
    # Validation Result
    result = Column(String(50), default='V') # V, S, X, or New Location

    supply_list = relationship("SupplyList", back_populates="items")

class MissingItem(Base):
    __tablename__ = 'missing_items'
    id = Column(Integer, primary_key=True)
    product_code = Column(String(50))
    # designation removed, linked via nomenclature
    source = Column(String(50), default='Inconnu')
    quantity = Column(Integer, default=1)
    reported_at = Column(DateTime, default=datetime.now)
    is_deleted = Column(Boolean, default=False)

    nomenclature = relationship("Nomenclature", primaryjoin="foreign(MissingItem.product_code) == Nomenclature.code", viewonly=True)

class Notification(Base):
    __tablename__ = 'notifications'
    id = Column(Integer, primary_key=True)
    sender_station = Column(String(50))
    target_role = Column(String(50), default='SERVER')
    product_code = Column(String(50))
    product_name = Column(String(255))
    quantity = Column(Integer)
    message = Column(String(500))
    is_urgent = Column(Boolean, default=False)
    status = Column(String(20), default='pending') # pending, confirmed, rejected, received
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

class EventLog(Base):
    __tablename__ = 'event_logs'
    id = Column(Integer, primary_key=True)
    event_type = Column(String(50), nullable=False) # VIEW_LOCATION, LIST_STARTED, LIST_CLOSED, LIST_VALIDATED, INVENTORY_ADD, INVENTORY_CLEANING_LOSS
    timestamp = Column(DateTime, default=datetime.now)
    details = Column(String(500), nullable=True) # JSON or Text
    source = Column(String(50), nullable=True) # Widget name
    machine_name = Column(String(100), nullable=True) # PC Name
    delay = Column(Float, nullable=True) # Délai en heures pour INVENTORY_ADD
