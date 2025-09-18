# app.py
import streamlit as st
import json
import uuid
from datetime import datetime, date, timedelta, timezone
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field, asdict
from app.services import trips as tripServices
from supabase import create_client, Client
import json
import os

from dotenv import load_dotenv

load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")  # or anon key if email/password login

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="Atlas", layout="wide")


USER_ID = "034894ce-bbf6-4d40-b7f2-3f142d71b4f2"

ATTACHMENT = "attachment"
BUDGET_ENTRY = "budget_entry"
EVENT_ACTIVITY = "event_activity"
ITEM_TAG = "item_tag"
ITINERARY_ITEM = "itinerary_item"
LODGING = "lodging"
PLACE = "place"
REQUIRED_DOCUMENT = "required_document"
TAG = "tag"
TICKET_LINK = "ticket_link"
TRANSPORT_RENTAL = "transport_rental"
TRAVEL_SEGMENT = "travel_segment"
TRAVELER = "traveler"
TRIP = "trip"
TRIP_TRAVELER = "trip_traveler"
# ----------------------------
# Utilities
# ----------------------------

import asyncio

def run_async(coro):
    try:
        return asyncio.run(coro)
    except RuntimeError as e:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(coro)


def uid() -> str:
    return str(uuid.uuid4())

def now() -> str:
    return datetime.now(timezone.utc).isoformat()

def as_json(obj) -> str:
    return json.dumps(obj, indent=2, default=str)

def parse_json(s: str) -> Any:
    return json.loads(s) if s.strip() else None

def money_fmt(amount: Optional[float], currency: Optional[str]) -> str:
    if amount is None: return "-"
    return f"{currency or ''} {amount:,.2f}".strip()

def get_table(name: str, key: str = "id") -> Dict[str, Any]:
    rows = supabase.table(name).select("*").execute().data
    return {row[key]: row for row in rows}


# ----------------------------
# Data structures (lightweight)
# ----------------------------
ITEM_TYPES = ("lodging","travel","transport_rental","event")
ITEM_STATUS = ("planned","confirmed","canceled")
TRAVEL_MODES = ("flight","train","ferry","car","bus","walk","other")
VEHICLE_TYPES = ("car","boat","bicycle","scooter","rv","other")

@dataclass
class Place:
    id: str
    name: str
    address: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    time_zone: Optional[str] = None
    external_refs: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=now)
    updated_at: str = field(default_factory=now)

@dataclass
class Trip:
    id: str
    owner_user_id: str
    title: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    default_currency: str = "USD"
    time_zone: Optional[str] = None
    notes: Optional[str] = None
    created_at: str = field(default_factory=now)
    updated_at: str = field(default_factory=now)

@dataclass
class Traveler:
    id: str
    user_id: Optional[str] = None
    display_name: str = ""
    passport: Dict[str, Any] = field(default_factory=dict)
    emergency_contacts: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=now)
    updated_at: str = field(default_factory=now)

@dataclass
class ItineraryItem:
    id: str
    trip_id: str
    type: str
    name: str
    link: Optional[str] = None
    cost_amount: Optional[float] = None
    cost_currency: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    all_day: bool = False
    status: str = "planned"
    notes: Optional[str] = None
    created_at: str = field(default_factory=now)
    updated_at: str = field(default_factory=now)

# Subtype payloads are stored on a side-table map keyed by item_id
# lodging, transport_rental, travel_segment, event_activity

@dataclass
class BudgetEntry:
    id: str
    trip_id: str
    item_id: Optional[str]
    category: Optional[str]
    amount: float
    currency: str
    created_at: str = field(default_factory=now)

@dataclass
class TicketLink:
    id: str
    item_id: str
    url: str
    type: Optional[str] = None

@dataclass
class RequiredDocument:
    id: str
    trip_id: str
    doc_type: str
    status: str = "needed"
    due_by: Optional[str] = None
    file_id: Optional[str] = None

@dataclass
class Attachment:
    id: str
    owner_user_id: str
    item_id: Optional[str]
    file_path: str
    mime: Optional[str] = None
    size: Optional[int] = None
    created_at: str = field(default_factory=now)

# ----------------------------
# Streamlit UI
# ----------------------------
st.title("Atlas Demo (Streamlit)")

tab_trips, tab_itin, tab_budget, tab_docs, tab_export, tab_console, tab_db = st.tabs(
    ["Trips", "Itinerary", "Budget", "Docs", "Export", "REST Console", "Raw DB"]
)

