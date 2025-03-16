import os.path
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime
from typing import Union, List

from config.utils import DS_FILE_NAME, DS_DATA_DIR, IDATA_TABLE_NAME


class ElementNotFoundException(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


@dataclass
class IglooDataElement:
    timestamp: Union[datetime, str]
    reading_now: int = field(default=0)
    reading_20: int = field(default=0)
    velocity: float = field(default=0.0)
    notes: str = field(default="")

    @property
    def timestamp_str(self) -> str:
        return str(self.timestamp)

    @property
    def notes_list(self) -> List[str]:
        return [s for s in self.notes.split(",") if s]

    @staticmethod
    def get_notes_str(notes_list: List[str]) -> str:
        return ",".join(notes_list)

    def __post_init__(self):
        if isinstance(self.timestamp, str):
            self.timestamp = parse_timestamp(self.timestamp)

    def merge_with(self, new):
        if not isinstance(new, IglooDataElement):
            raise ValueError("Can only merge with another IglooDataElement instance.")

        assert self.timestamp_str == new.timestamp_str
        assert self.reading_now == new.reading_now or new.reading_now == 0
        try:
            self.reading_20 = new_or_nz(self.reading_20, new.reading_20)
            self.velocity = new_or_nz(self.velocity, new.velocity)
        except ValueError as exc:
            print(f"Failed merging : {exc}")
            raise

        if self.notes != new.notes:
            notes_list = list(set(self.notes_list + new.notes_list))
            self.notes = self.get_notes_str(notes_list)

    @classmethod
    def from_db_record(cls, record):
        return cls(
            timestamp=parse_timestamp(record[0]),
            reading_now=record[1],
            reading_20=record[2],
            velocity=record[3],
            notes=record[4]
        )


def new_or_nz(old, new):
    if not isinstance(old, (int, float)) or not isinstance(new, (int, float)):
        print(f"Received {old} and {new}")
        raise ValueError("can only operate with numbers")

    if old and new and old != new:
        print(f"Both old:{old} and new:{new} are non-zero, returning new")
        return new
    else:
        return old or new


def parse_timestamp(ts_str: str) -> datetime:
    try:
        return datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        raise ValueError(f"Invalid timestamp format: {ts_str}. Expected format: 'YYYY-MM-DD HH:MM:SS'.")


class SqliteDatabase:
    def __init__(self, data_dir=DS_DATA_DIR, db_filename=DS_FILE_NAME):
        db_path = os.path.join(data_dir, db_filename)
        self.db_conn = sqlite3.connect(db_path)
        self.cursor = self.db_conn.cursor()
        self.create_table()

    def create_table(self):
        create_table_query = f'''
        CREATE TABLE IF NOT EXISTS {IDATA_TABLE_NAME} (
            timestamp TEXT PRIMARY KEY,
            reading_now INT,
            reading_20 REAL,
            velocity REAL,
            notes TEXT
        );
        '''
        print(f"Table created : {IDATA_TABLE_NAME}")
        self.cursor.execute(create_table_query)
        self.db_conn.commit()

    def insert_element(self, element: IglooDataElement):
        timestamp_str = element.timestamp_str
        try:
            existing_elem = self.fetch_w_ts(timestamp=timestamp_str)
            element.merge_with(existing_elem)
        except ElementNotFoundException:
            pass

        insert_element_query = f'''
            INSERT OR REPLACE INTO {IDATA_TABLE_NAME} (
                timestamp,
                reading_now,
                reading_20,
                velocity,
                notes
            ) VALUES (
                '{element.timestamp_str}',
                '{element.reading_now}', 
                '{element.reading_20}', 
                '{element.velocity}', 
                '{element.notes}'
            );
            '''
        print(f"inserting {element} into {IDATA_TABLE_NAME}")
        self.cursor.execute(insert_element_query)
        self.db_conn.commit()

    def if_exists(self, timestamp: Union[str, datetime]) -> bool:
        try:
            self.fetch_w_ts(timestamp)
            return True
        except ElementNotFoundException:
            return False

    def fetch_w_ts(self, timestamp: Union[str, datetime]) -> IglooDataElement:
        print(f"querying {IDATA_TABLE_NAME} for record of {timestamp}")
        timestamp = str(timestamp) if isinstance(timestamp, datetime) else timestamp
        fetch_record_query = f'''
        SELECT 
            * 
        FROM 
            {IDATA_TABLE_NAME} 
        WHERE 
            timestamp = '{timestamp}'
        ;
        '''
        self.cursor.execute(fetch_record_query)
        record = self.cursor.fetchone()
        if not record:
            raise ElementNotFoundException(f"{timestamp} : Not found")

        return IglooDataElement.from_db_record(record=record)

    def fetch_w_ts_range(self, ts_start: Union[str, datetime], ts_end: Union[str, datetime]) -> List[IglooDataElement]:
        ts_start = str(ts_start) if isinstance(ts_start, datetime) else ts_start
        ts_end = str(ts_end) if isinstance(ts_end, datetime) else ts_end
        # print(f"querying {IDATA_TABLE_NAME} for records between {ts_start} and {ts_end}")
        fetch_range_query = f'''
        SELECT 
            * 
        FROM 
            {IDATA_TABLE_NAME} 
        WHERE 
            timestamp BETWEEN '{ts_start}' AND '{ts_end}'
        ORDER BY
            timestamp DESC
        ;
        '''
        self.cursor.execute(fetch_range_query)
        records = self.cursor.fetchall()
        idel_list = [IglooDataElement.from_db_record(rec) for rec in records]

        print(f"returning {len(idel_list)} results")
        return idel_list


if __name__ == '__main__':
    sqldb = SqliteDatabase()
    ts = parse_timestamp("2025-03-09 21:30:58")
    new_el = IglooDataElement(
        timestamp=ts,
        reading_now=152,
        # notes="sugar"
    )
    sqldb.insert_element(new_el)

    new_el = IglooDataElement(
        timestamp=ts,
        # reading_now=152,
        notes="sugar"
    )
    sqldb.insert_element(new_el)

    fel = sqldb.fetch_w_ts(ts)
    follow = sqldb.fetch_w_ts_range("2025-03-08 21:35:58", "2025-03-10 21:35:58")
    sqldb.db_conn.close()
    pass
