"""SQLite database repository for FestiWise AI.

Handles relational persistence for events, allocations, expenses, tasks,
day schedules, vendors, guidance, and guest lists using safe parameterized queries.
"""

import sqlite3
import json
import uuid
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime

from config import DATABASE_PATH
from models.schemas import (
    FullEventPlan,
    EventInput,
    BudgetAllocation,
    ExpenseItem,
    TaskItem,
    EventScheduleItem,
    VendorItem,
    VendorCategoryGuidance,
    GuestItem,
    CreativeConcepts,
)


def get_connection(db_path: Optional[str] = None) -> sqlite3.Connection:
    """Create and return a database connection with foreign keys enabled."""
    path = db_path or DATABASE_PATH
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db(db_path: Optional[str] = None) -> None:
    """Initialize database tables with indexes."""
    conn = get_connection(db_path)
    try:
        with conn:
            conn.executescript("""
            CREATE TABLE IF NOT EXISTS events (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                event_date TEXT NOT NULL,
                city TEXT NOT NULL,
                venue_type TEXT NOT NULL,
                guest_count INTEGER NOT NULL,
                total_budget REAL NOT NULL,
                currency TEXT NOT NULL DEFAULT 'INR',
                preferred_theme TEXT,
                food_preference TEXT,
                special_requirements TEXT,
                additional_notes TEXT,
                overview TEXT,
                creative_json TEXT,
                risks_json TEXT,
                assumptions_json TEXT,
                rescue_history_json TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS budget_allocations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id TEXT NOT NULL,
                category TEXT NOT NULL,
                planned_amount REAL NOT NULL,
                percentage REAL NOT NULL,
                notes TEXT,
                is_flexible INTEGER NOT NULL DEFAULT 1,
                FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS expenses (
                id TEXT PRIMARY KEY,
                event_id TEXT NOT NULL,
                category TEXT NOT NULL,
                item_name TEXT NOT NULL,
                estimated_cost REAL NOT NULL DEFAULT 0.0,
                actual_cost REAL,
                vendor_name TEXT,
                payment_status TEXT NOT NULL DEFAULT 'Pending',
                is_verified INTEGER NOT NULL DEFAULT 0,
                notes TEXT,
                FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                event_id TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                suggested_deadline TEXT NOT NULL,
                days_before_event INTEGER,
                priority TEXT NOT NULL DEFAULT 'Medium',
                status TEXT NOT NULL DEFAULT 'Not Started',
                responsible_person TEXT,
                category TEXT NOT NULL DEFAULT 'General',
                FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS day_schedule (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id TEXT NOT NULL,
                start_time TEXT NOT NULL,
                activity_name TEXT NOT NULL,
                duration_minutes INTEGER NOT NULL,
                notes TEXT,
                FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS vendors (
                id TEXT PRIMARY KEY,
                event_id TEXT NOT NULL,
                category TEXT NOT NULL,
                name TEXT NOT NULL,
                contact_info TEXT,
                quoted_price REAL NOT NULL DEFAULT 0.0,
                booking_status TEXT NOT NULL DEFAULT 'Researching',
                follow_up_date TEXT,
                notes TEXT,
                FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS vendor_guidance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id TEXT NOT NULL,
                category TEXT NOT NULL,
                guidance_json TEXT NOT NULL,
                FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS guests (
                id TEXT PRIMARY KEY,
                event_id TEXT NOT NULL,
                name TEXT NOT NULL,
                contact TEXT,
                rsvp_status TEXT NOT NULL DEFAULT 'Pending',
                plus_ones INTEGER NOT NULL DEFAULT 0,
                dietary_notes TEXT,
                table_group TEXT,
                FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_allocations_event ON budget_allocations(event_id);
            CREATE INDEX IF NOT EXISTS idx_expenses_event ON expenses(event_id);
            CREATE INDEX IF NOT EXISTS idx_tasks_event ON tasks(event_id);
            CREATE INDEX IF NOT EXISTS idx_schedule_event ON day_schedule(event_id);
            CREATE INDEX IF NOT EXISTS idx_vendors_event ON vendors(event_id);
            CREATE INDEX IF NOT EXISTS idx_guests_event ON guests(event_id);
            """)
    finally:
        conn.close()


