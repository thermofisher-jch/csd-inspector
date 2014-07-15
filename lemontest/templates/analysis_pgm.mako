<%doc>
	Author: Anthony Rodriguez
	Last Modified: 14 July 2014
</%doc>
<%inherit file="analysis_base.mako"/>

<form id="filter" class="filter_drawer form-horizontal" action="/analysis/pgm" method="GET">
	<div class="form-group some-space">
		<select class="form-control" name="metric_type" id="metric_type">
			<option value=""></option>
			% for column in filter_columns:
				<option value="${column}" ${'selected="selected"' if column==search['metric_type'] else ''}>${column}</option>
			% endfor
		</select>
		<input type="text" class="form-control" style="width: 6em;" name="min_number" id="min_number" placeholder="Lower Bound" value="${search['min_number']}">
		<input type="text" class="form-control" style="width: 6em;" name="max_number" id="max_number" placeholder="Upper Bound" value="${search['max_number']}">
	</div>
	<div class="form-group some-space">
		<select class="form-control" name="seq_kit_type" id="seq_kit_type">
			<option value=""></option>
			% for type in seq_kit_types:
				<option value="${type}" ${'selected="selected"' if type==search['seq_kit_type'] else ''}>
					${type}
				</option>
			% endfor
		</select>
	</div>
	<div class = "form-group some-space">
		<select class="form-control" name="chip_type" id="chipType">
			<option value=""></option>
	    	% for type in chip_types:
	        	<option value="${type}" ${'selected="selected"' if type==search['chip_type'] else ''}>
		            ${type}
		        </option>
		    % endfor
	    </select>
	</div>
	<button type="submit" class="btn btn-primary">Filter</button>
</form>

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
		<div class="pull-left">
			<button id="filter_toggle" class="btn btn-success">Filters</button>
		</div>
	    
	    <form id="csv_filter" action="/analysis.csv" method="POST">
			<div class="">
			        <div class="pull-right">
			            <input type="submit" class="btn btn-success" value="Download CSV"/>
					</div>
			</div>
		    
		    <input type="hidden" name="chip_type" value="${search['chip_type']}"></input>
		    <input type="hidden" name="seq_kit_type" value="${search['seq_kit_type']}"></input>
		</form>
	</div>
</%block>
<table class="table table-striped table-hover" id="analysis">
    <thead>
        <tr>    	
	    	% for column in pgm_columns:
	    		<th>${column}</th>
	    	% endfor
        </tr>
    </thead>
    <tbody>
        % for metric in metrics:
            <tr>
                <td><a href="${request.route_url('check', archive_id=metric.archive.id)}">${metric.archive.id}</a></td>
                <td><a href="${request.route_url('check', archive_id=metric.archive.id)}">${metric.archive.label}</a></td>
                <td><a href="${request.route_url('check', archive_id=metric.archive.id)}">${metric.pgm_temperature}</a></td>
                <td><a href="${request.route_url('check', archive_id=metric.archive.id)}">${metric.pgm_pressure}</a></td>
                <td><a href="${request.route_url('check', archive_id=metric.archive.id)}">${metric.chip_temperature}</a></td>
                <td><a href="${request.route_url('check', archive_id=metric.archive.id)}">${metric.chip_noise}</a></td>
                <td><a href="${request.route_url('check', archive_id=metric.archive.id)}">${metric.seq_kit}</a></td>
                <td><a href="${request.route_url('check', archive_id=metric.archive.id)}">${metric.chip_type}</a></td>
                <td><a href="${request.route_url('check', archive_id=metric.archive.id)}">${metric.isp_loading}</a></td>
                <td><a href="${request.route_url('check', archive_id=metric.archive.id)}">${metric.system_snr}</a></td>
            </tr>
        % endfor
    </tbody>
</table>