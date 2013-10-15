<%inherit file="base.mako"/>

<!-- Main hero unit for a primary marketing message or call to action -->
<h1>Ion Inspector</h1>
<div class="clearfix" style="margin-top:20px;">
  <div class="pull-left" style="margin-right: 20px;"><img src="/static/img/inspector_ion.png"/></div>
  <div>
    <p>Ion Inspector is a simple customer support testing tool.  It automatically runs a battery of tests on a customer support archive and reports actionable information for any known issues, simple.</p>
    <p><a href="${request.route_url('upload')}">Submit an archive.</a></p>
    <p>If you ever inspect a support archive, you can write a simple testing script to automatically perform the repetitive parts of this analysis, scalable.</p>
    <p><a href="${request.route_url('documentation')}">Read test author documentation.</a></p>
  </div>
</div>