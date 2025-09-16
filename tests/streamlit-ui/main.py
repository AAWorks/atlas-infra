# app.py
import streamlit as st
import json
import uuid
from datetime import datetime, date, timedelta, timezone
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field, asdict
from copy import deepcopy

st.set_page_config(page_title="Atlas Mock API", layout="wide")

# ----------------------------
# Utilities
# ----------------------------
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
# In-memory "DB"
# ----------------------------
class MemoryDB:
    def __init__(self):
        self.place: Dict[str, Place] = {}
        self.trip: Dict[str, Trip] = {}
        self.traveler: Dict[str, Traveler] = {}
        self.trip_traveler: List[Tuple[str, str, str]] = []  # (trip_id, traveler_id, role)

        self.itinerary_item: Dict[str, ItineraryItem] = {}
        self.lodging: Dict[str, Dict[str, Any]] = {}
        self.transport_rental: Dict[str, Dict[str, Any]] = {}
        self.travel_segment: Dict[str, Dict[str, Any]] = {}
        self.event_activity: Dict[str, Dict[str, Any]] = {}

        self.budget_entry: Dict[str, BudgetEntry] = {}
        self.ticket_link: Dict[str, TicketLink] = {}
        self.required_document: Dict[str, RequiredDocument] = {}
        self.attachment: Dict[str, Attachment] = {}
        self.tag: Dict[str, Dict[str, Any]] = {}
        self.item_tag: List[Tuple[str, str]] = []

    # seed with one trip
    def seed(self):
        lax = Place(id=uid(), name="Los Angeles International (LAX)", lat=33.9416, lng=-118.4085, time_zone="America/Los_Angeles")
        jfk = Place(id=uid(), name="John F. Kennedy Intl (JFK)", lat=40.6413, lng=-73.7781, time_zone="America/New_York")
        hotel = Place(id=uid(), name="Hotel Aurora", address="123 Sunset Blvd, Los Angeles, CA", time_zone="America/Los_Angeles")
        self.place[lax.id] = lax
        self.place[jfk.id] = jfk
        self.place[hotel.id] = hotel

        t = Trip(
            id=uid(),
            owner_user_id=uid(),
            title="LA Getaway",
            start_date=(date.today()+timedelta(days=45)).isoformat(),
            end_date=(date.today()+timedelta(days=50)).isoformat(),
            default_currency="USD",
            time_zone="America/Los_Angeles",
            notes="Seed trip"
        )
        self.trip[t.id] = t

        # Travel segment
        item1 = ItineraryItem(
            id=uid(), trip_id=t.id, type="travel",
            name="NYC → LAX", link="https://airline.example/ABC123",
            cost_amount=328.50, cost_currency="USD",
            start_time=f"{t.start_date}T08:30:00-04:00",
            end_time=f"{t.start_date}T11:45:00-07:00",
            status="confirmed", notes="1 checked bag"
        )
        self.itinerary_item[item1.id] = item1
        self.travel_segment[item1.id] = {
            "mode": "flight", "operator": "Delta", "number": "DL123",
            "origin_id": jfk.id, "destination_id": lax.id,
            "depart_time": item1.start_time, "arrive_time": item1.end_time,
            "seat": {"row": 12, "seat": "A"}
        }

        # Lodging
        item2 = ItineraryItem(
            id=uid(), trip_id=t.id, type="lodging",
            name="Hotel Aurora", link="https://hotel.example/booking/XYZ",
            cost_amount=612.00, cost_currency="USD",
            start_time=f"{t.start_date}T15:00:00-07:00",
            end_time=f"{(date.fromisoformat(t.start_date)+timedelta(days=4)).isoformat()}T11:00:00-07:00",
        )
        self.itinerary_item[item2.id] = item2
        self.lodging[item2.id] = {
            "place_id": hotel.id, "check_in": t.start_date,
            "check_out": (date.fromisoformat(t.start_date)+timedelta(days=4)).isoformat(),
            "provider": "Booking.com", "booking_ref": "XYZ-999",
            "room_type": "King", "guests": 2
        }

        # Budget line
        b = BudgetEntry(id=uid(), trip_id=t.id, item_id=item2.id, category="lodging", amount=612.0, currency="USD")
        self.budget_entry[b.id] = b

