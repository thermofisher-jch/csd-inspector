import os

from django.http import HttpResponse
from django.template import loader, Template, Context, TemplateDoesNotExist
import django.views.static


# Need alphabetical order on dir listings
# django/views/static.py#L102


def directory_index(path, fullpath):
    try:
        t = loader.select_template(
            ["static/directory_index.html", "static/directory_index"]
        )
    except TemplateDoesNotExist:
        t = Template(
            django.views.static.DEFAULT_DIRECTORY_INDEX_TEMPLATE,
            name="Default directory index template",
        )
    files = []
    for f in sorted(os.listdir(fullpath), key=lambda s: s.lower()):
        if not f.startswith("."):
            if os.path.isdir(os.path.join(fullpath, f)):
                f += "/"
            files.append(f)
    c = Context(
        {
            "directory": path + "/",
            "file_list": files,
        }
    )
    return HttpResponse(t.render(c))


django.views.static.directory_index = directory_index
