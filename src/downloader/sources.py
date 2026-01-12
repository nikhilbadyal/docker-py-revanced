"""APK Sources used."""

APK_MIRROR_BASE_URL = "https://www.apkmirror.com"
APK_MIRROR_BASE_APK_URL = f"{APK_MIRROR_BASE_URL}/apk"
APK_MIRROR_PACKAGE_URL = f"{APK_MIRROR_BASE_URL}/?s=" + "{}"
APK_MIRROR_APK_CHECK = f"{APK_MIRROR_BASE_URL}/wp-json/apkm/v1/app_exists/"
UPTODOWN_SUFFIX = "en.uptodown.com/android"
UPTODOWN_BASE_URL = "https://{}." + UPTODOWN_SUFFIX
APK_PURE_BASE_URL = "https://apkpure.net"
APK_PURE_URL = APK_PURE_BASE_URL + "/-/{}"
APK_PURE_ICON_URL = APK_PURE_BASE_URL + "/search?q={}"
APKS_SOS_BASE_URL = "https://apksos.com/download-app"
APK_SOS_URL = APKS_SOS_BASE_URL + "/{}"
GITHUB_BASE_URL = "https://github.com"
PLAY_STORE_BASE_URL = "https://play.google.com"
PLAY_STORE_APK_URL = f"{PLAY_STORE_BASE_URL}/store/apps/details?id=" + "{}"
APK_COMBO_BASE_URL = "https://apkcombo.com"
APK_COMBO_GENERIC_URL = APK_COMBO_BASE_URL + "/genericApp/{}"
not_found_icon = "https://www.svgrepo.com/download/441689/page-not-found.svg"
revanced_api = "https://api.revanced.app/v4/patches/list"
APK_MONK_BASE_URL = "https://www.apkmonk.com"
APKEEP = "apkeep"
APK_MONK_APK_URL = APK_MONK_BASE_URL + "/app/{}/"
APK_MONK_ICON_URL = "https://cdn.apkmonk.com/logos/{}"
apk_sources = {
    "backdrops": f"{APK_MIRROR_BASE_APK_URL}/backdrops/backdrops-wallpapers/backdrops-wallpapers",
    "bacon": f"{APK_MIRROR_BASE_APK_URL}/onelouder-apps/baconreader-for-reddit/baconreader-for-reddit",
    "boost": f"{APK_MIRROR_BASE_APK_URL}/ruben-mayayo/boost-for-reddit/boost-for-reddit",
    "candyvpn": f"{APK_MIRROR_BASE_APK_URL}/liondev-io/candylink-vpn/candylink-vpn",
    "duolingo": f"{APK_MIRROR_BASE_APK_URL}/duolingo/duolingo-duolingo/duolingo-language-lessons",
    "grecorder": f"{APK_MIRROR_BASE_APK_URL}/google-inc/google-recorder/google-recorder",
    "icon_pack_studio": f"{APK_MIRROR_BASE_APK_URL}/smart-launcher-team/icon-pack-studio/icon-pack-studio",
    "infinity": f"{APK_MIRROR_BASE_APK_URL}/docile-alligator/infinity-for-reddit/infinity-for-reddit",
    "inshorts": (
        f"{APK_MIRROR_BASE_APK_URL}/inshorts-formerly-news-in-shorts/"
        "inshorts-news-in-60-words-2/inshorts-news-in-60-words"
    ),
    "instagram": f"{APK_MIRROR_BASE_APK_URL}/instagram/instagram-instagram/instagram",
    "irplus": f"{APK_MIRROR_BASE_APK_URL}/binarymode/irplus-infrared-remote/irplus-infrared-remote",
    "lightroom": f"{APK_MIRROR_BASE_APK_URL}/adobe/lightroom/lightroom-photo-video-editor",
    "meme-generator-free": f"{APK_MIRROR_BASE_APK_URL}/zombodroid/meme-generator-free/meme-generator",
    "messenger": f"{APK_MIRROR_BASE_APK_URL}/facebook-2/messenger/facebook-messenger",
    "netguard": f"{APK_MIRROR_BASE_APK_URL}/marcel-bokhorst/netguard-no-root-firewall/netguard-no-root-firewall",
    "nova_launcher": f"{APK_MIRROR_BASE_APK_URL}/teslacoil-software/nova-launcher/nova-launcher",
    "nyx-music-player": f"{APK_MIRROR_BASE_APK_URL}/o16i-apps/nyx-music-player/nyx-music-player-offline-mp3",
    "pixiv": f"{APK_MIRROR_BASE_APK_URL}/pixiv-inc/pixiv/pixiv",
    "reddit": f"{APK_MIRROR_BASE_APK_URL}/redditinc/reddit/reddit",
    "relay": f"{APK_MIRROR_BASE_APK_URL}/dbrady/relay-for-reddit-2/relay-for-reddit",
    "rif": f"{APK_MIRROR_BASE_APK_URL}/talklittle/reddit-is-fun/reddit-is-fun",
    "slide": f"{APK_MIRROR_BASE_APK_URL}/haptic-apps/slide-for-reddit/slide-for-reddit",
    "solidexplorer": f"{APK_MIRROR_BASE_APK_URL}/neatbytes/solid-explorer-beta/solid-explorer-file-manager",
    "sonyheadphone": f"{APK_MIRROR_BASE_APK_URL}/sony-corporation/sony-headphones-connect/sony-sound-connect",
    "sync": f"{APK_MIRROR_BASE_APK_URL}/red-apps-ltd/sync-for-reddit/sync-for-reddit",
    "tasker": f"{APK_MIRROR_BASE_APK_URL}/joaomgcd/tasker-crafty-apps-eu/tasker-crafty-apps-eu",
    "ticktick": (
        f"{APK_MIRROR_BASE_APK_URL}/appest-inc/ticktick-to-do-list-with-reminder-day-planner/"
        "ticktickto-do-list-calendar"
    ),
    "tiktok": f"{APK_MIRROR_BASE_APK_URL}/tiktok-pte-ltd/tik-tok/tiktok",
    "musically": f"{APK_MIRROR_BASE_APK_URL}/tiktok-pte-ltd/tik-tok-including-musical-ly/tiktok",
    "trakt": f"{APK_MIRROR_BASE_APK_URL}/trakt/trakt/trakt-tv-shows-movies",
    "twitch": f"{APK_MIRROR_BASE_APK_URL}/twitch-interactive-inc/twitch/twitch-live-streaming",
    "twitter": f"{APK_MIRROR_BASE_APK_URL}/x-corp/twitter/x",
    "vsco": f"{APK_MIRROR_BASE_APK_URL}/vsco/vsco-photo-video-editor-3/vsco-photo-editor",
    "warnwetter": f"{APK_MIRROR_BASE_APK_URL}/deutscher-wetterdienst/warnwetter/warnwetter",
    "windy": (
        f"{APK_MIRROR_BASE_APK_URL}/windy-weather-world-inc/windy-wind-weather-forecast/windy-app-enhanced-forecast"
    ),
    "youtube": f"{APK_MIRROR_BASE_APK_URL}/google-inc/youtube/youtube",
    "youtube_music": f"{APK_MIRROR_BASE_APK_URL}/google-inc/youtube-music/youtube-music",
    "yuka": f"{APK_MIRROR_BASE_APK_URL}/yuka-apps/yuka-food-cosmetic-scan/yuka-food-cosmetic-scanner",
    "strava": f"{APK_MIRROR_BASE_APK_URL}/strava-inc/strava-run-bike-hike-2/strava-run-bike-hike",
    "tumblr": f"{APK_MIRROR_BASE_APK_URL}/tumblr-inc/tumblr/tumblr-social-media-art",
    "fitnesspal": (
        f"{APK_MIRROR_BASE_APK_URL}/myfitnesspal-inc/calorie-counter-myfitnesspal/myfitnesspal-calorie-counter"
    ),
    "facebook": f"{APK_MIRROR_BASE_APK_URL}/facebook-2/facebook/facebook",
    "lemmy-sync": f"{APK_MIRROR_BASE_APK_URL}/sync-apps-ltd/sync-for-lemmy/sync-for-lemmy",
    "xiaomi-wearable": (
        f"{APK_MIRROR_BASE_APK_URL}/beijing-xiaomi-mobile-software-co-ltd/mi-wear-小米穿戴/mi-fitness-xiaomi-wear"
    ),
    "my-expenses": UPTODOWN_BASE_URL.format("my-expenses"),
    "spotify": UPTODOWN_BASE_URL.format("spotify"),
    "joey": UPTODOWN_BASE_URL.format("joey-for-reddit"),
    "scbeasy": UPTODOWN_BASE_URL.format("scb-easy"),
    "expensemanager": UPTODOWN_BASE_URL.format("bishinews-expense-manager"),
    "androidtwelvewidgets": APK_PURE_URL,
    "reddit-news": APK_PURE_URL,
    "hex-editor": APK_PURE_URL,
    "photomath": APK_PURE_URL,
    "spotify-lite": APK_PURE_URL,
    "digitales": APK_PURE_URL,
    "finanz-online": APK_SOS_URL,
    "photos": f"{APK_MIRROR_BASE_APK_URL}/google-inc/photos/google-photos",
    "amazon": f"{APK_MIRROR_BASE_APK_URL}/amazon-mobile-llc/amazon-shopping/amazon-shopping",
    "bandcamp": f"{APK_MIRROR_BASE_APK_URL}/bandcamp-inc/bandcamp/bandcamp",
    "magazines": f"{APK_MIRROR_BASE_APK_URL}/google-inc/google-news/google-news-daily-headlines",
    "winrar": f"{APK_MIRROR_BASE_APK_URL}/rarlab-published-by-win-rar-gmbh/rar/rar",
    "soundcloud": f"{APK_MIRROR_BASE_APK_URL}/soundcloud/soundcloud-soundcloud/soundcloud-the-music-you-love",
    "stocard": f"{APK_MIRROR_BASE_APK_URL}/stocard-gmbh/stocard-rewards-cards-wallet/stocard-rewards-cards-wallet",
    "willhaben": f"{APK_MIRROR_BASE_APK_URL}/willhaben/willhaben/willhaben",
    "proton-mail": (
        f"{APK_MIRROR_BASE_APK_URL}/proton-technologies-ag/protonmail-encrypted-email/proton-mail-encrypted-email"
    ),
    "prime-video": f"{APK_MIRROR_BASE_APK_URL}/amazon-mobile-llc/amazon-prime-video/amazon-prime-video",
    "cricbuzz": (
        f"{APK_MIRROR_BASE_APK_URL}/cricbuzz-com/cricbuzz-live-cricket-scores-news/cricbuzz-live-cricket-scores"
    ),
    "crunchyroll": f"{APK_MIRROR_BASE_APK_URL}/crunchyroll-llc-2/crunchyroll/crunchyroll",
    "threads": f"{APK_MIRROR_BASE_APK_URL}/instagram/threads-an-instagram-app/threads",
    "orf-on": (
        f"{APK_MIRROR_BASE_APK_URL}/orf-osterreichischer-rundfunk/orf-tvthek-video-on-demand-android-tv/orf-on-android-tv"
    ),
    "pandora": f"{APK_MIRROR_BASE_APK_URL}/pandora/pandora-music-podcasts/pandora-music-podcasts",
    "cieid": f"{APK_MIRROR_BASE_APK_URL}/istituto-poligrafico-e-zecca-dello-stato-s-p-a/cieid/cieid",
    "infinity-patreon": (
        f"{APK_MIRROR_BASE_APK_URL}/docile-alligator/infinity-for-reddit-patreon-github-version/infinity-for-reddit-patreon-github-version"
    ),
    "infinity-plus": f"{APK_MIRROR_BASE_APK_URL}/docile-alligator/infinity-for-reddit-plus/infinity-for-reddit",
    "samsung-radio": f"{APK_MIRROR_BASE_APK_URL}/samsung-electronics-co-ltd/samsung-radio/samsung-radio",
    "rakuten-viber": f"{APK_MIRROR_BASE_APK_URL}/viber-media-s-a-r-l/viber/rakuten-viber-messenger",
}
