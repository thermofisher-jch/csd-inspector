<%inherit file="base.mako"/>

<%block name="extra_head">
  <script src="${request.static_url('lemontest:static/js/bootstrap-typeahead.js')}"></script>
  <script src="${request.static_url('lemontest:static/js/modernizr.custom.js')}"></script>
  <script>
    if ( !Modernizr.xhr2 ) {
      window.location.href = "${request.route_url('old_browser')}";
    }
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
      $("#name").typeahead({source: sourcerer("name")});
      $("#site").typeahead({source: sourcerer("site")});
      
      function on_upload_progress(event) {
        var progress = Math.round(event.loaded / event.total * 100)+'%';
        $("#progress_bar").css('width', progress);
        $("#progress_percent").html(progress);
      }
      
      $('#new_archive').submit(function(event) {
        event.preventDefault();
        $("#file_select").hide();
        $("#file_progress").show();
        var formData = new FormData($('#new_archive')[0]);
        dumb = $.ajax({
          url: '/upload',  //server script to process data
          type: 'POST',
          xhr: function() {  // custom xhr
            var myXhr = $.ajaxSettings.xhr();
            if(myXhr.upload){ // check if upload property exists
              myXhr.upload.addEventListener('progress', on_upload_progress, false); // for handling the progress of the upload
            }
            return myXhr;
          },
          // Form data
          data: formData,
          dataType: 'json',
          //Options to tell JQuery not to process data or worry about content-type
          cache: false,
          contentType: false,
          processData: false
        }).done(function(data){
          $("#progress_bar").css('width', "100%");
          $("#progress_percent").html("100%");
          if (data.valid) {
            window.location.href = data.url;
          } else {
            $("#file_select").show();
            $("#file_progress").hide();
            $("#log").prepend('<p class="alert alert-error">Invalid upload.<p>');
            $("#log_container").slideDown();
          }
        }).fail(function(xhr, status){
          console.log("Request failed: " + status);
          $("#log").prepend('<p class="alert alert-error">Upload error ' + status + '. Refresh the page and retry.<p>');
          $("#action_container").slideUp();
          $("#log_container").slideDown();
        });
      });
    });
  </script>
  <style type="text/css">
    #progress_bar {
      -webkit-transition: none;
         -moz-transition: none;
           -o-transition: none;
              transition: none;
    }
  </style>
</%block>

<h1>Upload <small> a new archive for testing</small></h1>
<div class="row">
  <div class="span6">
    <form id="new_archive" action="/upload" method="post" accept-charset="UTF-8" enctype="multipart/form-data">
      <input type="hidden" name="csrf_token" value="${request.session.get_csrf_token()}"/>
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
      <div style="height: 60px;">
        <div id="file_select">
          <label for="technicalFile">Select file</label>
          <input type="file" name="fileInput" id="fileInput" style="max-width: 100%"/>
        </div>
        <div id="file_progress" style="display: none;">
          <p>Upload in progress <span id="progress_percent">0%</span></p>
          <div class="progress progress-striped active">
            <div id="progress_bar" class="bar" style="width: 0%;"></div>
          </div>
        </div>
      </div>
      <div id="action_container">
        <div class="form-actions">
          <input type="submit" value="Submit Archive" class="btn btn-primary">
          <button class="btn" type="reset">Reset</button>
        </div>
      </div>
      <div id="log_container" style="display: none;">
        <div id="log" style="margin: 20px 0;"></div>
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
