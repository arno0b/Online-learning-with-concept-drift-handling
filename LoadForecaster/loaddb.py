from sqlalchemy import create_engine, Column, Integer, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
import os
from sqlalchemy import desc

Base = declarative_base()

class Data(Base):
    __tablename__ = 'data'

    id = Column(Integer, primary_key=True, autoincrement=True)
    datetime = Column(DateTime, nullable=False)
    actual_value = Column(Float)
    forecasted_value = Column(Float)
    forecasted_value = Column(Float)
    mae_value = Column(Float)
    mse_value = Column(Float)

def init_db(db_uri):
    # Extract the file path from the database URI
    db_file_path = db_uri.replace("sqlite:///", "")

    # Check if the database file already exists
    if os.path.isfile(db_file_path):
        engine = create_engine(db_uri)
        Session = sessionmaker(bind=engine)
        return Session()

    # If the file doesn't exist, create the database and tables
    engine = create_engine(db_uri)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session()

def save_data(session, datetime, actual_value, forecasted_value, mae_value, mse_value):
    new_data = Data(datetime=datetime, 
                    actual_value=actual_value, 
                    forecasted_value=forecasted_value,
                    mae_value=mae_value,
                    mse_value = mse_value)
    session.add(new_data)
    session.commit()

def datetime_exists(session, datetime_to_check):
    # Check if a record with the given datetime exists in the database
    existing_record = session.query(Data).filter(Data.datetime == datetime_to_check).first()

    return existing_record is not None

def get_last_hours_data(session):
    # Retrieve the timestamp of the last entry in the database
    last_entry = session.query(Data).order_by(desc(Data.datetime)).first()

    if last_entry:
        end_datetime = last_entry.datetime
        start_datetime = end_datetime - timedelta(hours=36)

        # Retrieve data within the last 24 hours based on the last entry's timestamp
        data = session.query(Data).filter(Data.datetime.between(start_datetime, end_datetime)).all()
        return data

    # If there are no entries in the database, return an empty list
    return []

def update_actual_value(session, datetime, new_actual_value):
    data_entry = session.query(Data).filter(Data.datetime == datetime).first()
    if data_entry:
        data_entry.actual_value = new_actual_value
        session.commit()
        return True
    return False
