<!DOCTYPE html>
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

<div class="container">
<h4>Chef versions</h4>
<p>
	Serial Number: ${serial}
</p>
<table class="table table-striped table-hover">
	<thead>
		<tr>
			<th>Name</th>
			<th>Version</th>
		</tr>
	</thead>
	<tbody>
	% for header, value in versions:
		<tr>
			<td>${header}</td>
			<td>${value}</td>
		</tr>
	% endfor
	</tbody>
</table>
</div>

</body>
</html>