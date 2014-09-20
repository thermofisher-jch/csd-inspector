<%doc>
	Author: Anthony Rodriguez
</%doc>

<%inherit file="base.mako"/>

<html>
	<head>
		<script type="text/javascript">
			// status of report components
			var report_status = '';
			var boxplot_status = '';
			var histogram_status = '';
			var static_url = "${request.static_url('lemontest:static/img/plots')}";
			$(function(){
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

				$('#boxplot_edit_btn').click(function(){
					$('.boxplot_edit_axes').toggleClass('edit_axis_form_show');
				});

				$('#histogram_edit_btn').click(function(){
					$('.histogram_edit_axes').toggleClass('edit_axis_form_show');
				});
			});
		</script>
	</head>
	<div id="blank_error" class="row-fluid" style="display: none; margin-top: 20px;">
		<div class="alert alert-danger" style="text-align: center; margin-bottom: 0px;">
			<h4>Error!</h4>
			<h5>Report does not exist</h5>
			<button id="alert_dismiss" type="button" class="btn btn-danger">Dismiss</button>
		</div>
	</div>
	<div class="reports_page">
		<div class="statistics">
			<div class="">
				<table class="table table-striped table-hover report_filter_table">
					<h4>Filter Parameters</h4>
					<tbody>
						% if filter_obj:
							% if filter_obj.type != "temp":
								<tr>
									<td><strong>Filter Name: </strong></td>
									<td>${filter_obj.name}</td>
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
			<div class="graphs">
				<div class="graphs-table">
					% if report:
						% for graph in report.graphs:
							<div class="graph">
								<div class="graph-left">
									<div class="edit_graph" id="${graph.graph_type}_custom_axes" style="display: none;">

										<div class="" style="display: table-cell; vertical-align: middle;">
											<form class="form-vertical ${graph.graph_type}_edit_axes edit_axes_hidden" style="vertical-align: middle; float: right;" action="${request.route_url('trace_customize_report')}">
												<div class="axis_form">
													<h5 class="control-label">Graph Title</h5>
													<input type="text" style="width: 12em;" placeholder="Graph Title" id="${graph.graph_type}_title" name="${graph.graph_type}_title" value="">
												</div>

												% if graph.graph_type != 'boxplot':
													<div class="axis_form">
														<h5 class="control-label">X Axis</h5>
														<input type="text" style="width: 12em;" placeholder="Label" id="${graph.graph_type}_x_axis_label" name="${graph.graph_type}_label_x" value="">
														<input type="text" style="width: 6em;" placeholder="Lower Bound" id="${graph.graph_type}_x_axis_min" name="${graph.graph_type}_x_axis_min" value="">
														<input type="text" style="width: 6em;" placeholder="Upper Bound" id="${graph.graph_type}_x_axis_max" name="${graph.graph_type}_x_axis_max" value="">
													</div>
												% endif

												<div class="axis_form">
													<h5 class="control-label">Y Axis</h5>
													<input type="text" style="width: 12em;" placeholder="Label" id="${graph.graph_type}_y_axis_label" name="${graph.graph_type}_label_y" value="">
													<input type="text" style="width: 6em;" placeholder="Lower Bound" id="${graph.graph_type}_y_axis_min" name="${graph.graph_type}_y_axis_min" value="">
													<input type="text" style="width: 6em;" placeholder="Upper Bound" id="${graph.graph_type}_y_axis_max" name="${graph.graph_type}_y_axis_max" value="">
												</div>

												<div class="form-group" style="margin-top: 10px;">
													<input class="btn btn-success" type="submit" value="Submit">
													<input type="hidden" name="report"  value="${report.id}">
													<input type="hidden" name="graph_to_update"  value="${graph.graph_type}">
												</div>
											</form>
										</div>

										<div class="edit_axis_btn edit_axis_btn_closed">
											<button class="btn btn-small btn-info pull-right" id="${graph.graph_type}_edit_btn" >Edit Graph</button>
										</div>
									</div>
								</div>

								<div class="graph-right pull-right" style="display: table; width: 800px; height: 600px;">
									<div style="vertical-align: middle; display: table-cell;">
										<img id="${graph.graph_type}_img" alt="${graph.graph_type}" src="${request.static_url('lemontest:static/img/ajax-loader.gif')}" style="display: block; margin: auto;">
									</div>
								</div>
							</div>
						% endfor
					% endif
				</div>
			</div>
		</%block>
	</div>
</html>