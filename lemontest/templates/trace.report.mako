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
				% for graph in report.graphs:
					<table class="table table-striped table-hover">
						<h4>Graph Data</h4>
						<tbody>
							<tr>
								<td><strong>Time Created: </strong></td>
								<td>${graph.fileprogress.time.strftime('%d %b %Y %H:%M:%S')}</td>
							</tr>
							<tr>
								<td><strong>Column Graphed: </strong></td>
								<td>${graph.column_name}</td>
							</tr>
							<tr>
								<td><strong>Data Points: </strong></td>
								<td>${graph.data_n}</td>
							</tr>
							<tr>
								<td><strong>Graph Type: </strong></td>
								<td>${graph.graph_type}</td>
							</tr>
						</tbody>
					</table>
				% endfor
			</div>
			% for graph in report.graphs:
				<div class="pull-right" style="display: inline-block;">
				<% image = request.static_url('lemontest:static/img/plots/') %>
				<% image += graph.fileprogress.path %>
					<img alt="plot" src='${image}'>
				</div>
			% endfor
		</div>
	</body>
</html>