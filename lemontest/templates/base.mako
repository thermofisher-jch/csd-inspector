<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <title>Ion Inspector: simple, scalable, fast</title>
    <meta name="description" content="Ion Inspector, Ion Torrent internal customer support tests for field specialists.">
    <meta name="author" content="Brian Kennedy">
    <meta http-equiv="X-UA-Compatible" content="IE=edge,chrome=1">

    <!-- Le HTML5 shim, for IE6-8 support of HTML elements -->
    <!--[if lt IE 9]>
      <script src="http://html5shim.googlecode.com/svn/trunk/html5.js" type="text/javascript"></script>
    <![endif]-->

    <!-- Le styles -->
    <link href="${request.static_url('lemontest:static/css/bootstrap.css')}" rel="stylesheet">
    <link rel="icon" href="/static/img/inspector_background.png" type="image/png" />
    <style type="text/css">
      body {
        padding-top: 60px;
        background-color: #FEFEFE;
      }
    </style>
    <script src="${request.static_url('lemontest:static/js/jquery-1.8.3.min.js')}"></script>
    <script src="${request.static_url('lemontest:static/js/dropdown.js')}"></script>
    <script src="${request.static_url('lemontest:static/js/modal.js')}"></script>
    <%block name="extra_head"/>
  </head>

  <body>
    <div class="navbar navbar-fixed-top">
      <div class="navbar-inner">
        <div class="container-fluid">
          <a class="brand" href="${request.route_path('index')}">Ion Inspector</a>
          <div class="nav-collapse">
            <ul class="nav">
              <li><a href="${request.route_path('upload')}">Submit Archive</a></li>
              <li><a href="${request.route_path('reports')}">List Reports</a></li>
              <li><a href="${request.route_path('documentation')}">Documentation</a></li>
              <li class="dropdown"><a class="dropdown-toggle" data-toggle="dropdown" href="#">Analysis<span class="caret"></span></a>
              	<ul class="dropdown-menu" role="menu">
              		<li><a href="${request.route_path('analysis_pgm')}">PGM</a></li>
              		<li><a href="${request.route_path('analysis_proton')}">Proton</a></li>
              		<li><a>Something</a></li>
              		<li><a>Something Else</a></li>
              	</ul>
              </li>
            </ul>
            <form id="jump_form" class="navbar-form pull-left">
              <div class="input-append">
                <input type="text" id="id_jump" placeholder="ID" class="span1"/>
                <button type="submit" id="jump_button" class="btn">Go</button>
              </div>
            </form>
            <div id="auth_controls" class="pull-right">
              % if request.user:
                <a href="${request.route_url('apex_logout')}" class="btn">Logout</a>
              % else:
                <!--<a href="${request.route_url('apex_login')}" class="btn">Login</a>
                or
                <a href="${request.route_url('apex_register')}" class="btn">Register</a>-->
              % endif
            </div>
          </div><!--/.nav-collapse -->
        </div>
      </div>
    </div>

    <div class="container-fluid">
      ${self.body()}
      <footer>
        <p>&copy; Ion Torrent 2013</p>
      </footer>
    </div> <!-- /container -->
    
    <%block name="piwik">
        <script type="text/javascript"> 
          var _paq = _paq || [];
          _paq.push(['trackPageView']);
          _paq.push(['enableLinkTracking']);
          (function() {
            var u=(("https:" == document.location.protocol) ? "https" : "http") + "://inspector.itw:4242//";
            _paq.push(['setTrackerUrl', u+'piwik.php']);
            _paq.push(['setSiteId', 1]);
            var d=document, g=d.createElement('script'), s=d.getElementsByTagName('script')[0]; g.type='text/javascript';
            g.defer=true; g.async=true; g.src=u+'piwik.js'; s.parentNode.insertBefore(g,s);
          })();
        </script>
        <noscript><p><img src="http://inspector.itw:4242/piwik.php?idsite=1" style="border:0" alt="" /></p></noscript>
    </%block>
    
    <script type="text/javascript">
      $(function(){
        function isNumber(n) {
          return !isNaN(parseFloat(n)) && isFinite(n);
        }
        $("#jump_form").submit(function(){
          var id = $('#id_jump').val();
          if (isNumber(id) && id > 0)
            window.location='/check/'+id;
          else
            alert("Enter an upload ID number to jump directly to it.");
          return false;
        });
      });
    </script>
    <script type="text/javascript" src="https://jira.itw/s/d41d8cd98f00b204e9800998ecf8427e/en_US-youeiq-1988229788/6144/144/1.4.0-m6/_/download/batch/com.atlassian.jira.collector.plugin.jira-issue-collector-plugin:issuecollector/com.atlassian.jira.collector.plugin.jira-issue-collector-plugin:issuecollector.js?collectorId=d397043f"></script>
  </body>
</html>