import json, re
import time, os, sys
from typing import Generator

import requests
from urllib3.util.retry import Retry
from http.cookiejar import MozillaCookieJar
from typing_extensions import Literal

from datetime import datetime
from zoneinfo import ZoneInfo

type_property_map = {
    "videos": "videoRenderer",
    "streams": "videoRenderer",
    "shorts": "reelWatchEndpoint"
}

tabs_url_map = {
    "videos": "/@(.*)/videos",
    "streams": "/@(.*)/streams",
    "shorts": "/@(.*)/shorts"
}

LOGGING = {"enabled": True, "tzinfo": ZoneInfo("Europe/Paris"),
            "dateFormats": {"dateString": "%d/%m/%Y %H:%M:%S", "dateDBString": "%Y-%m-%d %H:%M:%S", "dateFileString": "%d%m%Y%H%M%S"},
            "logfilename": os.path.dirname(os.path.realpath(__file__)) + "/scrapetube.log"}

RETRY_STRATEGY = {"requests_module":
                    {"retries": 3, "backoff_factor": 1, "backoff_jitter": 0.5,
                    "allowed_methods": frozenset(["GET", "POST", "HEAD", "OPTIONS"]), "status_forcelist": (408, 425, 429, 500, 502, 503, 504)},
                 "error_html": {"retries": 3, "sleep_after_error": 5}
}
CALLING_FILE = sys.argv[0]
       
def get_channel(
    channel_id: str = None,
    channel_url: str = None,
    channel_username: str = None,
    limit: int = None,
    sleep: float = 1,
    proxies: dict = None,
    cookies: str = None,
    logging: dict = LOGGING,
    retry_strategy: dict = RETRY_STRATEGY,
    sort_by: Literal["newest", "oldest", "popular"] = "newest",
    content_type: Literal["videos", "shorts", "streams"] = "videos",
) -> Generator[dict, None, None]:

    """Get videos for a channel.

    Parameters:
        channel_id (``str``, *optional*):
            The channel id from the channel you want to get the videos for.
            If you prefer to use the channel url instead, see ``channel_url`` below.

        channel_url (``str``, *optional*):
            The url to the channel you want to get the videos for.
            Since there is a few type's of channel url's, you can use the one you want
            by passing it here instead of using ``channel_id``.

        channel_username (``str``, *optional*):
            The username from the channel you want to get the videos for.
            Ex. ``LinusTechTips`` (without the @).
            If you prefer to use the channel url instead, see ``channel_url`` above.

        limit (``int``, *optional*):
            Limit the number of videos you want to get.

        sleep (``int``, *optional*):
            Seconds to sleep between API calls to youtube, in order to prevent getting blocked.
            Defaults to 1.

        proxies (``dict``, *optional*):
            A dictionary with the proxies you want to use. Ex:
            ``{'https': 'http://username:password@101.102.103.104:3128'}``
        
        sort_by (``str``, *optional*):
            In what order to retrieve to videos. Pass one of the following values.
            ``"newest"``: Get the new videos first.
            ``"oldest"``: Get the old videos first.
            ``"popular"``: Get the popular videos first. Defaults to "newest".

        content_type (``str``, *optional*):
            In order to get content type. Pass one of the following values.
            ``"videos"``: Videos
            ``"shorts"``: Shorts
            ``"streams"``: Streams
    """

    base_url = ""
    if channel_url:
        base_url = channel_url+'ezee'
    elif channel_id:
        base_url = f"https://www.youtube.com/channel/{channel_id}"
    elif channel_username:
        base_url = f"https://www.youtube.com/@{channel_username}"

    url = "{base_url}/{content_type}?view=0&flow=grid".format(
        base_url=base_url,
        content_type=content_type,
    )
    api_endpoint = "https://www.youtube.com/youtubei/v1/browse"
       
    videos = get_videos(url, api_endpoint, "contents", type_property_map[content_type], content_type, limit, sleep, proxies, cookies, logging, retry_strategy, sort_by)
    for video in videos:
        yield video


