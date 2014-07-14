<%inherit file="base.mako"/>

<%block name="extra_head">
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
    #filter_name, #filter_site {
        max-width: 150px;
    }
    .hide_me {
    	height: 0px;
    	width: 0px;
    	border: none;
    	padding: 0px;
    }
    </style>
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

<form id="csv_filter" action="/analysis.csv" method="POST>
	<div class="buttons">
	        <div class="pull-right">
	            <input type="submit" class="btn btn-success" value="Download CSV"/>
			</div>
	</div>
    
    <input type="hidden" name="chip_type" value="${search['chip_type']}"></input>
    <input type="hidden" name="seq_kit_type" value="${search['seq_kit_type']}"></input>
</form>

<form id="filter" action="/analysis" method="GET">
<table class="table table-striped table-hover" id="analysis">
    <thead>
        <tr>    	
	    	% for column in pgm_columns:
	    		<th>${column}</th>
	    	% endfor
        </tr>
        
        <tr class="filter-row">
        	<th></th>
        	<th></th>
        	<th></th>
        	<th></th>
        	<th></th>
        	<th></th>
        	<th>
        		<select name="seq_kit_type" id="seq_kit_type" onchange="$('#filter').submit();">
        			<option value=""></option>
        			% for type in seq_kit_types:
        				<option value="${type}" ${'selected="selected"' if type==search['seq_kit_type'] else ''}>
        					${type}
        				</option>
        			% endfor
        		</select>
        	</th>
        	<th>
        		<select name="chip_type" id="chipType" onchange="$('#filter').submit();">
					<option value=""></option>
			    	% for type in chip_types:
			        	<option value="${type}" ${'selected="selected"' if type==search['chip_type'] else ''}>
				            ${type}
				        </option>
				    % endfor
			    </select>
        	</th>
        	<th></th>
        	<th></th>
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
<input type="submit" class="hide_me">
</form>