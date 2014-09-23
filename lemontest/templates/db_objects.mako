<%inherit file="base.mako"/>
<!-- THIS TEMPLATE IS USED TO VIEW ALL THE OBJECTS IN THE DATABASE ALL AT ONCE
	 FOR THE MOST PART THIS WILL ONLY BE USED IN DEUGGIN, AND THE VIEW FUNCTION
	 THAT GOVERNS OVER THIS IS CURRENTLY COMMENTED OUT AT THE BOTTOM OF VIEW.PY -->
<style>
	.table_divs .container {
		margin-left: 0px;
		margin-right: 0px;
		height: 600px;
		width: 100%;
		overflow: auto;
	}
	table {
		
	}
</style>
<div class="table_divs">
	<div class="container">
		<h4>Session Objects</h4>
		<table class="table table-hover table-striped" width="800">
			<thead>
				% if request.session:
				<tr>
					% for key in request.session.keys():
						<th>${key}</th>
					% endfor
				</tr>
				% endif
			</thead>
			<tbody>
				% if request.session:
				<tr>
					% for key, value in request.session.items():
							<td>${value}</td>
					% endfor
				</tr>
				% endif
			</tbody>
		</table>
	</div>

	% for each_query in db_entities.values():
		<div class="container">
			% if each_query:
				<h4>${type(each_query[0])}</h4>
			% endif
			<table class="table table-hover table-striped" width="800">
				<thead>
					<tr>
						% if each_query:
							% for column in each_query[0].inspect():
								<th>${str(column).split('.')[1]}</th>
							% endfor
						% endif
					</tr>
				</thead>
				<tbody>
					% if each_query:
						% for each in each_query:
							<tr>
								% for column in each.inspect():
									<td>${getattr(each, str(column).split('.')[1])}</td>
								% endfor
							</tr>
						% endfor
					% endif
				</tbody>
			</table>
		</div>
	% endfor
</div>