# ---- Trips ----
with tab_trips:
    st.subheader("Your Trips")

    trips = run_async(tripServices.get_trips(USER_ID))
    if not trips:
        st.info("No trips yet. Create one below.")
        selected_trip_id = None
    else:
        trip_titles = [t["title"] for t in trips]
        selected_trip_name = st.selectbox("Select Trip", trip_titles)
        selected_trip = next(t for t in trips if t["title"] == selected_trip_name)

        with st.expander("Trip Details", expanded=True):
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Title:** {selected_trip['title']}")
                st.write(f"**Start:** {selected_trip['start_date']}")
                st.write(f"**End:** {selected_trip['end_date']}")
                st.write(f"**Time Zone:** {selected_trip['time_zone']}")
            with col2:
                st.write(f"**Currency:** {selected_trip['home_currency']}")
                st.write(f"**Notes:** {selected_trip.get('notes', '-')}")
                st.caption(f"Created at: {selected_trip['created_at']}")
    
    st.markdown("### Create Trip")
    with st.form("create_trip"):
        title = st.text_input("Title", "New Trip")
        start_date = st.date_input("Start date", value=date.today() + timedelta(days=20))
        end_date = st.date_input("End date", value=date.today() + timedelta(days=27))
        currency = st.text_input("Default currency", "USD")
        tz = st.text_input("Time zone", "UTC")
        notes = st.text_area("Notes", "")
        submitted = st.form_submit_button("Create")
        if submitted:
            new = run_async(tripServices.create_trip(USER_ID, {
                "title": title,
                "description": "",
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "home_currency": currency,
                "time_zone": tz,
                "notes": notes
            }))
            st.success("Created trip successfully!")
            st.rerun()


