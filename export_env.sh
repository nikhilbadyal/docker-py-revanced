#!/bin/bash

set -o errexit
set -o pipefail
set -o nounset

export PATCH_APPS=youtube,youtube_music
export BUILD_EXTENDED=True
export EXCLUDE_PATCH_YOUTUBE=custom-branding,debugging
export EXCLUDE_PATCH_TWITCH=debug-mode
export EXCLUDE_PATCH_YOUTUBE_EXTENDED=custom-branding-icon-afn-red,custom-branding-icon-afn-blue,custom-branding-icon-revancify,custom-branding-name
export EXCLUDE_PATCH_YOUTUBE_MUSIC_EXTENDED=custom-branding-music-red,custom-branding-music-revancify,compact-header
export ARCHS_TO_BUILD=arm64-v8a
