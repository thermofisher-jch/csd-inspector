<%doc>
	Author: Anthony Rodriguez
</%doc>

<%inherit file="base.mako"/>

<html>
	<head>
		<script type="text/javascript">
			var check_for_updates = function(report_id, url) {
				var interval = setInterval(function(){
					$.ajax({
						type: "GET",
						url: url,
						data: {'report_id': report_id}
					}).done(function(data){
// 						if (data.status == "done") {
// 							clearInterval(interval);
// 							console.log(data);
// 							//location.reload();
// 						} else if (data.status == "error"){
// 							clearInterval(interval);
// 							console.log(data);
// 						} else {
// 							console.log(data);
// 						}
						clearInterval(interval);
						console.log(data);
					});
				}, 1000);
			}
	
			$(function(){
				check_for_updates(${report.id}, "${request.route_path('trace_check_report_update')}");
			});
		</script>
	</head>
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
							<tr>
								<td><strong>${column[0]}:</strong></td>
								<td>Pending...</td>
							</tr>
						% endfor
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