from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Date,
    ForeignKey,
    DECIMAL,
    func,
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from faker import Faker
import random

faker = Faker()

DATABASE_URL = "mysql+pymysql://root:root@localhost:3306/supply_chain"

engine = create_engine(DATABASE_URL)
Base = declarative_base()


class Supplier(Base):
    __tablename__ = "suppliers"

    supplier_id = Column(Integer, primary_key=True, autoincrement=True)
    company_name = Column(String(255), nullable=False)
    contact_person = Column(String(255), nullable=False)
    phone = Column(String(20))
    account_number = Column(String(20))

    deliveries = relationship("Delivery", back_populates="supplier")


class Material(Base):
    __tablename__ = "materials"

    material_id = Column(Integer, primary_key=True, autoincrement=True)
    material_name = Column(String(255), nullable=False)
    price = Column(DECIMAL(10, 2), nullable=False)

    deliveries = relationship("Delivery", back_populates="material")


class Delivery(Base):
    __tablename__ = "deliveries"

    delivery_id = Column(Integer, primary_key=True, autoincrement=True)
    delivery_date = Column(Date, nullable=False)
    supplier_id = Column(Integer, ForeignKey("suppliers.supplier_id"), nullable=False)
    material_id = Column(Integer, ForeignKey("materials.material_id"), nullable=False)
    delivery_days = Column(Integer, nullable=False)
    quantity = Column(Integer, nullable=False)

    supplier = relationship("Supplier", back_populates="deliveries")
    material = relationship("Material", back_populates="deliveries")


def create_tables():
    Base.metadata.create_all(engine)
    print("Таблиці створені успішно!")


def insert_data(session):
    suppliers_data = [
        (
            faker.company(),
            faker.name(),
            faker.phone_number(),
            faker.random_int(min=1000, max=9999),
        )
        for _ in range(4)
    ]

    materials_data = [("Wood", 10.00), ("Varnish", 5.50), ("Steel Parts", 15.00)]

    suppliers = [
        Supplier(
            company_name=company,
            contact_person=contact,
            phone=phone.split("x")[0],
            account_number=str(account),
        )
        for company, contact, phone, account in suppliers_data
    ]
    session.add_all(suppliers)
    session.commit()

    materials = [
        Material(material_name=name, price=price) for name, price in materials_data
    ]
    session.add_all(materials)
    session.commit()

    supplier_ids = [supplier.supplier_id for supplier in session.query(Supplier).all()]
    material_ids = [material.material_id for material in session.query(Material).all()]

    deliveries_data = []
    for _ in range(22):
        delivery_date = faker.date_between(start_date="-30d", end_date="today")
        supplier_id = random.choice(supplier_ids)
        material_id = random.choice(material_ids)
        delivery_days = random.randint(1, 7)
        quantity = random.randint(1, 100)
        deliveries_data.append(
            (delivery_date, supplier_id, material_id, delivery_days, quantity)
        )

    deliveries = [
        Delivery(
            delivery_date=date,
            supplier_id=supplier_id,
            material_id=material_id,
            delivery_days=delivery_days,
            quantity=quantity,
        )
        for date, supplier_id, material_id, delivery_days, quantity in deliveries_data
    ]
    session.add_all(deliveries)
    session.commit()
    print("Дані успішно вставлені!")


def execute_queries(session):
    print("\nПоставки за 3 або менше днів:")
    results = (
        session.query(Delivery, Supplier)
        .join(Supplier)
        .filter(Delivery.delivery_days <= 3)
        .order_by(Supplier.company_name)
        .all()
    )
    for delivery, supplier in results:
        print(
            f"{delivery.delivery_id}: {supplier.company_name}, Delivery Days: {delivery.delivery_days}"
        )

    print("\nСума до сплати за кожну поставку:")
    results = session.query(Delivery, Material).join(Material).all()
    for delivery, material in results:
        total_amount = material.price * delivery.quantity
        print(f"Delivery ID: {delivery.delivery_id}, Total Amount: {total_amount:.2f}")

    selected_material = "Wood"
    print(f"\nПоставки для матеріалу: {selected_material}:")
    results = (
        session.query(Delivery, Supplier)
        .join(Supplier)
        .join(Material)
        .filter(Material.material_name == selected_material)
        .all()
    )
    for delivery, supplier in results:
        print(f"Delivery ID: {delivery.delivery_id}, Supplier: {supplier.company_name}")

    print("\nКількість матеріалів, що постачаються кожним постачальником:")
    results = (
        session.query(
            Supplier.company_name, Material.material_name, func.sum(Delivery.quantity)
        )
        .select_from(Supplier)
        .join(Delivery)
        .join(Material)
        .group_by(Supplier.company_name, Material.material_name)
        .all()
    )
    for supplier_name, material_name, total_quantity in results:
        print(
            f"Supplier: {supplier_name}, Material: {material_name}, Total Quantity: {total_quantity}"
        )

    print("\nЗагальна кількість кожного матеріалу:")
    results = (
        session.query(Material.material_name, func.sum(Delivery.quantity))
        .join(Delivery)
        .group_by(Material.material_name)
        .all()
    )
    for material_name, total_quantity in results:
        print(f"Material: {material_name}, Total Quantity: {total_quantity}")

    print("\nКількість поставок від кожного постачальника:")
    results = (
        session.query(Supplier.company_name, func.count(Delivery.delivery_id))
        .join(Delivery)
        .group_by(Supplier.company_name)
        .all()
    )
    for supplier_name, total_deliveries in results:
        print(f"Supplier: {supplier_name}, Total Deliveries: {total_deliveries}")


def main():
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # create_tables()

        # insert_data(session)

        execute_queries(session)

    except Exception as e:
        print(e)
    finally:
        session.close()


if __name__ == "__main__":
    main()
