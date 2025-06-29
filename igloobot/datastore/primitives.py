import os.path
import sqlite3
from abc import abstractmethod, ABC
from dataclasses import dataclass, field
from datetime import datetime
from typing import Union, List

from config.utils import DS_FILE_NAME, DS_DATA_DIR, IDATA_TABLE_NAME, TIMESTAMP_FORMAT, UPDATES_DATA_TABLE


class ElementNotFoundException(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)

@dataclass
class IglooUpdatesElement:
    timestamp: Union[datetime, str]
    ins_units: int = field(default=0)
    food_note: str = field(default="")
    misc_note: str = field(default="")
    upd_rowid: int = field(default=0)

    @property
    def timestamp_str(self) -> str:
        return datetime.strftime(self.timestamp, TIMESTAMP_FORMAT)

    def __post_init__(self):
        if isinstance(self.timestamp, str):
            self.timestamp = parse_timestamp(self.timestamp)
        elif isinstance(self.timestamp, datetime):
            self.timestamp = self.timestamp.replace(second=0, microsecond=0)

    @classmethod
    def from_db_record(cls, record):
        ins_value = 0 if isinstance(record[1], str) or not record[1] else record[1]
        return cls(
            timestamp=parse_timestamp(record[0]),
            ins_units=ins_value,
            food_note=record[2] or "",
            misc_note=record[3] or "",
            upd_rowid=record[4]
        )

@dataclass
class IglooDataElement:
    timestamp: Union[datetime, str]
    reading_now: int = field(default=0)
    reading_20: int = field(default=0)
    velocity: float = field(default=0.0)

    @property
    def timestamp_str(self) -> str:
        return datetime.strftime(self.timestamp, TIMESTAMP_FORMAT)

    def __post_init__(self):
        if isinstance(self.timestamp, str):
            self.timestamp = parse_timestamp(self.timestamp)
        elif isinstance(self.timestamp, datetime):
            self.timestamp = self.timestamp.replace(second=0, microsecond=0)

    @classmethod
    def from_db_record(cls, record):
        return cls(
            timestamp=parse_timestamp(record[0]),
            reading_now=record[1],
            reading_20=record[2],
            velocity=record[3],
        )

    def __str__(self):
        return f"({self.timestamp_str}, {self.reading_now}, {self.reading_20}, {self.velocity})"

def parse_timestamp(ts_str: str) -> datetime:
    try:
        return datetime.strptime(ts_str[:16], TIMESTAMP_FORMAT)
    except ValueError:
        raise ValueError(f"Invalid timestamp format: {ts_str}. Expected format: {TIMESTAMP_FORMAT}.")

class SqliteDatabase:
    def __init__(self, data_dir=DS_DATA_DIR, db_filename=DS_FILE_NAME):
        self.db_path = os.path.join(data_dir, db_filename)

        self._set_database_good_habits()
        self.main_table = MainTable(self)
        self.updates_table = UpdatesTable(self)

    def execute_query(self, sql_query, params=()):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(sql_query, params)
        return cursor

    def _set_database_good_habits(self):
        # Enable Write-Ahead Logging for better read/write concurrency
        self.execute_query("PRAGMA journal_mode=WAL;")
        # Set a busy timeout (in milliseconds).
        # If the DB is locked, SQLite will retry for up to this many ms.
        self.execute_query("PRAGMA busy_timeout = 6000;")

class BaseTable(ABC):
    def __init__(self, db: SqliteDatabase):
        self.db = db

    @abstractmethod
    def _create(self):
        pass

    def execute(self, query, params=()):
        return self.db.execute_query(query, params)

