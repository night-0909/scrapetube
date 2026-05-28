# Edits done from original module
scrapetube had problems due to Youtube changes :
- Youtube mixes three structures for videos listing : videoRenderer, lockupViewModel and shortsLockupViewModel.
- Youtube can return some videos when demanded tab don't exists, eg it returns Streams videos if channel has no stream but has regular videos.
That's the case when Home tab isn't present in channel.
- Youtube tabs don't have filter options when there's not enough videos.
- popular and oldest filter when presents for a tab are not working anymore, as Youtube updated their structure.<br />

videoId, title and is_live are properties directly available when iterating on scrapetube.get_channel()<br />

# Warning
As Youtube auto-translate some elements (channel title, video title/description, etc...) based on your location, video title/description
can be auto-translated.<br />
    
So when you iterate on scrapetube.get_channel(), title can be auto-translated in session.headers["Accept-Language"] language set below.<br />
To retrieve the title/description from the default language or added language by the channel owner :<br />
get title and description from Youtube Data Api V3 /videos on each videos<br />
or hit watch?v= and get title and description from ytPlayerResponse->videoDetails<br />
or get snippet.defaultLanguage from Youtube Data Api V3 /channels and set it in header Accept-Language or set a cookie name:PREF
value:hl=XX // but defaultLanguage isn't always present<br />

In the end, don't use videos title when iterating scrapetube.get_channel().<br />
I personally use Youtube Data Api V3 /videos because its faster and hitting watch?v= too much could trigger anti-bot detection and need loging in to
Youtube or solving captcha.<br />

To install this version of scrapetube, download all files then type :
```bash
pip3 install .
```

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
