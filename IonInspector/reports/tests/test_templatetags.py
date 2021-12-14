from django.test import SimpleTestCase
from django.template import Context, Template, engines


class HrefifyTemplateTagTest(SimpleTestCase):
    def test_noop_case(self):
        context = Context({"title": "my_title:true-true"})
        template_to_render = Template(
            "{% load reports_templatetags %}",
            "{% title|hrefify %}",
            engine=engines["Inspector"],
        )
        rendered_template = template_to_render.render(context)
        self.assertInHTML("<h1>my_title:true-true</h1>", rendered_template)

    def test_blank_href(self):
        context = Context({"title": None})
        template_to_render = Template(
            "{% load reports_templatetags %}",
            "{% title|hrefify %}",
            engine=engines["Inspector"],
        )
        rendered_template = template_to_render.render(context)

    def test_simple_period(self):
        context = Context({"title": "ML4-100._10"})
        template_to_render = Template(
            "{% load reports_templatetags %}",
            "{% title|hrefify %}",
            engine=engines["Inspector"],
        )
        rendered_template = template_to_render.render(context)
        self.assertInHTML("<h1>ML4-100__10</h1>", rendered_template)

    def test_leading_fixup(self):
        context = Context({"title": ":ML4-100_.10"})
        template_to_render = Template(
            "{% load reports_templatetags %}",
            "{% title|hrefify %}",
            engine=engines["Inspector"],
        )
        rendered_template = template_to_render.render(context)
        self.assertInHTML("<h1>x:ML4-100__10</h1>", rendered_template)

    def test_leading_sub_and_fixup(self):
        context = Context({"title": "$.#words"})
        template_to_render = Template(
            "{% load reports_templatetags %}",
            "{% title|hrefify %}",
            engine=engines["Inspector"],
        )
        rendered_template = template_to_render.render(context)
        self.assertInHTML("<h1>x___words</h1>", rendered_template)

    def test_type_coercion(self):
        context = Context({"title": -901.8})
        template_to_render = Template(
            "{% load reports_templatetags %}",
            "{% (title|hrefify) %}",
            engine=engines["Inspector"],
        )
        rendered_template = template_to_render.render(context)
        self.assertInHTML("<h1>x-901_8</h1>", rendered_template)
