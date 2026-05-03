# Edits done from original module
scrapetube had problems due to Youtube changes :<br />
- Youtube mixes three structures for videos listing : videoRenderer, lockupViewModel and shortsLockupViewModel.<br />
- Youtube can return some videos when demanded tab don't exists, eg it returns Streams videos if channel has no stream but has regular videos.<br />
- That's the case when Home tab isn't present in channel.<br />
- Youtube tabs don't have filter options when there's not enough videos.<br />
- popular and oldest filter when presents for a tab are not working anymore, as Youtube updated their structure.<br /><br />

- videoId, title and is_live are properties directly available when iterating on scrapetube.get_channel()<br />

# Scrapetube
This module will help you scrape youtube without the official youtube api and without selenium.

With this module you can:


* Get all videos from a Youtube channel.
* Get all videos from a playlist.
* Search youtube.

# Installation

```bash
pip3 install scrapetube
```

# Usage
Here's a few short code examples.

## Get all videos for a channel
```python
import scrapetube

videos = scrapetube.get_channel("UCCezIgC97PvUuR4_gbFUs5g")

for video in videos:
    print(video['videoId'], video['title'], video['is_live'])
```

## Get all videos for a playlist
```python
import scrapetube

videos = scrapetube.get_playlist("PL-osiE80TeTt2d9bfVyTiXJA-UTHn6WwU")

for video in videos:
    print(video['videoId'])
```

## Make a search
```python
import scrapetube

videos = scrapetube.get_search("python")

for video in videos:
    print(video['videoId'])
```

# Full Documentation

[https://scrapetube.readthedocs.io/en/latest/](https://scrapetube.readthedocs.io/en/latest/)