# ---- Itinerary ----
with tab_itin:
    st.subheader("Itinerary")
    trips = run_async(tripServices.get_trips(USER_ID))
    
    if not trips:
        st.info("Create a trip first.")
    else:
        trip_map = {t["title"]: t["id"] for t in trips}
        selected_trip_name = st.selectbox("Trip", list(trip_map.keys()), index=0)
        tid = trip_map[selected_trip_name]
        selected_trip = next((t for t in trips if t["id"] == tid), {})
        
        st.write(f"**Currency:** {selected_trip.get('home_currency', 'N/A')}")
        st.write(f"**Dates:** {selected_trip.get('start_date', '')} → {selected_trip.get('end_date', '')}")
        
        colA, colB, colC = st.columns(3)
        with colA:
            from_ = st.text_input("From (YYYY-MM-DD)", "")
        with colB:
            to_ = st.text_input("To (YYYY-MM-DD)", "")
        with colC:
            bucket = st.selectbox("Bucket", ["day", "week"], index=0)

        # Fetch itinerary
        raw_itin = run_async(tripServices.get_itinerary(tid))
        items = raw_itin if isinstance(raw_itin, list) else raw_itin.get("items", [])

        if items:
            st.markdown("### 🗓️ Itinerary Items")
            for item in items:
                with st.expander(f"{item.get('name', 'Unnamed')} ({item.get('type', '-')})"):
                    st.write(f"**Start:** {item.get('start_time')}")
                    st.write(f"**End:** {item.get('end_time')}")
                    st.write(f"**Status:** `{item.get('status')}`")
                    st.write(f"**Cost:** {money_fmt(item.get('cost_amount'), item.get('cost_currency'))}")
                    if item.get("link"):
                        st.markdown(f"[🔗 Link]({item.get('link')})")
                    if item.get("notes"):
                        st.info(item["notes"])
        else:
            st.warning("No itinerary items found.")

        # --- Add Item Form ---
        st.markdown("### ➕ Add Item")
        with st.form("add_item"):
            itype = st.selectbox("Type", ITEM_TYPES, index=0)
            iname = st.text_input("Name", "New Item")
            link = st.text_input("Link", "")
            cost_amount = st.number_input("Cost amount", min_value=0.0, value=0.0, step=1.0)
            cost_currency = st.text_input("Cost currency", "USD")
            start_time = st.text_input("Start time (ISO)", "")
            end_time = st.text_input("End time (ISO)", "")
            notes = st.text_area("Notes", "")
            subtype = {}

            if itype == "travel":
                st.caption("Travel segment")
                mode = st.selectbox("Mode", TRAVEL_MODES, index=0)
                operator = st.text_input("Operator", "")
                number = st.text_input("Number", "")
                place_table = get_table(PLACE)
                origin_id = st.text_input("Origin place_id (UUID)", next(iter(place_table)) if place_table else "")
                destination_id = st.text_input("Destination place_id (UUID)", next(iter(place_table)) if place_table else "")
                depart_time = st.text_input("Depart time (ISO)", start_time)
                arrive_time = st.text_input("Arrive time (ISO)", end_time)
                subtype = {"travel_segment": {
                    "mode": mode, "operator": operator, "number": number,
                    "origin_id": origin_id, "destination_id": destination_id,
                    "depart_time": depart_time, "arrive_time": arrive_time
                }}
            elif itype == "lodging":
                st.caption("Lodging")
                place_table = get_table(PLACE)
                place_id = st.text_input("place_id (UUID)", next(iter(place_table)) if place_table else "")
                check_in = st.text_input("check_in (YYYY-MM-DD)", "")
                check_out = st.text_input("check_out (YYYY-MM-DD)", "")
                provider = st.text_input("Provider", "")
                booking_ref = st.text_input("Booking ref", "")
                room_type = st.text_input("Room type", "")
                guests = st.number_input("Guests", min_value=1, value=2, step=1)
                subtype = {"lodging": {
                    "place_id": place_id, "check_in": check_in, "check_out": check_out,
                    "provider": provider, "booking_ref": booking_ref,
                    "room_type": room_type, "guests": int(guests)
                }}
            elif itype == "transport_rental":
                st.caption("Transport rental")
                vehicle = st.selectbox("Vehicle", VEHICLE_TYPES, index=0)
                vendor = st.text_input("Vendor", "")
                confirmation_code = st.text_input("Confirmation", "")
                place_table = get_table(PLACE)
                pickup_place_id = st.text_input("Pickup place_id", next(iter(place_table)) if place_table else "")
                dropoff_place_id = st.text_input("Dropoff place_id", next(iter(place_table)) if place_table else "")
                pickup_time = st.text_input("Pickup time (ISO)", start_time)
                dropoff_time = st.text_input("Dropoff time (ISO)", end_time)
                subtype = {"transport_rental": {
                    "vehicle": vehicle, "vendor": vendor, "confirmation_code": confirmation_code,
                    "pickup_place_id": pickup_place_id, "dropoff_place_id": dropoff_place_id,
                    "pickup_time": pickup_time, "dropoff_time": dropoff_time
                }}
            elif itype == "event":
                st.caption("Event/activity")
                place_table = get_table(PLACE)
                venue_id = st.text_input("venue_id (UUID)", next(iter(place_table)) if place_table else "")
                category = st.text_input("Category", "excursion")
                admission = st.text_area("Admission (JSON)", "{}")
                try:
                    admission_obj = json.loads(admission or "{}")
                except Exception:
                    admission_obj = {}
                subtype = {"event_activity": {
                    "venue_id": venue_id,
                    "category": category,
                    "admission": admission_obj
                }}

            submitted = st.form_submit_button("Create item")
            if submitted:
                body = {
                    "type": itype,
                    "name": iname,
                    "link": link or None,
                    "cost_amount": (None if cost_amount == 0 else float(cost_amount)),
                    "cost_currency": cost_currency or None,
                    "start_time": start_time or None,
                    "end_time": end_time or None,
                    "notes": notes or None
                } | subtype
                created = run_async(tripServices.create_itinerary_item(tid, body))
                st.success("Item created")
                st.json(created)
                st.rerun()


# ---- Budget ----
with tab_budget:
    st.subheader("💰 Trip Budget")

    trips = run_async(tripServices.get_trips(USER_ID))

    if not trips:
        st.info("Create a trip first.")
    else:
        trip_map = {t["title"]: t["id"] for t in trips}
        selected_trip_name = st.selectbox("Trip (budget)", list(trip_map.keys()), index=0)
        tid = trip_map[selected_trip_name]
        selected_trip = next((t for t in trips if t["id"] == tid), {})

        st.markdown(f"**Currency:** `{selected_trip.get('default_currency', 'USD')}`")

        budget_data = run_async(tripServices.get_budget(tid))
        entries = budget_data if isinstance(budget_data, list) else budget_data.get("entries", [])

        if entries:
            st.markdown("### 📋 Budget Entries")

            budget_df = [
                {
                    "Category": entry.get("category", "misc"),
                    "Amount": money_fmt(entry.get("amount"), entry.get("currency")),
                    "Linked Item": entry.get("item_id", "—"),
                    "Created At": entry.get("created_at", "—"),
                }
                for entry in entries
            ]

            st.dataframe(budget_df, use_container_width=True)
        else:
            st.warning("No budget entries found.")

        st.markdown("---")
        st.markdown("### ➕ Add Budget Entry")
        with st.form("add_budget"):
            item_id = st.text_input("Item ID (optional)", "")
            category = st.text_input("Category", "misc")
            amount = st.number_input("Amount", min_value=0.0, value=10.0, step=1.0)
            currency = st.text_input("Currency", selected_trip.get("default_currency", "USD"))
            ok = st.form_submit_button("Add")

            if ok:
                body = {
                    "item_id": item_id or None,
                    "category": category,
                    "amount": amount,
                    "currency": currency
                }
                created = run_async(tripServices.create_budget_entry(tid, body))
                st.success("Budget entry added")
                st.json(created)
                st.rerun()


