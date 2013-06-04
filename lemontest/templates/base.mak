<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <title>Ion Inspector: simple, scalable, fast</title>
    <meta name="description" content="Ion Inspector, Ion Torrent internal customer support tests for field specialists.">
    <meta name="author" content="Brian Kennedy">

    <!-- Le HTML5 shim, for IE6-8 support of HTML elements -->
    <!--[if lt IE 9]>
      <script src="http://html5shim.googlecode.com/svn/trunk/html5.js" type="text/javascript"></script>
    <![endif]-->

    <!-- Le styles -->
    <link href="${request.static_url('lemontest:static/css/bootstrap.css')}" rel="stylesheet">
    <style type="text/css">
      body {
        padding-top: 60px;
      }
    </style>
    <script src="${request.static_url('lemontest:static/js/jquery-1.8.3.min.js')}"></script>
    <%block name="header"/>
  </head>

  <body>
    <div class="navbar navbar-fixed-top">
      <div class="navbar-inner">
        <div class="container">
          <a class="brand" href="${request.route_path('index')}">Ion Inspector</a>
          <div class="nav-collapse">
            <ul class="nav">
              <li><a href="${request.route_path('upload')}">Submit Archive</a></li>
              <li><a href="${request.route_path('reports')}">List Reports</a></li>
              <li><a href="${request.route_path('documentation')}">Documentation</a></li>
              <li><a href="${request.route_path('changes')}">Change Log</a></li>
            </ul>
          </div><!--/.nav-collapse -->
        </div>
      </div>
    </div>

    <div class="container">
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
  </body>
</html>