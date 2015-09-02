from pyramid.events import subscriber
from pyramid.events import BeforeRender
from pyramid.settings import asbool


@subscriber(BeforeRender)
def add_global(event):
    event['show_test_instance_warning'] = asbool(
        event["request"].registry.settings.get("is_test_instance", "false")
    )
