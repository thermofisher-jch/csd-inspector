<%doc>
	Author: Anthony Rodriguez
</%doc>

<%inherit file="base.mako"/>

<%block name="extra_head">
<script type="text/javascript">

	var global_columns_default = ${show_hide_defaults | n};
	var global_columns_false = ${show_hide_false | n};
	var global_columns = ${metric_columns | n};
	var numeric_filters_obj = ${numeric_filters_json | n};
	var categorical_filters_obj = ${categorical_filters_json | n};
	var extra_filters = 1;

	$(function(){

		var check_for_updates = function(l, fileprogress_id, url, success_url) {
			var interval = setInterval(function(){
				$.ajax({
					type: "GET",
					url: url,
					data: {'fileprogress_id': fileprogress_id, "metric_type": "proton"}
				}).done(function(data){
					if (data.status == "done") {
						clearInterval(interval);
						l.setProgress(data.progress);
						l.stop();
						window.location.href = (success_url + "?file_id=" + data.fileprogress_id + "&metric_type=" + 'proton');
					} else if (data.status == "error"){
						clearInterval(interval);
						l.stop();
						console.log(data);
					} else {
						l.setProgress(data.progress);
					}
				});
			}, 1000);
		}

		// retrieves proper stored session of shown and hidden columns
		% if 'show_hide_session_proton' in request.session and request.session['show_hide_session_proton']:
			var show_hide_session = ${request.session['show_hide_session_proton'] | n};
			show_hide_columns(show_hide_session);
		% else:
			var show_hide_session = global_columns_default;
			show_hide_columns(show_hide_session);
		% endif

		% if 'file_pending_proton' in request.session and request.session['file_pending_proton']:
			var l = Ladda.create(document.getElementById('csv_download'));
			l.start()
			check_for_updates(l, "${request.session['file_pending_proton']}")
		% endif

		add_filters_onload(${search['extra_filters_template']})

		if (has_filters()) {
			$('.filter_drawer').show();
		}

		if ("${search['filterid'] | n}" == "blank") {
			$('.filter_drawer').show();
			$('#blank_error').slideDown();
		} else if ("${filter_name | n}" == "not_found") {
			$('.filter_drawer').show();
			var error_div = document.getElementById('blank_error');
			error_div.getElementsByTagName('h5')[0].innerHTML = "Filter does not exist";
			$('#blank_error').slideDown();
		}

		$('#show_plot_modal').click(function() {
			$('.show_plot_modal').modal('show');
		});

		$('#show_plot').click(function() {
			$('.show_plot_modal').modal('hide');

			var l = Ladda.create(document.getElementById('show_plot_modal'));
			l.start();

			var params = get_csv_params();
			var serialized = $(params).serialize();

			$.ajax({
				type: "GET",
				url: "${request.route_path('trace_request_plot')}" + "?" + serialized,
				data: {"metric_type": "proton", 'graph_column_name': document.getElementById('graph_column_name').value, 'graph_type': document.getElementById('graph_type').value}
			}).done(function(data) {
				if (data.status == 'ok'){
					var fileprogress_id = data.fileprogress_id;
					check_for_updates(l, fileprogress_id, "${request.route_path('trace_check_file_update')}", "${request.route_path('trace_show_report')}");
				} else {
					l.stop();
					console.log(data);
				}
			});
		});

		$('#csv_download').click(function(){
			var l = Ladda.create(this);
			l.start();

			var params = get_csv_params();
			var serialized = $(params).serialize();

			$.ajax({
				type: "GET",
				url: "${request.route_path('trace_request_csv')}" + "?" + serialized,
				data: {"metric_type": "proton"}
			}).done(function(data) {
				if (data.status == 'ok'){
					var fileprogress_id = data.fileprogress_id;
					check_for_updates(l, fileprogress_id, "${request.route_path('trace_check_file_update')}", "${request.route_path('trace_serve_csv')}");
				} else {
					l.stop();
					console.log(data);
				}
			});
		});

		// save filters modal pop up
		$('#save_filters_modal').click(function(){
			$('.saved_filter_modal').modal('show');
		});

		// enable submit
		$('#saved_filter_name').change(function(){
			$('#save_filters').prop('disabled', false);
		});

		// save filters
		$('#save_filters').click(function(){
			save_filters();
			('#saved_filter_name').val == "";
		});

		$('.remove_saved_filter').click(function() {
			document.getElementById('filter_to_delete').value = this.id;
			$('.remove_confirmation').modal('show');
		});

		// dismiss alert
		$('#alert_dismiss').click(function(){
			$('#blank_error').slideUp();
		});

		// clear filters
		$('#clear_filters').click(function(){
			clear_filters();
		});

		// add new numerical filter option
		$("#add_filter").click(function(event){
			add_new_filter();
		});

		// toggles filter options
		$("#filter_toggle").click(function(){
			$(".filter_drawer").slideToggle();
		});

		// show all columns
		$("#show_all").click(function() {
			all_columns(true);
		});

		// hide all columns
		$("#hide_all").click(function() {
			all_columns(false);
		});

		// show hide modal button
		$("#show_hide_btn").click(function(){

			show_hide_session = get_shown_columns();
			show_hide_columns(show_hide_session);

			var csrf_token = '${request.session.get_csrf_token()}';
			$.ajax({
			  type: "POST",
			  url: "${request.route_path('trace_show_hide')}",
			  data: {"csrf_token": csrf_token, "metric_type": "proton", "show_hide_columns_proton": JSON.stringify(show_hide_session)}
			}).done(function(data){
				show_hide_columns(show_hide_session);
			});
		});
	});

