<html>
<head>
	<link rel="stylesheet" href="/static/css/bootstrap.css"/>
	<style type="text/css">
		#files {
			font-family: monospace;
		}
	</style>
</head>
<body>

% if errors:
	% for error in errors:
		<h3 class="alert alert-danger">${error}</h3>
	% endfor
% endif

% if xml_path:
	<h3>Run Log:${xml_path}</h3>
	% if warnings:
		<h3 class="alert alert-warning">${len(warnings)} warnings</h3>
		<table class="table table-striped table-hover">
			<thead>
				<tr>
					% for head in headers:
						<th>${head}</th>
					% endfor
				</tr>
			</thead>
			<tbody>
			% for warn in warnings:
				<tr>
					% for col in warn:
						<td>${col}</td>
					% endfor
				</tr>
			% endfor
			</tbody>
		</table>

	% elif not errors:
		<h3 class="alert alert-success">All is well, no warnings!</h3>
	% endif
% else:
	<h3 class="alert alert-danger">No run log could be found</h3>
% endif


</body>
</html>