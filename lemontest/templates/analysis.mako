<%inherit file="base.mako"/>

<%block name="extra_head">
    <style type="text/css">
    tr td:nth-child(3), tr td:nth-child(4) {
        white-space: nowrap;
    }
    #reports td {
        padding: 0;
    }
    #reports td a {
        padding: 12px 8px;
        display: block;
        color: #333333;
    }
    #reports td a:hover {
        text-decoration: none;
     }

    #reports thead tr th {
        border-top: 0 none;
        background-image: linear-gradient(to bottom, white, #EFEFEF);
    }
    #reports thead tr.filter-row th {
        padding-top: 0;
        background-image: none;
        background-color: #EEEEEE;
    }
    #reports thead tr th:last-child {
        border-right: 0 none;
    }
    #reports th input, #reports th select {
        margin: 0;
        width: auto;
    }
    #filter_name, #filter_site {
        max-width: 150px;
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

<form id="filter" action="/analysis" method="GET">
<table class="table table-striped table-hover" id="reports">
    <thead>
        <tr>
            <th>ID</th><th>Label</th><th>PGM Temperature</th><th>PG Pressure</th><th>Chip Temperature</th><th>Chip Noise</th>
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
            </tr>
        % endfor
    </tbody>
</table>
<input type="submit" style="height: 0px; width: 0px; border: none; padding: 0px;" hidefocus="true" />
</form>