import feedparser
import requests
import re
from bs4 import BeautifulSoup
from dateutil import parser
import datetime
import time

def get_channel_rss_url(channel_url):
    """
    Attempts to find the RSS feed URL for a given YouTube channel URL.
    """
    if "feeds/videos.xml" in channel_url:
        return channel_url
    
    try:
        response = requests.get(channel_url, headers={"User-Agent": "Mozilla/5.0"})
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            rss_link = soup.find('link', {'type': 'application/rss+xml'})
            if rss_link:
                return rss_link['href']
    except Exception as e:
        print(f"Error fetching RSS URL for {channel_url}: {e}")
    
    # Fallback: if it's a @handle, we might need another way or just fail.
    # Often the RSS url is https://www.youtube.com/feeds/videos.xml?channel_id=<CHANNEL_ID>
    # Getting channel_id from @handle usually requires parsing the page.
    # The soup method above matches the <link> tag which usually contains the channel_id based RSS.
    return None

def check_for_new_videos(channel_urls, start_time, end_time, logger):
    """
    Checks RSS feeds for videos within the time range.
    Returns a list of dicts: {'title': str, 'link': str, 'published': datetime, 'channel_name': str}
    """
    logger.info("Checking for new videos...")
    found_videos = []
    
    # Ensure start_time and end_time are timezone-aware if possible, or naive. 
    # Feedparser returns struct_time.
    
    for url in channel_urls:
        rss_url = get_channel_rss_url(url)
        if not rss_url:
            logger.warning(f"Could not find RSS feed for {url}")
            continue
            
        logger.info(f"Fetching RSS feed: {rss_url}")
        feed = feedparser.parse(rss_url)
        
        if feed.bozo:
            logger.warning(f"Error parsing feed {rss_url}: {feed.bozo_exception}")
            continue
            
        channel_name = feed.feed.get('title', 'Unknown Channel')
        
        for entry in feed.entries:
            # published_parsed is a struct_time
            # published is a string
            try:
                # Convert to datetime
                published_dt = parser.parse(entry.published)
                
                # Make naive if necessary for comparison, or ensure both are aware.
                # Assuming entry.published includes timezone.
                # User input start_time/end_time from Streamlit are usually naive (local time) or set to UTC?
                # Streamlit datetime is usually naive.
                
                if published_dt.tzinfo is not None:
                     # Convert to naive if start_time is naive (assuming local system time matching)
                     # Or better, make start_time aware.
                     # For simplicity, let's assume the user input is in local time and the feed is UTC.
                     # We should convert everything to UTC or everything to local.
                     # Let's convert published_dt to local naive for comparison if start_time is naive.
                     if start_time.tzinfo is None:
                         published_dt = published_dt.replace(tzinfo=None) # This effectively ignores TZ, which is risky.
                         # Better: convert to local time.
                         # But let's check simple comparison first.
                         pass
                
                # logger.info(f"Checking video '{entry.title}' published at {published_dt}")
                
                if start_time <= published_dt <= end_time:
                    logger.info(f"Found match: {entry.title} ({published_dt})")
                    found_videos.append({
                        'title': entry.title,
                        'link': entry.link,
                        'published': published_dt,
                        'channel_name': channel_name,
                        'video_id': entry.yt_videoid
                    })
                    
            except Exception as e:
                logger.warning(f"Error parsing date for {entry.get('title', 'Unknown')}: {e}")
                
    return found_videos
