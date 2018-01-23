from django.views.static import serve


def custom_serve(request, path, document_root=None, show_indexes=False):
    """ Chrome unzips tar.gz files when Content-Encoding == gzip but does not change the extension.
    Removing Content-Encoding on application/x-tar fixes the issue.
    See https://bugs.chromium.org/p/chromium/issues/detail?id=268085 """
    response = serve(request, path, document_root, show_indexes)
    if response['Content-Type'] == "application/x-tar":
        del response["Content-Encoding"]
    return response
