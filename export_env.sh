#!/bin/bash

set -o errexit
set -o pipefail
set -o nounset

export PATCH_APPS=youtube,twitter,reddit,youtube_music,spotify
export BUILD_EXTENDED=True
export EXCLUDE_PATCH_YOUTUBE=custom-branding,enable-debugging
export EXCLUDE_PATCH_YOUTUBE_EXTENDED=custom-branding-red,custom-branding-blue,amoled
export EXCLUDE_PATCH_YOUTUBE_MUSIC_EXTENDED=custom-branding-music
