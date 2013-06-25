<%inherit file="base.mak"/>

<%block name="extra_head">
    <style type="text/css">
    tr td:nth-child(3), tr td:nth-child(4) {
        white-space: nowrap;
    }
    #reports td {
        padding: 12px 8px;
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

<div class="row-fluid" style="margin-bottom: 20px;">
    <div class="span9">
        <div class="pagination" style="margin:0;">
            <ul>
                % if archives.page > 1:
                    <li><a href="${page_url(archives.page-1)}">&laquo;</a></li>
                % else:
                    <li class="disabled"><span>&laquo;</span></li>
                % endif

                % for page in pages:
                    % if page == archives.page:
                        <li class="active"><span>${page}</span></li>
                    % elif page == '..':
                        <li class="disabled"><span>${page}</span></li>
                    % else:
                        <li><a href="${page_url(page)}">${page}</a></li>
                    % endif
                % endfor
                
                % if archives.page < archives.page_count:
                    <li><a href="${page_url(archives.page+1)}">&raquo;</a></li>
                % else:
                    <li class="disabled"><span>&raquo;</span></li>
                % endif
            </ul>
        </div>
    </div>
    <div class="span3" style="line-height: 30px; text-align: right;">
        ${archives.first_item} to ${archives.last_item} of ${archives.item_count}
    </div>
</div>

<form id="filter" action="/reports" method="GET">
<table class="table table-striped table-hover" id="reports">
    <thead>
        <tr>
            <th>ID</th><th>Submitter</th><th>Date</th><th>Type</th><th>Site</th><th>Label</th><th>Summary</th>
        </tr>
        <tr class="filter-row">
                <th></th>
                <th><input id="filter_name" name="submitter_name" type="text" value="${filters.submitter_name}"></th>
                <th></th>
                <th>
                    <select name="archive_type" id="archiveType" onchange="$('#filter').submit();">
                        <option value=""></option>
                        % for type in archive_types:
                            <option value="${type}" ${'selected="selected"' if type==filters.archive_type else ''}>
                                ${type.replace("_", " ")}
                            </option>
                        % endfor
                    </select>
                </th>
                <th><input id="filter_site" name="site" type="text" value="${filters.site}"></th>
                <th>
                    <input id="filter_label" name="label" type="text" value="${filters.label}">
                </th>
                <th>
                    % if is_search:
                        <a href="${request.current_route_url()}" class="btn btn-inverse">Clear</a>
                    % endif
                </th>
        </tr>
    </thead>
    <tbody>
        % for archive in archives:
            <tr onclick="window.location='${request.route_url('check', archive_id=archive.id)}';" style="cursor: pointer;">
                <td>${archive.id}</td>
                <td>${archive.submitter_name}</td>
                <td>${h.prettydate(archive.time)}</td>
                <td>${archive.archive_type.replace("_", " ")}</td>
                <td>${archive.site}</td>
                <td>${archive.label}</td>
                <td>${archive.summary}</td>
            </tr>
        % endfor
    </tbody>
</table>
<input type="submit" style="height: 0px; width: 0px; border: none; padding: 0px;" hidefocus="true" />
</form>
