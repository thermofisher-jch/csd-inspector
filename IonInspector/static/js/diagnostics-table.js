var diagnosticsTableApp = {
    resource: null,
    activeAjaxRequest: null,
    activeTimeout: null,
    statusClasses: {
        "Unexecuted": "",
        "Executing": "",
        "Alert": "label-important",
        "Info": "label-info",
        "Warning": "label-warning",
        "OK": "label-success",
        "NA": "",
        "Failed": "label-inverse"
    },
    filterDiagnostics: function (diagnostics) {
        return diagnostics.filter(function (diagnostic) {
            return diagnostic.category === this.selectedCategoryChoice;
        }.bind(this));
    },
    computeDisplayValues: function (diagnostics) {
        for (var i = 0; i < diagnostics.length; i++) {
            //Add spaces to name
            diagnostics[i].display_name = diagnostics[i].name.replace(/_/g, " ");
            //Compute status label class
            diagnostics[i].status_class = "";
            if (this.statusClasses.hasOwnProperty(diagnostics[i].status)) {
                diagnostics[i].status_class = this.statusClasses[diagnostics[i].status];
            }
            //Format date
            diagnostics[i].display_start_execute = "";
            if (diagnostics[i].start_execute) {
                //Use the built in very fast Date.parse instead of moment parsing
                diagnostics[i].display_start_execute = moment(Date.parse(diagnostics[i].start_execute)).format("MMM D, YYYY, h:mm a");
            }
        }
    },
    updateDiagnostics: function () {
        var diagnostics = this.resource.diagnostics.slice();
        diagnostics = this.filterDiagnostics(diagnostics);
        this.computeDisplayValues(diagnostics);
        Vue.set(this.vue, "diagnostics", diagnostics);

        //enable or disable the category chooser
        var previousCategory = null;
        for (var i = 0; i < this.resource.diagnostics.length; i++) {
            if (!previousCategory) {
                previousCategory = this.resource.diagnostics[i].category;
            }
            else if (this.resource.diagnostics[i].category !== previousCategory) {
                $("#category-chooser").show();
                break;
            }
        }

    },
    testsStillRunning: function (diagnostics) {
        for (var i = 0; i < diagnostics.length; i++) {
            if (diagnostics[i].status === "Executing" || diagnostics[i].status === "Unexecuted") {
                return true
            }
        }
        return false
    },
    setUnexecuted: function () {
        var diagnostics = this.resource.diagnostics.slice();
        for (var i = 0; i < diagnostics.length; i++) {
            diagnostics[i].status = "Unexecuted";
            diagnostics[i].details = "";
            diagnostics[i].start_execute = "";
            diagnostics[i].html = "";
            diagnostics[i].readme = "";
        }
        this.computeDisplayValues(diagnostics);
        this.resource.diagnostics = diagnostics;
    },
    update: function (callback) {
        if (this.activeAjaxRequest) {
            this.activeAjaxRequest.abort();
        }
        if (this.activeTimeout) {
            clearTimeout(this.activeTimeout);
        }
        this.activeAjaxRequest = $.ajax({
            url: "/api/v1/Archive/" + this.resource.id + "/",
            dataType: "json",
            success: function (response) {
                this.resource.diagnostics = response.diagnostics;
                this.updateDiagnostics();

                Vue.set(this.vue, "results", response.results);

                if (this.testsStillRunning(response.diagnostics)) {
                    this.activeTimeout = setTimeout(this.update.bind(this), 1000);
                }
                if (typeof callback === 'function') {
                    return callback();
                }
            }.bind(this)
        })
    },
    init: function (selector, initialResource, categoryChoices, isSequencer) {
        this.resource = initialResource;
        this.selectedCategoryChoice = isSequencer ? "SEQ" : "PRE";

        //events
        $("#category-chooser > button").click(function (event) {
            this.selectedCategoryChoice = $(event.target).attr("data-category");
            this.updateDiagnostics();
        }.bind(this));

        this.vue = new Vue({
            el: selector,
            data: {
                archiveId: this.resource.id,
                diagnostics: [],
                results: {}
            }
        });
        this.updateDiagnostics();
        this.update();
    }
};