db = MemoryDB()
db.seed()

# ----------------------------
# Fake API that mimics endpoints
# ----------------------------
class FakeAPI:
    def __init__(self, db: MemoryDB):
        self.db = db

    # --- Trips ---
    def get_trips(self) -> List[Dict[str, Any]]:
        return [asdict(x) for x in self.db.trip.values()]

    def post_trips(self, body: Dict[str, Any]) -> Dict[str, Any]:
        t = Trip(
            id=uid(),
            owner_user_id=body.get("owner_user_id") or uid(),
            title=body["title"],
            start_date=body.get("start_date"),
            end_date=body.get("end_date"),
            default_currency=body.get("default_currency", "USD"),
            time_zone=body.get("time_zone"),
            notes=body.get("notes"),
        )
        self.db.trip[t.id] = t
        return asdict(t)

    def get_trip(self, trip_id: str) -> Dict[str, Any]:
        t = self.db.trip.get(trip_id)
        if not t: raise KeyError("Trip not found")
        return asdict(t)

    def patch_trip(self, trip_id: str, body: Dict[str, Any]) -> Dict[str, Any]:
        t = self.db.trip.get(trip_id)
        if not t: raise KeyError("Trip not found")
        for k,v in body.items():
            if hasattr(t, k) and k not in ("id","created_at"):
                setattr(t, k, v)
        t.updated_at = now()
        return asdict(t)

    # --- Itinerary ---
    def get_trip_itinerary(self, trip_id: str, from_: Optional[str]=None, to_: Optional[str]=None, bucket: str="day") -> Dict[str, Any]:
        items = [i for i in self.db.itinerary_item.values() if i.trip_id == trip_id]
        def in_window(i: ItineraryItem) -> bool:
            if not from_ and not to_: return True
            stime = i.start_time or i.end_time
            if not stime: return True
            d = stime[:10]
            if from_ and d < from_: return False
            if to_ and d > to_: return False
            return True
        items = [i for i in items if in_window(i)]
        # attach subtypes
        def with_subtype(i: ItineraryItem) -> Dict[str, Any]:
            base = asdict(i)
            if i.type == "lodging": base["lodging"] = deepcopy(self.db.lodging.get(i.id))
            elif i.type == "transport_rental": base["transport_rental"] = deepcopy(self.db.transport_rental.get(i.id))
            elif i.type == "travel": base["travel_segment"] = deepcopy(self.db.travel_segment.get(i.id))
            elif i.type == "event": base["event_activity"] = deepcopy(self.db.event_activity.get(i.id))
            base["tickets"] = [asdict(t) for t in self.db.ticket_link.values() if t.item_id == i.id]
            return base

        enriched = [with_subtype(i) for i in items]

        # bucket by date
        buckets: Dict[str, List[Dict[str, Any]]] = {}
        if bucket == "week":
            # group by ISO week
            def wk_key(dt_str: Optional[str]) -> str:
                if not dt_str: return "unknown"
                d = datetime.fromisoformat(dt_str).date()
                y, w, _ = d.isocalendar()
                return f"{y}-W{w:02d}"
            for i in enriched:
                k = wk_key(i.get("start_time") or i.get("end_time"))
                buckets.setdefault(k, []).append(i)
        else:
            def day_key(dt_str: Optional[str]) -> str:
                if not dt_str: return "unknown"
                return dt_str[:10]
            for i in enriched:
                k = day_key(i.get("start_time") or i.get("end_time"))
                buckets.setdefault(k, []).append(i)

        return {"trip_id": trip_id, "bucket": bucket, "buckets": buckets}

    def post_items(self, trip_id: str, body: Dict[str, Any]) -> Dict[str, Any]:
        itype = body["type"]
        if itype not in ITEM_TYPES: raise ValueError("invalid type")
        i = ItineraryItem(
            id=uid(), trip_id=trip_id, type=itype,
            name=body["name"], link=body.get("link"),
            cost_amount=body.get("cost_amount"), cost_currency=body.get("cost_currency"),
            start_time=body.get("start_time"), end_time=body.get("end_time"),
            all_day=body.get("all_day", False), status=body.get("status", "planned"),
            notes=body.get("notes")
        )
        self.db.itinerary_item[i.id] = i
        # subtypes
        if itype == "lodging" and "lodging" in body:
            self.db.lodging[i.id] = body["lodging"]
        if itype == "transport_rental" and "transport_rental" in body:
            self.db.transport_rental[i.id] = body["transport_rental"]
        if itype == "travel" and "travel_segment" in body:
            self.db.travel_segment[i.id] = body["travel_segment"]
        if itype == "event" and "event_activity" in body:
            self.db.event_activity[i.id] = body["event_activity"]
        return asdict(i) | {
            "lodging": self.db.lodging.get(i.id),
            "transport_rental": self.db.transport_rental.get(i.id),
            "travel_segment": self.db.travel_segment.get(i.id),
            "event_activity": self.db.event_activity.get(i.id),
        }

    def patch_item(self, item_id: str, body: Dict[str, Any]) -> Dict[str, Any]:
        i = self.db.itinerary_item.get(item_id)
        if not i: raise KeyError("Item not found")
        for k,v in body.items():
            if hasattr(i, k) and k not in ("id","trip_id","created_at"):
                setattr(i, k, v)
        i.updated_at = now()
        # subtype patches (optional)
        if i.type == "lodging" and "lodging" in body:
            self.db.lodging[i.id] = self.db.lodging.get(i.id, {}) | body["lodging"]
        if i.type == "transport_rental" and "transport_rental" in body:
            self.db.transport_rental[i.id] = self.db.transport_rental.get(i.id, {}) | body["transport_rental"]
        if i.type == "travel" and "travel_segment" in body:
            self.db.travel_segment[i.id] = self.db.travel_segment.get(i.id, {}) | body["travel_segment"]
        if i.type == "event" and "event_activity" in body:
            self.db.event_activity[i.id] = self.db.event_activity.get(i.id, {}) | body["event_activity"]
        return asdict(i)

    # --- Tickets/Attachments ---
    def post_ticket(self, item_id: str, url: str, type_: Optional[str]) -> Dict[str, Any]:
        t = TicketLink(id=uid(), item_id=item_id, url=url, type=type_)
        self.db.ticket_link[t.id] = t
        return asdict(t)

    # --- Budget ---
    def get_trip_budget(self, trip_id: str) -> Dict[str, Any]:
        lines = [asdict(b) for b in self.db.budget_entry.values() if b.trip_id == trip_id]
        # rollup (cost_amount + explicit lines)
        explicit_totals: Dict[Tuple[str], float] = {}
        for b in lines:
            k = (b["currency"],)
            explicit_totals[k] = explicit_totals.get(k, 0.0) + float(b["amount"])
        embedded_totals: Dict[Tuple[str], float] = {}
        for i in self.db.itinerary_item.values():
            if i.trip_id != trip_id: continue
            if i.cost_amount and i.cost_currency:
                k = (i.cost_currency,)
                embedded_totals[k] = embedded_totals.get(k, 0.0) + float(i.cost_amount)
        return {
            "trip_id": trip_id,
            "lines": lines,
            "embedded_totals": {k[0]: v for k,v in embedded_totals.items()},
            "explicit_totals": {k[0]: v for k,v in explicit_totals.items()},
        }

    def post_trip_budget(self, trip_id: str, body: Dict[str, Any]) -> Dict[str, Any]:
        b = BudgetEntry(
            id=uid(), trip_id=trip_id, item_id=body.get("item_id"),
            category=body.get("category"), amount=float(body["amount"]),
            currency=body["currency"]
        )
        self.db.budget_entry[b.id] = b
        return asdict(b)

    # --- Docs ---
    def post_required_doc(self, trip_id: str, body: Dict[str, Any]) -> Dict[str, Any]:
        r = RequiredDocument(
            id=uid(), trip_id=trip_id, doc_type=body["doc_type"],
            status=body.get("status","needed"), due_by=body.get("due_by"), file_id=body.get("file_id")
        )
        self.db.required_document[r.id] = r
        return asdict(r)

    # --- Export (mock) ---
    def export_trip(self, trip_id: str, format_: str) -> Dict[str, Any]:
        it = self.get_trip_itinerary(trip_id)
        t = self.get_trip(trip_id)
        budget = self.get_trip_budget(trip_id)
        if format_ not in ("md","html","pdf"):
            format_ = "md"
        content = f"# {t['title']}\n\nDates: {t.get('start_date')} → {t.get('end_date')}\n\n"
        for day, items in sorted(it["buckets"].items()):
            content += f"## {day}\n"
            for i in items:
                line = f"- **{i['type']}**: {i['name']} ({i.get('start_time','?')} → {i.get('end_time','?')})"
                if i.get("cost_amount"):
                    line += f" — {money_fmt(i['cost_amount'], i.get('cost_currency'))}"
                content += line + "\n"
            content += "\n"
        content += "## Budget\n"
        for cur, amt in budget["embedded_totals"].items():
            content += f"- Embedded: {cur} {amt:,.2f}\n"
        for cur, amt in budget["explicit_totals"].items():
            content += f"- Explicit: {cur} {amt:,.2f}\n"
        return {"format": format_, "content": content}

