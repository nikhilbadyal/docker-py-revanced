# Docker-Py-ReVanced

A little python script that will help you in building [Revanced apps.](#note)

## Build

You can use any of the following methods to build.

<details>
<summary>🚀In GitHub(Recommended)</summary>

1. Fork the project.
2. Add following secrets to the repo.
    1. _GH_TOKEN_ (**required**) - GitHub token so that it can upload to GitHub
       after building.
    2. _VT_API_KEY_ (optional) - required only if you want Virus total scan.
    3. _ENVS_ (optional) - required only if you want to cook specific apps/versions.
        <details>
          <summary>Samples</summary>

          - **`GitHub Secrets`** might look like this
           ![img.png](img.png)

          - **`ENVS`** secret might look like this
            ```
            PATCH_APPS=youtube_music,twitter
            EXCLUDE_PATCH_YOUTUBE=custom-branding
            EXCLUDE_PATCH_YOUTUBE_MUSIC=yt-music-is-shit
            YOUTUBE_VERSION=67.68.69
            YOUTUBE_MUSIC_VERSION=latest
            TWITTER_VERSION=0.2.2
            REDDIT_VERSION=latest
            TIKTOK_VERSION=latest
            WARNWETTER_VERSION=latest
            ```

       </details>

3. Go to actions tab. Select `Build Revanced APK`.Click on `Run Workflow`.

</details>

<details>
<summary>🐳With Docker</summary>

1.  Install Docker
2.  Run script with
    ```shell
    docker-compose up
    ```

</details>

<details>
<summary>🫠Without Docker</summary>

1.  Install Java17 (zulu preferred)
2.  Install Python
3.  Create virtual environment
    ```
    python3 -m venv venv
    ```
4.  Activate virtual environment
    ```
    source venv/bin/activate
    ```
5.  Install Dependencies with
    ```
    pip install -r requirements.txt
    ```
6.  Run the script with
    ```
    python python main.py
    ```
</details>


### Note

By default, script build the version as recommended by Revanced team.

1. Supported values for **_<REVANCED_APPS_NAME>_** are :
   1. youtube
   2. youtube_music
   3. twitter
   4. reddit
   5. tiktok
   6. warnwetter
2. If you want to build a specific version . Add `version` in `environment` in the
   format
   ```
   <APPNAME>_VERSION=<VERSION>
   ```
   Example:
   ```
   YOUTUBE_VERSION=17.31.36
   YOUTUBE_MUSIC_VERSION=X.X.X
   TWITTER_VERSION=X.X.X
   REDDIT_VERSION=X.X.X
   TIKTOK_VERSION=X.X.X
   WARNWETTER_VERSION=X.X.X
   ```
3. If you want to a `latest` version, whatever latest is available(including beta) .
   Add `latest` in `environment` in the format
   ```
   <APPNAME>_VERSION=latest
   ```
   Example:
   ```
   YOUTUBE_VERSION=latest
   YOUTUBE_MUSIC_VERSION=latest
   TWITTER_VERSION=latest
   REDDIT_VERSION=latest
   TIKTOK_VERSION=latest
   WARNWETTER_VERSION=latest
   ```
4. By default, it will build [all](#note) build app supported by Revanced team. If you
   don't
   want to waste time and build only few apps. Add the apps you want to build in
   `environment` in the format
   ```
   PATCH_APPS=<REVANCED_APPS_NAME>
   ```
   Example:
   ```
   PATCH_APPS=youtube,twitter,reddit
   ```
5. If you don't want to use default keystore. You can provide your own by placing it
   inside `apks` folder. And adding the name of `keystore-file` in `environment` like
   ```
    KEYSTORE_FILE_NAME=revanced.keystore
   ```
6. If you want to exclude any patch. Set comma separated patch in `environment` in
   the format
   ```
   EXCLUDE_PATCH_<REVANCED_APPS_NAME>=<PATCH_TO_EXCLUDE-1,PATCH_TO_EXCLUDE-2>
   ```
   Example:
   ```
    EXCLUDE_PATCH_YOUTUBE=custom-branding,hide-get-premium
    EXCLUDE_PATCH_YOUTUBE_MUSIC=yt-music-is-shit
   ```

Thanks to [@aliharslan0](https://github.com/aliharslan0/pyrevanced) for his work.
