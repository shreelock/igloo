import datetime

from datastore.primitives import SqliteDatabase, IglooUpdatesElement, ElementNotFoundException

MINS = 60
POLL_INTERVAL = 1 * MINS


def record_insu(event_ts, ins_val: int):
    # we update values of current insulin in the system
    sqldb = SqliteDatabase()
    for min_from_now in range(120):
        ins_added_note = f"{ins_val}u-added" if min_from_now == 0 else ""
        ts_to_process = event_ts + datetime.timedelta(minutes=min_from_now)
        try:
            curr_el = sqldb.updates_table.fetch_w_ts(ts_to_process)
            curr_ins_val = curr_el.ins_units
        except ElementNotFoundException:
            curr_ins_val = 0

        new_el = IglooUpdatesElement(
            timestamp=ts_to_process,
            ins_units=curr_ins_val + ins_val,
            misc_note=ins_added_note
        )
        push_event(updates_ele=new_el)

def record_food(event_ts, food_text: str):
    el = IglooUpdatesElement(timestamp=event_ts, food_note=food_text)
    push_event(updates_ele=el)

def record_misc(event_ts, misc_text: str):
    el = IglooUpdatesElement(timestamp=event_ts, misc_note=misc_text)
    push_event(updates_ele=el)

def push_event(updates_ele: IglooUpdatesElement):
    sqldb = SqliteDatabase()
    sqldb.updates_table.update_(updates_ele)
    print(f"--------")
