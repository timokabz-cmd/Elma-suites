# Hotel Rooms — QR-to-WhatsApp Booking

A Streamlit app for a hotel with multiple rooms:

- Guests scan one QR code and land on a page listing every room with a photo.
- Tapping a room opens a gallery of 5 photos, the price, and an availability badge.
- "Book via WhatsApp" opens a chat pre-filled with the room, dates, and total —
  you take it from there and confirm payment.
- A password-protected admin panel lets you mark rooms as Available/Booked and
  generate a printable QR code once the app is live.

## 1. Push this to GitHub

Create a new repo on GitHub, then from this folder:

```bash
git init
git add .
git commit -m "Hotel rooms booking app"
git branch -M main
git remote add origin https://github.com/<your-username>/<your-repo>.git
git push -u origin main
```

`.streamlit/secrets.toml` (your real WhatsApp number and password) is
git-ignored on purpose — see step 3.

## 2. Deploy on Streamlit Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io), sign in, "New app".
2. Pick your repo, branch `main`, main file `app.py`. Deploy.

## 3. Set your WhatsApp number and admin password

Real secrets don't get committed to GitHub — set them in Streamlit Cloud instead:

1. On your app's page, open **Settings → Secrets**.
2. Paste:
   ```toml
   whatsapp_number = "256700000000"
   admin_password = "yourpassword"
   ```
   For `whatsapp_number`: digits only, country code first, no `+` and no
   leading `0` (a Uganda number like `0700 000 000` becomes `256700000000`).
3. Save — the app restarts automatically with your real values.

(For testing on your own laptop first, copy `.streamlit/secrets.toml.example`
to `.streamlit/secrets.toml` and fill in the same two values there.)

## 4. Swap the header photo or hotel name

The banner image at the top of the rooms page lives at
`images/branding/hero.jpg` — replace that file (keep the same name, or
update `HERO_IMAGE` in `app.py`) to change it. The hotel name shown as the
page title comes from `HOTEL_NAME` near the top of `app.py`.

## 5. Replace the sample room photos and details

Everything about your rooms lives in **`data/rooms.json`** — this is the one
file you'll come back to whenever something changes:

- To update a price, description, or availability by hand, just edit the
  matching field for that room.
- To swap photos: replace the files under `images/room_1/`, `images/room_2/`,
  etc. with your real photos (keep 5 per room, any of `.jpg`/`.png`, same
  filenames or update the paths in `rooms.json` to match).
- To add a room: copy one of the blocks in `rooms.json`, give it a new `id`
  and `number`, point `photos` at a new `images/room_5/` folder with 5 photos
  in it, and commit.
- `generate_placeholders.py` only made the sample colored placeholder images —
  once you've added real photos you can delete it.

Commit and push (`git add . && git commit -m "update rooms" && git push`) —
Streamlit Cloud redeploys automatically.

## 6. Turning availability on/off day to day

You don't need to touch GitHub for this — open your live app, toggle
**"🔒 Owner admin panel"** in the sidebar, enter your admin password, and
flip each room's Available/Booked switch. It saves immediately.

**Note on this:** Streamlit Cloud's free tier keeps this file on the app's
own server while it's running, so toggles work fine for everyday use, but a
redeploy (e.g. after a `git push`) resets it back to whatever's committed in
`rooms.json`. If you want booked/available status to survive redeploys
permanently, that needs a small external store (like Google Sheets or a
proper database) — worth doing later if this takes off, not needed to launch.

## 7. Get your QR code

Once deployed, open the admin panel, paste your live app URL (something like
`https://your-app.streamlit.app`) into the QR box, and download the image to
print at reception or on a table stand.