api = FakeAPI(db)

# ----------------------------
# Streamlit UI
# ----------------------------
st.title("Atlas Mock API (Streamlit)")

with st.expander("About this mock", expanded=False):
    st.markdown("""
This Streamlit app **mimics** the Atlas FastAPI endpoints entirely in memory.
Use the tabs to explore Trips, Itinerary, Budget, Docs, or try the **REST Console** to simulate requests.
No external services are called and nothing is persisted beyond the running session.
""")

tab_trips, tab_itin, tab_budget, tab_docs, tab_export, tab_console, tab_db = st.tabs(
    ["Trips", "Itinerary", "Budget", "Docs", "Export", "REST Console", "Raw DB"]
)

# ---- Trips ----
with tab_trips:
    st.subheader("Trips")
    trips = api.get_trips()
    trip_options = {t["title"]: t["id"] for t in trips}
    if not trips:
        st.info("No trips yet. Create one below.")
        selected_trip_id = None
    else:
        selected_trip_name = st.selectbox("Select Trip", list(trip_options.keys()))
        selected_trip_id = trip_options[selected_trip_name]
        st.json(api.get_trip(selected_trip_id))

    st.markdown("### Create Trip")
    with st.form("create_trip"):
        title = st.text_input("Title", "New Trip")
        start_date = st.date_input("Start date", value=date.today()+timedelta(days=20))
        end_date = st.date_input("End date", value=date.today()+timedelta(days=27))
        currency = st.text_input("Default currency", "USD")
        tz = st.text_input("Time zone", "UTC")
        notes = st.text_area("Notes", "")
        submitted = st.form_submit_button("Create")
        if submitted:
            new = api.post_trips({
                "title": title,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "default_currency": currency,
                "time_zone": tz,
                "notes": notes
            })
            st.success("Created trip")
            st.json(new)
            st.rerun()

