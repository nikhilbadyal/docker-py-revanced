#!/bin/bash

set -o errexit
set -o pipefail
set -o nounset

export PATCH_APPS=youtube,youtube_music
export BUILD_EXTENDED=True
export EXCLUDE_PATCH_YOUTUBE=custom-branding,debugging
export EXCLUDE_PATCH_TWITCH=debug-mode
export EXCLUDE_PATCH_YOUTUBE_EXTENDED=custom-branding-icon-afn-red,custom-branding-icon-afn-blue,custom-branding-icon-revancify,custom-branding-name
export EXCLUDE_PATCH_YOUTUBE_MUSIC_EXTENDED=custom-branding-music-afn-red,custom-branding-music-afn-blue,custom-branding-music-revancify,compact-header
export ALTERNATIVE_YOUTUBE_PATCHES=custom-branding-icon-afn-blue,custom-branding-icon-afn-red,custom-branding-icon-revancify
export ALTERNATIVE_YOUTUBE_MUSIC_PATCHES=custom-branding-music-afn-red,custom-branding-music-afn-blue,custom-branding-music-revancify
