import os.path
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime
from typing import Union, List

from config.utils import DS_FILE_NAME, DS_DATA_DIR, IDATA_TABLE_NAME, TIMESTAMP_FORMAT


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
    insulin_units: int = field(default=0)
    food: str = field(default="")
    notes: str = field(default="")

    @property
    def timestamp_str(self) -> str:
        return datetime.strftime(self.timestamp, TIMESTAMP_FORMAT)

    @property
    def notes_list(self) -> List[str]:
        return [s for s in self.notes.split(",") if s]

    @staticmethod
    def get_notes_str(notes_list: List[str]) -> str:
        return ",".join(notes_list)

    def __post_init__(self):
        if isinstance(self.timestamp, str):
            self.timestamp = parse_timestamp(self.timestamp)
        elif isinstance(self.timestamp, datetime):
            self.timestamp = self.timestamp.replace(second=0, microsecond=0)

    def merge_with(self, ex_elem):
        if not isinstance(ex_elem, IglooDataElement):
            raise ValueError("Can only merge with another IglooDataElement instance.")

        assert self.timestamp_str == ex_elem.timestamp_str
        try:
            self.reading_now = merge_nums(ex_elem.reading_now, p=self.reading_now)
            self.reading_20 = merge_nums(ex_elem.reading_20, p=self.reading_20)
            self.velocity = merge_nums(ex_elem.velocity, p=self.velocity)
            self.insulin_units = merge_nums(ex_elem.insulin_units, p=self.insulin_units)
            self.food = join_strings(self.food, ex_elem.food)
            self.notes = join_strings(self.notes, ex_elem.notes)
        except ValueError as exc:
            print(f"Failed merging : {exc}")
            raise

    @classmethod
    def from_db_record(cls, record):
        ins_value = 0 if isinstance(record[5], str) or not record[5] else record[5]
        return cls(
            timestamp=parse_timestamp(record[0]),
            reading_now=record[1],
            reading_20=record[2],
            velocity=record[3],
            notes=record[4],
            insulin_units=ins_value,
            food=record[6],
        )


def merge_nums(a, p):
    a = 0 if not a else a
    p = 0 if not p else p
    # In case both are non-zero, prioritize p
    if a == 0 or p == 0:
        return a or p
    else:
        return p


def join_strings(old, new):
    old = '' if not old else old.strip(",")
    new = '' if not new else new.strip(",")
    return ",".join(list(set(old.split(",") + new.split(",")))).strip(",")


def parse_timestamp(ts_str: str) -> datetime:
    try:
        return datetime.strptime(ts_str[:16], TIMESTAMP_FORMAT)
    except ValueError:
        raise ValueError(f"Invalid timestamp format: {ts_str}. Expected format: {TIMESTAMP_FORMAT}.")


class SqliteDatabase:
    def __init__(self, data_dir=DS_DATA_DIR, db_filename=DS_FILE_NAME):
        db_path = os.path.join(data_dir, db_filename)
        self.db_conn = sqlite3.connect(db_path)
        self.cursor = self.db_conn.cursor()
        self.create_table()
        self.alter_table()
        self.table_updates()

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

    def table_updates(self):
        update_query = f"UPDATE {IDATA_TABLE_NAME} SET timestamp = substr(timestamp, 1, 16);"
        self.cursor.execute(update_query)
        self.db_conn.commit()

    def alter_table(self):
        self.cursor.execute(f"PRAGMA table_info({IDATA_TABLE_NAME});")
        columns = self.cursor.fetchall()
        existing_columns = [col[1] for col in columns]
        new_columns_to_add = ["insulin_units", "food"]

        for column_name in new_columns_to_add:
            if column_name not in existing_columns:
                alter_table_query = f'ALTER TABLE {IDATA_TABLE_NAME} ADD COLUMN {column_name} INT;'
                self.cursor.execute(alter_table_query)
                self.db_conn.commit()

    def insert_element(self, new_element: IglooDataElement):
        timestamp_str = new_element.timestamp_str
        try:
            existing_elem = self.fetch_w_ts(timestamp=timestamp_str)
            new_element.merge_with(ex_elem=existing_elem)
        except ElementNotFoundException:
            pass

        insert_element_query = f'''
            INSERT OR REPLACE INTO {IDATA_TABLE_NAME} (
                timestamp,
                reading_now,
                reading_20,
                velocity,
                insulin_units,
                food,
                notes
            ) VALUES (
                '{new_element.timestamp_str}',
                '{new_element.reading_now}', 
                '{new_element.reading_20}', 
                '{new_element.velocity}',
                '{new_element.insulin_units}',
                '{new_element.food}', 
                '{new_element.notes}'
            );
            '''
        print(f"inserting {new_element} into {IDATA_TABLE_NAME}")
        self.cursor.execute(insert_element_query)
        self.db_conn.commit()

    def if_exists(self, timestamp: Union[str, datetime]) -> bool:
        try:
            elem = self.fetch_w_ts(timestamp)
            if elem.reading_now:
                return True
            return False
        except ElementNotFoundException:
            return False

    def fetch_w_ts(self, timestamp: Union[str, datetime]) -> IglooDataElement:
        # print(f"querying {IDATA_TABLE_NAME} for record of {timestamp}")
        timestamp = datetime.strftime(timestamp, TIMESTAMP_FORMAT) if isinstance(timestamp, datetime) else timestamp
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
    # sqldb = SqliteDatabase()
    # ts = parse_timestamp("2025-03-09 21:30:58")
    # new_el = IglooDataElement(
    #     timestamp=ts,
    #     reading_now=152,
    #     # notes="sugar"
    # )
    # sqldb.insert_element(new_el)
    #
    # new_el = IglooDataElement(
    #     timestamp=ts,
    #     # reading_now=152,
    #     notes="sugar"
    # )
    # sqldb.insert_element(new_el)
    #
    # fel = sqldb.fetch_w_ts(ts)
    # follow = sqldb.fetch_w_ts_range("2025-03-08 21:35:58", "2025-03-10 21:35:58")
    # sqldb.db_conn.close()
    pass