# ---- Itinerary ----
with tab_itin:
    st.subheader("Itinerary")
    trips = api.get_trips()
    if not trips:
        st.info("Create a trip first.")
    else:
        trip_map = {t["title"]: t["id"] for t in trips}
        name = st.selectbox("Trip", list(trip_map.keys()), index=0)
        tid = trip_map[name]
        colA, colB, colC = st.columns(3)
        with colA:
            from_ = st.text_input("From (YYYY-MM-DD)", "")
        with colB:
            to_ = st.text_input("To (YYYY-MM-DD)", "")
        with colC:
            bucket = st.selectbox("Bucket", ["day","week"], index=0)
        res = api.get_trip_itinerary(tid, from_ or None, to_ or None, bucket)
        st.markdown("**Buckets**")
        st.json(res)

        st.markdown("### Add Item")
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
                origin_id = st.text_input("Origin place_id (UUID)", next(iter(db.place)) if db.place else "")
                destination_id = st.text_input("Destination place_id (UUID)", next(iter(db.place)) if db.place else "")
                depart_time = st.text_input("Depart time (ISO)", start_time)
                arrive_time = st.text_input("Arrive time (ISO)", end_time)
                subtype = {"travel_segment": {
                    "mode": mode, "operator": operator, "number": number,
                    "origin_id": origin_id, "destination_id": destination_id,
                    "depart_time": depart_time, "arrive_time": arrive_time
                }}
            elif itype == "lodging":
                st.caption("Lodging")
                place_id = st.text_input("place_id (UUID)", next(iter(db.place)) if db.place else "")
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
                pickup_place_id = st.text_input("Pickup place_id", next(iter(db.place)) if db.place else "")
                dropoff_place_id = st.text_input("Dropoff place_id", next(iter(db.place)) if db.place else "")
                pickup_time = st.text_input("Pickup time (ISO)", start_time)
                dropoff_time = st.text_input("Dropoff time (ISO)", end_time)
                subtype = {"transport_rental": {
                    "vehicle": vehicle, "vendor": vendor, "confirmation_code": confirmation_code,
                    "pickup_place_id": pickup_place_id, "dropoff_place_id": dropoff_place_id,
                    "pickup_time": pickup_time, "dropoff_time": dropoff_time
                }}
            elif itype == "event":
                st.caption("Event/activity")
                venue_id = st.text_input("venue_id (UUID)", next(iter(db.place)) if db.place else "")
                category = st.text_input("Category", "excursion")
                admission = st.text_area("Admission (JSON)", "{}")
                try:
                    admission_obj = json.loads(admission or "{}")
                except Exception:
                    admission_obj = {}
                subtype = {"event_activity": {"venue_id": venue_id, "category": category, "admission": admission_obj}}

            submitted = st.form_submit_button("Create item")
            if submitted:
                body = {
                    "type": itype, "name": iname, "link": link or None,
                    "cost_amount": (None if cost_amount == 0 else float(cost_amount)),
                    "cost_currency": cost_currency or None,
                    "start_time": start_time or None, "end_time": end_time or None,
                    "notes": notes or None
                } | subtype
                created = api.post_items(tid, body)
                st.success("Item created")
                st.json(created)
                st.rerun()

