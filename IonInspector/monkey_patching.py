import os

from django.http import HttpResponse
from django.core.exceptions import ImproperlyConfigured
from django.template import engines, loader, Context, Engine, Template, TemplateDoesNotExist
import django.views.static


# Need alphabetical order on dir listings
# django/views/static.py#L102


def directory_index(path, fullpath):
    try:
        t = loader.select_template(
            ["static/directory_index.html", "static/directory_index"], using="Inspector"
        )
    except TemplateDoesNotExist:
        t = Template(
            django.views.static.DEFAULT_DIRECTORY_INDEX_TEMPLATE,
            name="Default directory index template",
            engine=engines["Inspector"].engine,
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


@staticmethod
def get_default():
    from django.template import engines
    from django.template.backends.django import DjangoTemplates
    django_engines = [engine for engine in engines.all()
                      if isinstance(engine, DjangoTemplates)]
    if len(django_engines) == 1:
        # Unwrap the Engine instance inside DjangoTemplates
        return django_engines[0].engine
    elif len(django_engines) == 0:
        raise ImproperlyConfigured("No DjangoTemplates backend is configured.")
    elif "Inspector" in engines:
        return engines["Inspector"].engine
    else:
        raise ImproperlyConfigured(
            "Several DjangoTemplates backends are configured. "
            "You must name one 'Inspector' explicitly.")


django.template.engine.Engine.get_default = get_default