</script>
</%block>

<%block name="filter_drawer">
<div class="filter_drawer">
	<%block name="filter">
	<form id="filter_form" class="form-inline" style="display: inline-block" action="${request.path}" method="GET" onclick="get_extra_filter_number()">
		<h4>Current Filter: <span>${search['current_selected_filter']}</span></h4>
		<input type="hidden" id="filterid" value="${search['filterid'] | n}">
		<div class="" style="display: inline-block">
			<!-- BEGIN CATEGORICAL FILTERS -->
			<div class="form-group form-group-column1">
				<div class="some_space_below">
				<h5 class="pull-left label_spacing control-label"> Seq Kit Type </h5>
					<select class="form-control" name="Seq Kit" id="Seq Kit">
						<option value=""></option>
						% for type in seq_kits:
							<option class="filter_option" value="${type}">
								${type}
							</option>
						% endfor
					</select>
				</div>

				<div class="some_space_below">
				<h5 class="pull-left label_spacing control-label"> Chip Type </h5>
					<select class="form-control" name="Chip Type" id="Chip Type">
						<option value=""></option>
						% for type in chip_types:
							<option class="filter_option" value="${type}">
								${type}
							</option>
						% endfor
					</select>
				</div>

				<div class="some_space_below">
				<h5 class="pull-left label_spacing control-label"> Run Type </h5>
					<select class="form-control" name="Run Type" id="Run Type">
						<option value=""></option>
						% for type in run_types:
							<option class="filter_option" value="${type}">
								${type}
							</option>
						% endfor
					</select>
				</div>

				<div class="some_space_below">
				<h5 class="pull-left label_spacing control-label"> Reference Library </h5>
					<select class="form-control" name="Ref Lib" id="Ref Lib">
						<option value=""></option>
						% for type in reference_libs:
							<option class="filter_option" value="${type}">
								${type}
							</option>
						% endfor
					</select>
				</div>
			</div>

			<div class="form-group form-group-column2">
				<div class="some_space_below">
				<h5 class="pull-left label_spacing control-label"> SW Version </h5>
					<select class="form-control" name="SW Version" id="SW Version">
						<option value=""></option>
						% for type in sw_versions:
							<option class="filter_option" value="${type}">
								${type}
							</option>
						% endfor
					</select>
				</div>

				<div class="some_space_below">
				<h5 class="pull-left label_spacing control-label"> TSS Version </h5>
					<select class="form-control" name="TSS Version" id="TSS Version">
						<option value=""></option>
						% for type in tss_versions:
							<option class="filter_option" value="${type}">
								${type}
							</option>
						% endfor
					</select>
				</div>

				<div class="some_space_below">
				<h5 class="pull-left label_spacing control-label"> HW Version </h5>
					<select class="form-control" name="HW Version" id="HW Version">
						<option value=""></option>
						% for type in hw_versions:
							<option class="filter_option" value="${type}">
								${type}
							</option>
						% endfor
					</select>
				</div>

				<div class="some_space_below">
				<h5 class="pull-left label_spacing control-label"> Barcode Set </h5>
					<select class="form-control" name="Barcode Set" id="Barcode Set">
						<option value=""></option>
						% for type in barcode_sets:
							<option class="filter_option" value="${type}">
								${type}
							</option>
						% endfor
					</select>
				</div>
			</div>
			<!-- END CATEGORICAL FILTERS -->

			<!-- BEGIN NUMERICAL FILTERS -->
			<div class="form-group form-group-column3" style="display: block;">
				<div class="some_space_below">
					<h5 class="pull-left label_spacing control-label"> Metric Type </h5>
					<select id="metric_type_filter0" class="form-control" name="metric_type_filter0">
						<option value=""></option>
						% for column in metric_object_type.numeric_columns:
							<option class="filter_option" value="${column[0]}">${column[0]}</option>
						% endfor
					</select>
					<input type="text" class="form-control" style="width: 6em;" name="min_number0" id="min_number0" placeholder="Lower Bound" value="">
					<input type="text" class="form-control" style="width: 6em;" name="max_number0" id="max_number0" placeholder="Upper Bound" value="">
					<input type="hidden" id="extra_filters_template" name="extra_filters_template" value="">

					<button type="button" id="add_filter" class="btn btn-info btn-mini"><span class="icon-white icon-plus"></span></button>
				</div>
				<div id="dynamic_filters" class="some_space_below"></div>
			</div>
			<!-- END NUMERICAL FILTERS -->

			<!-- BEGIN FILTER BUTTONS -->
			<div class="form-group" style="display: block; float: right; margin-top: 10px" id="filter_buttons" style="position: relative;">
				<button type="submit" class="btn btn-info">Apply Filters</button>
				<button id="clear_filters" type="button" class="btn btn-info">Clear Filters</button>
				<button id="save_filters_modal" type="button" class="btn btn-info">Save Filters</button>
			</div>
			<!-- END FILTER BUTTONS -->
		</div>
		<input type="hidden" id="upload_time_sort" name="upload_time_sort" value="" />
		<input type="hidden" id="start_time_sort" name="start_time_sort" value="" />
		<input type="hidden" id="end_time_sort" name="end_time_sort" value="" />

		<%block name="blank_error">
		<div id="blank_error" class="row-fluid" style="display: none; margin-top: 20px;">
			<div class="alert alert-danger" style="text-align: center; margin-bottom: 0px;">
				<h4>Error!</h4>
				<h5>Saved filters must not be blank</h5>
				<button id="alert_dismiss" type="button" class="btn btn-danger">Dismiss</button>
			</div>
		</div>
		</%block>
	</form>
	</%block>

	<%block name="saved_filters_table">
		<div class="saved_filters">
			<h4 style="margin-top: 0px;">Saved Filters</h4>
			<table class="table table-hover table-striped">
				<tbody>
					% for filter in saved_filters.all():
						<tr>
							<td onclick="apply_saved_filter('${filter.id}')"><span>${filter.name}</span></td>
							<td>
								<span class="remove_saved_filter icon-remove pull-right" id="${filter.id}"></span>
							</td>
						</tr>
					% endfor
				</tbody>
			</table>
		</div>
	</%block>
