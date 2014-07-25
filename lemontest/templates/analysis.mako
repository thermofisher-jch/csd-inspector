<%doc>
	Author: Anthony Rodriguez
</%doc>

<%inherit file="base.mako"/>

<%block name="extra_head">

	<script type="text/javascript">

		$(function(){
			% if '/analysis/pgm' == request.path:
				% if 'show_hide_session/analysis/pgm' in request.session and request.session['show_hide_session/analysis/pgm']:
					var show_hide_session = ${request.session['show_hide_session/analysis/pgm'] | n};
					show_hide_columns(show_hide_session);
				% else:
					var show_hide_session = ${show_hide_defaults | n};
					show_hide_columns(show_hide_session);
				% endif
			% elif '/analysis/proton' == request.path:
				% if 'show_hide_session/analysis/proton' in request.session and request.session['show_hide_session/analysis/proton']:
					var show_hide_session = ${request.session['show_hide_session/analysis/proton'] | n};
					show_hide_columns(show_hide_session);
				% else:
					var show_hide_session = ${show_hide_defaults | n};
					show_hide_columns(show_hide_session);
				% endif
			% endif

			$("#filter_toggle").click(function(){
				$(".filter_drawer").slideToggle();
			});

			$("#show_all").click(function() {
				all_columns(true);
			});

			$("#hide_all").click(function() {
				all_columns(false);
			});

			$("#")

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

		function show_hide_columns(array_of_columns) {
			try {
				for (var item in array_of_columns) {
					if (array_of_columns[item] == "true") {
						var elements = document.getElementsByClassName(item);
						for (i = 0; i < elements.length; i++) {
							elements[i].style.display = 'table-cell';
						}
						document.getElementById(item).checked = true;
					} else {
						var elements = document.getElementsByClassName(item);
						for (i = 0; i < elements.length; i++) {
							elements[i].style.display = 'none';
						}
						document.getElementById(item).checked = false;
					}
				}
			} catch (err) {
				//This only happens if there is a session saved version of a renamed column name.
			}
		}

		function get_shown_columns(){
			var array_of_columns = ${show_hide_defaults | n};
			for (var item in array_of_columns) {
				var checkbox = document.getElementById(item);
				if (checkbox.checked) {
					array_of_columns[item] = "true";
				} else {
					array_of_columns[item] = "false";
				}
			}

			document.getElementById("show_hide").value = JSON.stringify(array_of_columns);

			return array_of_columns;
		}

		function all_columns(show){
			if (show){
				var array_of_columns = ${show_hide_defaults | n};
				show_hide_columns(array_of_columns);
			} else {
				var array_of_columns = ${show_hide_false | n};
				show_hide_columns(array_of_columns);
			}
		}
	</script>

	<style type="text/css">
	tr td:nth-child(3), tr td:nth-child(4) {
		white-space: nowrap;
	}
	.show_hide_table_spacing {
		padding-right: 20px;
	}
	#analysis td {
		padding: 0;
	}
	#analysis td a {
		padding: 12px 8px;
		display: block;
		color: #333333;
	}
	#analysis td a:hover {
		text-decoration: none;
	 }

	#analysis thead tr th {
		border-top: 0 none;
		background-image: linear-gradient(to bottom, white, #EFEFEF);
	}
	#analysis thead tr.filter-row th {
		padding-top: 0;
		background-image: none;
		background-color: #EEEEEE;
	}
	#analysis thead tr th:last-child {
		border-right: 0 none;
	}
	#analysis th input, #analysis th select {
		margin: 0;
		width: auto;
	}
	.hide_me {
		height: 0px;
		width: 0px;
		border: none;
		padding: 0px;
	}
	.filter_drawer {
		display: none;
	}
	.some-space {
		margin-bottom: 10px;
	}
	</style>
</%block>

