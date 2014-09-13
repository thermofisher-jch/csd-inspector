// shows and hides columns
function show_hide_columns(array_of_columns) {
	try {
		for (var item in array_of_columns) {
			if (array_of_columns[item] == "true") {
				var elements = document.getElementsByClassName(item);
				for (i = 0; i < elements.length; i++) {
					elements[i].style.display = 'table-cell';
				}
				document.getElementById(item).checked = true;
			} else {
				var elements = document.getElementsByClassName(item);
				for (i = 0; i < elements.length; i++) {
					elements[i].style.display = 'none';
				}
				document.getElementById(item).checked = false;
			}
		}
	} catch (err) {
		//Some error
	}
}

// returns array of shown and hidden columns to be saved in the session
function get_shown_columns() {
	var array_of_columns = {};
	for ( var item in global_columns_default) {
		var checkbox = document.getElementById(item);
		if (checkbox.checked) {
			array_of_columns[item] = "true";
		} else {
			array_of_columns[item] = "false";
		}
	}

	return array_of_columns;
}

// sets proper values for the hidden inputs used for csv support
function get_shown_columns_csv() {
	var arguments = {};
	for (var item in global_columns_default) {
		var checkbox = document.getElementById(item);
		if (checkbox.checked) {
			arguments[item] = "true";
		} else {
			arguments[item] = "false";
		}
	}

	return JSON.stringify(arguments);
}

function get_csv_params() {
	var filter_id_re = /\d+/

	var csv_form = document.createElement('form');
	csv_form.action = '/trace/request_csv';

	if (filter_id_re.test(document.getElementById('filterid').value)) {
		var input = document.createElement('input');
		input.name = "filterid";
		input.value = document.getElementById('filterid').value;

		csv_form.appendChild(input);
	} else {
		var numeric_filter_re = /metric_type_filter\d+/
		var all_selects = document.getElementsByTagName('select');

		for (var i = 0; i < all_selects.length; i++) {
			var input = document.createElement('select');
			input.name = all_selects[i].name;

			var option = document.createElement('option');
			option.value = document.getElementById(input.name).options[document.getElementById(input.name).options.selectedIndex].value;

			if (numeric_filter_re.test(all_selects[i].id)) {
				var number = all_selects[i].id.replace(/^\D+/g, '');
				var min = document.createElement('input');
				min.type = 'text';
				min.name = 'min_number' + number;
				min.value = document.getElementById('min_number' + number).value;

				var max = document.createElement('input');
				max.type = 'text';
				max.name = 'max_number' + number;
				max.value = document.getElementById('max_number' + number).value;

				input.appendChild(option);
				csv_form.appendChild(input);
				csv_form.appendChild(min);
				csv_form.appendChild(max);
			} else {
				input.appendChild(option);
				csv_form.appendChild(input);
			}
		}
	}

	var input = document.createElement('input');
	input.type = 'hidden';
	input.name = 'show_hide';
	input.value = get_shown_columns_csv();
	csv_form.appendChild(input);

	return csv_form
}

// show or hide all columns at once
function all_columns(show) {
	if (show) {
		show_hide_columns(global_columns_default);
	} else {
		show_hide_columns(global_columns_false);
	}
}