</div>
</%block>

<%block name="buttons">
<div class="row-fluid" style="margin-bottom: 5px;">
	<div class="form-group pull-left">
		<button type="button" class="btn btn-default btn-lg some_space_right" id="filter_toggle">Filter <span class="caret"></span></button>
		<button type="button" class="btn btn-default" data-toggle="modal" data-target=".show_hide_modal">Show / Hide Columns</button>
	</div>

	<div class="form-group pull-right">
		<%block name="plot_this_buttons">
			<button id="show_plot_modal" type="button" class="btn btn-success ladda-button" data-style="expand-left">
				<span class="ladda-label">Plot this data</span>
				<span class="ladda-spinner"></span>
				<span class="ladda-progress"></span>
				<span class="icon-white icon-picture"></span>
			</button>
		</%block>
	
		<%block name="download_csv_form">
			<button id="csv_download" type="button" class="btn btn-success ladda-button" data-style="expand-left">
				<span class="ladda-label">Download CSV</span>
				<span class="ladda-spinner"></span>
				<span class="ladda-progress"></span>
				<span class="icon-white icon-download"></span>
			</button>
		</%block>
	</div>
</div>
</%block>

<%block name="pager">
<div class="row-fluid" style="margin-bottom: 15px;">
	<div class="span9">
		<div class="pagination" style="margin:0;">
			<ul>
				% if metrics.page > 1:
					<li><a href="${page_url(metrics.page-1)}">&laquo;</a></li>
				% else:
					<li class="disabled"><span>&laquo;</span></li>
				% endif

				% for page in pages:
					% if page == metrics.page:
						<li class="active"><span>${page}</span></li>
					% elif page == '..':
						<li class="disabled"><span>${page}</span></li>
					% else:
						<li><a href="${page_url(page)}">${page}</a></li>
					% endif
				% endfor

				% if metrics.page < metrics.page_count:
					<li><a href="${page_url(metrics.page+1)}">&raquo;</a></li>
				% else:
					<li class="disabled"><span>&raquo;</span></li>
				% endif
			</ul>
		</div>
	</div>
	<div class="span3" style="line-height: 30px; text-align: right;">
		${metrics.first_item} to ${metrics.last_item} of ${metrics.item_count}
	</div>
