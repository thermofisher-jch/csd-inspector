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
	var filter_id = 1;

	$(function(){
		// retrieves proper stored session of shown and hidden columns
		% if request.path == '/analysis/pgm':
			% if 'show_hide_session/analysis/pgm' in request.session and request.session['show_hide_session/analysis/pgm']:
				var show_hide_session = ${request.session['show_hide_session/analysis/pgm'] | n};
				show_hide_columns(show_hide_session);
			% else:
				var show_hide_session = global_columns_default;
				show_hide_columns(show_hide_session);
			% endif
		% elif request.path == '/analysis/proton':
			% if 'show_hide_session/analysis/proton' in request.session and request.session['show_hide_session/analysis/proton']:
				var show_hide_session = ${request.session['show_hide_session/analysis/proton'] | n};
				show_hide_columns(show_hide_session);
			% else:
				var show_hide_session = global_columns_default;
				show_hide_columns(show_hide_session);
			% endif
		% endif

		// resets filter options before GET method
		add_filters_onload(${search['extra_filter_number']})

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
			  url: "${request.route_path('analysis_show_hide')}",
			  data: {"csrf_token": csrf_token, "metric_type": "${request.path}", "show_hide_columns${request.path}": JSON.stringify(show_hide_session)}
			}).done(
					function(data){
						show_hide_columns(show_hide_session);
					});
		});
	});

</script>
</%block>

<%block name="filter">
<!-- <form id="filter" class="filter_drawer form-horizontal" action="${request.path}" method="GET"> -->
<form id="filter" class="filter_drawer form-inline" action="${request.path}" method="GET" onclick="get_extra_filter_number()">
	<div class="">
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

			<div class="pull-right" id="filter_buttons" style="position: relative;">
				<button type="submit" class="btn btn-info">Filter</button>
				<button type="button" class="btn btn-info">Clear Filters</button>
			</div>
		</div>
		<!-- END CATEGORICAL FILTERS -->

		<!-- BEGIN NUMERICAL FILTERS -->
		<div class="form-group form-group-column3">
			<div class="some_space_below">
				<h5 class="pull-left label_spacing control-label numeric_label"> Metric Type </h5>
				<select id="metric_type_filter0" class="form-control" name="metric_type_filter0">
					<option value=""></option>
					% for column in metric_object_type.numeric_columns:
						<option class="filter_option" value="${column[0]}">${column[0]}</option>
					% endfor
				</select>
				<input type="text" class="form-control" style="width: 6em;" name="min_number0" id="min_number0" placeholder="Lower Bound" value="">
				<input type="text" class="form-control" style="width: 6em;" name="max_number0" id="max_number0" placeholder="Upper Bound" value="">
				<input type="hidden" id="extra_filter_number" name="extra_filter_number" value="">

				<button type="button" id="add_filter" class="btn btn-info btn-mini"><span class="icon-white icon-plus"></span></button>
			</div>
			<div id="dynamic_filters" class="some_space_below"></div>
		</div>
		<!-- END NUMERICAL FILTERS -->
	</div>
	<input type="hidden" id="upload_time_sort" name="upload_time_sort" value="" />
	<input type="hidden" id="start_time_sort" name="start_time_sort" value="" />
	<input type="hidden" id="end_time_sort" name="end_time_sort" value="" />
</form>
</%block>

<%block name="buttons">
<div class="row-fluid" style="margin-bottom: 5px;">
	<div class="btn-group pull-left">
		<button type="button" class="btn btn-default btn-lg some_space_right" id="filter_toggle">Filter <span class="caret"></span></button>
		<button type="button" class="btn btn-default" data-toggle="modal" data-target=".show_hide_modal">Show / Hide Columns</button>

		<%block name="download_csv_form">
		<form class="form_spacing" id="csv_filter" action="${request.route_path('analysis_csv')}" method="POST" onclick="get_shown_columns_csv()">
			<input type="hidden" name="csrf_token" value="${request.session.get_csrf_token()}"/>
			<input type="hidden" name="metric_type" value="${request.path}"/>
			<input type="hidden" name="show_hide"  id="show_hide" value="" />

			<input type="hidden" id="Chip Type_csv" name="Chip Type" value=""/>
			<input type="hidden" id="Seq Kit_csv" name="Seq Kit" value=""/>
			<input type="hidden" id="Run Type_csv" name="Run Type" value=""/>
			<input type="hidden" id="Ref Lib_csv" name="Ref Lib" value=""/>
			<input type="hidden" id="SW Version_csv" name="SW Version" value=""/>
			<input type="hidden" id="TSS Version_csv" name="TSS Version" value=""/>
			<input type="hidden" id="HW Version_csv" name="HW Version" value=""/>
			<input type="hidden" id="Barcode Set_csv" name="Barcode Set" value=""/>
			<input type="hidden" id="metric_type_filter0_csv" name="metric_type_filter0" value=""/>
			<input type="hidden" id="min_number0_csv" name="min_number0" value=""/>
			<input type="hidden" id="max_number0_csv" name="max_number0" value=""/>
			<div id="csv_filter_extras"></div>

			<button type="submit" class="btn btn-success">Download CSV <span class="icon-white icon-download"></span></button>
		</form>
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
<%block name="shide_show_modal">
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
