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
					$('.boxplot_edit_axes').animate({width: 'toggle'});
				});

				$('#histogram_edit_btn').click(function(){
					$('.histogram_edit_axes').toggle("slide");
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
			<div class="graphs">
				<div class="graphs-table">
					% if report:
						% for graph in report.graphs:
							<div class="graph">
								<div class="graph-left">
									<div class="edit_graph" id="${graph.graph_type}_custom_axes" style="display: none;">
										<div class="${graph.graph_type}_edit_axes edit_axes" style="display: none;">
											<h5 class="label_spacing control-label text-center">${graph.graph_type.capitalize()}</h5>
											<div class="">
												<div class="text-center">
													<h5 class="pull-left label_spacing control-label"> Graph Title </h5>
													<input type="text" class="form-control" style="width: 12em;" name="${graph.graph_type}_title" placeholder="Graph Title" value="">
												</div>

												<div class="text-center">
													<h5 class="pull-left label_spacing control-label"> X Axis </h5>
													<input type="text" class="form-control" style="width: 12em;" name="${graph.graph_type}_label_x" placeholder="X Axis Label" value="">
													<input type="text" class="form-control" style="width: 6em;" name="${graph.graph_type}_x_axis_max" placeholder="Upper Bound" value="">
													<input type="text" class="form-control" style="width: 6em;" name="${graph.graph_type}_x_axis_min" placeholder="Lower Bound" value="">
												</div>

												<div class="text-center">
													<h5 class="pull-left label_spacing control-label"> Y Axis </h5>
													<input type="text" class="form-control" style="width: 12em;" name="${graph.graph_type}_label_y" placeholder="Y Axis Label" value="">
													<input type="text" class="form-control" style="width: 6em;" name="${graph.graph_type}_y_axis_max" placeholder="Upper Bound" value="">
													<input type="text" class="form-control" style="width: 6em;" name="${graph.graph_type}_y_axis_min" placeholder="Lower Bound" value="">
												</div>
											</div>
										</div>

										<div class="pull-right" style="vertical-align: bottom; display: table-cell; padding-left: 5px;">
											<button class="btn btn-small btn-success" id="${graph.graph_type}_edit_btn" >Edit Graph</button>
										</div>
									</div>
								</div>

								<div class="graph-right pull-right" style="display: table; width: 800px; height: 600px;">
									<div style="vertical-align: middle; display: table-cell;">
										<img id="${graph.graph_type}" alt="${graph.graph_type}" src="${request.static_url('lemontest:static/img/ajax-loader.gif')}" style="display: block; margin: auto;">
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