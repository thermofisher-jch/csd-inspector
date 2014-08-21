<%inherit file="base.mako"/>
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
	
	<div class="container">
		<h4>File Progress</h4>
		<table class="table table-hover table-striped" width="800">
			<thead>
				<tr>
					% if file_progress_query:
						% for column in file_progress_query[0].inspect():
							<th>${str(column).split('.')[1]}</th>
						% endfor
					% endif
				</tr>
			</thead>
			<tbody>
				% if file_progress_query:
					% for each in file_progress_query:
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
	
	<div class="container">
		<h4>Saved Filters PGM</h4>
		<table class="table table-hover table-striped" width="800">
			<thead>
				<tr>
					% if saved_filters_pgm:
						% for column in saved_filters_pgm[0].inspect():
							<th>${str(column).split('.')[1]}</th>
						% endfor
					% endif
				</tr>
			</thead>
			<tbody>
				% if saved_filters_pgm:
					% for each in saved_filters_pgm:
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
	
	<div class="container">
		<h4>Saved Filters Proton</h4>
		<table class="table table-hover table-striped" width="800">
			<thead>
				<tr>
					% if saved_filters_proton:
						% for column in saved_filters_proton[0].inspect():
							<th>${str(column).split('.')[1]}</th>
						% endfor
					% endif
				</tr>
			</thead>
			<tbody>
				% if saved_filters_proton:
					% for each in saved_filters_proton:
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
	
	<div class="container">
		<h4>Archive</h4>
		<table class="table table-hover table-striped" width="800">
			<thead>
				<tr>
					% if archive_query:
						% for column in archive_query[0].inspect():
							<th>${str(column).split('.')[1]}</th>
						% endfor
					% endif
				</tr>
			</thead>
			<tbody>
				% if archive_query:
					% for each in archive_query:
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
	
	<div class="container">
		<h4>Metrics PGM</h4>
		<table class="table table-hover table-striped" width="800">
			<thead>
				<tr>
					% if metrics_pgm_query:
						% for column in metrics_pgm_query[0].inspect():
							<th>${str(column).split('.')[1]}</th>
						% endfor
					% endif
				</tr>
			</thead>
			<tbody>
				% if metrics_pgm_query:
					% for each in metrics_pgm_query:
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
	
	<div class="container">
		<h4>Metrics Proton</h4>
		<table class="table table-hover table-striped" width="800">
			<thead>
				<tr>
					% if metrics_proton_query:
						% for column in metrics_proton_query[0].inspect():
							<th>${str(column).split('.')[1]}</th>
						% endfor
					% endif
				</tr>
			</thead>
			<tbody>
				% if metrics_proton_query:
					% for each in metrics_proton_query:
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
</div>