</div>
</%block>

<%block name="metrics_table">
<table class="table table-striped table-hover" id="analysis">
	<thead>
		<tr>
			<th>ID</th>
			<th>Label</th>
			<th>Upload Time <span id="upload_time_sort" onclick="sort_by(this);" class="caret"></span></th>
			% for column in metric_object_type.ordered_columns:
				% if column[0] == "Start Time" or column[0] == "End Time":
					<th class="${column[1]}">${column[0]} <span id="${column[1]}_sort" onclick="sort_by(this);" class="caret"></span></th>
				% else:
					<th class="${column[1]}">${column[0]}</th>
				%endif
			% endfor
		</tr>
	</thead>
	<tbody>
		% for metric in metrics:
			<tr>
				<td><a class="archive_id" href="${request.route_url('check', archive_id=metric.archive.id)}">${metric.archive.id}</a></td>
				<td><a class="archive_label" href="${request.route_url('check', archive_id=metric.archive.id)}">${metric.archive.label}</a></td>
				<td><a title="${metric.archive.time.strftime('%d %b %Y %H:%M:%S')}" class="archive_upload_time" href="${request.route_url('check', archive_id=metric.archive.id)}">${metric.archive.time.strftime('%d %b %Y')}</a></td>
				% for column in metric.ordered_columns:
					% if (column[1] == 'start_time' or column[1] == 'end_time') and metric.get_formatted(column[0]):
						<td title="${metric.get_formatted(column[0]).strftime('%d %b %Y %H:%M:%S')}" class="${column[1]}"><a href="${request.route_url('check', archive_id=metric.archive.id)}">${metric.get_formatted(column[0]).strftime('%d %b %Y')}</a></td>
					% else:
						<td class="${column[1]}"><a href="${request.route_url('check', archive_id=metric.archive.id)}">${metric.get_formatted(column[0])}</a></td>
					% endif
				% endfor
			</tr>
		% endfor
	</tbody>
</table>
</%block>

<%block name="hide_show_modal">
<div class="modal fade show_hide_modal" tabindex="-1" role="dialog" aria-labelledby="show_hide_modal" aria-hidden="true">
	<div class="modal-dialog modal-lg">
		<div class="modal-content">
			<div class="modal-header">
				<button type="button" class="close" data-dismiss="modal"><span aria-hidden="true">&times;</span></button>
				<h4 class="modal-title">Hide / Show Columns</h4>
			</div>
			<div class="modal-body">
				<table>
					<thead>
						<tr>
							<th class="show_hide_table_spacing">Show</th>
							<th class="show_hide_table_spacing">Column Name</th>
							<th class="show_hide_table_spacing">Show</th>
							<th class="show_hide_table_spacing">Column Name</th>
							<th class="show_hide_table_spacing">Show</th>
							<th class="show_hide_table_spacing">Column Name</th>
							<th class="show_hide_table_spacing">Show</th>
							<th class="show_hide_table_spacing">Column Name</th>
						</tr>
					</thead>
					<tbody>
						<% column_mod = 4 %>
						<tr>
						% for position, column in enumerate(metric_object_type.ordered_columns):
							% if (position % column_mod) == 0:
								</tr>
								<tr>
									<td class="show_hide_table_spacing">
										<input id="${column[1]}" type="checkbox"/>
									</td>
									<td class="show_hide_table_spacing">
										<span>${column[0]}</span>
									</td>
							% else:
								<td class="show_hide_table_spacing">
									<input id="${column[1]}" type="checkbox"/>
								</td>
								<td class="show_hide_table_spacing">
									<span>${column[0]}</span>
								</td>
							% endif
						% endfor
						</tr>
					</tbody>
				</table>
			</div>
			<div class="modal-footer">
				<button type="button" id="show_hide_btn" class="btn btn-success pull-right" data-dismiss="modal">Done</button>
				<button type="button" id="show_all" class="btn btn-success pull-left">Show All</button>
				<button type="button" id="hide_all" class="btn btn-success pull-left">Hide All</button>
			</div>
		</div>
	</div>
