"""
Signal collection from RSS feeds with scoring integration
"""
import feedparser
from datetime import datetime
from scorer import calculate_score, should_collect
from database import Database
from config import config
import logging

logger = logging.getLogger(__name__)


def collect_signals(db: Database = None, score_threshold: int = 40):
    """
    Collect high-intent signals from RSS feeds and store in database.
    
    Args:
        db: Database instance
        score_threshold: Minimum score to collect a signal
    
    Returns:
        List of collected signals
    """
    if db is None:
        db = Database(config.get("db_path", "signalforge.db"))
    
    rss_feeds = config.get("rss_feeds", [])
    results = []
    
    for feed_url in rss_feeds:
        try:
            feed = feedparser.parse(feed_url)
            
            for entry in feed.entries:
                title = entry.get("title", "")
                summary = entry.get("summary", "")
                link = entry.get("link", "")
                published = entry.get("published", datetime.now().isoformat())
                
                # Score the signal
                score, matched_keywords = calculate_score(title, summary, link)
                
                # Check if meets threshold
                if should_collect(score, score_threshold):
                    # Store in database
                    signal_id = db.save_signal(
                        score=score,
                        title=title,
                        keywords=", ".join(matched_keywords),
                        link=link,
                        published=published,
                        summary=summary,
                        source=feed_url
                    )
                    
                    results.append({
                        "id": signal_id,
                        "score": score,
                        "title": title,
                        "keywords": ", ".join(matched_keywords),
                        "link": link,
                        "published": published,
                    })
                    
                    logger.info(f"Collected signal: {title} (score: {score})")
        
        except Exception as e:
            logger.error(f"Error parsing feed {feed_url}: {e}")
    
    return sorted(results, key=lambda x: x["score"], reverse=True)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    signals = collect_signals()
    print(f"Collected {len(signals)} signals")
    for signal in signals[:5]:
        print(f"  [{signal['score']}] {signal['title']}")