def get_playlist(
    playlist_id: str, limit: int = None, sleep: int = 1, proxies: dict = None, cookies: str = None, logging: dict = LOGGING, retry_strategy: dict = RETRY_STRATEGY
) -> Generator[dict, None, None]:

    """Get videos for a playlist.

    Parameters:
        playlist_id (``str``):
            The playlist id from the playlist you want to get the videos for.

        limit (``int``, *optional*):
            Limit the number of videos you want to get.

        sleep (``int``, *optional*):
            Seconds to sleep between API calls to youtube, in order to prevent getting blocked.
            Defaults to 1.
        
        proxies (``dict``, *optional*):
            A dictionary with the proxies you want to use. Ex:
            ``{'https': 'http://username:password@101.102.103.104:3128'}``
    """

    url = f"https://www.youtube.com/playlist?list={playlist_id}"
    api_endpoint = "https://www.youtube.com/youtubei/v1/browse"
    videos = get_videos(url, api_endpoint, "playlistVideoListRenderer", "playlistVideoRenderer", None, limit, sleep, proxies, cookies, logging, retry_strategy)
    for video in videos:
        yield video


def get_search(
    query: str,
    limit: int = None,
    sleep: int = 1,
    sort_by: Literal["relevance", "upload_date", "view_count", "rating"] = "relevance",
    results_type: Literal["video", "channel", "playlist", "movie"] = "video",
    proxies: dict = None,
    cookies: str = None,
    logging: dict = LOGGING,
    retry_strategy: dict = RETRY_STRATEGY,
    
) -> Generator[dict, None, None]:

    """Search youtube and get videos.

    Parameters:
        query (``str``):
            The term you want to search for.

        limit (``int``, *optional*):
            Limit the number of videos you want to get.

        sleep (``int``, *optional*):
            Seconds to sleep between API calls to youtube, in order to prevent getting blocked.
            Defaults to 1.

        sort_by (``str``, *optional*):
            In what order to retrieve to videos. Pass one of the following values.
            ``"relevance"``: Get the new videos in order of relevance.
            ``"upload_date"``: Get the new videos first.
            ``"view_count"``: Get the popular videos first.
            ``"rating"``: Get videos with more likes first.
            Defaults to "relevance".

        results_type (``str``, *optional*):
            What type you want to search for. Pass one of the following values:
            ``"video"|"channel"|"playlist"|"movie"``. Defaults to "video".
        
        proxies (``dict``, *optional*):
            A dictionary with the proxies you want to use. Ex:
            ``{'https': 'http://username:password@101.102.103.104:3128'}``

    """

    sort_by_map = {
        "relevance": "A",
        "upload_date": "I",
        "view_count": "M",
        "rating": "E",
    }

    results_type_map = {
        "video": ["B", "videoRenderer"],
        "channel": ["C", "channelRenderer"],
        "playlist": ["D", "playlistRenderer"],
        "movie": ["E", "videoRenderer"],
    }

    param_string = f"CA{sort_by_map[sort_by]}SAhA{results_type_map[results_type][0]}"
    url = f"https://www.youtube.com/results?search_query={query}&sp={param_string}"
    api_endpoint = "https://www.youtube.com/youtubei/v1/search"
    videos = get_videos(
        url, api_endpoint, "contents", results_type_map[results_type][1], None, limit, sleep, proxies, cookies, logging, retry_strategy
    )
    for video in videos:
        yield video



def get_video(
    id: str,
    proxies: dict = None,
    cookies: str = None,
    logging: dict = LOGGING,
    retry_strategy: dict = RETRY_STRATEGY
) -> dict:

    """Get a single video.

    Parameters:
        id (``str``):
            The video id from the video you want to get.
    """

    session = get_session(proxies, cookies, retry_strategy)
    url = f"https://www.youtube.com/watch?v={id}"
    
    try:
        html = get_initial_data(session, url)
    except Exception as e:
        print("Exception in requests call getting initial data")
        raise(e)
        
    try:        
        client = json.loads(
            get_json_from_html(html, "INNERTUBE_CONTEXT", 2, '"}},') + '"}}'
        )["client"]
    except Exception as e:
        print("Error getting INNERTUBE_CONTEXT")
        raise(e)
        
    session.headers["X-YouTube-Client-Name"] = "1"
    session.headers["X-YouTube-Client-Version"] = client["clientVersion"]
    
    try: 
        data = json.loads(
            get_json_from_html(html, "var ytInitialData = ", 0, "};") + "}"
        )
    except Exception as e:
        print("Error getting var ytInitialData = ")
        raise(e)
        
    return next(search_dict(data, "videoPrimaryInfoRenderer"))