# ---- Docs ----
with tab_docs:
    st.subheader("📄 Required Documents")

    trips = run_async(tripServices.get_trips(USER_ID))

    if not trips:
        st.info("Create a trip first.")
    else:
        trip_map = {t["title"]: t["id"] for t in trips}
        selected_trip_name = st.selectbox("Trip (docs)", list(trip_map.keys()), index=0)
        tid = trip_map[selected_trip_name]

        docs = [
            doc for doc in get_table(REQUIRED_DOCUMENT).values()
            if doc.get("trip_id") == tid
        ]

        if docs:
            st.markdown("### 📋 Documents List")
            doc_rows = [
                {
                    "Type": doc.get("doc_type", "—"),
                    "Status": doc.get("status", "—"),
                    "Due By": doc.get("due_by", "—"),
                    "File ID": doc.get("file_id", "—"),
                }
                for doc in docs
            ]
            st.dataframe(doc_rows, use_container_width=True)
        else:
            st.warning("No documents found for this trip.")

        st.markdown("---")
        st.markdown("### ➕ Add New Document")
        with st.form("add_doc"):
            doc_type = st.text_input("Document Type", "Passport")
            status = st.selectbox("Status", ["needed", "uploaded", "approved"], index=0)
            due_by = st.text_input("Due by (YYYY-MM-DD)", "")
            add = st.form_submit_button("Add document")

            if add:
                body = {
                    "doc_type": doc_type,
                    "status": status,
                    "due_by": due_by or None
                }
                # Placeholder response until service implementation
                st.warning("Item services not available yet.")
                st.json(body)
                st.rerun()


# ---- Export ----
with tab_export:
    st.subheader("Export (mock)")
    trips = run_async(tripServices.get_trips(USER_ID))
    if trips:
        trip_map = {t["title"]: t["id"] for t in trips}
        name = st.selectbox("Trip (export)", list(trip_map.keys()), index=0)
        tid = trip_map[name]
        fmt = st.selectbox("Format", ["md","html","pdf"], index=0)
        preview = run_async(tripServices.export_trip_data(tid))#, fmt))
        #st.code(preview["content"], language="markdown")
    else:
        st.info("Create a trip first. (or mock export not implemented yet)")

