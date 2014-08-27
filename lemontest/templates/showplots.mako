<%doc>
	Author: Anthony Rodriguez
</%doc>

<%inherit file="base.mako"/>

<html>
	<head>
	</head>
	<body>
		<div class="container-fluid">
			<div class="pull-left" style="display: inline-block; margin-top: 10px; text-align: left;">
				<table class="table table-striped table-hover">
					<h4>Graph Data</h4>
					<tbody>
						<tr>
							<td><strong>Time Created: </strong></td>
							<td>${graph.time.strftime('%d %b %Y %H:%M:%S')}</td>
						</tr>
					</tbody>
				</table>
			</div>
			<div class="pull-right" style="display: inline-block;">
			<% image = request.static_url('lemontest:static/img/plots/') %>
			<% image += graph.path %>
				<img alt="plot" src='${image}'>
			</div>
		</div>
	</body>
</html>