<%doc>
	Author: Anthony Rodriguez
</%doc>

<%inherit file="base.mako"/>

<html>
	<head>
	</head>
	<body>
		<div class="">
		<% image = request.static_url('lemontest:static/img/plots/') %>
		<% image += isp_loading %>
			<img alt="plot" src='${image}'>
		</div>
	</body>
</html>