def get_videos(
    url: str, api_endpoint: str, selector_list: str, selector_item: str, content_type: str, limit: int, sleep: float, proxies: dict, cookies: str, logging: dict, retry_strategy: dict, sort_by: str = None
) -> Generator[dict, None, None]:
    session = get_session(proxies, cookies, retry_strategy)
    is_first = True
    quit_it = False
    count = 0
    attempt_initial_data = 0
    exceptions = []   

    while True:
        if is_first:           
            # Sometimes Youtube doesn't return expected content ("var ytInitialData = " not present), so we try to call get_initial_data() again.
            # Solutions :
            # - using cookies : solves it.
            # - browser impersonation ? Not tested
            if attempt_initial_data < retry_strategy['error_html']['retries']:
                try:
                    html = get_initial_data(session, url)
                except Exception as e:
                    dateNow = getDateNow(logging)["dateString"]
                    log(logging, f"{dateNow} : {CALLING_FILE} {url} Exception in requests call getting initial data : {e}")                   
                    print("Exception in requests call getting initial data")
                    raise(e)
                
                try:
                    INNERTUBE_CONTEXT = get_json_from_html(html, "INNERTUBE_CONTEXT", 2, '"}},') + '"}}'
                    client = json.loads(INNERTUBE_CONTEXT)["client"]
                except Exception as e:
                    dateNow = getDateNow(logging)["dateString"]
                    exceptions.append(f"{dateNow} : {url} Can't get ytInitialData from initial data : {e}")
                    log(logging, f"{dateNow} : {CALLING_FILE} {url} Can't get INNERTUBE_CONTEXT from initial data : {e}")
                    
                    is_first = True
                    attempt_initial_data = attempt_initial_data + 1
                    time.sleep(retry_strategy['error_html']['sleep_after_error'])
                    continue
                
                try:
                    api_key = get_json_from_html(html, "innertubeApiKey", 3)            
                except Exception as e:
                    dateNow = getDateNow(logging)["dateString"]
                    exceptions.append(f"{dateNow} : {url} Can't get ytInitialData from initial data : {e}")
                    log(logging, f"{dateNow} : {CALLING_FILE} {url} Can't get innertubeApiKey from initial data : {e}")
                            
                    is_first = True
                    attempt_initial_data = attempt_initial_data + 1
                    time.sleep(retry_strategy['error_html']['sleep_after_error'])
                    continue
                
                session.headers["X-YouTube-Client-Name"] = "1"
                session.headers["X-YouTube-Client-Version"] = client["clientVersion"]
                
                try:
                    ytInitialData = get_json_from_html(html, "var ytInitialData = ", 0, "};") + "}"
                    data = json.loads(ytInitialData)
                except Exception as e:   
                    dateNow = getDateNow(logging)["dateString"]
                    exceptions.append(f"{dateNow} : {url} Can't get ytInitialData from initial data : {e}")
                    log(logging, f"{dateNow} : {CALLING_FILE} {url} Can't get ytInitialData from initial data : {e}")                   
                    
                    is_first = True
                    attempt_initial_data = attempt_initial_data + 1
                    time.sleep(retry_strategy['error_html']['sleep_after_error'])
                    continue
            else:
                dateNow = getDateNow(logging)["dateString"]
                log(logging, f"{dateNow} : {CALLING_FILE} {url} Can't get Youtube vars from initial data after {retry_strategy['error_html']['retries']} retries\nHistory of exceptions : {CALLING_FILE} {exceptions}")
                raise Exception(f"{dateNow} : {url} Can't get Youtube vars from initial data after {retry_strategy['error_html']['retries']} retries\nHistory of exceptions : {exceptions}")
            
            # For get_channel we search "contents"
            data = next(search_dict(data, selector_list), None)
                        
            # When content_type is specified (only in get_channel()), verify that channel has a Tab for content we are looking for and is the selected Tab.
            if content_type is not None:
                tabFound = False
                if data is not None:
                    for tab in data["twoColumnBrowseResultsRenderer"]["tabs"]:
                        # endpoint can be missing if no Home tab and /videos is scraped, with channel has no content at all
                        if "tabRenderer" in tab and "endpoint" in tab["tabRenderer"]:
                            if len(re.findall(tabs_url_map[content_type], tab["tabRenderer"]["endpoint"]["commandMetadata"]["webCommandMetadata"]["url"])) > 0 and tab["tabRenderer"]["selected"] is True:
                                tabFound = True
                                break
                
                if tabFound is False:
                    break
            
            next_data = get_next_data(data, sort_by)    
            
            is_first = False
            
            # If next_data is empty we jump to generator construction and then quit
            if content_type is not None:
                if next_data is not None and sort_by and sort_by != "newest": 
                    continue
        else:
            try:
                data = get_ajax_data(session, api_endpoint, api_key, next_data, client)
                next_data = get_next_data(data)
            except Exception as e:
                dateNow = getDateNow(logging)["dateString"]
                log(logging, f"{dateNow} : {CALLING_FILE} {url} Exception in getting next data : {e}")                   
                print("Exception in getting next data")
                raise e       
            
        # When a channel tab is called, Youtube can use multiple renderer : videoRenderer, lockupViewModel or shortsLockupViewModel
        # So we change selector_item
        if content_type is not None:
            if next(search_dict(data, "lockupViewModel"), None) is not None:
                selector_item = "lockupViewModel"
            elif next(search_dict(data, "shortsLockupViewModel"), None) is not None:
                selector_item = "shortsLockupViewModel"

        for result in get_videos_items(data, selector_item):
            try:
                count += 1
                if content_type is not None:    
                    # When we get videos of channel, set videoId, title and is_live values according to used renderer
                    result = set_video_info(content_type, result, selector_item)
                yield result
                if count == limit:
                    quit_it = True
                    break
            except GeneratorExit:
                quit_it = True
                break

        if not next_data or quit_it:
            break

        time.sleep(sleep)

    session.close()

