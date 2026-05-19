"""
COSC2671 Social Media and Network Analytics
@author Hexu Chen, RMIT University, 2026
@author Chenglong Ma, RMIT University, 2026

Utility script to fetch YouTube data and save as a JSON file.
This produces a data dump in the same structure as youtubeDataDump.json
so it can be used with the offline analysis scripts
(youtubeTextProcessing.py, youtubeSentimentAnalysis.py).

Usage:
  python fetchYoutubeData.py

Make sure to set your API key in youtubeClient.py first!

** Modified by Undergraduate (UG) Group 1 for Assignment 2: Choose Your Own Analysis **

It collects:
  - video metadata
  - channel metadata available from search/video endpoints
  - top-level comments
  - replies to top-level comments
  - parent-child relationships between comments
  - author names and author channel IDs
  - timestamps
  - like counts
  - reply counts
"""
import json
import time
from datetime import datetime
from youtubeClient import youtube_client

def safe_int(value, default=0):
    """
    Convert API values to integers safely.

    @param value: value from YouTube API
    @param default: default value if conversion fails
    @returns: integer
    """

    try:
        return int(value)
    except (TypeError, ValueError):
        return default

def execute_with_retry(request, max_retries=3, sleep_seconds=2):
    """
    Execute a YouTube API request with simple retry logic.

    @param request: YouTube API request object
    @param max_retries: number of retry attempts
    @param sleep_seconds: delay between retries
    @returns: API response dictionary
    """
    for attempt in range(max_retries):
        try:
            return request.execute()

        except Exception as e:
            if attempt == max_retries - 1:
                raise e

            print(f'API error: {e}')
            print(f'Retrying in {sleep_seconds} seconds...')
            time.sleep(sleep_seconds)

    return {}

def search_videos(client, search_query, max_videos=25, order='relevance'):
    """
    Search YouTube videos using a query.

    @param client: YouTube API client
    @param search_query: query string, e.g. 'AI on music'
    @param max_videos: maximum number of videos to collect
    @param order: YouTube search order, e.g. relevance, viewCount, date
    @returns: list of video IDs
    """
    video_ids = []
    next_page_token = None

    while len(video_ids) < max_videos:
        request = client.search().list(
            q=search_query,
            part='snippet',
            type='video',
            order=order,
            maxResults=min(50, max_videos - len(video_ids)),
            pageToken=next_page_token
        )

        response = execute_with_retry(request)

        for item in response.get('items', []):
            video_id = item.get('id', {}).get('videoId')

            if video_id and video_id not in video_ids:
                video_ids.append(video_id)

        next_page_token = response.get('nextPageToken')

        if not next_page_token:
            break

    return video_ids

def fetch_video_metadata(client, video_ids):
    """
    Fetch detailed metadata for videos.

    @param client: YouTube API client
    @param video_ids: list of YouTube video IDs
    @returns: dictionary keyed by video ID
    """
    videos = {}

    # YouTube videos().list allows up to 50 IDs per request
    for i in range(0, len(video_ids), 50):
        batch_ids = video_ids[i:i + 50]

        request = client.videos().list(
            id=','.join(batch_ids),
            part='snippet,statistics,contentDetails'
        )

        response = execute_with_retry(request)

        for item in response.get('items', []):
            video_id = item.get('id')
            snippet = item.get('snippet', {})
            statistics = item.get('statistics', {})
            content_details = item.get('contentDetails', {})

            videos[video_id] = {
                'video_id': video_id,
                'title': snippet.get('title', ''),
                'description': snippet.get('description', ''),
                'channel_id': snippet.get('channelId', ''),
                'channel_title': snippet.get('channelTitle', ''),
                'published_at': snippet.get('publishedAt', ''),
                'tags': snippet.get('tags', []),
                'category_id': snippet.get('categoryId', ''),
                'duration': content_details.get('duration', ''),
                'view_count': safe_int(statistics.get('viewCount')),
                'like_count': safe_int(statistics.get('likeCount')),
                'comment_count': safe_int(statistics.get('commentCount')),
                'comments': []
            }

    return videos

def extract_comment_snippet(comment_item):
    """
    Extract useful fields from a YouTube comment item.

    @param comment_item: comment object from YouTube API
    @returns: dictionary of comment fields
    """
    snippet = comment_item.get('snippet', {})

    return {
        'comment_id': comment_item.get('id', ''),
        'author_display_name': snippet.get('authorDisplayName', ''),
        'author_channel_id': snippet.get('authorChannelId', {}).get('value', ''),
        'text': snippet.get('textDisplay', ''),
        'text_original': snippet.get('textOriginal', ''),
        'like_count': safe_int(snippet.get('likeCount')),
        'published_at': snippet.get('publishedAt', ''),
        'updated_at': snippet.get('updatedAt', '')
    }