# ---- REST Console ----
with tab_console:
    st.subheader("REST Console (simulated)")
    # Endpoint catalog
    endpoints = {
        "GET /trips": ("GET", "list_trips"),
        "POST /trips": ("POST", "create_trip"),
        "GET /trips/{id}": ("GET", "get_trip"),
        "PATCH /trips/{id}": ("PATCH", "patch_trip"),
        "GET /trips/{id}/itinerary": ("GET", "get_itinerary"),
        "POST /trips/{id}/items": ("POST", "post_item"),
        "PATCH /items/{item_id}": ("PATCH", "patch_item"),
        "POST /items/{item_id}/tickets": ("POST", "post_ticket"),
        "GET /trips/{id}/budget": ("GET", "get_budget"),
        "POST /trips/{id}/budget": ("POST", "post_budget"),
        "POST /trips/{id}/export?format=md|html|pdf": ("POST", "export_trip")
    }

    ep_name = st.selectbox("Endpoint", list(endpoints.keys()), index=0)
    method = endpoints[ep_name][0]
    st.write(f"**Method:** {method}")

    trips = run_async(tripServices.get_trips(USER_ID))
    any_trip_id = trips[0]["id"] if trips else ""
    any_item_id = next(iter(get_table(ITINERARY_ITEM))) if get_table(ITINERARY_ITEM) else ""

    trip_id_input = st.text_input("trip_id (if required)", any_trip_id)
    item_id_input = st.text_input("item_id (if required)", any_item_id)
    qs_format = st.text_input("export format (md|html|pdf)", "md")
    qs_from = st.text_input("query from (YYYY-MM-DD)", "")
    qs_to = st.text_input("query to (YYYY-MM-DD)", "")
    qs_bucket = st.text_input("bucket (day|week)", "day")

    body_str = st.text_area("Request body (JSON)", "", height=200)

    if st.button("Send"):
        try:
            body = parse_json(body_str) or {}
            if "list_trips" in endpoints[ep_name][1]:
                resp = run_async(tripServices.get_trips(USER_ID))
            elif "create_trip" in endpoints[ep_name][1]:
                resp = run_async(tripServices.create_trip(USER_ID, body))
            elif "get_trip" in endpoints[ep_name][1]:
                resp = run_async(tripServices.get_trip(USER_ID, trip_id_input))
            elif "patch_trip" in endpoints[ep_name][1]:
                resp = run_async(tripServices.update_trip(USER_ID ,trip_id_input, body))
            elif "get_itinerary" in endpoints[ep_name][1]:
                resp = run_async(tripServices.get_itinerary(trip_id_input))# should update service with this functionality: qs_from or None, qs_to or None, qs_bucket or "day")
            elif "post_item" in endpoints[ep_name][1]:
                resp = run_async(tripServices.create_itinerary_item(trip_id_input, body))
            #elif "patch_item" in endpoints[ep_name][1]:
            #    resp = run_async(tripServices.upda(item_id_input, body))
            #elif "post_ticket" in endpoints[ep_name][1]:
            #    resp = run_async(tripServices.post_ticket(item_id_input, body.get("url",""), body.get("type")))
            elif "get_budget" in endpoints[ep_name][1]:
                resp = run_async(tripServices.get_budget(trip_id_input))
            elif "post_budget" in endpoints[ep_name][1]:
                resp = run_async(tripServices.create_budget_entry(trip_id_input, body))
            elif "export_trip" in endpoints[ep_name][1]:
                resp = run_async(tripServices.export_trip_data(trip_id_input))# should include format aswell, qs_format or "md")
            else:
                resp = {"error": "Unknown endpoint"}
            st.success("Response")
            st.code(as_json(resp), language="json")
        except Exception as e:
            st.error(f"Error: {e}")

# ---- Raw DB ----
with tab_db:
    st.subheader("🛢️ Raw In-Memory State (Read-only)")

    col1, col2, col3 = st.columns(3)

    # --- Column 1: Trips & Places ---
    with col1:
        st.markdown("### ✈️ Trips")
        with st.expander("View Trips"):
            trips_data = get_table(TRIP)
            if trips_data:
                st.code(as_json(trips_data), language="json")
            else:
                st.info("No trips found.")

        st.markdown("### 📍 Places")
        with st.expander("View Places"):
            places_data = get_table(PLACE)
            if places_data:
                st.code(as_json(places_data), language="json")
            else:
                st.info("No places found.")

    # --- Column 2: Itinerary Items & Subtypes ---
    with col2:
        st.markdown("### 📅 Itinerary Items")
        with st.expander("View Items"):
            items_data = get_table(ITINERARY_ITEM)
            if items_data:
                st.code(as_json(items_data), language="json")
            else:
                st.info("No itinerary items found.")

        st.markdown("### 🔀 Subtypes")
        with st.expander("View Subtype Tables"):
            subtypes = {
                "lodging": get_table(LODGING),
                "transport_rental": get_table(TRANSPORT_RENTAL),
                "travel_segment": get_table(TRAVEL_SEGMENT),
                "event_activity": get_table(EVENT_ACTIVITY)
            }
            st.code(as_json(subtypes), language="json")

    # --- Column 3: Budget & Documents ---
    with col3:
        st.markdown("### 💵 Budget Entries")
        with st.expander("View Budget Entries"):
            budget_data = get_table(BUDGET_ENTRY)
            if budget_data:
                st.code(as_json(budget_data), language="json")
            else:
                st.info("No budget entries found.")

        st.markdown("### 🧾 Required Documents")
        with st.expander("View Required Docs"):
            docs_data = get_table(REQUIRED_DOCUMENT)
            if docs_data:
                st.code(as_json(docs_data), language="json")
            else:
                st.info("No required documents found.")

