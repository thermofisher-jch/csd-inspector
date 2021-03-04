var reportEditorApp = {
    archiveId: null,
    archiveTypes: null,
    elements: {
        editButton: $("#archive-edit"),
        archiveIdentifier: $("#archive-identifier"),
        archiveSite: $("#archive-site"),
        archiveType: $("#archive-type"),
        archiveSummary: $("#archive-summary"),
        archiveFailureMode: $("#archive-failure-mode"),
        archiveIsBaseline: $("#archive-is-baseline"),
        archiveTaser: $("#archive-taser"),
    },
    init: function (archiveId, archiveTypes, initialBaseline) {
        this.archiveId = archiveId;
        this.archiveTypes = archiveTypes;
        this.elements.archiveIsBaseline.addClass("label");
        if (initialBaseline) {
            this.elements.archiveIsBaseline.addClass("label-success");
            this.elements.archiveIsBaseline.data('value', 'true');
            this.elements.archiveIsBaseline.text("Baseline Run");
        } else {
            this.elements.archiveIsBaseline.addClass("label-warning");
            this.elements.archiveIsBaseline.data('value', 'false');
            this.elements.archiveIsBaseline.text("Issue Run");
        }
        this.elements.editButton.click(
            this.enable.bind(this));
    },
    enable: function () {
        // Switch button to save button
        this.elements.editButton.html("<i class='icon-ok icon-white'></i> Save");
        this.elements.editButton.addClass("btn-primary");
        this.elements.editButton.off('click');
        this.elements.editButton.click(this.save.bind(this));

        // Switch text to inputs
        [{
            element: this.elements.archiveIdentifier,
            fontSize: 25,
            type: "text",
            placeholder: "No Label"
        }, {
            element: this.elements.archiveSite,
            fontSize: 25,
            type: "text",
            placeholder: "No Site"
        }, {
            element: this.elements.archiveSummary,
            fontSize: 14,
            type: "text",
            placeholder: "No Summary"
        }, {
            element: this.elements.archiveFailureMode,
            fontSize: 14,
            type: "text",
            placeholder: "No Failure Mode"
        }, {
            element: this.elements.archiveTaser,
            fontSize: 14,
            type: "number",
            placeholder: "No TASER #"
        }].map(function (item) {
            var value = item.element.text();
            item.element.html("").append($("<input/>", {
                type: item.type,
                value: item.element.data("value"),
                placeholder: item.placeholder,
                style: "font-size:" + item.fontSize + "px;" +
                "height: auto;" +
                "vertical-align: top;" +
                "margin-bottom: 0px;" +
                "box-sizing: border-box;" +
                "width: 100%;"
            }))
        }.bind(this));

        //Switch toggle badge to checkbox widgets
        this.elements.archiveIsBaseline.removeClass("label");
        let initialBaseline = (this.elements.archiveIsBaseline.data('value') === 'true');
        if (initialBaseline) {
            this.elements.archiveIsBaseline.removeClass("label-success");
        } else {
            this.elements.archiveIsBaseline.removeClass("label-warning");
        }
        this.elements.archiveIsBaseline.text("");
        var checkbox = this.elements.archiveIsBaseline.html($("<input/>", {
            type: "checkbox",
            checked: initialBaseline,
            style: "float: right;"
            })
        );
        checkbox.wrapInner(
            $("<label>Is Baseline Run:&nbsp;</label>")
        );


        // Switch machine type to select with option list.
        var archiveTypeSelect = $("<select/>", {
            type: "text",
            dir: "rtl",
            style: "font-size: 25px;" +
            "height: auto;" +
            "vertical-align: top;" +
            "margin-bottom: 0px;" +
            "height: 40px;" +
            "border-radius: 4px;" +
            "box-shadow: inset 0 1px 1px rgba(0, 0, 0, 0.075);" +
            "box-sizing: border-box;" +
            "width: 100%;"
        });
        this.archiveTypes.map(function (type) {
            archiveTypeSelect.append($("<option/>", {
                text: type.name,
                value: type.value,
                selected: this.elements.archiveType.data("value") == type.value
            }));
        }.bind(this));
        this.elements.archiveType.html("").append(archiveTypeSelect);

    },
    save: function () {
        $.ajax({
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            },
            url: '/api/v1/Archive/' + this.archiveId + '/',
            type: 'PATCH',
            data: JSON.stringify({
                identifier: this.elements.archiveIdentifier.find("input").val(),
                site: this.elements.archiveSite.find("input").val(),
                archive_type: this.elements.archiveType.find("select").val(),
                summary: this.elements.archiveSummary.find("input").val(),
                failure_mode: this.elements.archiveFailureMode.find("input").val(),
                taser_ticket_number: this.elements.archiveTaser.find("input").val() || null,
                is_baseline: this.elements.archiveIsBaseline.find("input")[0].checked
            }),
            success: function (response, textStatus, jqXhr) {
            },
            error: function (jqXHR, textStatus, errorThrown) {
                alert("Error saving changes!");
            },
            complete: function () {
                window.location = "";
            }
        });
    }
};