def get_session(proxies: dict = None, cookies: str = None, retry_strategy: dict = RETRY_STRATEGY) -> requests.Session:
    session = requests.Session()
    if proxies:
        session.proxies.update(proxies)
    session.headers[
        "User-Agent"
    ] = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
    session.headers["Accept-Language"] = "en"
       
    if cookies:
        if os.path.isfile(cookies):
            cookie_jar = MozillaCookieJar(cookies)
            cookie_jar.load(ignore_discard=True)
            session.cookies = cookie_jar
    else:
        session.cookies.set("CONSENT", "YES+cb", domain=".youtube.com")

    retry = Retry(
        total=retry_strategy['requests_module']['retries'],
        backoff_factor=retry_strategy['requests_module']['backoff_factor'],
        backoff_jitter=retry_strategy['requests_module']['backoff_jitter'],
        allowed_methods=retry_strategy['requests_module']['allowed_methods'],
        status_forcelist=retry_strategy['requests_module']['status_forcelist'],
        raise_on_status=True
    )

    adapter = requests.adapters.HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)    
    return session
    
    # Warning : as Youtube auto-translate some elements (channel title, video title/description, etc...) based on your location, video titles/description
    # can be auto-translated.
    
    # So when you iterate on scrapetube.get_channel(), title can be auto-translated in session.headers["Accept-Language"] language set below or
    # with language set 
    # To retrieve the title/description from the default language or added language by the channel owner :
    # get title and description from Youtube Data Api V3 /videos on each videos
    # or hit watch?v= and get title and description from ytPlayerResponse->videoDetails // complete get_video function for that
    # or get snippet.defaultLanguage from Youtube Data Api V3 /channels and set it in header Accept-Language or set a cookie name:PREF
    # value:hl=XX // but defaultLanguage isn't always present

def get_initial_data(session: requests.Session, url: str) -> str:    
    try:
        response = session.get(url, params={"ucbcb":1}, timeout=(3.05, 20))
    except Exception as e:
        raise e

    html = response.text
    return html

def get_ajax_data(
    session: requests.Session,
    api_endpoint: str,
    api_key: str,
    next_data: dict,
    client: dict,
) -> dict:
    data = {
        "context": {"clickTracking": next_data["click_params"], "client": client},
        "continuation": next_data["token"],
    }
    
    try:
        response = session.post(api_endpoint, params={"key": api_key}, json=data, timeout=(3.05, 20))
    except Exception as e:
        raise e
        
    return response.json()

def get_json_from_html(html: str, key: str, num_chars: int = 2, stop: str = '"') -> str:
    pos_key = html.find(key)

    if (pos_key < 0):
        raise ValueError(f"Could not find key in YouTube HTML: {key}")

    pos_begin = pos_key + len(key) + num_chars
    pos_end = html.find(stop, pos_begin)

    if (pos_end < 0):
        raise ValueError(f"Could not find stop marker after key: {key}")

    return html[pos_begin:pos_end]

