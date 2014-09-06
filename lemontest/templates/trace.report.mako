<%doc>
	Author: Anthony Rodriguez
</%doc>

<%inherit file="base.mako"/>

<html>
	<head>
		<script type="text/javascript">
		var report_status = '';
		var boxplot_status = '';
		var histogram_status = '';
		var static_url = "${request.static_url('lemontest:static/img/plots')}";
		$(function(){
				// status of report components

				// checks status of report components until done
				var check_for_updates = function(report_id, url) {
					var interval = setInterval(function(){
						$.ajax({
							type: "GET",
							url: url,
							data: {'report_id': report_id}
						}).done(function(data){
							if(data.status == 'found') {
								var data = JSON.parse(data.data);
								var report = data.report;
								var boxplot = data.boxplot;
								var histogram = data.histogram;

								if(update_report(report, boxplot, histogram)) {
									clearInterval(interval);
								}
							}
						});
					}, 1000);
				}

				% if status == 'not_found':
					$('#blank_error').slideDown();
				% else:
					% if report:
						check_for_updates(${report.id}, "${request.route_path('trace_check_report_update')}");
					% endif
				% endif

				$('#alert_dismiss').click(function() {
					$('#blank_error').slideUp();
					window.location.href = ('/');
				});
			});
		</script>
	</head>
	<body class="container-fuild">
		<div id="blank_error" class="row-fluid" style="display: none; margin-top: 20px;">
			<div class="alert alert-danger" style="text-align: center; margin-bottom: 0px;">
				<h4>Error!</h4>
				<h5>Report does not exist</h5>
				<button id="alert_dismiss" type="button" class="btn btn-danger">Dismiss</button>
			</div>
		</div>

		<div class="span6">
			<div class="">
				<table class="table table-striped table-hover report_filter_table">
					<h4>Filter Parameters</h4>
					<tbody>
						% if filter_obj:
							% if filter_obj.type != "temp":
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
						% if report:
							<tr>
								<td><strong>Column Graphed:</strong></td>
								<td>${report.metric_column}</td>
							</tr>
							% for column in report.ordered_columns:
								<tr>
									<td><strong>${column[0]}:</strong></td>
									<td id="${column[0]}">Pending...</td>
								</tr>
							% endfor
						% else:
							<tr>
								<td><strong>Column Graphed:</strong></td>
								<td>None</td>
							</tr>
						% endif
					</tbody>
				</table>
			</div>
		</div>

		<%block name='show_graphs'>
			<div class="" style="float: right;">
				<div class="container-fluid">
					<div class="pull-right" style="display: table; width: 800px; height: 600px;">
						<div style="vertical-align: middle; display: table-cell;">
							<img id="boxplot" alt="boxplot" src="${request.static_url('lemontest:static/img/ajax-loader.gif')}" style="display: block; margin: auto;">
						</div>
					</div>
				</div>

				<div class="container-fluid">
					<div class="pull-right" style="display: table; width: 800px; height: 600px;">
						<div style="vertical-align: middle; display: table-cell;">
							<img id="histogram" alt="histogram" src="${request.static_url('lemontest:static/img/ajax-loader.gif')}" style="display: block; margin: auto;">
						</div>
					</div>
				</div>
			</div>
		</%block>
	</body>
</html>