<%block name="filter">
<form id="filter" class="filter_drawer form-horizontal" action="${request.path}" method="GET">
	<div class="form-group some-space">
		<select class="form-control" name="metric_type_filter" id="metric_type">
			<option value=""></option>
			% for column in metric_object_type.numeric_columns:
				<option value="${column[0]}" ${'selected="selected"' if column[0]==search['metric_type_filter'] else ''}>${column[0]}</option>
			% endfor
		</select>
		<input type="text" class="form-control" style="width: 6em;" name="min_number" id="min_number" placeholder="Lower Bound" value="${search['min_number']}">
		<input type="text" class="form-control" style="width: 6em;" name="max_number" id="max_number" placeholder="Upper Bound" value="${search['max_number']}">
	</div>
	<div class="form-group some-space">
		<select class="form-control" name="seq_kit_type" id="seq_kit_type">
			<option value=""></option>
			% for type in metric_object_type.ordered_kits:
				<option value="${type[0]}" ${'selected="selected"' if type[0]==search['Seq Kit'] else ''}>
					${type[1]}
				</option>
			% endfor
		</select>
	</div>
	<div class = "form-group some-space">
		<select class="form-control" name="chip_type" id="chipType">
			<option value=""></option>
			% for type in metric_object_type.chip_types:
				<option value="${type}" ${'selected="selected"' if type==search['Chip Type'] else ''}>
					${type}
				</option>
			% endfor
		</select>
	</div>
	<button type="submit" class="btn btn-primary">Filter</button>
</form>
</%block>

<%block name="pager">
<div class="row-fluid" style="margin-bottom: 20px;">
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

<%block name="buttons">
<div class="row-fluid" style="margin-bottom: 20px;">
	<button type="button" class="pull-left btn btn-default btn-lg" id="filter_toggle">
		<span class="caret"></span>
	</button>

	<button id="ajax_test" class="btn btn-primary" data-toggle="modal" data-target=".show_hide_modal">Show / Hide Columns</button>

	<form id="csv_filter" action="${request.route_path('analysis_csv')}" method="POST" onclick="get_shown_columns()">
		<input type="hidden" name="csrf_token" value="${request.session.get_csrf_token()}"/>
		
		<input type="hidden" name="chip_type" value="${search['Chip Type']}"/>
		<input type="hidden" name="seq_kit_type" value="${search['Seq Kit']}"/>
		<input type="hidden" name="metric_type" value="${search['metric_type']}"/>
		<input type="hidden" name="min_number" value="${search['min_number']}"/>
		<input type="hidden" name="max_number" value="${search['max_number']}"/>
		<input type="hidden" name="metric_type" value="${request.path}"/>
		<input type="hidden" name="show_hide"  id="show_hide" value="" />

		<div class="pull-right">
			<input type="submit" class="btn btn-success" value="Download CSV"/>
		</div>
	</form>
</div>
</%block>

<%block name="metrics_table">
<table class="table table-striped table-hover" id="analysis">
	<thead>
		<tr>
			<th>ID</th>
			<th>Label</th>
			% for column in metric_object_type.ordered_columns:
				<th class="${column[1]}">${column[0]}</th>
			% endfor
		</tr>
	</thead>
	<tbody>
	
		% for metric in metrics:
			<tr>
				<td><a class="archive_id" href="${request.route_url('check', archive_id=metric.archive.id)}">${metric.archive.id}</a></td>
				<td><a class="archive_label" href="${request.route_url('check', archive_id=metric.archive.id)}">${metric.archive.label}</a></td>
				% for column in metric.ordered_columns:
					<td class="${column[1]}"><a href="${request.route_url('check', archive_id=metric.archive.id)}">${metric.get_formatted(column[0])}</a></td>
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
							<th>Show</th>
							<th class="show_hide_table_spacing">Column Name</th>
							<th></th>
							<th>Show</th>
							<th class="show_hide_table_spacing">Column Name</th>
						</tr>
					</thead>
					<tbody>
<!-- 						<tr> -->
<!-- 							<td> -->
<!-- 								<input id="archive_id" type="checkbox"/> -->
<!-- 							</td> -->
<!-- 							<td>ID</td> -->
<!-- 							<td> -->
<!-- 								<input id="archive_label" type="checkbox"/> -->
<!-- 							</td> -->
<!-- 							<td>Label</td> -->
<!-- 						<tr> -->
						% for column1, column2 in map(None, metric_object_type.ordered_columns[::2], metric_object_type.ordered_columns[1::2]):
							<tr>
								% if column1:
									<td>
										<input id="${column1[1]}" type="checkbox"/>
									</td>
									<td class="show_hide_table_spacing">
										<span>${column1[0]}</span>
									</td>
								% endif
								<td></td>
								% if column2:
									<td>
										<input id="${column2[1]}" type="checkbox"/>
									</td>
									<td class="show_hide_table_spacing">
										<span>${column2[0]}</span>
									</td>
								% endif
							</tr>
						% endfor
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