// adds new numeric filter parameters to the filter options
// also adds new hidden inputs to csv support
function add_new_filter() {
	var label = document.createElement('h5');
	label.innerHTML = " Metric Type ";
	label.className = "pull-left control-label label_spacing"

	var new_filter = document.createElement('div');
	new_filter.className = "some_space_below";
	new_filter.id = "extra_filter" + extra_filters

	new_filter.appendChild(label);
	new_filter.innterHTML = " ";

	var new_filter_select = document.createElement('select');
	new_filter_select.className = "form-control";
	new_filter_select.name = "metric_type_filter" + extra_filters;
	new_filter_select.id = "metric_type_filter" + extra_filters;

	var new_filter_select_option0 = document.createElement('option');
	new_filter_select_option0.value = "";
	new_filter_select.appendChild(new_filter_select_option0);

	for ( var item in global_columns) {
		var new_filter_select_option = document.createElement('option');
		new_filter_select_option.value = global_columns[item][0];
		new_filter_select_option.innerHTML = global_columns[item][0];
		new_filter_select_option.className = "filter_option";

		new_filter_select.appendChild(new_filter_select_option);
	}

	new_filter.appendChild(new_filter_select);
	new_filter.innerHTML += " ";

	var new_filter_input1 = document.createElement('input');
	new_filter_input1.type = "text";
	new_filter_input1.className = "form-control";
	new_filter_input1.style.width = "6em";
	new_filter_input1.name = "min_number" + extra_filters;
	new_filter_input1.id = new_filter_input1.name;
	new_filter_input1.placeholder = "Lower Bound";

	var new_filter_input2 = document.createElement('input');
	new_filter_input2.type = "text";
	new_filter_input2.className = "form-control";
	new_filter_input2.style.width = "6em";
	new_filter_input2.name = "max_number" + extra_filters;
	new_filter_input2.id = new_filter_input2.name;
	new_filter_input2.placeholder = "Upper Bound";

	var delete_filter_btn = document.createElement('span');
	delete_filter_btn.innerHTML = '<button type="button" class="btn btn-info btn-mini" onclick="remove_filter(\'extra_filter' + extra_filters + '\')"><span class="icon-white icon-minus"></span></button>';

	new_filter.appendChild(new_filter_input1);
	new_filter.innerHTML += " ";
	new_filter.appendChild(new_filter_input2);
	new_filter.innerHTML += " ";
	new_filter.appendChild(delete_filter_btn);

	document.getElementById("dynamic_filters").appendChild(new_filter);

	// csv support hidden inputs
	var csv_form = document.getElementById('csv_filter_extras');
	var input_metric_type = document.createElement('input');
	input_metric_type.type = "hidden";
	input_metric_type.name = "metric_type_filter" + extra_filters;
	input_metric_type.id = "metric_type_filter" + extra_filters + "_csv";

	var input_metric_min = document.createElement('input');
	input_metric_min.type = "hidden";
	input_metric_min.name = "min_number" + extra_filters;
	input_metric_min.id = "min_number" + extra_filters + "_csv";

	var input_metric_max = document.createElement('input');
	input_metric_max.type = "hidden";
	input_metric_max.name = "max_number" + extra_filters;
	input_metric_max.id = "max_number" + extra_filters + "_csv";

	csv_form.appendChild(input_metric_type);
	csv_form.appendChild(input_metric_min);
	csv_form.appendChild(input_metric_max);

	extra_filters++;
}

// sets filter options
function add_filters_onload(number) {
	for (var i = 0; i < number; i++) {
		add_new_filter();
	}
	fill_filters();
}

// removes a numeric filter parameter
function remove_filter(id) {
	var child = document.getElementById(id);
	child.parentNode.removeChild(child);

	extra_filters--;
}

// sets hidden input to value of how many extra dynamic numeric filter parameters the user created
function get_extra_filter_number() {
	document.getElementById('extra_filters_template').value = extra_filters - 1;
	return (extra_filters - 1)
}

function has_filters() {
	try {
		var all_selects = document.getElementsByTagName('select');
		for (var i = 0; i < all_selects.length; i++) {
			if (all_selects[i].options.selectedIndex != 0) {
				return true;
			}
		}

		return false;

	} catch(err) {
		console.log(err);
	}
}

function clear_filters() {
	try {
		var all_selects = document.getElementsByTagName('select');
		for (var i = 0; i < all_selects.length; i++) {
			all_selects[i].options.selectedIndex = 0;
		}

		var all_inputs = document.getElementsByTagName('input');
		for (var i = 0; i < all_inputs.length; i++) {
			if (all_inputs[i].type == "text" && all_inputs[i].className == "form-control") {
				all_inputs[i].value = "";
			}
		}

		for (var i = get_extra_filter_number(); i > 0; i--) {
			remove_filter('extra_filter' + i);
		}

	} catch(err) {
		console.log(err);
	}
}

function apply_saved_filter(id) {
	var apply_filter_form = document.createElement('form');
	apply_filter_form.action = '/trace/apply_filter';

	var extra_input1 = document.createElement('input');
	extra_input1.type = 'hidden';
	extra_input1.name = 'filterid';
	extra_input1.value = id;
	apply_filter_form.appendChild(extra_input1);

	var extra_input2 = document.createElement('input');
	extra_input2.type = 'hidden';
	extra_input2.name = 'metric_type';
	extra_input2.value = document.getElementById('metric_type_input').value;
	apply_filter_form.appendChild(extra_input2);

	apply_filter_form.submit();
}

