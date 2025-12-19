import requests
import json
import subprocess

def test_search(term):
    url = "https://itunes.apple.com/search"
    params = {"term": term, "media": "music", "entity": "song", "limit": 1}
    try:
        response = requests.get(url, params=params)
        data = response.json()
        if data["resultCount"] > 0:
            track = data["results"][0]
            print(f"Found: {track['trackName']} by {track['artistName']}")
            print(f"URL: {track['trackViewUrl']}")
            return track['trackViewUrl']
        else:
            print("No results found.")
    except Exception as e:
        print(f"Error: {e}")

# Test
term = "Starboy The Weeknd"
link = test_search(term)
if link:
    # subprocess.run(["open", link]) # Uncomment to test actual open
    pass