def save_full_event(event: FullEventPlan, db_path: Optional[str] = None) -> None:
    """Save or replace a full event plan including all relational child records."""
    init_db(db_path)
    conn = get_connection(db_path)
    now = datetime.now().isoformat()
    try:
        with conn:
            # 1. Upsert event record
            conn.execute("""
            INSERT INTO events (
                id, name, category, event_date, city, venue_type, guest_count,
                total_budget, currency, preferred_theme, food_preference,
                special_requirements, additional_notes, overview, creative_json,
                risks_json, assumptions_json, rescue_history_json, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                name=excluded.name,
                category=excluded.category,
                event_date=excluded.event_date,
                city=excluded.city,
                venue_type=excluded.venue_type,
                guest_count=excluded.guest_count,
                total_budget=excluded.total_budget,
                currency=excluded.currency,
                preferred_theme=excluded.preferred_theme,
                food_preference=excluded.food_preference,
                special_requirements=excluded.special_requirements,
                additional_notes=excluded.additional_notes,
                overview=excluded.overview,
                creative_json=excluded.creative_json,
                risks_json=excluded.risks_json,
                assumptions_json=excluded.assumptions_json,
                rescue_history_json=excluded.rescue_history_json,
                updated_at=excluded.updated_at;
            """, (
                event.id,
                event.input_details.event_name,
                event.input_details.event_category,
                event.input_details.event_date,
                event.input_details.city_location,
                event.input_details.venue_type,
                event.input_details.guest_count,
                event.input_details.total_budget,
                event.input_details.currency,
                event.input_details.preferred_theme,
                event.input_details.food_preference,
                event.input_details.special_requirements,
                event.input_details.additional_notes,
                event.overview,
                json.dumps(event.creative.model_dump()),
                json.dumps(event.risks_and_contingencies),
                json.dumps(event.assumptions),
                json.dumps(event.rescue_history),
                event.created_at or now,
                now
            ))

            # 2. Refresh budget allocations
            conn.execute("DELETE FROM budget_allocations WHERE event_id = ?", (event.id,))
            for alloc in event.budget_allocations:
                conn.execute("""
                INSERT INTO budget_allocations (event_id, category, planned_amount, percentage, notes, is_flexible)
                VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    event.id,
                    alloc.category,
                    alloc.planned_amount,
                    alloc.percentage,
                    alloc.notes or "",
                    1 if alloc.is_flexible else 0
                ))

            # 3. Refresh day schedule
            conn.execute("DELETE FROM day_schedule WHERE event_id = ?", (event.id,))
            for s in event.day_schedule:
                conn.execute("""
                INSERT INTO day_schedule (event_id, start_time, activity_name, duration_minutes, notes)
                VALUES (?, ?, ?, ?, ?)
                """, (
                    event.id,
                    s.start_time,
                    s.activity_name,
                    s.duration_minutes,
                    s.notes or ""
                ))

            # 4. Refresh vendor guidance
            conn.execute("DELETE FROM vendor_guidance WHERE event_id = ?", (event.id,))
            for vg in event.vendor_guidance:
                conn.execute("""
                INSERT INTO vendor_guidance (event_id, category, guidance_json)
                VALUES (?, ?, ?)
                """, (
                    event.id,
                    vg.category,
                    json.dumps(vg.model_dump())
                ))

            # 5. Upsert tasks (preserve existing task IDs if already present)
            existing_task_ids = {r[0] for r in conn.execute("SELECT id FROM tasks WHERE event_id = ?", (event.id,)).fetchall()}
            for t in event.tasks:
                if t.id in existing_task_ids:
                    conn.execute("""
                    UPDATE tasks SET
                        title = ?, description = ?, suggested_deadline = ?,
                        days_before_event = ?, priority = ?, status = ?,
                        responsible_person = ?, category = ?
                    WHERE id = ? AND event_id = ?
                    """, (
                        t.title, t.description or "", t.suggested_deadline,
                        t.days_before_event, t.priority, t.status,
                        t.responsible_person or "", t.category or "General",
                        t.id, event.id
                    ))
                else:
                    conn.execute("""
                    INSERT INTO tasks (id, event_id, title, description, suggested_deadline, days_before_event, priority, status, responsible_person, category)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        t.id or str(uuid.uuid4()), event.id, t.title, t.description or "",
                        t.suggested_deadline, t.days_before_event, t.priority, t.status,
                        t.responsible_person or "", t.category or "General"
                    ))

            # 6. Expenses upsert
            existing_exp_ids = {r[0] for r in conn.execute("SELECT id FROM expenses WHERE event_id = ?", (event.id,)).fetchall()}
            for exp in event.expenses:
                if exp.id in existing_exp_ids:
                    conn.execute("""
                    UPDATE expenses SET
                        category = ?, item_name = ?, estimated_cost = ?,
                        actual_cost = ?, vendor_name = ?, payment_status = ?,
                        is_verified = ?, notes = ?
                    WHERE id = ? AND event_id = ?
                    """, (
                        exp.category, exp.item_name, exp.estimated_cost,
                        exp.actual_cost, exp.vendor_name or "", exp.payment_status,
                        1 if exp.is_verified else 0, exp.notes or "",
                        exp.id, event.id
                    ))
                else:
                    conn.execute("""
                    INSERT INTO expenses (id, event_id, category, item_name, estimated_cost, actual_cost, vendor_name, payment_status, is_verified, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        exp.id or str(uuid.uuid4()), event.id, exp.category, exp.item_name,
                        exp.estimated_cost, exp.actual_cost, exp.vendor_name or "",
                        exp.payment_status, 1 if exp.is_verified else 0, exp.notes or ""
                    ))

            # 7. Vendors upsert
            existing_ven_ids = {r[0] for r in conn.execute("SELECT id FROM vendors WHERE event_id = ?", (event.id,)).fetchall()}
            for v in event.vendors:
                if v.id in existing_ven_ids:
                    conn.execute("""
                    UPDATE vendors SET
                        category = ?, name = ?, contact_info = ?,
                        quoted_price = ?, booking_status = ?, follow_up_date = ?, notes = ?
                    WHERE id = ? AND event_id = ?
                    """, (
                        v.category, v.name, v.contact_info or "",
                        v.quoted_price, v.booking_status, v.follow_up_date or "", v.notes or "",
                        v.id, event.id
                    ))
                else:
                    conn.execute("""
                    INSERT INTO vendors (id, event_id, category, name, contact_info, quoted_price, booking_status, follow_up_date, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        v.id or str(uuid.uuid4()), event.id, v.category, v.name,
                        v.contact_info or "", v.quoted_price, v.booking_status,
                        v.follow_up_date or "", v.notes or ""
                    ))

            # 8. Guests upsert
            existing_gst_ids = {r[0] for r in conn.execute("SELECT id FROM guests WHERE event_id = ?", (event.id,)).fetchall()}
            for g in event.guests:
                if g.id in existing_gst_ids:
                    conn.execute("""
                    UPDATE guests SET
                        name = ?, contact = ?, rsvp_status = ?,
                        plus_ones = ?, dietary_notes = ?, table_group = ?
                    WHERE id = ? AND event_id = ?
                    """, (
                        g.name, g.contact or "", g.rsvp_status,
                        g.plus_ones, g.dietary_notes or "", g.table_group or "",
                        g.id, event.id
                    ))
                else:
                    conn.execute("""
                    INSERT INTO guests (id, event_id, name, contact, rsvp_status, plus_ones, dietary_notes, table_group)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        g.id or str(uuid.uuid4()), event.id, g.name,
                        g.contact or "", g.rsvp_status, g.plus_ones,
                        g.dietary_notes or "", g.table_group or ""
                    ))
    finally:
        conn.close()


def get_full_event(event_id: str, db_path: Optional[str] = None) -> Optional[FullEventPlan]:
    """Retrieve complete event plan by ID."""
    init_db(db_path)
    conn = get_connection(db_path)
    try:
        row = conn.execute("SELECT * FROM events WHERE id = ?", (event_id,)).fetchone()
        if not row:
            return None

        # Reconstruct EventInput
        input_details = EventInput(
            event_name=row["name"],
            event_category=row["category"],
            event_date=row["event_date"],
            city_location=row["city"],
            venue_type=row["venue_type"],
            guest_count=row["guest_count"],
            total_budget=row["total_budget"],
            currency=row["currency"],
            preferred_theme=row["preferred_theme"] or "",
            food_preference=row["food_preference"] or "",
            special_requirements=row["special_requirements"] or "",
            additional_notes=row["additional_notes"] or ""
        )

        # Creative
        creative_dict = json.loads(row["creative_json"]) if row["creative_json"] else {}
        creative = CreativeConcepts(**creative_dict) if creative_dict else CreativeConcepts(
            recommended_theme="Celebration Classic",
            theme_rationale="Tailored for guest experience",
            color_palette=[],
            decor_concepts=[]
        )

        # Allocations
        alloc_rows = conn.execute("SELECT * FROM budget_allocations WHERE event_id = ? ORDER BY id", (event_id,)).fetchall()
        allocations = [
            BudgetAllocation(
                category=r["category"],
                planned_amount=r["planned_amount"],
                percentage=r["percentage"],
                notes=r["notes"] or "",
                is_flexible=bool(r["is_flexible"])
            ) for r in alloc_rows
        ]

        # Expenses
        exp_rows = conn.execute("SELECT * FROM expenses WHERE event_id = ? ORDER BY category, item_name", (event_id,)).fetchall()
        expenses = [
            ExpenseItem(
                id=r["id"],
                category=r["category"],
                item_name=r["item_name"],
                estimated_cost=r["estimated_cost"],
                actual_cost=r["actual_cost"],
                vendor_name=r["vendor_name"] or "",
                payment_status=r["payment_status"],
                is_verified=bool(r["is_verified"]),
                notes=r["notes"] or ""
            ) for r in exp_rows
        ]

        # Tasks
        task_rows = conn.execute("SELECT * FROM tasks WHERE event_id = ? ORDER BY suggested_deadline ASC", (event_id,)).fetchall()
        tasks = [
            TaskItem(
                id=r["id"],
                title=r["title"],
                description=r["description"] or "",
                suggested_deadline=r["suggested_deadline"],
                days_before_event=r["days_before_event"],
                priority=r["priority"],
                status=r["status"],
                responsible_person=r["responsible_person"] or "",
                category=r["category"] or "General"
            ) for r in task_rows
        ]

        # Day Schedule
        sch_rows = conn.execute("SELECT * FROM day_schedule WHERE event_id = ? ORDER BY id ASC", (event_id,)).fetchall()
        day_schedule = [
            EventScheduleItem(
                start_time=r["start_time"],
                activity_name=r["activity_name"],
                duration_minutes=r["duration_minutes"],
                notes=r["notes"] or ""
            ) for r in sch_rows
        ]

        # Vendor Guidance
        guidance_rows = conn.execute("SELECT * FROM vendor_guidance WHERE event_id = ?", (event_id,)).fetchall()
        vendor_guidance = [
            VendorCategoryGuidance(**json.loads(r["guidance_json"]))
            for r in guidance_rows
        ]

        # Vendors
        ven_rows = conn.execute("SELECT * FROM vendors WHERE event_id = ?", (event_id,)).fetchall()
        vendors = [
            VendorItem(
                id=r["id"],
                category=r["category"],
                name=r["name"],
                contact_info=r["contact_info"] or "",
                quoted_price=r["quoted_price"],
                booking_status=r["booking_status"],
                follow_up_date=r["follow_up_date"] or "",
                notes=r["notes"] or ""
            ) for r in ven_rows
        ]

        # Guests
        guest_rows = conn.execute("SELECT * FROM guests WHERE event_id = ?", (event_id,)).fetchall()
        guests = [
            GuestItem(
                id=r["id"],
                name=r["name"],
                contact=r["contact"] or "",
                rsvp_status=r["rsvp_status"],
                plus_ones=r["plus_ones"],
                dietary_notes=r["dietary_notes"] or "",
                table_group=r["table_group"] or ""
            ) for r in guest_rows
        ]

        risks = json.loads(row["risks_json"]) if row["risks_json"] else []
        assumptions = json.loads(row["assumptions_json"]) if row["assumptions_json"] else []
        rescue_history = json.loads(row["rescue_history_json"]) if row["rescue_history_json"] else []

        return FullEventPlan(
            id=row["id"],
            input_details=input_details,
            overview=row["overview"] or "",
            creative=creative,
            budget_allocations=allocations,
            expenses=expenses,
            tasks=tasks,
            day_schedule=day_schedule,
            vendor_guidance=vendor_guidance,
            vendors=vendors,
            guests=guests,
            risks_and_contingencies=risks,
            assumptions=assumptions,
            rescue_history=rescue_history,
            created_at=row["created_at"],
            updated_at=row["updated_at"]
        )
    finally:
        conn.close()


def list_events(db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """Return concise list of all saved events for cards and dropdown selector."""
    init_db(db_path)
    conn = get_connection(db_path)
    try:
        rows = conn.execute("""
        SELECT id, name, category, event_date, city, guest_count, total_budget, currency, updated_at
        FROM events
        ORDER BY updated_at DESC
        """).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def delete_event(event_id: str, db_path: Optional[str] = None) -> bool:
    """Delete an event and all associated records."""
    init_db(db_path)
    conn = get_connection(db_path)
    try:
        with conn:
            # Foreign key cascade ensures child records are removed
            cursor = conn.execute("DELETE FROM events WHERE id = ?", (event_id,))
            return cursor.rowcount > 0
    finally:
        conn.close()


def update_task_status(task_id: str, new_status: str, db_path: Optional[str] = None) -> bool:
    """Quick update of task status (e.g. checkbox completion)."""
    init_db(db_path)
    conn = get_connection(db_path)
    try:
        with conn:
            cursor = conn.execute("UPDATE tasks SET status = ? WHERE id = ?", (new_status, task_id))
            return cursor.rowcount > 0
    finally:
        conn.close()


def add_or_update_expense(event_id: str, expense: ExpenseItem, db_path: Optional[str] = None) -> None:
    """Add or update an individual expense record."""
    init_db(db_path)
    conn = get_connection(db_path)
    try:
        with conn:
            conn.execute("""
            INSERT INTO expenses (id, event_id, category, item_name, estimated_cost, actual_cost, vendor_name, payment_status, is_verified, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                category = excluded.category,
                item_name = excluded.item_name,
                estimated_cost = excluded.estimated_cost,
                actual_cost = excluded.actual_cost,
                vendor_name = excluded.vendor_name,
                payment_status = excluded.payment_status,
                is_verified = excluded.is_verified,
                notes = excluded.notes;
            """, (
                expense.id, event_id, expense.category, expense.item_name,
                expense.estimated_cost, expense.actual_cost, expense.vendor_name or "",
                expense.payment_status, 1 if expense.is_verified else 0, expense.notes or ""
            ))
    finally:
        conn.close()


def delete_expense(expense_id: str, db_path: Optional[str] = None) -> bool:
    """Delete a specific expense item."""
    init_db(db_path)
    conn = get_connection(db_path)
    try:
        with conn:
            cursor = conn.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
            return cursor.rowcount > 0
    finally:
        conn.close()
