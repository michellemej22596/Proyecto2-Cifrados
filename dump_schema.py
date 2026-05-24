from back.database import engine
from back.models import Base
from sqlalchemy.schema import CreateTable

with open("init.sql", "w") as f:
    for table in Base.metadata.sorted_tables:
        f.write(str(CreateTable(table).compile(engine)) + ";\n")