# ---- Budget ----
with tab_budget:
    st.subheader("Budget")
    trips = api.get_trips()
    if trips:
        trip_map = {t["title"]: t["id"] for t in trips}
        name = st.selectbox("Trip (budget)", list(trip_map.keys()), index=0)
        tid = trip_map[name]
        st.json(api.get_trip_budget(tid))

        st.markdown("### Add budget entry")
        with st.form("add_budget"):
            item_id = st.text_input("Item ID (optional)", "")
            category = st.text_input("Category", "misc")
            amount = st.number_input("Amount", min_value=0.0, value=10.0, step=1.0)
            currency = st.text_input("Currency", "USD")
            ok = st.form_submit_button("Add")
            if ok:
                body = {"item_id": item_id or None, "category": category, "amount": amount, "currency": currency}
                st.json(api.post_trip_budget(tid, body))
                st.rerun()
    else:
        st.info("Create a trip first.")

# ---- Docs ----
with tab_docs:
    st.subheader("Required documents")
    trips = api.get_trips()
    if trips:
        trip_map = {t["title"]: t["id"] for t in trips}
        name = st.selectbox("Trip (docs)", list(trip_map.keys()), index=0)
        tid = trip_map[name]
        docs = [asdict(d) for d in db.required_document.values() if d.trip_id == tid]
        st.json({"docs": docs})

        with st.form("add_doc"):
            doc_type = st.text_input("Doc type", "Passport")
            status = st.selectbox("Status", ["needed","uploaded","approved"], index=0)
            due_by = st.text_input("Due by (YYYY-MM-DD)", "")
            add = st.form_submit_button("Add document")
            if add:
                body = {"doc_type": doc_type, "status": status, "due_by": due_by or None}
                st.json(api.post_required_doc(tid, body))
                st.rerun()
    else:
        st.info("Create a trip first.")