def get_next_data(data: dict, sort_by: str = None) -> dict:
    # Youtube, please don't change the order of these
    sort_by_map = {
        "newest": 0, 
        "popular": 1,
        "oldest": 2, 
    }
    
    # Warning : when members subscriptions are active on channel, newest/popular/oldest filters are embedded in
    # chipBarViewModel->["chips"][0]["chipViewModel"]["tapCommand"]["innertubeCommand"]["showSheetCommand"]
    if sort_by and sort_by != "newest":
        # When only few videos are present in a tab, no filter options are displayed so chipBarViewModel don't exist.
        nextchipBarViewModel = next(search_dict(data, "chipBarViewModel"), None)
        if nextchipBarViewModel is not None:
            # Search for presence of showSheetCommand (channel with members subscriptions)
            firstFilter = nextchipBarViewModel["chips"][0]["chipViewModel"]["tapCommand"]["innertubeCommand"]
            if "showSheetCommand" in firstFilter:
                listFilters = next(search_dict(firstFilter, "listItems"), None)
                endpoint = listFilters[sort_by_map[sort_by]]["listItemViewModel"]["rendererContext"]["commandContext"]["onTap"]["innertubeCommand"]
                if not endpoint:
                    return None
                    
                commands = endpoint["commandExecutorCommand"]["commands"]
                for command in commands:
                    token = safely_get_value_from_key(command, 'continuationCommand', "token")
                    if token is not None:
                        clickTrackingParams = command["clickTrackingParams"]
                        break
                
                next_data = {
                    "token": token,
                    "click_params": {"clickTrackingParams": clickTrackingParams},
                }

                return next_data
            else:
                endpoint = nextchipBarViewModel["chips"][sort_by_map[sort_by]]["chipViewModel"]["tapCommand"]["innertubeCommand"]
        else:
            endpoint = None
    else:
        endpoint = next(search_dict(data, "continuationEndpoint"), None)
    if not endpoint:
        return None
    next_data = {
        "token": endpoint["continuationCommand"]["token"],
        "click_params": {"clickTrackingParams": endpoint["clickTrackingParams"]},
    }

    return next_data
  
def search_dict(partial: dict, search_key: str) -> Generator[dict, None, None]:
    stack = [partial]
    while stack:
        current_item = stack.pop(0)
        if isinstance(current_item, dict):
            for key, value in current_item.items():
                if key == search_key:
                    yield value
                else:
                    stack.append(value)
        elif isinstance(current_item, list):
            for value in current_item:
                stack.append(value)


def get_videos_items(data: dict, selector: str) -> Generator[dict, None, None]:
    return search_dict(data, selector)

def set_video_info(content_type, result, selector_item):
    # Warning for video title and description languages
    # To get these infos in original language, read comment in get_session()
    
    # videos or streams
    if selector_item == "videoRenderer":
        result["videoId"] = result["videoId"]                
        result["title"] = result['title']['runs'][0]['text']

        result["is_live"] = False
        thumbnailOverlayTimeStatusRenderer_style = safely_get_value_from_key(result, 'thumbnailOverlays', 0, 'thumbnailOverlayTimeStatusRenderer', "style")
        if thumbnailOverlayTimeStatusRenderer_style is not None and thumbnailOverlayTimeStatusRenderer_style == "LIVE":
            result["is_live"] = True    
    # videos or streams
    elif selector_item == "lockupViewModel":
        result["videoId"] = result["contentId"]
        result["title"] = result["metadata"]["lockupMetadataViewModel"]["title"]["content"]
        
        result["is_live"] = False
        thumbnailBadgeViewModel_badgeStyle = safely_get_value_from_key(result, "contentImage", "thumbnailViewModel", "overlays", 0, "thumbnailBottomOverlayViewModel", "badges", 0, "thumbnailBadgeViewModel", "badgeStyle")
        if thumbnailBadgeViewModel_badgeStyle is not None and thumbnailBadgeViewModel_badgeStyle == 'THUMBNAIL_OVERLAY_BADGE_STYLE_LIVE':
            result["is_live"] = True
    # shorts
    elif selector_item == "shortsLockupViewModel":
        result["videoId"] = result["onTap"]["innertubeCommand"]["reelWatchEndpoint"]["videoId"]
        result["title"] = result["overlayMetadata"]["primaryText"]["content"]
        result["is_live"] = False
        
    return result
    
def safely_get_value_from_key(*args, default=None):
    obj = args[0]
    keys = args[1:]

    for key in keys:
        try:
            obj = obj[key]
        except Exception:
            return default

    return obj   
    
def getDateNow(logging):
    timestamp_now = datetime.now().timestamp()
    date = datetime.fromtimestamp(timestamp_now, logging['tzinfo'])
    dateString = date.strftime(logging['dateFormats']['dateString'])
    dateDBString = date.strftime(logging['dateFormats']['dateDBString'])
    dateFileString = date.strftime(logging['dateFormats']['dateFileString'])
    
    dateNow = {"dateString": dateString, "dateDBString": dateDBString, "dateFileString": dateFileString}
    
    return dateNow    
    
def log(logging, message):
    if logging['enabled'] is True:
        with open(logging['logfilename'], "a", encoding="utf-8") as f:
            f.write(message + "\n")
            f.flush()