class MainTable(BaseTable):
    def __init__(self, db: SqliteDatabase):
        super().__init__(db)
        self.tablename = IDATA_TABLE_NAME
        self._create()
        # self._col_updates()

    def _create(self):
        create_table_query = f'''
               CREATE TABLE IF NOT EXISTS {self.tablename} (
                   timestamp TEXT PRIMARY KEY,
                   reading_now INT,
                   reading_20 REAL,
                   velocity REAL
               );
               '''
        self.execute(create_table_query)

    def _col_updates(self):
        """
        Fixes existing values in the dataset, to be executed only once
        :return:
        """
        update_query = f"UPDATE {self.tablename} SET timestamp = substr(timestamp, 1, 16);"
        self.execute(update_query)

        for col_to_drop in ["notes", "food", "insulin_units"]:
            try:
                update_query = f"ALTER TABLE {self.tablename} DROP COLUMN {col_to_drop};"
                self.execute(update_query)
            except sqlite3.OperationalError:
                pass

    def insert_element(self, new_element: IglooDataElement):
        insert_element_query = f'''
            INSERT INTO {self.tablename} (
                timestamp,
                reading_now,
                reading_20,
                velocity
            ) VALUES (
                '{new_element.timestamp_str}',
                '{new_element.reading_now}', 
                '{new_element.reading_20}', 
                '{new_element.velocity}'
            );
            '''
        print(f"Trying to insert {new_element} into {self.tablename}")
        self.execute(insert_element_query)

    def update_reading_and_velocity(self, timestamp: str, reading_20: float, velocity: float):
        timestamp = datetime.strftime(timestamp, TIMESTAMP_FORMAT) if isinstance(timestamp, datetime) else timestamp
        print(f"Updating reading_20:{reading_20}, velocity:{velocity} for timestamp {timestamp}")
        update_element_query = f"""
        UPDATE {self.tablename}
           SET reading_20 = ?,
               velocity = ?
         WHERE timestamp = ?;
        """
        self.execute(update_element_query, (reading_20, velocity, timestamp))

    def update_computed_vals(self, new_element: IglooDataElement):
        print(f"Trying to update {new_element} into {self.tablename}")
        update_element_query = f'''
            UPDATE {self.tablename}
               SET reading_20 = ?,
                   velocity = ?
             WHERE timestamp = ?;
            '''
        self.execute(update_element_query, (new_element.reading_20, new_element.velocity, new_element.timestamp_str))

    def fetch_w_ts(self, timestamp: Union[str, datetime]) -> IglooDataElement:
        timestamp = datetime.strftime(timestamp, TIMESTAMP_FORMAT) if isinstance(timestamp, datetime) else timestamp
        fetch_record_query = f'''
        SELECT 
            * 
        FROM 
            {self.tablename} 
        WHERE 
            timestamp = '{timestamp}'
        ;
        '''
        cursor = self.execute(fetch_record_query)
        record = cursor.fetchone()
        if not record:
            raise ElementNotFoundException(f"{timestamp} : Not found")

        return IglooDataElement.from_db_record(record=record)

    def fetch_w_ts_range(self, ts_start: Union[str, datetime], ts_end: Union[str, datetime]) -> List[IglooDataElement]:
        ts_start = str(ts_start) if isinstance(ts_start, datetime) else ts_start
        ts_end = str(ts_end) if isinstance(ts_end, datetime) else ts_end
        # print(f"querying {self.tablename} for records between {ts_start} and {ts_end}")
        fetch_range_query = f'''
        SELECT 
            * 
        FROM 
            {self.tablename} 
        WHERE 
            timestamp BETWEEN '{ts_start}' AND '{ts_end}'
        ORDER BY
            timestamp DESC
        ;
        '''
        cursor = self.execute(fetch_range_query)
        records = cursor.fetchall()
        idel_list = [IglooDataElement.from_db_record(rec) for rec in records]
        return idel_list

