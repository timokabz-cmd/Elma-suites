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

BUSINESS_NAME = "Vennie Suites"
HERO_IMAGE = "images/branding/hero.jpg"

ROOMS_FILE = "data/rooms.json"
BAR_FILE = "data/bar.json"
RESTAURANT_FILE = "data/restaurant.json"

st.set_page_config(page_title=BUSINESS_NAME, page_icon="🏨", layout="wide")

# ---------- data helpers ----------
def load_json(path):
    with open(path, "r") as f:
        return json.load(f)

def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

def get_secret(key, default):
    try:
        return st.secrets[key]
    except Exception:
        return default

def whatsapp_number():
    return get_secret("whatsapp_number", "256700000000")

def admin_password():
    return get_secret("admin_password", "changeme")

# ---------- session state ----------
defaults = {
    "section": "home",
    "view": "list",
    "selected_room": None,
    "cart": [],
    "admin_open": False,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

qp = st.query_params
if "section" in qp and st.session_state.section == "home":
    st.session_state.section = qp["section"]
if "room" in qp and st.session_state.selected_room is None:
    st.session_state.section = "rooms"
    st.session_state.view = "detail"
    st.session_state.selected_room = qp["room"]

rooms = load_json(ROOMS_FILE)
bar_items = load_json(BAR_FILE)
restaurant_items = load_json(RESTAURANT_FILE)

# ---------- cart helpers ----------
def cart_add(item, section):
    for line in st.session_state.cart:
        if line["id"] == item["id"] and line["section"] == section:
            line["qty"] += 1
            return
    st.session_state.cart.append({
        "id": item["id"],
        "section": section,
        "name": item["name"],
        "price": item["price"],
        "currency": item["currency"],
        "prep_time": item.get("prep_time_minutes", 0),
        "qty": 1,
    })

def cart_total():
    return sum(l["price"] * l["qty"] for l in st.session_state.cart)

def cart_count():
    return sum(l["qty"] for l in st.session_state.cart)

def cart_currency():
    return st.session_state.cart[0]["currency"] if st.session_state.cart else "UGX"

def build_food_whatsapp_link(service_option, location_note):
    lines = [f"Hi! I'd like to place an order at {BUSINESS_NAME}.", ""]
    for line in st.session_state.cart:
        lines.append(f"- {line['qty']}x {line['name']} ({line['currency']} {line['price']:,} each)")
    max_prep = max((l["prep_time"] for l in st.session_state.cart), default=0)
    lines += [
        "",
        f"Service: {service_option}",
    ]
    if location_note:
        lines.append(f"Details: {location_note}")
    lines += [
        f"Estimated prep time: ~{max_prep} min",
        f"Total: {cart_currency()} {cart_total():,}",
        "Please confirm and send payment details.",
    ]
    encoded = urllib.parse.quote("\n".join(lines))
    return f"https://wa.me/{whatsapp_number()}?text={encoded}"

def build_room_whatsapp_link(room, checkin, checkout, nights, total):
    message = (
        f"Hi! I'd like to book Room {room['number']} - {room['name']} at {BUSINESS_NAME}.\n"
        f"Check-in: {checkin}\n"
        f"Check-out: {checkout}\n"
        f"Nights: {nights}\n"
        f"Total: {room['currency']} {total:,}\n"
        f"Please confirm availability and send payment details."
    )
    encoded = urllib.parse.quote(message)
    return f"https://wa.me/{whatsapp_number()}?text={encoded}"

def go_home():
    st.session_state.section = "home"
    st.session_state.view = "list"
    st.session_state.selected_room = None
    st.query_params.clear()

# ---------- HOME ----------
def show_home():
    if os.path.exists(HERO_IMAGE):
        st.image(HERO_IMAGE, use_container_width=True)
    st.title(f"👋 Welcome to {BUSINESS_NAME}")
    st.caption("Choose a section to get started.")
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("🛏️ Rooms", use_container_width=True):
            st.session_state.section = "rooms"; st.session_state.view = "list"; st.rerun()
    with c2:
        if st.button("🍽️ Restaurant", use_container_width=True):
            st.session_state.section = "restaurant"; st.rerun()
    with c3:
        if st.button("🍸 Bar", use_container_width=True):
            st.session_state.section = "bar"; st.rerun()
    if cart_count() > 0:
        st.divider()
        st.info(f"🛒 {cart_count()} item(s) in your order — {cart_currency()} {cart_total():,}")
        if st.button("View cart / checkout"):
            st.session_state.section = "cart"; st.rerun()

# ---------- ROOMS ----------
def show_rooms_list():
    st.title("🛏️ Rooms")
    if st.button("← Back to menu"):
        go_home(); st.rerun()
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
                st.write(f"{badge} · {room['currency']} {room['price_per_night']:,} / night")
                if st.button("View Room", key=f"view_{room['id']}", use_container_width=True):
                    st.session_state.view = "detail"
                    st.session_state.selected_room = room["id"]
                    st.query_params["room"] = room["id"]
                    st.rerun()

def show_room_detail():
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
    st.success("🟢 Available") if room["status"] == "available" else st.error("🔴 Currently booked")
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
        st.warning("This room is currently booked. Message us on WhatsApp to be notified when it opens up.")
    c1, c2 = st.columns(2)
    with c1:
        checkin = st.date_input("Check-in", value=date.today(), min_value=date.today())
    with c2:
        checkout = st.date_input("Check-out", value=date.today() + timedelta(days=1), min_value=date.today() + timedelta(days=1))
    nights = max((checkout - checkin).days, 0)
    total = nights * room["price_per_night"]
    st.write(f"**{nights} night(s) · Estimated total: {room['currency']} {total:,}**")
    link = build_room_whatsapp_link(room, checkin, checkout, nights, total)
    st.link_button("📲 Book via WhatsApp", link, use_container_width=True,
                   disabled=(room["status"] != "available" or nights <= 0))

# ---------- BAR / RESTAURANT ----------
def show_menu_list(items, section, label, icon):
    st.title(f"{icon} {label}")
    if st.button("← Back to menu", key=f"back_{section}"):
        go_home(); st.rerun()
    categories = sorted(set(i.get("category", "Other") for i in items))
    for cat in categories:
        st.subheader(cat)
        cat_items = [i for i in items if i.get("category", "Other") == cat]
        cols = st.columns(2)
        for i, item in enumerate(cat_items):
            with cols[i % 2]:
                with st.container(border=True):
                    photo = item.get("photo")
                    if photo and os.path.exists(photo):
                        st.image(photo, use_container_width=True)
                    available = item.get("available", True)
                    badge = "🟢 Available" if available else "🔴 Sold out"
                    st.write(f"**{item['name']}**")
                    st.write(f"{badge} · {item['currency']} {item['price']:,} · ~{item.get('prep_time_minutes', 0)} min")
                    if st.button("Add to cart", key=f"add_{section}_{item['id']}",
                                 use_container_width=True, disabled=not available):
                        cart_add(item, section)
                        st.toast(f"Added {item['name']} to cart")
    if cart_count() > 0:
        st.divider()
        if st.button(f"🛒 View cart ({cart_count()}) — {cart_currency()} {cart_total():,}", use_container_width=True):
            st.session_state.section = "cart"; st.rerun()

# ---------- CART / CHECKOUT ----------
def show_cart():
    st.title("🛒 Your order")
    if st.button("← Continue browsing"):
        go_home(); st.rerun()
    if not st.session_state.cart:
        st.info("Your cart is empty.")
        return
    remove_idx = None
    for idx, line in enumerate(st.session_state.cart):
        c1, c2, c3, c4 = st.columns([3, 1, 1, 1])
        with c1:
            st.write(f"{line['name']} ({line['section']})")
        with c2:
            line["qty"] = st.number_input("Qty", min_value=1, value=line["qty"],
                                           key=f"qty_{idx}", label_visibility="collapsed")
        with c3:
            st.write(f"{line['currency']} {line['price']*line['qty']:,}")
        with c4:
            if st.button("✕", key=f"rm_{idx}"):
                remove_idx = idx
    if remove_idx is not None:
        st.session_state.cart.pop(remove_idx)
        st.rerun()
    st.divider()
    st.write(f"**Total: {cart_currency()} {cart_total():,}**")
    st.subheader("How would you like this served?")
    service_option = st.radio("Service option", ["Room delivery", "Dine-in", "Pickup"], label_visibility="collapsed")
    location_note = ""
    if service_option == "Room delivery":
        location_note = st.text_input("Room number")
    elif service_option == "Dine-in":
        location_note = st.text_input("Table number (if known)")
    link = build_food_whatsapp_link(service_option, location_note)
    st.link_button("📲 Send order via WhatsApp", link, use_container_width=True,
                   disabled=(service_option == "Room delivery" and not location_note))
    if st.button("Clear cart"):
        st.session_state.cart = []
        st.rerun()

# ---------- ADMIN ----------
def show_admin():
    st.title("🔒 Admin panel")
    pw = st.text_input("Admin password", type="password")
    if pw != admin_password():
        if pw:
            st.error("Incorrect password.")
        return
    st.success("Logged in.")
    tab_rooms, tab_bar, tab_restaurant, tab_qr = st.tabs(["Rooms", "Bar", "Restaurant", "QR code"])

    with tab_rooms:
        changed = False
        for room in rooms:
            c1, c2 = st.columns([3, 1])
            with c1:
                st.write(f"Room {room['number']} — {room['name']}")
            with c2:
                is_available = st.toggle("Available", value=(room["status"] == "available"), key=f"room_toggle_{room['id']}")
            new_status = "available" if is_available else "booked"
            if new_status != room["status"]:
                room["status"] = new_status
                changed = True
        if changed:
            save_json(ROOMS_FILE, rooms)
            st.success("Room availability updated.")
            st.rerun()

    def item_admin(items, path, key_prefix):
        changed = False
        for item in items:
            c1, c2 = st.columns([3, 1])
            with c1:
                st.write(f"{item['name']} — {item['currency']} {item['price']:,}")
            with c2:
                is_available = st.toggle("Available", value=item.get("available", True), key=f"{key_prefix}_{item['id']}")
            if is_available != item.get("available", True):
                item["available"] = is_available
                changed = True
        if changed:
            save_json(path, items)
            st.success("Menu availability updated.")
            st.rerun()

    with tab_bar:
        item_admin(bar_items, BAR_FILE, "bar_toggle")
    with tab_restaurant:
        item_admin(restaurant_items, RESTAURANT_FILE, "rest_toggle")

    with tab_qr:
        st.caption("One QR code opens the whole app — guests pick a section from there.")
        app_url = st.text_input("Paste your deployed Streamlit app URL", placeholder="https://your-app.streamlit.app")
        if app_url and qrcode:
            img = qrcode.make(app_url)
            buf = BytesIO()
            img.save(buf, format="PNG")
            st.image(buf.getvalue(), caption="Scan to open", width=250)
            st.download_button("Download QR code", buf.getvalue(), file_name="vennie_qr.png", mime="image/png")
        elif app_url and not qrcode:
            st.warning("The `qrcode` package isn't installed — check requirements.txt.")

# ---------- sidebar ----------
with st.sidebar:
    st.header(BUSINESS_NAME)
    if st.button("🏠 Home", use_container_width=True):
        go_home(); st.rerun()
    if cart_count() > 0:
        if st.button(f"🛒 Cart ({cart_count()})", use_container_width=True):
            st.session_state.section = "cart"; st.rerun()
    st.session_state.admin_open = st.toggle("🔒 Owner admin panel", value=st.session_state.admin_open)

# ---------- router ----------
if st.session_state.admin_open:
    show_admin()
elif st.session_state.section == "rooms":
    show_room_detail() if st.session_state.view == "detail" else show_rooms_list()
elif st.session_state.section == "bar":
    show_menu_list(bar_items, "bar", "Bar", "🍸")
elif st.session_state.section == "restaurant":
    show_menu_list(restaurant_items, "restaurant", "Restaurant", "🍽️")
elif st.session_state.section == "cart":
    show_cart()
else:
    show_home()
