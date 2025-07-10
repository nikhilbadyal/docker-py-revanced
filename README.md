# 🤓Docker-Py-ReVanced

![Docker Pulls](https://img.shields.io/docker/pulls/nikhilbadyal/docker-py-revanced)

A little python script that will help you in building [Revanced](https://revanced.app/) [apps](#any-patch-apps) and sharing them anywhere.

**`Note`** - If you are a root user and want magisk module (Extended). Get them [here](https://github.com/nikhilbadyal/revanced-magisk-module)

 <a id="only-builder-support"></a>This is just a builder for revanced and not a revanced support. Please be
 understanding and refrain from asking about revanced features/bugs. Discuss those on proper relevant forums.

## Pre-Built APKs

You can get pre-built apks [here](https://revanced_apkss.t.me/)

## Facing issues? Click [here](https://github.com/nikhilbadyal/docker-py-revanced/issues/new/choose).<br>
## Build Yourself

You can use any of the following methods to build.

- 🚀 **GitHub** (**_`Recommended`_**)

     1. Click Star to support the project.<br>
       <img src="https://i.imgur.com/FFyXaWY.png" width="400" style="left"><br>
     2. Fork the project.<br>
     <img src="https://i.imgur.com/R5HdByI.png" width="400" style="left"><br>
     3. Add `ENVS` (**optional**) secret to the repo. Required only if you want to cook specific apps/versions.
         <details>
           <summary>🚶Detailed step by step guide</summary>

         - Go to the repo settings and then to actions->secret<br>
           <img src="https://i.imgur.com/Inj82KK.png" width="600" style="left"><br>
         - Add Repository secret<br>
           <img src="https://i.imgur.com/V2Wfx3J.png" width="600" style="left">

        </details>

     4. Go to actions tab. Select `Build & Release`.Click on `Run Workflow`.

        <details>
          <summary>🚶Detailed step by step guide</summary>

         - Go to actions tab<br>
           <img src="https://i.imgur.com/XSCvzav.png" width="600" style="left"><br>
         - Check the status of build, It should look green.<br>
           <img src="https://i.imgur.com/CsJt9W1.png" width="600" style="left">

        </details>

     5. If the building process is successful, you'll get your APKs in the<br>
        <img src="https://i.imgur.com/S5d7qAO.png" width="700" style="left">
     6. Make sure to do below steps once in a while(daily or weekly) to keep the builder bug free.<br>
        <img src="https://i.imgur.com/CbdH7vM.png" width="700" style="left">

- 🐳 **_Docker Compose_**<br>

    1. Install [Docker Desktop](https://www.docker.com/products/docker-desktop/).
    2. Clone the repo
       ```bash
       git clone https://github.com/nikhilbadyal/docker-py-revanced
       ```
    3. cd to the cloned repo
       ```bash
       cd docker-py-revanced
       ```
    4. Update `.env` file if you want some customization(See notes)
    5. Run script with
       ```shell
       docker compose up --build
       ```

- 🐳With Docker

    1. Install Docker or [Docker Desktop](https://www.docker.com/products/docker-desktop/).
       ```bash
       curl -fsSL https://get.docker.com -o get-docker.sh
       sh get-docker.sh
       ```
    2. Run script with
       ```shell
       docker run -v "$(pwd)"/apks:/app/apks/  nikhilbadyal/docker-py-revanced
       ```
       You can pass the below environment variables (See notes) with the `-e` flag or use the `--env-file`
       [flag](https://docs.docker.com/engine/reference/commandline/run/#options).

- 🫠Without Docker

    1. Install Java >= 17
    2. Install Python >= 3.11
    3. Create virtual environment
       ```
       python3 -m venv venv
       ```
    4. Activate virtual environment
       ```
       source venv/bin/activate
       ```
    5. Install Dependencies with
       ```
       pip install -r requirements.txt
       ```
    6. Run the script with
       ```
       python main.py
       ```

## Configurations

### Global Config

| **Env Name**                                             |                     **Description**                     | **Default**                                                                                                           |
|:---------------------------------------------------------|:-------------------------------------------------------:|:----------------------------------------------------------------------------------------------------------------------|
| [PATCH_APPS](#patch-apps)                                |                   Apps to patch/build                   | youtube                                                                                                               |
| [EXISTING_DOWNLOADED_APKS ](#existing-downloaded-apks)   |              Already downloaded clean apks              | []                                                                                                                    |
| [PERSONAL_ACCESS_TOKEN](#personal-access-token)          |                 Github Token to be used                 | None                                                                                                                  |
| DRY_RUN                                                  |                      Do a dry run                       | False                                                                                                                 |
| [~~GLOBAL_CLI_DL*~~](#global-resources)                  | DL for CLI to be used for patching apps.(Disabled Temp) | [Revanced CLI](https://github.com/revanced/revanced-cli)                                                              |
| [GLOBAL_PATCHES_DL*](#global-resources)                  |      DL for Patches to be used for patching apps.       | [Revanced Patches](https://github.com/revanced/revanced-patches)                                                      |
| [GLOBAL_SPACE_FORMATTED_PATCHES*](#global-resources)     |          Whether patches are space formatted.           | True                                                                                                                  |
| [GLOBAL_KEYSTORE_FILE_NAME*](#global-keystore-file-name) |          Key file to be used for signing apps           | [Builder's own key](https://github.com/nikhilbadyal/docker-py-revanced/blob/main/apks/revanced.keystore)              |
| [GLOBAL_OLD_KEY*](#global-keystore-file-name)            |    Whether key was generated with cli v4(new) or not    | <br/>[Builder's v3(old) own key](https://github.com/nikhilbadyal/docker-py-revanced/blob/main/apks/revanced.keystore) |
| [GLOBAL_OPTIONS_FILE*](#global-options-file)             |                 Options file to be used                 | [Builder's default file](https://github.com/nikhilbadyal/docker-py-revanced/blob/main/apks/options.json)              |
| [GLOBAL_ARCHS_TO_BUILD*](#global-archs-to-build)         |            Arch to keep in the patched apk.             | All                                                                                                                   |
| REDDIT_CLIENT_ID                                         |          Reddit Client ID to patch reddit apps          | None                                                                                                                  |
| [TELEGRAM_CHAT_ID](#telegram-support)                    |               Receiver in Telegram upload               | None                                                                                                                  |
| [TELEGRAM_BOT_TOKEN](#telegram-support)                  |             APKs Sender for Telegram upload             | None                                                                                                                  |
| [TELEGRAM_API_ID](#telegram-support)                     |            Used for telegram Authentication             | None                                                                                                                  |
| [TELEGRAM_API_HASH](#telegram-support)                   |            Used for telegram Authentication             | None                                                                                                                  |
| [EXTRA_FILES](#extra-files)                              |       Extra files apk to upload in GitHub upload.       | None                                                                                                                  |
| [APPRISE_URL](#apprise)                                  |                      Apprise URL .                      | None                                                                                                                  |
| [APPRISE_NOTIFICATION_TITLE](#apprise)                   |              Apprise Notification Title .               | None                                                                                                                  |
| [APPRISE_NOTIFICATION_BODY](#apprise)                    |               Apprise Notification Body .               | None                                                                                                                  |
| MAX_RESOURCE_WORKERS                                     |        Maximum workers for downloading resources        | 3                                                                                                                     |
| MAX_PARALLEL_APPS                                        |      Maximum number of apps to process in parallel      | 4                                                                                                                     |
| DISABLE_CACHING                                          |          Disable download and resource caching          | False                                                                                                                 |

`*` - Can be overridden for individual app.
### App Level Config

| Env Name                                                      |                                             Description                                              | Default                        |
|:--------------------------------------------------------------|:----------------------------------------------------------------------------------------------------:|:-------------------------------|
| [~~**APP_NAME**_CLI_DL~~](#global-resources)                  |                   DL for CLI to be used for patching **APP_NAME**.(Disabled Temp)                    | GLOBAL_CLI_DL                  |
| [**APP_NAME**_PATCHES_DL](#global-resources)                  | DL for Patches to be used for patching **APP_NAME**. Supports multiple bundles via comma separation. | GLOBAL_PATCHES_DL              |
| [**APP_NAME**_SPACE_FORMATTED_PATCHES](#global-resources)     |                         Whether patches are space formatted.   **APP_NAME**.                         | GLOBAL_SPACE_FORMATTED_PATCHES |
| [**APP_NAME**_KEYSTORE_FILE_NAME](#global-keystore-file-name) |                            Key file to be used for signing **APP_NAME**.                             | GLOBAL_KEYSTORE_FILE_NAME      |
| [**APP_NAME**_OLD_KEY](#global-keystore-file-name)            |     Whether key used was generated with cli > v4(new) <br/><br/>**APP_NAME**.      <br/>   <br/>     | GLOBAL_OLK_KEY                 |
| [**APP_NAME**_ARCHS_TO_BUILD](#global-archs-to-build)         |                              Arch to keep in the patched **APP_NAME**.                               | GLOBAL_ARCHS_TO_BUILD          |
| [**APP_NAME**_EXCLUDE_PATCH**](#custom-exclude-patching)      |                           Patches to exclude while patching  **APP_NAME**.                           | []                             |
| [**APP_NAME**_INCLUDE_PATCH**](#custom-include-patching)      |                           Patches to include while patching  **APP_NAME**.                           | []                             |
| [**APP_NAME**_VERSION](#app-version)                          |                              Version to use for download for patching.                               | Recommended by patch resources |
| [**APP_NAME**_PACKAGE_NAME***](#any-patch-apps)               |                                Package name of the app to be patched                                 | None                           |
| [**APP_NAME**_DL_SOURCE***](#any-patch-apps)                  |                           Download source of any of the supported scrapper                           | None                           |
| [**APP_NAME**_DL***](#app-dl)                                 |                                  Direct download Link for clean apk                                  | None                           |

`**` - By default all patches for a given app are included.<br>
`**` - Can be used to included universal patch.<br>
`***` - Can be used for unavailable apps in the repository (unofficial apps).

## Note

1. <a id="any-patch-apps"></a>**Officially** Supported values for **APP_NAME**** are :

    - [youtube](https://www.apkmirror.com/apk/google-inc/youtube/)
    - [youtube_music](https://www.apkmirror.com/apk/google-inc/youtube-music/)
    - [photos](https://www.apkmirror.com/apk/google-inc/photos)
    - [twitter](https://www.apkmirror.com/apk/twitter-inc/twitter/)
    - [reddit](https://www.apkmirror.com/apk/redditinc/reddit/)
    - [tiktok](https://www.apkmirror.com/apk/tiktok-pte-ltd/tik-tok-including-musical-ly/)
    - [warnwetter](https://www.apkmirror.com/apk/deutscher-wetterdienst/warnwetter/)
    - [spotify](https://spotify.en.uptodown.com/android)
    - [nyx-music-player](https://nyx-music-player.en.uptodown.com/android)
    - [icon_pack_studio](https://www.apkmirror.com/apk/smart-launcher-team/icon-pack-studio/)
    - [ticktick](https://www.apkmirror.com/apk/appest-inc/ticktick-to-do-list-with-reminder-day-planner/)
    - [twitch](https://www.apkmirror.com/apk/twitch-interactive-inc/twitch/)
    - [hex-editor](https://m.apkpure.com/hex-editor/com.myprog.hexedit)
    - [windy](https://www.apkmirror.com/apk/windy-weather-world-inc/windy-wind-weather-forecast/)
    - [my-expenses](https://my-expenses.en.uptodown.com/android)
    - [backdrops](https://backdrops.en.uptodown.com/android)
    - [expensemanager](https://apksos.com/app/com.ithebk.expensemanager)
    - [tasker](https://www.apkmirror.com/apk/joaomgcd/tasker-crafty-apps-eu/)
    - [irplus](https://irplus.en.uptodown.com/android)
    - [vsco](https://www.apkmirror.com/apk/vsco/vsco-cam/)
    - [meme-generator-free](https://meme-generator-free.en.uptodown.com/android)
    - [nova_launcher](https://www.apkmirror.com/apk/teslacoil-software/nova-launcher/)
    - [netguard](https://www.apkmirror.com/apk/marcel-bokhorst/netguard-no-root-firewall/)
    - [instagram](https://www.apkmirror.com/apk/instagram/instagram-instagram/)
    - [inshorts](https://www.apkmirror.com/apk/inshorts-formerly-news-in-shorts/)
    - [messenger](https://www.apkmirror.com/apk/facebook-/messenger/)
    - [grecorder](https://opnemer.en.uptodown.com/android)
    - [trakt](https://www.apkmirror.com/apk/trakt/trakt/)
    - [candyvpn](https://www.apkmirror.com/apk/liondev-io/candylink-vpn/)
    - [sonyheadphone](https://www.apkmirror.com/apk/sony-corporation/sony-headphones-connect/)
    - [androidtwelvewidgets](https://m.apkpure.com/android--widgets-twelve/com.dci.dev.androidtwelvewidgets)
    - [yuka](https://yuka.en.uptodown.com/android)
    - [relay](https://www.apkmirror.com/apk/dbrady/relay-for-reddit-/)
    - [boost](https://www.apkmirror.com/apk/ruben-mayayo/boost-for-reddit/)
    - [rif](https://www.apkmirror.com/apk/talklittle/reddit-is-fun/)
    - [sync](https://www.apkmirror.com/apk/red-apps-ltd/sync-for-reddit/)
    - [infinity](https://www.apkmirror.com/apk/docile-alligator/infinity-for-reddit/)
    - [slide](https://www.apkmirror.com/apk/haptic-apps/slide-for-reddit/)
    - [bacon](https://www.apkmirror.com/apk/onelouder-apps/baconreader-for-reddit/)
    - [microg](https://github.com/inotia00/mMicroG/releases/)
    - [pixiv](https://www.apkmirror.com/apk/pixiv-inc/pixiv/)
    - [strava](https://www.apkmirror.com/apk/strava-inc/strava-running-and-cycling-gps/)
    - [solidexplorer](https://www.apkmirror.com/apk/neatbytes/solid-explorer-beta/)
    - [lightroom](https://www.apkmirror.com/apk/adobe/lightroom/)
    - [duolingo](https://www.apkmirror.com/apk/duolingo/duolingo-duolingo/)
    - [musically](https://www.apkmirror.com/apk/tiktok-pte-ltd/tik-tok-including-musical-ly/)
    - [photomath](https://www.apkmonk.com/app/com.microblink.photomath/)
    - [joey](https://www.apkmonk.com/app/o.o.joey/)
    - [vanced](https://www.apkmirror.com/apk/team-vanced/youtube-vanced/)
    - [spotify-lite](https://www.apkmonk.com/app/com.spotify.lite/)
    - [digitales](https://www.apkmonk.com/app/at.gv.oe.app/)
    - [scbeasy](https://www.apkmonk.com/app/com.scb.phone/)
    - [reddit-news](https://m.apkpure.com/relay-for-reddit/reddit.news)
    - [finanz-online](https://apksos.com/app/at.gv.bmf.bmf2go)
    - [tumblr](https://www.apkmirror.com/apk/tumblr-inc/tumblr/)
    - [fitnesspal](https://www.apkmirror.com/apk/myfitnesspal-inc/calorie-counter-myfitnesspal/)
    - [facebook](https://www.apkmirror.com/apk/facebook-2/facebook/)
    - [lemmy-sync](https://www.apkmirror.com/apk/sync-apps-ltd/sync-for-lemmy/)
    - [amazon](https://www.apkmirror.com/apk/amazon-mobile-llc/amazon-shopping/)
    - [bandcamp](https://www.apkmirror.com/apk/bandcamp-inc/bandcamp/)
    - [magazines](https://www.apkmirror.com/apk/bandcamp-inc/bandcamp/)
    - [winrar](https://www.apkmirror.com/apk/rarlab-published-by-win-rar-gmbh/rar/)
    - [soundcloud](https://www.apkmirror.com/apk/soundcloud/soundcloud-soundcloud/)
    - [stocard](https://www.apkmirror.com/apk/stocard-gmbh/stocard-rewards-cards-wallet/)
    - [willhaben](https://www.apkmirror.com/apk/willhaben/willhaben/)
    - [proton-mail](https://www.apkmirror.com/apk/proton-technologies-ag/protonmail-encrypted-email/)

    <br>`**` - You can also patch any other app which is **not** supported officially.To do so, you need to provide
   few more inputs to the tool which are mentioned below. These config will override the sources config from the tool.
   ```ini
   <APP_NAME>_DL_SOURCE=<apk-link-to-any-of-the-suppored-scrapper>
   <APP_NAME>_PACKAGE_NAME=<package-name-of-the-application>
   ```
   You can also provide DL to the clean apk instead of providing DL_SOURCES as mentioned in this [note](#app-dl).
   Supported Scrappers are:
   1. APKMIRROR - Supports downloading any available version
        1. Link Format - https://www.apkmirror.com/apk/<organisation-name>/app-name/
        2. Example Link - https://www.apkmirror.com/apk/google-inc/youtube/
   2. UPTODOWN - Supports downloading any available version
        1. Link Format - https://<app-name>.en.uptodown.com/android
        2. Example Link - https://spotify.en.uptodown.com/android
   3. APKSOS - Supports downloading any available version
       1. Link Format - https://apksos.com/download-app/<package-name>
       2. Example Link - https://apksos.com/download-app/com.expensemanager
   4. APKPURE - Supports downloading any available version
       1. Link Format - https://apkpure.net/-/<package-name>
       2. Example Link - https://apkpure.net/-/com.google.android.youtube
   5. APKMonk - Supports downloading any available version
       1. Link Format - https://www.apkmonk.com/app/<package-name>/
       2. Example Link - https://www.apkmonk.com/app/<package-name>/
   6. APKEEP - Support downloading using [APKEEP](https://github.com/EFForg/apkeep)
      1. Link Format - apkeep
      2. Example Link - apkeep
      Note - You need to provide APKEEP_EMAIL and APKEEP_TOKEN in the **DOCKER_PY_REVANCED_SECRETS** Github Secrets.

   <br>Please verify the source of original APKs yourself with links provided. I'm not responsible for any damage
    caused.If you know any better/safe source to download clean. Open a discussion.

2. By default, script build the latest version mentioned in `patches.json` file.
3. Remember to download the **_Microg_**. Otherwise, you may not be able to open YouTube/YouTube Music.
4. <a id="patch-apps"></a>By default, tool will build only `youtube,youtube_music`. To build other apps supported by patching
   resources.Add the apps you want to build in `.env` file or in `ENVS` in `GitHub secrets` in the format
   ```ini
   PATCH_APPS=<APP_NAME>
   ```
   Example:
   ```ini
   PATCH_APPS=youtube,twitter,reddit
   ```
   Tip - If for some reason you want to patch app but want to go through all this .env while running you can enter app
   name in <img src="https://i.imgur.com/DwhBH9H.png" width="300" style="left"><br> to be patched box.
5. <a id="existing-downloaded-apks"></a>If APKMirror or other apk sources are blocked in your region or script
   somehow is unable to download from apkmirror. You can download apk manually from any source. Place them in
   `/apks` directory and provide environment variable in `.env` file or in `ENVS` in `GitHub secrets`(Recommended)
   in the format.
   ```dotenv
    EXISTING_DOWNLOADED_APKS=<Comma,Seperate,App,Name>
   ```
   Example:
   ```dotenv
    EXISTING_DOWNLOADED_APKS=youtube,youtube_music
   ```
   If you add above. Script will not download the `youtube` & `youtube_music`apk from internet and expects an apk in
   `/apks` folder with **same** name.
6. <a id="personal-access-token"></a>If you run script again & again. You might hit GitHub API limit. In that case
   you can provide your Personal GitHub Access Token in `.env` file or in `ENVS` in `GitHub secrets` (Recommended)
   in the format -
   ```dotenv
    PERSONAL_ACCESS_TOKEN=<PAT>
   ```
7. <a id="global-resources"></a>You can provide Direct download to the resource to used for patching apps `.env` file
   or in `ENVS` in `GitHub secrets` (Recommended) in the format -
   ```dotenv
    GLOBAL_CLI_DL=https://github.com/revanced/revanced-cli
    GLOBAL_PATCHES_DL=https://github.com/revanced/revanced-patches
   ```
   Resources downloaded from envs and will be used for patching for any **APP_NAME**.
   Unless provided different resource for the individual app.<br><br>
   Tool also support resource config at app level. You can patch A app with X resources while patching B with Y
   resources.
   This can be done by providing Direct download link for resources for app.<br>
   Example:
   ```dotenv
    YOUTUBE_CLI_DL=https://github.com/inotia00/revanced-cli
    YOUTUBE_PATCHES_DL=https://github.com/inotia00/revanced-patches
   ```
   With the config tool will try to patch YouTube with resources from inotia00 while other global resource will used
   for patching other apps.<br>

      **Multi-Patching Support**: You can now use multiple patch bundles from different creators for the same app:
   ```dotenv
    # Comma-separated URLs
    YOUTUBE_PATCHES_DL=https://github.com/ReVanced/revanced-patches,https://github.com/indrastorm/Dropped-patches
   ```
   The tool will download all specified patch bundles and apply them together using the ReVanced CLI's multiple `-p` argument support.<br>
   If you have want to provide resource locally in the apks folder. You can specify that by mentioning filename
   prefixed with `local://`.<br>
   _Note_ - The link provided must be DLs. Unless they are from GitHub.<br>
   _Note_ - If your patches resource are available on GitHub and you want to select latest resource without excluding
    pre-release you can add `latest-prerelease` to the URL.
    Example:
   ```dotenv
    YOUTUBE_PATCHES_DL=https://github.com/inotia00/revanced-patches/releases/latest-prerelease
   ```
   For above example tool while selecting latest patches will consider pre-releases/beta too.
    ```dotenv
    YOUTUBE_PATCHES_DL=https://github.com/inotia00/revanced-patches/releases/latest
   ```
   For above example tool while selecting latest patches will exclude any pre-release/beta ie. will consider only
    stable releases..<br>
   _Note_ - Some of the patch source like inotia00 still provides **-** separated patches while revanced shifted to
   Space formatted patches. Use `SPACE_FORMATTED_PATCHES` to define the type of patches.

8. <a id="global-keystore-file-name"></a>If you don't want to use default keystore. You can provide your own by
   placing it inside `apks` folder. And adding the name of `keystore-file` in `.env` file or in `ENVS` in `GitHub
   secrets` (Recommended) in the format
   ```dotenv
    GLOBAL_KEYSTORE_FILE_NAME=revanced.keystore
   ```
   Tool also support providing secret key at app level. You can sign A app with X key while signing B with Y
   key.<br>
    Example:
   ```dotenv
    YOUTUBE_KEYSTORE_FILE_NAME=youtube.keystore
   ```
   Note - If you are using your own keystore.And it was generated with cli > v4 Add
   Example:
   ```dotenv
    GLOBAL_OLD_KEY=False
   ```
   if you are using different key for different apps. You need to specify at app level.
    ```dotenv
    YOUTUBE_OLD_KEY=False
   ```
9. <a id="global-options-file"></a>If you don't want to use default options.json file. You can provide your own by
   placing it inside `apks` folder. And adding the name of `options-file` in `.env` file or in `ENVS` in `GitHub
   secrets` (Recommended) in the format
   ```dotenv
    GLOBAL_OPTIONS_FILE=my_options.json
   ```
   Tool also support providing secret key at app level. You can sign A app with X key while signing B with Y
   key.<br>
    Example:
   ```dotenv
    YOUTUBE_OPTIONS_FILE=my_cool_yt_options.json
   ```
10. <a id="global-archs-to-build"></a>You can build only for a particular arch in order to get smaller apk files.This
    can be done with by adding comma separated `ARCHS_TO_BUILD` in `ENVS` in `GitHub secrets` (Recommended) in the
    format.
    ```dotenv
     GLOABAL_ARCHS_TO_BUILD=arm64-v8a,armeabi-v7a
    ```
    Tool also support configuring at app level.<br>

    Example:
    ```dotenv
     YOUTUBE_ARCHS_TO_BUILD=arm64-v8a,armeabi-v7a
    ```
    _Note_ -
    1. Possible values are: `armeabi-v7a`,`x86`,`x86_64`,`arm64-v8a`
    2. Make sure the patching resource(CLI) support this feature.
11. <a id="extra-files"></a>If you want to include any extra file to the Github upload. Set comma arguments
     in `.env` file or in `ENVS` in `GitHub secrets` (Recommended) in the format
    ```ini
    EXTRA_FILES=<url>@<appName>.apk
    ```
    Example:
    ```dotenv
     EXTRA_FILES=https://github.com/inotia00/mMicroG/releases/latest@mmicrog.apk
    ```
12. <a id="custom-exclude-patching"></a>If you want to exclude any patch. Set comma separated patch in `.env` file
    or in `ENVS` in `GitHub secrets` (Recommended) in the format
    ```ini
    <APP_NAME>_EXCLUDE_PATCH=<PATCH_TO_EXCLUDE-1,PATCH_TO_EXCLUDE-2>
    ```
    Example:
    ```dotenv
     YOUTUBE_EXCLUDE_PATCH=custom-branding,hide-get-premium
     YOUTUBE_MUSIC_EXCLUDE_PATCH=yt-music-is-shit
    ```
    Note -
    1. **All** the patches for an app are **included** by default.<br>
    2. Revanced patches are provided as space separated, make sure you type those **-** separated here.
    It means a patch named _**Hey There**_ must be entered as **_hey-there_** in the above example.
13. <a id="custom-include-patching"></a>If you want to include any universal patch. Set comma separated patch in `.env`
    file or in `ENVS` in `GitHub secrets` (Recommended) in the format
    ```ini
    <APP_NAME>_INCLUDE_PATCH=<PATCH_TO_EXCLUDE-1,PATCH_TO_EXCLUDE-2>
    ```
    Example:
    ```dotenv
     YOUTUBE_INCLUDE_PATCH=remove-screenshot-restriction
    ```
    Note -
    1. Revanced patches are provided as space separated, make sure you type those **-** separated here.
       It means a patch named _**Hey There**_ must be entered as **_hey-there_** in the above example.
14. <a id="app-version"></a>If you want to build a specific version or latest version. Add `version` in `.env` file
    or in `ENVS` in `GitHub secrets` (Recommended) in the format
    ```ini
    <APP_NAME>_VERSION=<VERSION>
    ```
    Example:
    ```ini
    YOUTUBE_VERSION=17.31.36
    YOUTUBE_MUSIC_VERSION=X.X.X
    TWITTER_VERSION=latest
    ```
15. <a id="app-dl"></a>If you have your personal source for apk to be downloaded. You can also provide that and tool
    will not scarp links from apk sources.Add `dl` in `.env` file or in `ENVS` in `GitHub secrets` (Recommended) in
    the format
    ```ini
    <APP_NAME>_DL=<direct-app-download>
    ```
    Example:
    ```ini
    YOUTUBE_DL=https://d.apkpure.com/b/APK/com.google.android.youtube?version=latest
    ```
16. <a id="telegram-support"></a>For Telegram Upload.
     1. Set up a telegram channel, send a message to it and forward the message to
        this telegram [bot](https://t.me/username_to_id_bot)
     2. Copy `id` and save it to `TELEGRAM_CHAT_ID`<br>
        <img src="https://i.imgur.com/22UiaWs.png" width="300" style="left"><br>
     3. `TELEGRAM_BOT_TOKEN` - Telegram provides BOT_TOKEN. It works as sender. Open [bot](https://t.me/BotFather) and
        create one copy api key<br>
        <img src="https://i.imgur.com/A6JCyK2.png" width="300" style="left"><br>
     4. `TELEGRAM_API_ID` - Telegram API_ID is provided by telegram [here](https://my.telegram.org/apps)<br>
        <img src="https://i.imgur.com/eha3nnb.png" width="300" style="left"><br>
     5. `TELEGRAM_API_HASH` - Telegram API_HASH is provided by telegram [here](https://my.telegram.org/apps)<br>
        <img src="https://i.imgur.com/7n5k1mp.png" width="300" style="left"><br>
     6. After Everything done successfully a part of the actions secrets of the repository may look like<br>
        <img src="https://i.imgur.com/Cjifz1M.png" width="400">
17. Configuration defined in `ENVS` in `GitHub secrets` will override the configuration in `.env` file. You can use this
    fact to define your normal configurations in `.env` file and sometimes if you want to build something different just
    once. Add it in `GitHub secrets`.<br>
18. Sample Envs<br>
    <img src="https://i.imgur.com/FxOtiGs.png" width="600" style="left">
19. <a id="apprise"></a>[Apprise](https://github.com/caronc/apprise)<br>
    We also have apprise support to upload built apk anywhere.To use apprise. Add belows envs in `.env` file
    or in `ENVS` in `GitHub secrets` (Recommended) in the format
    ```ini
    APPRISE_URL=tgram://bot-token/chat-id
    APPRISE_NOTIFICATION_BODY=What a great Body
    APPRISE_NOTIFICATION_TITLE=What a great title
    ```
