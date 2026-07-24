import json
import os
import urllib.parse
from datetime import date, timedelta
from io import BytesIO

import streamlit as st

try:
    import qrcode
except ImportError:
    qrcode = None

DATA_FILE = "data/rooms.json"
HOTEL_NAME = "ELMA Suites & Lounge"
HERO_IMAGE = "images/branding/hero.jpg"

st.set_page_config(page_title=HOTEL_NAME, page_icon="🏨", layout="wide")


# ---------- data helpers ----------

def load_rooms():
    with open(DATA_FILE, "r") as f:
        return json.load(f)


def save_rooms(rooms):
    with open(DATA_FILE, "w") as f:
        json.dump(rooms, f, indent=2)


def get_secret(key, default):
    try:
        return st.secrets[key]
    except Exception:
        return default


def whatsapp_number():
    # Digits only, country code first, no + and no leading zero.
    # e.g. Uganda number 0700 000 000 -> "256700000000"
    return get_secret("whatsapp_number", "256700000000")


def admin_password():
    return get_secret("admin_password", "changeme")


def build_whatsapp_link(room, checkin, checkout, nights, total):
    message = (
        f"Hi! I'd like to book Room {room['number']} - {room['name']}.\n"
        f"Check-in: {checkin}\n"
        f"Check-out: {checkout}\n"
        f"Nights: {nights}\n"
        f"Total: {room['currency']} {total:,}\n"
        f"Please confirm availability and send payment details."
    )
    encoded = urllib.parse.quote(message)
    return f"https://wa.me/{whatsapp_number()}?text={encoded}"


# ---------- session state ----------

if "view" not in st.session_state:
    st.session_state.view = "list"
if "selected_room" not in st.session_state:
    st.session_state.selected_room = None
if "admin_open" not in st.session_state:
    st.session_state.admin_open = False

# Deep link support: a QR code can point straight at ?room=<id>
qp = st.query_params
if "room" in qp and st.session_state.selected_room is None:
    st.session_state.view = "detail"
    st.session_state.selected_room = qp["room"]

rooms = load_rooms()


# ---------- views ----------

def show_list():
    if os.path.exists(HERO_IMAGE):
        st.image(HERO_IMAGE, use_container_width=True)

    st.title(f"🏨 {HOTEL_NAME}")
    st.caption("Tap a room to see photos, check availability, and book on WhatsApp.")

    cols = st.columns(2)
    for i, room in enumerate(rooms):
        with cols[i % 2]:
            with st.container(border=True):
                cover = room["photos"][0] if room["photos"] else None
                if cover and os.path.exists(cover):
                    st.image(cover, use_container_width=True)

                available = room["status"] == "available"
                badge = "🟢 Available" if available else "🔴 Booked"
                st.subheader(f"Room {room['number']} — {room['name']}")
                st.write(f"{badge}  ·  {room['currency']} {room['price_per_night']:,} / night")

                if st.button("View Room", key=f"view_{room['id']}", use_container_width=True):
                    st.session_state.view = "detail"
                    st.session_state.selected_room = room["id"]
                    st.query_params["room"] = room["id"]
                    st.rerun()


def show_detail():
    room = next((r for r in rooms if str(r["id"]) == str(st.session_state.selected_room)), None)

    if st.button("← Back to all rooms"):
        st.session_state.view = "list"
        st.session_state.selected_room = None
        st.query_params.clear()
        st.rerun()

    if not room:
        st.error("Room not found.")
        return

    st.title(f"Room {room['number']} — {room['name']}")

    if room["status"] == "available":
        st.success("🟢 Available")
    else:
        st.error("🔴 Currently booked")

    photos = [p for p in room["photos"] if os.path.exists(p)]
    if photos:
        n = min(len(photos), 5)
        photo_cols = st.columns(n)
        for idx, p in enumerate(photos):
            with photo_cols[idx % n]:
                st.image(p, use_container_width=True)

    st.write(room.get("description", ""))
    st.write(f"**Price:** {room['currency']} {room['price_per_night']:,} / night")
    st.write(f"**Max guests:** {room.get('max_guests', '—')}")

    st.divider()
    st.subheader("Book this room")

    if room["status"] != "available":
        st.warning("This room is currently booked. Message us on WhatsApp if you'd like to be notified when it opens up.")

    c1, c2 = st.columns(2)
    with c1:
        checkin = st.date_input("Check-in", value=date.today(), min_value=date.today())
    with c2:
        checkout = st.date_input(
            "Check-out", value=date.today() + timedelta(days=1), min_value=date.today() + timedelta(days=1)
        )

    nights = max((checkout - checkin).days, 0)
    total = nights * room["price_per_night"]
    st.write(f"**{nights} night(s) · Estimated total: {room['currency']} {total:,}**")

    link = build_whatsapp_link(room, checkin, checkout, nights, total)
    disabled = room["status"] != "available" or nights <= 0
    st.link_button("📲 Book via WhatsApp", link, use_container_width=True, disabled=disabled)


def show_admin():
    st.title("🔒 Room Management")
    pw = st.text_input("Admin password", type="password")
    if pw != admin_password():
        if pw:
            st.error("Incorrect password.")
        return

    st.success("Logged in.")
    changed = False
    for room in rooms:
        c1, c2 = st.columns([3, 1])
        with c1:
            st.write(f"Room {room['number']} — {room['name']}")
        with c2:
            is_available = st.toggle(
                "Available", value=(room["status"] == "available"), key=f"toggle_{room['id']}"
            )
            new_status = "available" if is_available else "booked"
            if new_status != room["status"]:
                room["status"] = new_status
                changed = True

    if changed:
        save_rooms(rooms)
        st.success("Availability updated.")
        st.rerun()

    st.divider()
    st.subheader("QR code for your rooms page")
    st.caption("Print this and stick it at reception, on room doors, or in a welcome pack.")
    app_url = st.text_input("Paste your deployed Streamlit app URL", placeholder="https://your-app.streamlit.app")
    if app_url and qrcode:
        img = qrcode.make(app_url)
        buf = BytesIO()
        img.save(buf, format="PNG")
        st.image(buf.getvalue(), caption="Scan to open your rooms page", width=250)
        st.download_button("Download QR code", buf.getvalue(), file_name="rooms_qr.png", mime="image/png")
    elif app_url and not qrcode:
        st.warning("The `qrcode` package isn't installed — check requirements.txt.")


# ---------- sidebar navigation ----------

with st.sidebar:
    st.header("Menu")
    if st.button("🏨 View rooms", use_container_width=True):
        st.session_state.view = "list"
        st.session_state.selected_room = None
        st.session_state.admin_open = False
        st.query_params.clear()
        st.rerun()
    st.session_state.admin_open = st.toggle("🔒 Owner admin panel", value=st.session_state.admin_open)

if st.session_state.admin_open:
    show_admin()
elif st.session_state.view == "detail":
    show_detail()
else:
    show_list()
