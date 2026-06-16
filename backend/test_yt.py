from yt_dlp import YoutubeDL
ydl_opts = {
    'format': 'bestaudio[ext=m4a]/bestaudio/best',
    'quiet': False,
    'no_warnings': False,
    'extractor_args': {'youtube': ['player_client=mweb']},
}
try:
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info("https://www.youtube.com/watch?v=jNQXAC9IVRw", download=False)
        print("SUCCESS:", info.get('title'))
except Exception as e:
    print(f"FAILED: {e}")
