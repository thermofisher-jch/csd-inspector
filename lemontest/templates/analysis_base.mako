<%doc>
	Author: Anthony Rodriguez
	Created: 15 July 2014
	Last Modified: 15 July 2014
</%doc>

<%inherit file="base.mako"/>

<%block name="extra_head">

	<script>
		$(function(){
			$("#filter_toggle").click(function(){
                $(".filter_drawer").slideToggle();
            });
		});
	</script>

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
    .hide_me {
    	height: 0px;
    	width: 0px;
    	border: none;
    	padding: 0px;
    }
    .filter_drawer {
    	display: none;
    }
    .some-space {
    	margin-bottom: 10px;
    }
    </style>
</%block>




























