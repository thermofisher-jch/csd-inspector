<%inherit file="base.mako"/>

<div class="row-fluid">
    <div class="span12">
        <div id="view_titles" class="clearfix">
            <h1>${archive.label}</h1>
            <div class="row-fluid">
                <h3 class="span9">${archive.site}</h3>
                <h3 class="span3" style="text-align: right">${archive.archive_type.replace("_", " ")}</h3>
            </div>
            <p style="float: right;"><em>${archive.time.strftime("%c")}, uploaded by ${archive.submitter_name}</em></p>
            % if archive.summary:
                <h4>${archive.summary}</h4>
            % endif
            % if archive.tags:
                <div id="tags">
                    % for tag in archive.tags:
                        <span class="label label-inverse">${tag.name}</span>
                    % endfor
                </div>
            % endif
        </div>
        <form id="edit_titles" action="${request.route_url('check', archive_id=archive.id)}" method="post" style="display:none;">
            <input type="hidden" name="csrf_token" value="${request.session.get_csrf_token()}"/>
            <input class="form-h1 span12" name="label" placeholder="Label" value="${archive.label}" />
            <div class="row-fluid">
                <div class="span7" style="text-align:left;">
                    <input class="form-h3 span7" name="site" placeholder="Site" value="${archive.site}" />
                </div>
                <div class="span5" style="text-align:right; margin-top:12px;">
                    <select name="archive_type" id="archiveType">
                        % for type in archive_types:
                            <option value="${type}" ${'selected="selected"' if type==archive.archive_type else ''}>
                                ${type.replace("_", " ")}
                            </option>
                        % endfor
                    </select>
                </div>
            </div>

            <div class="row-fluid">
                <div class="span6">
                    <input name="summary" class="form-h4" placeholder="Summary" value="${archive.summary}" style="width: 300px;" maxlength="30"></input><br/>
                    <input name="tags" placeholder="Tags" value="${tag_string}"></input>
                </div>
                <div class="span6" style="text-align: right;">
                    <p><em>${archive.time.strftime("%c")}, uploaded by ${archive.submitter_name}</em></p>
                    <input type="button" id="cancel" class="btn" value="Cancel" />
                    <input type="submit" class="btn btn-primary" value="Save Changes" />
                </div>
            </div>
        </form>
        <div class="form-actions">
            <div class="pull-left">
                <a class="btn btn-success" href="/archives/${basename}/archive.zip"><i class="icon-arrow-down icon-white"></i> Download Archive</a>
                <a class="btn" href="/archives/${basename}/"><i class="icon-folder-open"></i> View Files</a>
                <a id="edit" class="btn" href="#"><i class="icon-pencil"></i> Edit</a>
                <form method="POST" action="${request.route_url('rerun', archive_id=archive.id)}" style="margin: 0; display: inline">
                    <button type="submit"class="btn"><i class="icon-repeat"></i> Re-run Tests</button>
                </form>
            </div>
            <div class="pull-right">
                <span class="btn btn-danger disabled" ><i class="icon-trash icon-white"></i> Super Delete</span>
            </div>
        </div>
    </div>
</div>
% if archive.status != 'Diagnostics completed.':
    <div class="row-fluid">
        <h2 class="span12">Status: ${archive.status}</h2>
    </div>
% endif
% if archive.diagnostics:
    <div class="row-fluid">
        <div class="span12">
            <table id="test-summary" class="table table-striped table-hover">
                <thead>
                    <tr>
                        <th>Test</th><th>Status</th><th>Details</th>
                    </tr>
                </thead>
                <tbody>
                    % for test in archive.diagnostics:
                        <tr>
                            <td>${test.name.replace("_", " ")}</td>
                            <td>
                                <span class="label label-${status_highlights.get(test.status, '')}">${test.status}</span>
                            </td>
                            <td>
                                % if test.html or test.readme:
                                    <div class="links">
                                        <div>
                                            % if test.html:
                                                <a href="${request.static_url(test.html)}">Results</a>
                                            % endif
                                        </div>
                                        <div>
                                            % if test.readme:
                                                <a href="${request.route_url('test_readme', test_name=test.name)}">Readme</a>
                                            % endif
                                        </div>
                                    </div>
                                % endif
                                ${test.details | n}
                            </td>
                        </tr>
                    % endfor
                </tbody>
            </table>
        </div>
    </div>
% endif
<div class="row-fluid" style="margin-top: 20px;">
    <div id="run_report" class="span12">
        <div id="pdf"></div>
        <a href="/archives/${basename}/report.pdf" class="btn btn-success"><i class="icon-arrow-down icon-white"></i> Download Report</a>
    </div>
    <div id="no_report" class="span12" style="display:none;">
        <small>There is no report.pdf for this archive.</small>
    </div>
</div>


<%block name="extra_head">
    <script>
        $(function(){
            var report_url = "/archives/${basename}/report.pdf";
            var pdf_template = '<object type="application/pdf" data="/archives/${basename}/report.pdf" height="600px" width="100%"><p>Your browser does not support PDF display</p></object>';
            console.log("merp");
            $.ajax({
                type: 'HEAD',
                url: report_url,
                success: function () {
                    $("#pdf").html(pdf_template);
                },
                error: function () {
                    $("#run_report").hide();
                    $("#no_report").show();
                }
            });
            $("#derp").error(function(){
                console.log("mega derp");
            });
            $("#edit, #cancel").click(function(){
                $("#view_titles").toggle();
                $("#edit_titles").toggle();
                return false;
            });
        });
    </script>
</%block>