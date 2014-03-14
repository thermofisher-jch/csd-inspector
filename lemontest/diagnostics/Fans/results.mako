<!DOCTYPE html>
<html>
<head>
	<link rel="stylesheet" href="/static/css/bootstrap.css"/>
	<style type="text/css">
		.plot {
			max-width: 33%;
			min-width: 200px;
			float: left;
		}
	</style>
</head>
<body>
<div class="container-fluid">
	<div class="row">
	 	% for plot in plots:
		<div class="plot">
			<img src="${plot}" />
		</div>
		% endfor
	</div>
</div>
</body>
</html>