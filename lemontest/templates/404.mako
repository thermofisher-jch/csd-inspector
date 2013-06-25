<%inherit file="base.mako"/>

<h1>404 <small>Not Found</small></h1>
<p><code>${request.url}</code></p>
<p><strong>We looked but couldn't find the page you're looking for.</strong> Try clicking one of the links in the menu at the top of the page to proceed.</p>
<img src="${request.static_url('lemontest:static/img/chat_dans_les_boites.jpg')}"/>

<%block name="piwik">
    <script type="text/javascript"> 
      var _paq = _paq || [];
      _paq.push(['setDocumentTitle', '404/URL = '+String(document.location.pathname+document.location.search).replace(/\//g,"%2f") + '/From = ' + String(document.referrer).replace(/\//g,"%2f")]);
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