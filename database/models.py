from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Date
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
    
    location = relationship("Location", back_populates="products")
    nomenclature = relationship("Nomenclature", back_populates="products", foreign_keys=[code])

class SupplyList(Base):
    __tablename__ = 'supply_lists'
    id = Column(Integer, primary_key=True)
    title = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    status = Column(String(20), default='draft') # draft, validated

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
    designation = Column(String(255))
    reported_at = Column(DateTime, default=datetime.now)
