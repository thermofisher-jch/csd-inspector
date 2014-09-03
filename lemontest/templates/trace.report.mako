<%doc>
	Author: Anthony Rodriguez
</%doc>

<%inherit file="base.mako"/>

<html>
	<body class="container-fuild">
		<div class="span6">
			<div class="">
				<table class="table table-striped table-hover report_filter_table">
					<h4>Filter Parameters</h4>
					<tbody>
						% if filter.type != "temp":
							<tr>
								<td><strong>Filter Name: </strong></td>
								<td>${filter.name}</td>
							</tr>
							% if filter_params:
								% for key, value in filter_params.items():
									<tr>
										<td><strong>${key}</strong></td>
										<td>${value}</td>
									</tr>
								% endfor
							% endif
						% else:
							<tr>
								<td><strong>Filter Name: </strong></td>
								<td>None</td>
							</tr>
						% endif
					</tbody>
				</table>
			</div>
	
			<div class="">
				<table class="table table-striped table-hover report_stats_table">
					<h4>Report Statistics</h4>
					<tbody>
						<tr>
							<td><strong>Column Graphed:</strong></td>
							<td>${report.metric_column}</td>
						</tr>
						% for column in report.ordered_columns:
							% if report.get_formatted(column[0]):
								<tr>
									<td><strong>${column[0]}:</strong></td>
									<td>${report.get_formatted(column[0])}</td>
								</tr>
							% elif report.graphs and report.graphs[0].fileprogress.status == "Done":
								<tr>
									<td><strong>${column[0]}:</strong></td>
									<td>None</td>
								</tr>
							% else:
								<tr>
									<td><strong>${column[0]}:</strong></td>
									<td>Pending...</td>
								</tr>
							% endif
						% endfor
					</tbody>
				</table>
			</div>
		</div>
		<div class="" style="float: right;">
			% if report.graphs:
				% for graph in report.graphs:
					% if graph.fileprogress.path:
						<div class="container-fluid">
							<div class="pull-right" style="display: inline-block;">
								<% image = request.static_url('lemontest:static/img/plots/') %>
								<% image += graph.fileprogress.path %>
								<img alt="plot" src='${image}'>
							</div>
						</div>
					% endif
				% endfor
			% else:
				<div class="container-fluid">
					<div class="pull-right" style="display: table; width: 800px; height: 600px;">
						<div style="vertical-align: middle; display: table-cell;">
							<img alt="plot" src="${request.static_url('lemontest:static/img/ajax-loader.gif')}" style="display: block; margin: auto;">
						</div>
					</div>
				</div>

				<div class="container-fluid">
					<div class="pull-right" style="display: table; width: 800px; height: 600px;">
						<div style="vertical-align: middle; display: table-cell;">
							<img alt="plot" src="${request.static_url('lemontest:static/img/ajax-loader.gif')}" style="display: block; margin: auto;">
						</div>
					</div>
				</div>
			% endif
		</div>
	</body>
</html>