# ---- Export ----
with tab_export:
    st.subheader("Export (mock)")
    trips = api.get_trips()
    if trips:
        trip_map = {t["title"]: t["id"] for t in trips}
        name = st.selectbox("Trip (export)", list(trip_map.keys()), index=0)
        tid = trip_map[name]
        fmt = st.selectbox("Format", ["md","html","pdf"], index=0)
        preview = api.export_trip(tid, fmt)
        st.code(preview["content"], language="markdown")
    else:
        st.info("Create a trip first.")

# ---- REST Console ----
with tab_console:
    st.subheader("REST Console (simulated)")
    st.caption("Pick an endpoint, method, and optionally provide a JSON body. We'll execute against the in-memory FakeAPI and show the response.")

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

    trips = api.get_trips()
    any_trip_id = trips[0]["id"] if trips else ""
    any_item_id = next(iter(db.itinerary_item)) if db.itinerary_item else ""

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
                resp = api.get_trips()
            elif "create_trip" in endpoints[ep_name][1]:
                resp = api.post_trips(body)
            elif "get_trip" in endpoints[ep_name][1]:
                resp = api.get_trip(trip_id_input)
            elif "patch_trip" in endpoints[ep_name][1]:
                resp = api.patch_trip(trip_id_input, body)
            elif "get_itinerary" in endpoints[ep_name][1]:
                resp = api.get_trip_itinerary(trip_id_input, qs_from or None, qs_to or None, qs_bucket or "day")
            elif "post_item" in endpoints[ep_name][1]:
                resp = api.post_items(trip_id_input, body)
            elif "patch_item" in endpoints[ep_name][1]:
                resp = api.patch_item(item_id_input, body)
            elif "post_ticket" in endpoints[ep_name][1]:
                resp = api.post_ticket(item_id_input, body.get("url",""), body.get("type"))
            elif "get_budget" in endpoints[ep_name][1]:
                resp = api.get_trip_budget(trip_id_input)
            elif "post_budget" in endpoints[ep_name][1]:
                resp = api.post_trip_budget(trip_id_input, body)
            elif "export_trip" in endpoints[ep_name][1]:
                resp = api.export_trip(trip_id_input, qs_format or "md")
            else:
                resp = {"error": "Unknown endpoint"}
            st.success("Response")
            st.code(as_json(resp), language="json")
        except Exception as e:
            st.error(f"Error: {e}")

# ---- Raw DB ----
with tab_db:
    st.subheader("Raw in-memory state (read-only)")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("**Trips**")
        st.code(as_json({k: asdict(v) for k,v in db.trip.items()}), language="json")
        st.markdown("**Places**")
        st.code(as_json({k: asdict(v) for k,v in db.place.items()}), language="json")
    with col2:
        st.markdown("**Items**")
        st.code(as_json({k: asdict(v) for k,v in db.itinerary_item.items()}), language="json")
        st.markdown("**Subtypes**")
        st.code(as_json({
            "lodging": db.lodging,
            "transport_rental": db.transport_rental,
            "travel_segment": db.travel_segment,
            "event_activity": db.event_activity
        }), language="json")
    with col3:
        st.markdown("**Budget**")
        st.code(as_json({k: asdict(v) for k,v in db.budget_entry.items()}), language="json")
        st.markdown("**Docs**")
        st.code(as_json({k: asdict(v) for k,v in db.required_document.items()}), language="json")
