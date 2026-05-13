#
# COSC2671 Social Media and Network Analytics
# @author Hexu Chen, RMIT University, 2026
# @author Chenglong Ma, RMIT University, 2026
#
# Utility script to fetch YouTube data and save as a JSON file.
# This produces a data dump in the same structure as youtubeDataDump.json
# so it can be used with the offline analysis scripts
# (youtubeTextProcessing.py, youtubeSentimentAnalysis.py).
#
# Usage:
#   python fetchYoutubeData.py
#
# Make sure to set your API key in youtubeClient.py first!
#

import json
import sys
from youtubeClient import youtube_client


def fetch_youtube_data(searchQuery, maxVideos=25, maxCommentsPerVideo=50, outputFile='youtubeDataDump.json'):
    """
    Fetch YouTube videos and their comments, then save to a JSON file.

    @param searchQuery: search query string (e.g. 'RMIT University')
    @param maxVideos: maximum number of videos to retrieve
    @param maxCommentsPerVideo: maximum number of comments per video
    @param outputFile: output JSON filename
    """

    client = youtube_client()

    # Step 1: Search for videos
    print(f"Searching for videos with query: '{searchQuery}'...")
    search_response = client.search().list(
        q=searchQuery,
        part='snippet',
        type='video',
        order='viewCount',
        maxResults=min(maxVideos, 50)  # YouTube API max per request is 50
    ).execute()

    video_ids = []
    video_snippets = {}
    for item in search_response.get('items', []):
        video_id = item['id']['videoId']
        video_ids.append(video_id)
        video_snippets[video_id] = item['snippet']

    print(f"  Found {len(video_ids)} videos.")

    # Step 2: Get video statistics (viewCount, likeCount)
    print("Fetching video statistics...")
    stats_response = client.videos().list(
        id=','.join(video_ids),
        part='statistics'
    ).execute()

    video_stats = {}
    for item in stats_response.get('items', []):
        video_stats[item['id']] = item['statistics']

    # Step 3: Get comments for each video
    print("Fetching comments...")
    videos = []

    for video_id in video_ids:
        snippet = video_snippets[video_id]
        stats = video_stats.get(video_id, {})

        video = {
            'title': snippet['title'],
            'videoId': video_id,
            'channelTitle': snippet['channelTitle'],
            'publishedAt': snippet['publishedAt'],
            'viewCount': int(stats.get('viewCount', 0)),
            'likeCount': int(stats.get('likeCount', 0)),
            'comments': []
        }

        try:
            comment_response = client.commentThreads().list(
                videoId=video_id,
                part='snippet',
                maxResults=maxCommentsPerVideo,
                textFormat='plainText'
            ).execute()

            for comment_thread in comment_response.get('items', []):
                top_comment = comment_thread['snippet']['topLevelComment']['snippet']
                video['comments'].append({
                    'author': top_comment['authorDisplayName'],
                    'text': top_comment['textDisplay'],
                    'publishedAt': top_comment['publishedAt'],
                    'likeCount': top_comment.get('likeCount', 0)
                })

            print(f"  {snippet['title'][:50]}... → {len(video['comments'])} comments")

        except Exception as e:
            print(f"  {snippet['title'][:50]}... → Comments disabled or error: {e}")

        videos.append(video)

    # Step 4: Save to JSON
    data = {'videos': videos}
    with open(outputFile, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"\nDone! Saved {len(videos)} videos to '{outputFile}'.")


# ============================================================
# Main
# ============================================================

if __name__ == '__main__':
    # Default parameters — modify as needed
    SEARCH_QUERY = 'RMIT University'
    MAX_VIDEOS = 10     # Search for 10 videos about RMIT University
    MAX_COMMENTS = 5    # Fetch up to 5 comments per video
    OUTPUT_FILE = 'youtubeDataDump.json'

    fetch_youtube_data(SEARCH_QUERY, MAX_VIDEOS, MAX_COMMENTS, OUTPUT_FILE)
