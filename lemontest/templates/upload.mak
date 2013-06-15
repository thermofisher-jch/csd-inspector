<%inherit file="base.mak"/>

<%block name="extra_head">
  <script src="${request.static_url('lemontest:static/js/bootstrap-typeahead.js')}"></script>
  <script>
    $(function(){
      var sourcerer = function (what) {
        return function (query, process) {
          $.getJSON(
            "/api/auto_complete", 
            {what: what, match: query}, 
            process
          );
        };
      };
      $("#submitter").typeahead({source: sourcerer("name")});
      $("#site").typeahead({source: sourcerer("site")});
    });
  </script>
</%block>

<h1>Upload <small> a new archive for testing</small></h1>
<div class="row">
  <div class="span6">
    <form action="/upload" method="post" accept-charset="UTF-8" enctype="multipart/form-data">
      <div class="row">
        <div class="span3">
          <label for="name">Your Name</label>
          <input id="name" name="name" type="text" autocomplete="off" autofocus value="${name}" />
        </div>
        <div class="span3">
          <label for="site">Site Name</label>
          <input id="site" name="site" type="text" autocomplete="off" value="${site}"/>
        </div>
      </div>
      <div class="row">
        <div class="span3">
          <label for="label">Archive Label</label>
          <input id="label" name="label" type="text" value="${label}"/>
        </div>
        <div class="span3">
          <label for="archiveType">Archive Type</label>
          <select name="archive_type" id="archiveType">
            % for type in archive_types:
              <option value="${type}" ${'selected="selected"' if type == archive_type else ''}>
                ${type.replace("_", " ")}
              </option>
            % endfor
          </select>
        </div>
      </div>
      <label for="technicalFile">Select file</label>
      <input type="file" name="fileInput" id="fileInput" class="btn" />
      <div class="form-actions">
        <input type="submit" value="Submit Archive" class="btn btn-primary">
        <button class="btn" type="reset">Reset</button>
      </div>
    </form>
  </div>
  <div class="span6">
    <dl>
      <dt>Your name</dt>
      <dd>Use the name by which people can easily identify your uploads.</dd>
      <dt>Site name</dt>
      <dd>Use the name by which people can easily identify the site from which the upload originates, a consistent name that does not change between uploads which are from the same site.</dd>
      <dt>Archive Label</dt>
      <dd>Use label to label inidividual uploads something meaningful. For example, if you're fond of appending incrementing numbers to your uploads, do that in this field.  This will be auto-generated if left empty.</dd>
  </div>
</div>