def fetch_replies_for_comment(client, parent_comment_id, max_replies_per_comment=100):
    """
    Fetch replies for a single top-level comment.

    @param client: YouTube API client
    @param parent_comment_id: top-level comment ID
    @param max_replies_per_comment: maximum replies to collect
    @returns: list of reply dictionaries
    """
    replies = []
    next_page_token = None

    while len(replies) < max_replies_per_comment:
        request = client.comments().list(
            parentId=parent_comment_id,
            part='snippet',
            maxResults=min(100, max_replies_per_comment - len(replies)),
            pageToken=next_page_token,
            textFormat='plainText'
        )

        response = execute_with_retry(request)

        for item in response.get('items', []):
            reply = extract_comment_snippet(item)
            reply['parent_comment_id'] = parent_comment_id
            reply['comment_type'] = 'reply'
            replies.append(reply)

        next_page_token = response.get('nextPageToken')

        if not next_page_token:
            break

    return replies

def fetch_comments_for_video(
    client,
    video_id,
    max_comments_per_video=100,
    max_replies_per_comment=100,
    include_replies=True
):
    """
    Fetch top-level comments and replies for a video.

    @param client: YouTube API client
    @param video_id: YouTube video ID
    @param max_comments_per_video: maximum top-level comments to collect
    @param max_replies_per_comment: maximum replies per top-level comment
    @param include_replies: whether to collect replies
    @returns: list of top-level comment dictionaries, each with replies
    """
    comments = []
    next_page_token = None

    while len(comments) < max_comments_per_video:
        request = client.commentThreads().list(
            videoId=video_id,
            part='snippet',
            maxResults=min(100, max_comments_per_video - len(comments)),
            pageToken=next_page_token,
            textFormat='plainText',
            order='relevance'
        )

        response = execute_with_retry(request)

        for thread in response.get('items', []):
            thread_snippet = thread.get('snippet', {})
            top_comment_item = thread_snippet.get('topLevelComment', {})

            top_comment = extract_comment_snippet(top_comment_item)
            top_comment['comment_type'] = 'top_level'
            top_comment['parent_comment_id'] = None
            top_comment['total_reply_count'] = safe_int(thread_snippet.get('totalReplyCount'))
            top_comment['replies'] = []

            if include_replies and top_comment['total_reply_count'] > 0:
                try:
                    top_comment['replies'] = fetch_replies_for_comment(
                        client=client,
                        parent_comment_id=top_comment['comment_id'],
                        max_replies_per_comment=max_replies_per_comment
                    )

                except Exception as e:
                    print(f'Could not fetch replies for comment {top_comment["comment_id"]}: {e}')

            comments.append(top_comment)

        next_page_token = response.get('nextPageToken')

        if not next_page_token:
            break

    return comments

def build_flat_comments(videos):
    """
    Build a flat comment table from nested video/comment/reply data.

    This is useful for pandas, NLP, and network construction.

    @param videos: dictionary of video data
    @returns: list of flat comment records
    """

    flat_comments = []

    for video in videos.values():
        video_context = {
            'video_id': video.get('video_id', ''),
            'video_title': video.get('title', ''),
            'channel_id': video.get('channel_id', ''),
            'channel_title': video.get('channel_title', ''),
            'video_published_at': video.get('published_at', ''),
            'video_view_count': video.get('view_count', 0),
            'video_like_count': video.get('like_count', 0),
            'video_comment_count': video.get('comment_count', 0)
        }

        for comment in video.get('comments', []):
            top_record = {
                **video_context,
                'comment_id': comment.get('comment_id', ''),
                'parent_comment_id': None,
                'comment_type': 'top_level',
                'author_display_name': comment.get('author_display_name', ''),
                'author_channel_id': comment.get('author_channel_id', ''),
                'text': comment.get('text', ''),
                'text_original': comment.get('text_original', ''),
                'like_count': comment.get('like_count', 0),
                'published_at': comment.get('published_at', ''),
                'updated_at': comment.get('updated_at', ''),
                'reply_to_author_display_name': None,
                'reply_to_author_channel_id': None
            }

            flat_comments.append(top_record)

            for reply in comment.get('replies', []):
                reply_record = {
                    **video_context,
                    'comment_id': reply.get('comment_id', ''),
                    'parent_comment_id': comment.get('comment_id', ''),
                    'comment_type': 'reply',
                    'author_display_name': reply.get('author_display_name', ''),
                    'author_channel_id': reply.get('author_channel_id', ''),
                    'text': reply.get('text', ''),
                    'text_original': reply.get('text_original', ''),
                    'like_count': reply.get('like_count', 0),
                    'published_at': reply.get('published_at', ''),
                    'updated_at': reply.get('updated_at', ''),
                    'reply_to_author_display_name': comment.get('author_display_name', ''),
                    'reply_to_author_channel_id': comment.get('author_channel_id', '')
                }

                flat_comments.append(reply_record)

    return flat_comments

