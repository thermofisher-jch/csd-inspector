from django.views.generic import TemplateView


class CsrfView(TemplateView):
    template_name = "pages/csrf.html"
