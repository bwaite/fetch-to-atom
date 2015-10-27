

from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, DateTime
import yaml

conf = yaml.load(open('conf.yml'))
psql_cstr = conf['postgres_connection_str']
psql_schema = conf['postgres_schema']

engine = create_engine(psql_cstr)
conn = engine.connect()

metadata = MetaData(schema=psql_schema)

articles = Table('articles', metadata,
                 Column('id', Integer, primary_key=True),
                 Column('title', String),
                 Column('author', String),
                 Column('url', String),
                 Column('updated', DateTime)
)


# metadata.create_all(engine)