def fetch_youtube_data(
    search_query,
    max_videos=25,
    max_comments_per_video=100,
    max_replies_per_comment=100,
    order='relevance',
    output_file='youtubeDataDump.json',
    flat_output_file='youtubeFlatComments.json'
):
    """
    Fetch YouTube videos, comments, and replies.

    @param search_query: search query string, e.g. 'AI on music'
    @param max_videos: maximum number of videos to collect
    @param max_comments_per_video: maximum top-level comments per video
    @param max_replies_per_comment: maximum replies per top-level comment
    @param order: YouTube search order
    @param output_file: nested JSON output file
    @param flat_output_file: flat comments JSON output file
    """

    client = youtube_client()

    print(f"Searching YouTube for query: '{search_query}'")
    print(f'Order: {order}')
    print(f'Max videos: {max_videos}')
    print(f'Max top-level comments per video: {max_comments_per_video}')
    print(f'Max replies per comment: {max_replies_per_comment}')

    video_ids = search_videos(
        client=client,
        search_query=search_query,
        max_videos=max_videos,
        order=order
    )

    print(f'Found {len(video_ids)} videos.')

    videos = fetch_video_metadata(
        client=client,
        video_ids=video_ids
    )

    for index, video_id in enumerate(video_ids, start=1):
        video = videos.get(video_id)

        if not video:
            continue

        print(f'\n[{index}/{len(video_ids)}] Fetching comments for: {video["title"][:80]}')

        try:
            video['comments'] = fetch_comments_for_video(
                client=client,
                video_id=video_id,
                max_comments_per_video=max_comments_per_video,
                max_replies_per_comment=max_replies_per_comment,
                include_replies=True
            )

            total_replies = sum(len(comment.get('replies', [])) for comment in video['comments'])

            print(
                f'Collected {len(video["comments"])} top-level comments '
                f'and {total_replies} replies.'
            )

        except Exception as e:
            print(f'Could not fetch comments for video {video_id}: {e}')
            video['comments'] = []

    data = {
        'metadata': {
            'search_query': search_query,
            'collection_datetime': datetime.utcnow().isoformat() + 'Z',
            'max_videos': max_videos,
            'max_comments_per_video': max_comments_per_video,
            'max_replies_per_comment': max_replies_per_comment,
            'order': order,
            'source': 'YouTube Data API v3'
        },
        'videos': list(videos.values())
    }

    flat_comments = build_flat_comments(videos)

    flat_data = {
        'metadata': data['metadata'],
        'comments': flat_comments
    }

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    with open(flat_output_file, 'w', encoding='utf-8') as f:
        json.dump(flat_data, f, ensure_ascii=False, indent=2)

    print('\nDone.')
    print(f'Saved nested data to: {output_file}')
    print(f'Saved flat comments to: {flat_output_file}')
    print(f'Total flat comment/reply records: {len(flat_comments)}')

if __name__ == '__main__':
    SEARCH_QUERY = 'AI on music'

    MAX_VIDEOS = 25
    MAX_COMMENTS_PER_VIDEO = 100
    MAX_REPLIES_PER_COMMENT = 100

    OUTPUT_FILE = 'youtubeDataDump_AI_on_music.json'
    FLAT_OUTPUT_FILE = 'youtubeFlatComments_AI_on_music.json'

    fetch_youtube_data(
        search_query=SEARCH_QUERY,
        max_videos=MAX_VIDEOS,
        max_comments_per_video=MAX_COMMENTS_PER_VIDEO,
        max_replies_per_comment=MAX_REPLIES_PER_COMMENT,
        order='relevance',
        output_file=OUTPUT_FILE,
        flat_output_file=FLAT_OUTPUT_FILE
    )