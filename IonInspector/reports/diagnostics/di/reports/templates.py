from dependency_injector import containers, providers
from django.template import engines
from django.template.backends.django import DjangoTemplates


class TemplateEngineContainer(containers.DeclarativeContainer):
    template_engine = providers.Object(engines["Diagnostics"])
