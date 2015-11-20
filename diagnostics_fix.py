from lemontest.models import *
from pyramid.paster import bootstrap

env = bootstrap('/opt/inspector/inspector/production.ini')

diagnostics = DBSession.query(Diagnostic)

def fix_diag():
	for i in diagnostics:
		if i.html:
			transaction.begin()
			i.html = i.html.replace('/opt/lemontest/deployment/files/', '/opt/inspector/archive_files')
			transaction.commit()

	diag = DBSession.query(Diagnostic)
	for i in diag:
		if i.html:
			print i.html

fix_diag()