function save_filters() {
	try {
		var current_filters = document.getElementById('filter_form');

		var extra_input1 = document.createElement('input');
		extra_input1.type = 'hidden';
		extra_input1.name = 'saved_filter_name';
		extra_input1.value = document.getElementById('saved_filter_name').value;
		current_filters.appendChild(extra_input1);

		var extra_input2 = document.createElement('input');
		extra_input2.type = 'hidden';
		extra_input2.name = 'metric_type';
		extra_input2.value = document.getElementById('metric_type_input').value;
		current_filters.appendChild(extra_input2);

		current_filters.action = '/trace/save_filter';
		current_filters.submit();
	} catch(err) {
		console.log(err);
	}
}

// fills all the numeric and categorical filter options
function fill_filters() {
	try {
		for (var item in numeric_filters_obj) {
			if (item != 'extra_filters') {
				var element = document.getElementById(item);
				var options = element.getElementsByTagName('option');
				var inputs = element.parentNode.getElementsByTagName('input');

				for (var i = 0; i < options.length; i++) {
					if (options[i].value == numeric_filters_obj[item]['type']) {
						options[i].selected = true;
						inputs[0].value = numeric_filters_obj[item]['min'];
						inputs[1].value = numeric_filters_obj[item]['max'];
						break;
					}
				}
			}
		}
	} catch(err) {
		//error
	}

	try {
		for (var item in categorical_filters_obj) {
			var element = document.getElementById(item);
			var options = element.getElementsByTagName('option');

			for (var i = 0; i < options.length; i++) {
				if (options[i].value == categorical_filters_obj[item]) {
					options[i].selected = true;
					break;
				}
			}
		}
	} catch(err) {
		//error
	}
}

/*
 * Fills in report components as they are finished in celery
 */
function update_report(report, boxplot, histogram) {
	/*
	 * Set local copies of variables to prevent updating
	 * an already updated component
	 */
	if(report_status != report.status) {
		report_status = report.status;

		if (report_status == 'Statistics Available' || report_status == 'Done') {
			for(var stat in report.statistics) {
				document.getElementById(stat).innerHTML = report.statistics[stat];
			}
		}
	}

	if(boxplot_status != boxplot.status) {
		boxplot_status = boxplot.status;

		if(boxplot_status == "Done") {
			document.getElementById('boxplot_img').src = static_url + "/" + boxplot.src;
			$('#boxplot_custom_axes').css('display', 'table');
			$('#boxplot_title').val(boxplot.graph_details.title);
			$('#boxplot_x_axis_label').val(boxplot.graph_details.label_x);
			$('#boxplot_y_axis_label').val(boxplot.graph_details.label_y);
			$('#boxplot_x_axis_min').val(boxplot.graph_details.x_axis_min);
			$('#boxplot_x_axis_max').val(boxplot.graph_details.x_axis_max);
			$('#boxplot_y_axis_min').val(boxplot.graph_details.y_axis_min);
			$('#boxplot_y_axis_max').val(boxplot.graph_details.y_axis_max);
		}
	}

	if(histogram_status != histogram.status) {
		histogram_status = histogram.status;

		if(histogram_status == "Done") {
			document.getElementById('histogram_img').src = static_url + "/" + histogram.src;
			$('#histogram_custom_axes').css('display', 'table');
			$('#histogram_title').val(histogram.graph_details.title);
			$('#histogram_x_axis_label').val(histogram.graph_details.label_x);
			$('#histogram_y_axis_label').val(histogram.graph_details.label_y);
			$('#histogram_x_axis_min').val(histogram.graph_details.x_axis_min);
			$('#histogram_x_axis_max').val(histogram.graph_details.x_axis_max);
			$('#histogram_y_axis_min').val(histogram.graph_details.y_axis_min);
			$('#histogram_y_axis_max').val(histogram.graph_details.y_axis_max);
		}
	}

	return (report.status == "Done" && boxplot.status == "Done" && histogram.status == "Done");
}

function sort_by(thing) {
	var input = document.getElementsByName(thing.id);
	input[0].value = "desc";

	input[0].parentNode.submit()
}