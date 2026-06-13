"""
Daily Spotify artist/track popularity tracker.

Pulls current popularity score + follower count for chosen artists,
and popularity score for chosen tracks, then appends a timestamped
row to a CSV. Intended to be run once per day (e.g. via GitHub Actions cron).

Setup:
  1. Set environment variables SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET
     (get these from developer.spotify.com/dashboard -> your app).
  2. Edit ARTISTS and TRACKS below with the Spotify IDs you want to track.
  3. Run: python track_artists.py
     This appends to artist_history.csv and track_history.csv in the same folder.
"""

import os
import csv
import base64
import datetime
import requests

# ---- CONFIG: fill these in ----
# Spotify Artist IDs (find in the artist's open.spotify.com URL)
ARTISTS = {
    "Taylor Swift": "06HL4z0CvFAxyc27GXpf02",
    "The Weeknd": "1Xyo4u8uXC1ZmMpatF05PJ",
    "Bad Bunny": "4q3ewBCX7sLwd24euuV69X",
}

# Spotify Track IDs (find in the track's open.spotify.com URL)
TRACKS = {
    "Cruel Summer": "1BxfuPKGuaTgP7aM0Bbdwr",
    "Blinding Lights": "0VjIjW4GlUZAMYd2vXMi3b",
}

ARTIST_CSV = os.path.join(os.path.dirname(__file__), "artist_history.csv")
TRACK_CSV = os.path.join(os.path.dirname(__file__), "track_history.csv")


def get_access_token():
    client_id = os.environ["SPOTIFY_CLIENT_ID"]
    client_secret = os.environ["SPOTIFY_CLIENT_SECRET"]

    auth_str = f"{client_id}:{client_secret}"
    b64_auth = base64.b64encode(auth_str.encode()).decode()

    resp = requests.post(
        "https://accounts.spotify.com/api/token",
        headers={"Authorization": f"Basic {b64_auth}"},
        data={"grant_type": "client_credentials"},
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


def fetch_artist(token, artist_id):
    resp = requests.get(
        f"https://api.spotify.com/v1/artists/{artist_id}",
        headers={"Authorization": f"Bearer {token}"},
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json()
    return {
        "popularity": data["popularity"],
        "followers": data["followers"]["total"],
        "genres": ", ".join(data.get("genres", [])),
    }


def fetch_track(token, track_id):
    resp = requests.get(
        f"https://api.spotify.com/v1/tracks/{track_id}",
        headers={"Authorization": f"Bearer {token}"},
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json()
    return {
        "popularity": data["popularity"],
        "album": data["album"]["name"],
        "release_date": data["album"]["release_date"],
    }


def append_row(csv_path, fieldnames, row):
    file_exists = os.path.isfile(csv_path)
    with open(csv_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)


def main():
    token = get_access_token()
    today = datetime.date.today().isoformat()

    artist_fields = ["date", "artist", "artist_id", "popularity", "followers", "genres"]
    for name, artist_id in ARTISTS.items():
        info = fetch_artist(token, artist_id)
        row = {
            "date": today,
            "artist": name,
            "artist_id": artist_id,
            "popularity": info["popularity"],
            "followers": info["followers"],
            "genres": info["genres"],
        }
        append_row(ARTIST_CSV, artist_fields, row)
        print(f"Artist: {name} | popularity={info['popularity']} followers={info['followers']}")

    track_fields = ["date", "track", "track_id", "popularity", "album", "release_date"]
    for name, track_id in TRACKS.items():
        info = fetch_track(token, track_id)
        row = {
            "date": today,
            "track": name,
            "track_id": track_id,
            "popularity": info["popularity"],
            "album": info["album"],
            "release_date": info["release_date"],
        }
        append_row(TRACK_CSV, track_fields, row)
        print(f"Track: {name} | popularity={info['popularity']}")


if __name__ == "__main__":
    main()
