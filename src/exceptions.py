class APKMirrorScrapperFailure(Exception):
    """Failed to scrap icon from apkmirror."""

    pass


class ExtraAssetsFailure(Exception):
    """Failed to scrap icon from apkmirror."""

    pass


class PatchingFailed(Exception):
    """Patching Failed."""

    pass