</div>
</%block>

<%block name="saved_filter_name_modal">
<div class="modal fade saved_filter_modal" tableindex="-1" role="dialog" aria-labelledby="saved_filter_modal" aria-hidden="true">
	<div class="modal-dialog modal-sm">
		<div class="modal-content">
			<div class="modal-header">
				<button type="button" class="close" data-dismiss="modal"><span aria-hidden="true">&times;</span></button>
				<h4 class="modal-title">Enter new filter name</h4>
			</div>
			<div class="modal-body text-center">
				<input id="saved_filter_name" type="text" required>
			</div>
			<div class="modal-footer">
				<form id="save_filters_form" action="${request.route_path('trace_save_filter')}" method="POST">
					<input type="hidden" name="csrf_token" value="${request.session.get_csrf_token()}"/>
					<input type="hidden" id="metric_type_input" name="metric_type" value="proton"/>
					<button type="button" id="save_filters" class="btn btn-success pull-right" data-dismiss="modal" disabled>Save</button>
					<button type="button" id="cancel_save_filters" class="btn btn-success pull-left" data-dismiss="modal">Cancel</button>
				</form>
			</div>
		</div>
	</div>
</div>
</%block>

<%block name="remove_filter_confirm_modal">
<div class="modal fade remove_confirmation" tableindex="-1" role="dialog" aria-labelledby="remove_confirmation" aria-hidden="true">
	<div class="modal-dialog modal-sm">
		<div class="modal-content">
			<div class="modal-header">
				<button type="button" class="close" data-dismiss="modal"><span aria-hidden="true">&times;</span></button>
				<h4 class="modal-title">Remove this saved filter?</h4>
			</div>
			<div class="modal-footer">
				<form id="remove_filter_form" action="${request.route_path('trace_delete_saved_filter')}" method="POST">
					<input type="hidden" name="csrf_token" value="${request.session.get_csrf_token()}"/>
					<input type="hidden" name="metric_type" value="proton"/>
					<input type="hidden" id="filter_to_delete" name="filter_to_delete" value=""/>
					<button id="filter_delete_modal_btn" type="submit" class="btn btn-danger pull-right">Delete</button>
					<button data-dismiss="modal" class="btn btn-info pull-left">Cancel</button>
				</form>
			</div>
		</div>
	</div>
</div>
</%block>

<%block name="show_plot_modal">
<div class="modal fade show_plot_modal" tableindex="-1" role="dialog" aria-labelledby="remove_confirmation" aria-hidden="true">
	<div class="modal-dialog modal-sm">
		<div class="modal-content">
			<div class="modal-header">
				<button type="button" class="close" data-dismiss="modal"><span aria-hidden="true">&times;</span></button>
				<h4 class="modal-title">Graph Options</h4>
			</div>
			<div class="modal-body text-center">
				<div class="some_space_below">
					<h5 class="label_spacing control-label" style="margin-right: 20px; vertical-align: top; display: inline-block;"> Metric Type </h5>
					<select class="form-control" id="graph_column_name" name="graph_column_name">
						<option value=""></option>
						% for column in metric_object_type.numeric_columns:
							<option class="filter_option" value="${column[0]}">${column[0]}</option>
						% endfor
					</select>
				</div>
				<div class="some_space_below">
					<h5 class="label_spacing control-label" style="margin-right: 20px; vertical-align: top; display: inline-block;"> Graph Type </h5>
					<select class="form-control" id="graph_type" name="graph_type">
						<option value=""></option>
						<option class="filter_option" value="boxplot">Box Plot</option>
						<option class="filter_option" value="histogram">Histogram</option>
					</select>
				</div>
			</div>
			<div class="modal-footer">
				<button type="button" id="show_plot" class="btn btn-success">Graph</button>
			</div>
		</div>
	</div>
</div>
</%block>