class UpdatesTable(BaseTable):
    def __init__(self, db: SqliteDatabase):
        super().__init__(db)
        self.tablename = UPDATES_DATA_TABLE
        self._create()

    def _create(self):
        create_live_table_query = f'''
                CREATE TABLE IF NOT EXISTS {self.tablename} (
                    timestamp TEXT PRIMARY KEY,
                    ins_units INT DEFAULT 0,
                    food_note TEXT,
                    misc_note TEXT
                );
                '''
        self.execute(query=create_live_table_query)

    def insert(self, new_element: IglooUpdatesElement):
        try:
            insert_element_query = f'''
                        INSERT INTO {self.tablename} (
                            timestamp,
                            ins_units,
                            food_note,
                            misc_note
                        ) VALUES (
                            '{new_element.timestamp_str}',
                            '{new_element.ins_units}',
                            '{new_element.food_note}',
                            '{new_element.misc_note}' 
                        );
                        '''
            print(f"Inserting {new_element} into {self.tablename}")
            self.execute(query=insert_element_query)
        except sqlite3.IntegrityError:
            print("Received Integrity error. Passing")

    # Helper function to insert or replace the row if it doesn't exist
    def insert_or_replace_row(self, element: IglooUpdatesElement):
        try:
            sql = f'INSERT INTO {self.tablename} (timestamp) VALUES (?)'
            self.execute(query=sql, params=(element.timestamp_str,))
        except Exception as es:
            pass

    def update_(self, element: IglooUpdatesElement):
        """Update the database with the non-default values from the IglooUpdatesElement."""
        self.insert_or_replace_row(element)
        existing_row = self.fetch_w_ts(timestamp=element.timestamp)
        ex_food_note, ex_misc_note = existing_row.food_note, existing_row.misc_note
        # Build the UPDATE SQL query dynamically based on which fields are not empty
        columns_to_update = []
        values = []

        if element.ins_units != 0:
            columns_to_update.append("ins_units = ?")
            values.append(element.ins_units)

        if element.food_note != "":
            columns_to_update.append("food_note = ?")
            values.append(f"{ex_food_note},{element.food_note}".strip(","))

        if element.misc_note != "":
            columns_to_update.append("misc_note = ?")
            values.append(f"{ex_misc_note},{element.misc_note}".strip(","))

        # Only run update if there are values to update
        if columns_to_update:
            print(f"Trying to update {element} into {self.tablename}")
            sql = f"UPDATE {self.tablename} SET {', '.join(columns_to_update)} WHERE timestamp = ?"
            values.append(element.timestamp_str)
            self.execute(query=sql, params=tuple(values))
            print("update done.")

    def fetch_w_ts_range(self, ts_start: Union[str, datetime], ts_end: Union[str, datetime]) -> List[IglooUpdatesElement]:
        ts_start = str(ts_start) if isinstance(ts_start, datetime) else ts_start
        ts_end = str(ts_end) if isinstance(ts_end, datetime) else ts_end
        fetch_range_query = f'''
        SELECT 
            *,
            rowid 
        FROM 
            {self.tablename} 
        WHERE 
            timestamp BETWEEN '{ts_start}' AND '{ts_end}'
        ORDER BY
            timestamp DESC
        ;
        '''
        cursor = self.execute(fetch_range_query)
        records = cursor.fetchall()
        idul_list = [IglooUpdatesElement.from_db_record(rec) for rec in records]
        return idul_list

    def fetch_w_ts(self, timestamp: Union[str, datetime]) -> IglooUpdatesElement:
        timestamp = datetime.strftime(timestamp, TIMESTAMP_FORMAT) if isinstance(timestamp, datetime) else timestamp
        fetch_record_query = f'''
        SELECT 
            *,
            rowid 
        FROM 
            {self.tablename} 
        WHERE 
            timestamp = '{timestamp}'
        ;
        '''
        cursor = self.execute(fetch_record_query)
        record = cursor.fetchone()
        if not record:
            raise ElementNotFoundException(f"{timestamp} : Not found")

        return IglooUpdatesElement.from_db_record(record=record)

    def fetch_w_rowid(self, rowid: int) -> IglooUpdatesElement:
        fetch_record_query = f'''
        SELECT 
            *,
            rowid 
        FROM 
            {self.tablename} 
        WHERE 
            rowid = '{rowid}'
        ;
        '''
        cursor = self.execute(fetch_record_query)
        record = cursor.fetchone()
        if not record:
            raise ElementNotFoundException(f"{rowid} : Not found")

        return IglooUpdatesElement.from_db_record(record=record)


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
