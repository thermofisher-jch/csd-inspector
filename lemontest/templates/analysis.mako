<%doc>
	Author: Anthony Rodriguez
	Created: 15 July 2014
	Last Modified: 15 July 2014
</%doc>

<%inherit file="base.mako"/>

<%block name="extra_head">

	<script>
		$(function(){
			$("#filter_toggle").click(function(){
                $(".filter_drawer").slideToggle();
            });
		});
	</script>

    <style type="text/css">
    tr td:nth-child(3), tr td:nth-child(4) {
        white-space: nowrap;
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
		<select class="form-control" name="metric_type" id="metric_type">
			<option value=""></option>
			% for column in metric_object_type.neumeric_columns:
				<option value="${column[0]}" ${'selected="selected"' if column[0]==search['metric_type'] else ''}>${column[0]}</option>
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
    
    <form id="csv_filter" action="${request.route_path('analysis_csv')}" method="POST">
    	<input type="hidden" name="csrf_token" value="${request.session.get_csrf_token()}"/>
	    
	    <input type="hidden" name="chip_type" value="${search['Chip Type']}"/>
	    <input type="hidden" name="seq_kit_type" value="${search['Seq Kit']}"/>
	    <input type="hidden" name="metric_type" value="${search['metric_type']}"/>
	    <input type="hidden" name="min_number" value="${search['min_number']}"/>
	    <input type="hidden" name="max_number" value="${search['max_number']}"/>
	    <input type="hidden" name="metric_object_type" value="${request.path}"/>
	    
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
	    	% for column in metric_object_type.ordered_columns:
	    		<th>${column[0]}</th>
	    	% endfor
        </tr>
    </thead>
    <tbody>
    
        % for metric in metrics:
        	<tr>
	        	% for column in metric.ordered_columns:
	        		% if column[0] == 'Label':
	        			<td><a href="${request.route_url('check', archive_id=metric.archive.id)}">${metric.archive.label}</a></td>
	        		% else:
	        			<td><a href="${request.route_url('check', archive_id=metric.archive.id)}">${metric.get_formatted(column[0])}</a></td>
	        		% endif
				% endfor
			</tr>
        % endfor
    </tbody>
</table>
</%block>