def lyrics_to_tags(lyrics: str, top_k: int = 5):
    words = [w.lower() for w in lyrics.split() if len(w) > 2]
    freq = {}
    for w in words:
        freq[w] = freq.get(w, 0) + 1
    tags = sorted(freq.items(), key=lambda x: x[1], reverse=True)
    return [t[0] for t in tags[:top_k]]

def process_song_meta(meta: dict):
    lyrics = meta.get('lyrics', '')
    tags = lyrics_to_tags(lyrics)
    return {'title': meta.get('title'), 'tags': tags, 'lyrics': lyrics}
