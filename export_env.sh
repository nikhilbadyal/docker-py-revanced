#!/bin/bash

set -o errexit
set -o pipefail
set -o nounset

export PATCH_APPS=youtube,twitter,reddit,youtube_music
export BUILD_EXTENDED=True
export EXCLUDE_PATCH_YOUTUBE=custom-branding,enable-debugging
export EXCLUDE_PATCH_YOUTUBE_EXTENDED=custom-branding-icon-red,custom-branding-icon-blue,custom-branding-revancify,custom-branding-name,custom-package-name,materialyou,always-autorepeat,overlay-buttons-alternative-icon,enable-wide-searchbar,tablet-mini-player
export EXCLUDE_PATCH_YOUTUBE_MUSIC_EXTENDED=custom-branding-music,custom-branding-music-decipher3114,custom-package-name-music,custom-branding-music-red
export BUILD_OG_BRANDING_YOUTUBE=True
export BRANDING_PATCH=custom-branding-icon-blue
