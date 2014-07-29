// shows and hides columns
function show_hide_columns(array_of_columns) {
	try {
		for ( var item in array_of_columns) {
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
		// This only happens if there is a session saved version of a renamed
		// column name.
	}
}

// returns array of shown and hidden columns to be saved in the session
function get_shown_columns() {
	var array_of_columns = global_columns_default;
	for ( var item in array_of_columns) {
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
	var array_of_columns = global_columns_default;
	for (var item in array_of_columns) {
		var checkbox = document.getElementById(item);
		if (checkbox.checked) {
			array_of_columns[item] = "true";
		} else {
			array_of_columns[item] = "false";
		}
	}

	document.getElementById("show_hide").value = JSON.stringify(array_of_columns);

	for (var item in numeric_filters_obj) {
		var element = document.getElementById(item + "_csv");
		var number = item.replace( /^\D+/g, '');
		element.value = numeric_filters_obj[item][0];
		document.getElementById("min_number" + number + "_csv").value = numeric_filters_obj[item][1];
		document.getElementById("max_number" + number + "_csv").value = numeric_filters_obj[item][2];
	}

	for (var item in categorical_filters_obj) {
		var element = document.getElementById(item + "_csv");
		element.value = categorical_filters_obj[item];
	}
}

// show or hide all columns at once
function all_columns(show) {
	if (show) {
		var array_of_columns = global_columns_default;
		show_hide_columns(array_of_columns);
	} else {
		var array_of_columns = global_columns_false;
		show_hide_columns(array_of_columns);
	}
}

// adds new numeric filter parameters to the filter options
// also adds new hidden inputs to csv support
function add_new_filter() {
	var label = document.createElement('h5');
	label.innerHTML = " Metric Type ";
	label.className = "pull-left control-label label_spacing"

	var new_filter = document.createElement('div');
	new_filter.className = "form-group some_space_below";
	new_filter.id = "extra_filter" + filter_id

	new_filter.appendChild(label);
	new_filter.innterHTML = " ";

	var new_filter_select = document.createElement('select');
	new_filter_select.className = "form-control";
	new_filter_select.name = "metric_type_filter" + filter_id;
	new_filter_select.id = "metric_type_filter" + filter_id;

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
	new_filter_input1.name = "min_number" + filter_id;
	new_filter_input1.id = new_filter_input1.name;
	new_filter_input1.placeholder = "Lower Bound";

	var new_filter_input2 = document.createElement('input');
	new_filter_input2.type = "text";
	new_filter_input2.className = "form-control";
	new_filter_input2.style.width = "6em";
	new_filter_input2.name = "max_number" + filter_id;
	new_filter_input2.id = new_filter_input2.name;
	new_filter_input2.placeholder = "Upper Bound";
	
	var delete_filter_btn = document.createElement('span');
	delete_filter_btn.innerHTML = '<button type="button" class="btn btn-info btn-mini" onclick="remove_filter(\'extra_filter' + filter_id + '\')"><span class="icon-white icon-minus"></span></button>';

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
	input_metric_type.name = "metric_type_filter" + filter_id;
	input_metric_type.id = "metric_type_filter" + filter_id + "_csv";
	
	var input_metric_min = document.createElement('input');
	input_metric_min.type = "hidden";
	input_metric_min.name = "min_number" + filter_id;
	input_metric_min.id = "min_number" + filter_id + "_csv";
	
	var input_metric_max = document.createElement('input');
	input_metric_max.type = "hidden";
	input_metric_max.name = "max_number" + filter_id;
	input_metric_max.id = "max_number" + filter_id + "_csv";

	csv_form.appendChild(input_metric_type);
	csv_form.appendChild(input_metric_min);
	csv_form.appendChild(input_metric_max);

	filter_id++;
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

	filter_id--;
}

// sets hidden input to value of how many extra dynamic numeric filter parameters the user created
function get_extra_filter_number() {
	document.getElementById('extra_filter_number').value = filter_id - 1;
}

// fills all the numeric and categorical filter options
function fill_filters() {
	try {
		for (var item in numeric_filters_obj) {
			var element = document.getElementById(item);
			var options = element.getElementsByTagName('option');
			var inputs = element.parentNode.getElementsByTagName('input');

			for (var i = 0; i < options.length; i++) {
				if (options[i].value == numeric_filters_obj[item][0]) {
					options[i].selected = true;
					inputs[0].value = numeric_filters_obj[item][1];
					inputs[1].value = numeric_filters_obj[item][2];
					break;
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