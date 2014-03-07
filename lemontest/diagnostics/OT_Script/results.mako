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
<h4>Script Line:</h4>
<pre>${script_line}</pre>
<table class="table table-striped table-hover">
	% for header, value in rows:
		<tr>
			<th>${header}</th>
			<td>${value}</td>
		</tr>
	% endfor
</table>
</div>

</body>
</html>