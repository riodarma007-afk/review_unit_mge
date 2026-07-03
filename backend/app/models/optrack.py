from sqlalchemy import Column, Integer, String, Float, Date, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.core.database import Base

class DataUtama(Base):
    __tablename__ = "Optrack_data_event"
    
    ID_data = Column(String(50), primary_key=True, index=True)
    Date = Column(Date, index=True)
    Shift = Column(String(20), index=True)
    PIT = Column(String(50), index=True)
    Unit_Code = Column(String(50), index=True)
    Operator = Column(String(100))
    Activity = Column(String(50), index=True)
    HM_Awal = Column(Float)
    HM_Akhir = Column(Float)
    Ritasi = Column(Integer)
    HM = Column(Float)
    MOHH = Column(Float)
    WH = Column(Float)
    Downtime = Column(Float)
    Delay = Column(Float)
    Idle = Column(Integer)
    last_modified = Column(DateTime)
    is_deleted = Column(Integer, default=0, index=True)
    
    # Relationship to events
    events = relationship("LaporanEvent", back_populates="data_utama", foreign_keys="[LaporanEvent.ID_data_Input]")

class LaporanEvent(Base):
    __tablename__ = "Optrack_breakdown_list"
    
    Event_ID = Column(String(50), primary_key=True, index=True)
    ID_data_Input = Column(String(50), ForeignKey("Optrack_data_event.ID_data"), index=True)
    Date = Column(Date)
    Shift = Column(String(20))
    Unit_Code = Column('Unit Code', String(50)) # Mapping column name 'Unit Code' or 'Unit_Code', we use 'Unit_Code' as property
    User = Column(String(100))
    Activity = Column(String(50))
    PIT = Column(String(50))
    Time = Column(String(20))
    Code = Column(Integer, index=True)
    Status = Column(String(100), index=True)
    Start = Column(String(10))
    Stop = Column(String(10))
    Plan = Column(Integer)
    Durasi = Column(Float)
    Noted = Column(Text)
    
    data_utama = relationship("DataUtama", back_populates="events")
